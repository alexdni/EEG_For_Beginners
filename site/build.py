"""Build the static course site from the repo's Markdown.

    python site/build.py            # writes site/dist/
    python site/build.py --serve    # build, then serve on http://localhost:8000

Markdown stays the single source: every page under modules/ plus the top-level pages
is rendered into the same relative layout, so links between .md files keep working
once they are rewritten to .html. Figures, sample EDFs and lab scripts are copied
alongside so the site works offline and on any static host.
"""
import argparse
import html
import os
import json
import re
import shutil
from pathlib import Path

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DIST = SITE / "dist"
SITE_NAME = "EEG for Beginners"

# Top-level pages in sidebar order; modules are discovered from modules/*.md.
PAGES = {
    "README.md": "index.html",
    "schedule.md": "schedule.html",
    "checkpoints.md": "checkpoints.html",
    "resources.md": "resources.html",
    "glossary.md": "glossary.html",
    "notes-template.md": "notes-template.html",
    "open-source.md": "open-source.html",
    "project-branches.md": "project-branches.html",
    "data/README.md": "data/index.html",
    "site/README.md": "about-this-site.html",
    "AUTHORING.md": "authoring.html",
}

# Hand-written interactive pages: (source fragment, output path, title, summary)
INTERACTIVE = [
    ("pages/signal-lab.html", "lab/signal-lab.html", "Signal Lab",
     "Open the course EDFs in your browser: scroll, filter, re-reference and read the spectrum."),
    ("pages/electrode-map.html", "lab/electrode-map.html", "Electrode map",
     "An interactive 10-20 head map with a naming quiz."),
]

NAV_GROUPS = [
    ("Start", lambda m: m == 0),
    ("Week 1 · What EEG is", lambda m: 1 <= m <= 6),
    ("Week 2 · Working with the signal", lambda m: 7 <= m <= 12),
    ("Week 2 · Feedback loops", lambda m: m >= 13),
]

ALERTS = {"NOTE": "Note", "TIP": "Tip", "IMPORTANT": "Important", "WARNING": "Warning", "CAUTION": "Caution"}


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def slugify(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s).strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"[\s_]+", "-", s).strip("-")


def highlight_code(code: str, lang: str, _attrs) -> str:
    if lang == "mermaid":
        return f'<pre class="mermaid">{html.escape(code)}</pre>'
    try:
        lexer = get_lexer_by_name(lang or "text")
    except ClassNotFound:
        lexer = get_lexer_by_name("text")
    return highlight(code, lexer, HtmlFormatter(nowrap=True))


def make_md() -> MarkdownIt:
    md = (
        MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False, "highlight": highlight_code})
        .enable("table")
        .enable("strikethrough")
        .use(front_matter_plugin)
        .use(anchors_plugin, min_level=2, max_level=3, slug_func=slugify, permalink=True,
             permalinkSymbol="#", permalinkBefore=False)
    )

    default_fence = md.renderer.rules["fence"]

    def fence(tokens, idx, options, env):
        tok = tokens[idx]
        lang = tok.info.strip().split()[0] if tok.info.strip() else ""
        if lang == "mermaid":
            return highlight_code(tok.content, "mermaid", None)
        body = highlight_code(tok.content, lang, None)
        label = html.escape(lang or "text")
        return (f'<div class="code"><div class="code-bar"><span>{label}</span>'
                f'<button class="copy" type="button" aria-label="Copy code">Copy</button></div>'
                f'<pre><code class="language-{label}">{body}</code></pre></div>')

    md.renderer.rules["fence"] = fence
    del default_fence

    def blockquote_open(tokens, idx, options, env):
        kind = tokens[idx].meta.get("alert")
        if kind:
            return (f'<aside class="callout callout-{kind.lower()}"><p class="callout-title">'
                    f"{ALERTS[kind]}</p>\n")
        return "<blockquote>\n"

    def blockquote_close(tokens, idx, options, env):
        return "</aside>\n" if tokens[idx].meta.get("alert") else "</blockquote>\n"

    md.renderer.rules["blockquote_open"] = blockquote_open
    md.renderer.rules["blockquote_close"] = blockquote_close

    def table_open(tokens, idx, options, env):
        return '<div class="table-wrap"><table>\n'

    def table_close(tokens, idx, options, env):
        return "</table></div>\n"

    md.renderer.rules["table_open"] = table_open
    md.renderer.rules["table_close"] = table_close
    return md


