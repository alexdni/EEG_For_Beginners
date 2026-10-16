---
title: "About this site"
summary: "How the course site is generated from the Markdown, and how to deploy it."
---

# Course site

A dependency-light static site generated from the repo's Markdown. Markdown is the source of truth; nothing in `site/dist/` is edited by hand.

```bash
pip install -r site/requirements.txt
python site/build.py            # → site/dist/
python site/build.py --serve    # build and serve on http://localhost:8000
```

## What the builder does

- Renders `README.md`, `modules/*.md` and the reference pages with the same relative layout, rewriting `.md` links to `.html`.
- Turns GitHub alerts (`> [!NOTE]`) into callouts, ```` ```mermaid ```` fences into diagrams, and adds copy buttons, heading anchors, a per-page table of contents, prev/next links and a client-side search index.
- Wraps the hand-written interactive pages in `pages/` (Signal Lab, electrode map) in the same chrome.
- Copies `assets/`, `data/samples/` and `code/` so figures, EDF downloads and lab scripts work on the deployed site.

## Layout

```
site/
  build.py            the generator
  templates/page.html page shell
  pages/              interactive pages (HTML fragment; head above <!-- body -->)
  static/             site CSS/JS; static/lab/ holds the EDF reader, DSP and Signal Lab
  dist/               build output (git-ignored)
```

## Deploying

The site is fully static. `vercel.json` at the repo root builds it on Vercel (`python3 site/build.py`, output `site/dist`). For a subdomain such as `eeg.alexni.ai`, add the domain to the Vercel project and point a CNAME at Vercel. Any static host works: upload `site/dist/`.
