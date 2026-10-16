// Site chrome: theme toggle, mobile nav, copy buttons, TOC highlighting, search.
(function () {
  const root = document.documentElement;
  const base = document.querySelector("main")?.dataset.base || "./";

  // theme
  document.querySelector(".theme-btn")?.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) { /* storage blocked */ }
    document.dispatchEvent(new CustomEvent("themechange"));
  });

  // background: slowly drifting EEG-like traces. Each path holds two identical periods,
  // so translating it by half its width loops seamlessly.
  const bg = document.querySelector(".bg-waves");
  if (bg) {
    const W = 1440, H = 620, NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${W * 2} ${H}`);
    svg.setAttribute("preserveAspectRatio", "none");
    let seed = 7;
    const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    for (let k = 0; k < 9; k++) {
      // integer cycles per period keep the wave continuous at the seam
      const comps = [[1 + Math.floor(rand() * 2), 26 + rand() * 30], [3 + Math.floor(rand() * 3), 8 + rand() * 10],
                     [18 + Math.floor(rand() * 10), 2 + rand() * 3.5], [41 + Math.floor(rand() * 8), 0.8 + rand() * 1.4]];
      const phase = comps.map(() => rand() * Math.PI * 2);
      const y0 = 40 + k * 58 + rand() * 20;
      let d = "";
      for (let x = 0; x <= W * 2; x += 6) {
        let y = y0;
        comps.forEach(([cyc, amp], i) => { y += amp * Math.sin((2 * Math.PI * cyc * x) / W + phase[i]); });
        d += (x ? " L " : "M ") + x + " " + y.toFixed(1);
      }
      const path = document.createElementNS(NS, "path");
      path.setAttribute("d", d);
      path.setAttribute("opacity", (0.10 + 0.20 * (1 - k / 9)).toFixed(3));
      path.setAttribute("class", "drift");
      path.style.animationDuration = `${90 + k * 22}s`;
      path.style.animationDelay = `${-rand() * 80}s`;
      if (k % 3 === 2) path.style.color = "var(--violet-glow)";
      svg.appendChild(path);
    }
    bg.appendChild(svg);
  }

  // mobile nav
  const menu = document.querySelector(".menu-btn");
  menu?.addEventListener("click", () => {
    const open = document.body.classList.toggle("nav-open");
    menu.setAttribute("aria-expanded", String(open));
  });
  document.querySelector(".content")?.addEventListener("click", () => {
    if (document.body.classList.contains("nav-open")) {
      document.body.classList.remove("nav-open");
      menu?.setAttribute("aria-expanded", "false");
    }
  });
  document.querySelector(".sidebar a.active")?.scrollIntoView({ block: "center" });

  // copy buttons
  document.querySelectorAll(".code .copy").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const code = btn.closest(".code").querySelector("pre").innerText;
      try {
        await navigator.clipboard.writeText(code);
        btn.textContent = "Copied";
        btn.classList.add("done");
        setTimeout(() => { btn.textContent = "Copy"; btn.classList.remove("done"); }, 1400);
      } catch (e) { btn.textContent = "Select & copy"; }
    });
  });

  // TOC scrollspy
  const links = [...document.querySelectorAll(".toc a")];
  if (links.length) {
    const targets = links.map((a) => document.getElementById(decodeURIComponent(a.hash.slice(1)))).filter(Boolean);
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          links.forEach((a) => a.classList.toggle("on", a.hash.slice(1) === e.target.id));
        }
      });
    }, { rootMargin: "-80px 0px -70% 0px" });
    targets.forEach((t) => obs.observe(t));
  }

  // search
  const input = document.getElementById("search");
  const list = document.getElementById("search-results");
  let index = null;
  let active = -1;
  async function load() {
    if (index) return index;
    try { index = await (await fetch(base + "search-index.json")).json(); } catch (e) { index = []; }
    return index;
  }
  function snippet(text, q) {
    const i = text.toLowerCase().indexOf(q);
    if (i < 0) return text.slice(0, 110) + "…";
    const s = Math.max(0, i - 45);
    return (s ? "…" : "") + text.slice(s, i + 75) + "…";
  }
  function esc(s) { return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  async function run() {
    const q = input.value.trim().toLowerCase();
    if (q.length < 2) { list.hidden = true; return; }
    const terms = q.split(/\s+/);
    const docs = await load();
    const hits = docs.map((d) => {
      const t = d.t.toLowerCase(), h = d.h.join(" ").toLowerCase(), x = d.x.toLowerCase();
      let score = 0;
      for (const term of terms) {
        if (!x.includes(term) && !t.includes(term) && !h.includes(term)) return null;
        score += (t.includes(term) ? 10 : 0) + (h.includes(term) ? 4 : 0) + Math.min(5, x.split(term).length - 1);
      }
      return { d, score };
    }).filter(Boolean).sort((a, b) => b.score - a.score).slice(0, 8);
    active = -1;
    list.innerHTML = hits.length
      ? hits.map(({ d }) => `<li><a href="${base}${d.u}"><strong>${esc(d.t)}</strong><small>${esc(snippet(d.x, terms[0]))}</small></a></li>`).join("")
      : '<li><small style="padding:8px 10px;display:block">No matches</small></li>';
    list.hidden = false;
  }
  input?.addEventListener("input", run);
  input?.addEventListener("focus", load, { once: true });
  input?.addEventListener("keydown", (e) => {
    const items = [...list.querySelectorAll("a")];
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      active = (active + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
      items.forEach((a, i) => a.classList.toggle("on", i === active));
    } else if (e.key === "Enter" && items[Math.max(active, 0)]) {
      location.href = items[Math.max(active, 0)].href;
    } else if (e.key === "Escape") {
      list.hidden = true; input.blur();
    }
  });
  document.addEventListener("click", (e) => { if (!e.target.closest(".search")) list.hidden = true; });
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
      e.preventDefault(); input?.focus();
    }
  });
})();