def mark_alerts(tokens):
    """Turn GitHub '> [!NOTE]' blockquotes into callouts by tagging the token pair."""
    stack = []
    for i, tok in enumerate(tokens):
        if tok.type == "blockquote_open":
            stack.append(tok)
            if i + 2 < len(tokens) and tokens[i + 1].type == "paragraph_open" and tokens[i + 2].type == "inline":
                inline = tokens[i + 2]
                m = re.match(r"\[!(\w+)\]\s*", inline.content)
                if m and m.group(1).upper() in ALERTS:
                    tok.meta["alert"] = m.group(1).upper()
                    inline.content = inline.content[m.end():]
                    first = inline.children[0] if inline.children else None
                    if first is not None and first.type == "text":
                        first.content = re.sub(r"^\[!\w+\]\s*", "", first.content)
                        # drop the softbreak that followed the marker line
                        if not first.content and len(inline.children) > 1 and inline.children[1].type == "softbreak":
                            inline.children = inline.children[2:]
                    if not inline.content.strip():
                        tokens[i + 1].hidden = True
        elif tok.type == "blockquote_close" and stack:
            opener = stack.pop()
            tok.meta["alert"] = opener.meta.get("alert")


def rewrite_links(tokens, src_rel: Path):
    """Point .md links at their .html pages; leave external links alone."""

    here = out_path_for(src_rel)

    def fix(url: str) -> str:
        if re.match(r"^[a-z]+:", url) or url.startswith("#"):
            return url
        path, _, frag = url.partition("#")
        if path.endswith(".md"):
            target = out_path_for(normalise(src_rel.parent / path))
            path = os.path.relpath(target, os.path.dirname(here) or ".")
        return path + ("#" + frag if frag else "")

    for tok in tokens:
        for child in tok.children or []:
            if child.type == "link_open":
                href = child.attrGet("href")
                if href:
                    child.attrSet("href", fix(href))
                    if re.match(r"^https?:", href):
                        child.attrSet("target", "_blank")
                        child.attrSet("rel", "noopener")
            elif child.type == "image":
                child.attrSet("loading", "lazy")


def normalise(p: Path) -> Path:
    parts = []
    for part in p.parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)
    return Path(*parts) if parts else Path(".")


def out_path_for(src_rel: Path) -> str:
    key = str(src_rel)
    if key in PAGES:
        return PAGES[key]
    return str(src_rel.with_suffix(".html"))


def relpath(target: str, from_page: str) -> str:
    depth = len(Path(from_page).parts) - 1
    return "../" * depth + target


def render_page(md: MarkdownIt, src: Path):
    text = src.read_text(encoding="utf-8")
    tokens = md.parse(text)
    meta = {}
    if tokens and tokens[0].type == "front_matter":
        meta = yaml.safe_load(tokens[0].content) or {}
    src_rel = src.relative_to(ROOT)
    mark_alerts(tokens)
    rewrite_links(tokens, src_rel)
    toc = []
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.tag in ("h2", "h3"):
            title = tokens[i + 1].content
            toc.append((tok.tag, tok.attrGet("id"), re.sub(r"[`*_]", "", title)))
    body = md.renderer.render(tokens, md.options, {})
    # The first H1 becomes the page header, so drop it from the body.
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>\s*", body, flags=re.S)
    if h1:
        meta.setdefault("title", re.sub(r"<[^>]+>", "", h1.group(1)).strip())
        body = body[: h1.start()] + body[h1.end():]
    plain = re.sub(r"<[^>]+>", " ", body)
    plain = re.sub(r"\s+", " ", html.unescape(plain)).strip()
    return meta, body, toc, plain


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def nav_html(entries, current_out):
    """entries: list of (group, [(out, label, number)])."""
    out = []
    for group, items in entries:
        out.append(f'<p class="nav-group">{html.escape(group)}</p><ul>')
        for target, label, number in items:
            href = relpath(target, current_out)
            cls = ' class="active" aria-current="page"' if target == current_out else ""
            num = f'<span class="nav-num">{number:02d}</span>' if isinstance(number, int) else ""
            out.append(f'<li><a href="{href}"{cls}>{num}<span>{html.escape(label)}</span></a></li>')
        out.append("</ul>")
    return "\n".join(out)


def toc_html(toc):
    if len(toc) < 2:
        return ""
    items = "".join(
        f'<li class="toc-{tag}"><a href="#{anchor}">{html.escape(title)}</a></li>' for tag, anchor, title in toc
    )
    return f'<nav class="toc" aria-label="On this page"><p>On this page</p><ul>{items}</ul></nav>'


def page_header(meta):
    bits = []
    if meta.get("module") is not None:
        bits.append(f'<span class="chip">Module {int(meta["module"]):02d}</span>')
    if meta.get("week"):
        bits.append(f'<span class="chip">Week {meta["week"]}</span>')
    if meta.get("session"):
        bits.append(f'<span class="chip">Session {meta["session"]}</span>')
    if meta.get("time"):
        bits.append(f'<span class="chip chip-time">{html.escape(str(meta["time"]))}</span>')
    chips = f'<div class="chips">{"".join(bits)}</div>' if bits else ""
    summary = f'<p class="lede">{html.escape(str(meta["summary"]))}</p>' if meta.get("summary") else ""
    return f'<header class="page-head">{chips}<h1>{html.escape(str(meta.get("title", "")))}</h1>{summary}</header>'


def pager(prev, nxt, current_out):
    def link(item, cls, label):
        if not item:
            return "<span></span>"
        target, title = item
        return (f'<a class="{cls}" href="{relpath(target, current_out)}"><small>{label}</small>'
                f"<span>{html.escape(title)}</span></a>")

    return f'<nav class="pager">{link(prev, "prev", "Previous")}{link(nxt, "next", "Next")}</nav>'


def layout(template, *, title, out, nav, header, body, toc, pager_html, extra_head="", extra_scripts="",
           body_class=""):
    base = relpath("", out)
    return (template
            .replace("{{title}}", html.escape(f"{title} · {SITE_NAME}" if title != SITE_NAME else SITE_NAME))
            .replace("{{base}}", base or "./")
            .replace("{{nav}}", nav)
            .replace("{{header}}", header)
            .replace("{{body}}", body)
            .replace("{{toc}}", toc)
            .replace("{{pager}}", pager_html)
            .replace("{{extra_head}}", extra_head)
            .replace("{{extra_scripts}}", extra_scripts)
            .replace("{{body_class}}", body_class))


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    md = make_md()
    template = (SITE / "templates" / "page.html").read_text(encoding="utf-8")

    pages = []  # dicts: src, out, meta, body, toc, plain
    for src_rel, out in PAGES.items():
        src = ROOT / src_rel
        if src.exists():
            meta, body, toc, plain = render_page(md, src)
            pages.append(dict(src=src, out=out, meta=meta, body=body, toc=toc, plain=plain))
    modules = []
    for src in sorted((ROOT / "modules").glob("*.md")):
        meta, body, toc, plain = render_page(md, src)
        num = meta.get("module")
        if num is None:
            m = re.match(r"(\d+)", src.stem)
            num = int(m.group(1)) if m else 99
        meta["module"] = int(num)
        modules.append(dict(src=src, out=f"modules/{src.stem}.html", meta=meta, body=body, toc=toc, plain=plain))
    modules.sort(key=lambda p: p["meta"]["module"])
    by_out = {p["out"]: p for p in pages}

    def short(p):
        return str(p["meta"].get("nav_title") or p["meta"].get("title") or p["out"])

    nav = [("Course", [("index.html", "Home", None)] +
            ([("schedule.html", "Two-week schedule", None)] if "schedule.html" in by_out else []))]
    for group, pred in NAV_GROUPS:
        items = [(p["out"], short(p), p["meta"]["module"]) for p in modules if pred(p["meta"]["module"])]
        if items:
            nav.append((group, items))
    nav.append(("Interactive", [(out, title, None) for _, out, title, _ in INTERACTIVE]))
    beyond = [(o, short(by_out[o]), None) for o in ("open-source.html", "project-branches.html") if o in by_out]
    if beyond:
        nav.append(("Beyond the course", beyond))
    ref = [(o, short(by_out[o]), None) for o in
           ("checkpoints.html", "resources.html", "glossary.html", "data/index.html", "notes-template.html")
           if o in by_out]
    nav.append(("Reference", ref))

    # reading order for prev/next: home, modules, then reference pages
    order = [p for p in pages if p["out"] == "index.html"] + modules + [
        by_out[o] for o in ("open-source.html", "project-branches.html",
                            "schedule.html", "checkpoints.html", "resources.html", "glossary.html",
                            "data/index.html", "notes-template.html", "about-this-site.html", "authoring.html")
        if o in by_out]
    search = []
    for k, p in enumerate(order):
        prev = order[k - 1] if k > 0 else None
        nxt = order[k + 1] if k + 1 < len(order) else None
        body = p["body"]
        header = page_header(p["meta"])
        home = p["out"] == "index.html"
        if home:
            header = hero(modules)
            body = (feature_cards() + '<span class="eyebrow">The modules</span><h2 class="section-title">'
                    'Sixteen modules, two weeks</h2>' + module_cards(modules, p["out"]) +
                    '<span class="eyebrow">About this course</span>' + body)
        title = str(p["meta"].get("title", SITE_NAME))
        doc = layout(
            template, title=title if not home else SITE_NAME, out=p["out"], body_class="home" if home else "",
            nav=nav_html(nav, p["out"]), header=header, body=body, toc="" if home else toc_html(p["toc"]),
            pager_html=pager((prev["out"], short(prev)) if prev else None,
                             (nxt["out"], short(nxt)) if nxt else None, p["out"]),
            extra_scripts=mermaid_script(body),
        )
        write(DIST / p["out"], doc)
        search.append({"t": title, "u": p["out"], "h": [t for _, _, t in p["toc"]], "x": p["plain"][:6000]})

    for frag, out, title, summary in INTERACTIVE:
        src = SITE / frag
        if not src.exists():
            continue
        text = src.read_text(encoding="utf-8")
        head, _, body = text.partition("<!-- body -->")
        doc = layout(template, title=title, out=out, nav=nav_html(nav, out),
                     header=page_header({"title": title, "summary": summary}), body=body, toc="",
                     pager_html="", extra_head=head.replace("{{base}}", relpath("", out) or "./"),
                     extra_scripts="", body_class="wide")

        write(DIST / out, doc)
        search.append({"t": title, "u": out, "h": [], "x": summary})

    write(DIST / "search-index.json", json.dumps(search, ensure_ascii=False))
    copy_tree(SITE / "static", DIST / "static")
    copy_tree(ROOT / "assets", DIST / "assets")
    copy_tree(ROOT / "data" / "samples", DIST / "data" / "samples")
    for py in (ROOT / "code").rglob("*.py"):
        if "__pycache__" not in py.parts:
            dest = DIST / py.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(py, dest)
    shutil.copy2(ROOT / "code" / "requirements.txt", DIST / "code" / "requirements.txt")
    write(DIST / "static" / "pygments.css", pygments_css())
    write(DIST / "404.html", layout(template, title="Not found", out="404.html", nav=nav_html(nav, "404.html"),
                                     header=page_header({"title": "Page not found"}),
                                     body='<p><a href="index.html">Back to the course home</a></p>',
                                     toc="", pager_html=""))
    print(f"built {len(order) + len(INTERACTIVE)} pages into {DIST.relative_to(ROOT)}")


def pygments_css():
    dark = HtmlFormatter(style="github-dark").get_style_defs(":root:not([data-theme=light]) .code pre")
    light = HtmlFormatter(style="friendly").get_style_defs(":root[data-theme=light] .code pre")
    return dark + "\n" + light


def module_cards(modules, current_out):
    cards = []
    for p in modules:
        m = p["meta"]
        href = relpath(p["out"], current_out)
        time = f'<span class="card-time">{html.escape(str(m["time"]))}</span>' if m.get("time") else ""
        week = f'Week {m["week"]}' if m.get("week") else "Start"
        cards.append(
            f'<a class="card" href="{href}"><span class="card-num">{m["module"]:02d}</span>'
            f'<span class="card-week">{week}</span><strong>{html.escape(str(m.get("title", "")))}</strong>'
            f'<span class="card-sum">{html.escape(str(m.get("summary", "")))}</span>{time}</a>')
    return f'<section class="cards" aria-label="Modules">{"".join(cards)}</section>'


def hero(modules):
    labs = [p for p in (ROOT / "code" / "labs").glob("*.py") if not p.name.startswith("_")]
    edfs = list((ROOT / "data" / "samples").glob("*.edf"))
    figs = list((ROOT / "assets" / "figures").glob("*.png"))
    stats = [(f"{len(modules)}", "modules, Markdown first"), (f"{len(edfs)}", "real EDF recordings"),
             (f"{len(labs)}", "runnable Python labs"), (f"{len(figs)}", "figures drawn from the data")]
    first = modules[0]["out"] if modules else "index.html"
    return (
        '<section class="hero">'
        '<span class="pill">EEG · Signal processing · Neurofeedback · HRV</span>'
        '<h1>EEG for Beginners<span>Two weeks, real signals.</span></h1>'
        '<p class="lede">From zero to <strong>reading a raw trace, telling brain from artifact, and running a '
        'basic analysis in Python</strong>. Every figure and exercise uses real recordings you can open in '
        'the browser or in MNE.</p>'
        f'<div class="cta"><a class="btn-primary" href="{first}">Start the course →</a>'
        '<a class="btn-ghost" href="lab/signal-lab.html">Open the Signal Lab</a>'
        '<a class="btn-ghost" href="schedule.html">Two-week schedule</a></div>'
        '<div class="stats">' + "".join(f'<div class="stat"><b>{n}</b><span>{html.escape(t)}</span></div>'
                                        for n, t in stats) + "</div></section>")


def feature_cards():
    items = [
        ("lab/signal-lab.html", "Interactive", "Signal Lab",
         "Open any course EDF, or your own, in the browser. Filter, re-reference, and read the spectrum live."),
        ("lab/electrode-map.html", "Interactive", "Electrode map",
         "The 10-20 system as a clickable head, with a naming quiz."),
        ("open-source.html", "Ecosystem", "Open-source projects",
         "EEGEdu, BrainFlow, EEG-ExPy, Brainstorm, OpenBCI docs and the lecture sets behind them."),
        ("project-branches.html", "After week 2", "Project branches",
         "Heart-brain coupling, ASR/ICA validation, and neurally controlled game design."),
    ]
    cards = "".join(
        f'<a class="card feature" href="{href}"><span class="card-num">{html.escape(kind)}</span>'
        f'<strong>{html.escape(title)}</strong><span class="card-sum">{html.escape(text)}</span></a>'
        for href, kind, title, text in items if (DIST / href).exists() or href.startswith("lab/")
        or (ROOT / href.replace(".html", ".md")).exists())
    return f'<section class="cards" aria-label="Highlights">{cards}</section>'


def mermaid_script(body):
    if 'class="mermaid"' not in body:
        return ""
    return ('<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.esm.min.mjs";'
            'const dark=document.documentElement.dataset.theme!=="light";'
            'mermaid.initialize({startOnLoad:true,theme:dark?"dark":"neutral",fontFamily:"Inter, system-ui, sans-serif",'
            'themeVariables:dark?{primaryColor:"#0c1a24",primaryBorderColor:"#22d3ee",primaryTextColor:"#e2e8f0",'
            'lineColor:"#22d3ee",secondaryColor:"#141029",tertiaryColor:"#0c1019",background:"transparent",clusterBkg:"#0a1220",clusterBorder:"#1e4e5a",edgeLabelBackground:"#0c1019"}:{}});</script>')


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_tree(src: Path, dst: Path):
    if src.exists():
        shutil.copytree(src, dst, dirs_exist_ok=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="serve site/dist on localhost after building")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    build()
    if args.serve:
        import functools
        import http.server

        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        print(f"serving on http://localhost:{args.port}")
        http.server.ThreadingHTTPServer(("", args.port), handler).serve_forever()
