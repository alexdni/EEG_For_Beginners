// Signal Lab: load an EDF, scroll it, filter it, re-reference it, and read its spectrum.
import { parseEDF } from "./edf.js";
import { design, filtfilt, filterCausal, welch, bandPower } from "./dsp.js";
import { drawHead, canonical, NOTES } from "./electrodes.js";

const BANDS = [
  ["delta", 1, 4, "--violet"], ["theta", 4, 8, "--blue"], ["alpha", 8, 13, "--green"],
  ["beta", 13, 30, "--amber"], ["gamma", 30, 45, "--red"],
];

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const base = document.querySelector("main").dataset.base;

const state = {
  rec: null, name: "", raw: [], view: [], sf: 250, n: 0,
  start: 0, dur: 10, gain: 1, selected: null, psd: null, busy: false,
};

// ---------------------------------------------------------------- loading

async function loadUrl(url, name) {
  setStatus(`Loading ${name}…`);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not fetch ${url} (${res.status})`);
  loadBuffer(await res.arrayBuffer(), name);
}

function loadBuffer(buf, name) {
  const rec = parseEDF(buf);
  const sf = Math.max(...rec.signals.map((s) => s.sfreq));
  const sigs = rec.signals.filter((s) => s.sfreq === sf);
  state.rec = rec;
  state.name = name;
  state.sf = sf;
  state.n = Math.min(...sigs.map((s) => s.data.length));
  state.raw = sigs.map((s) => ({ label: s.label, data: s.data.subarray(0, state.n), prefilter: s.prefilter }));
  state.start = 0;
  state.selected = null;
  $("start").max = Math.max(0, state.n / sf - state.dur).toFixed(1);
  $("start").value = 0;
  const skipped = rec.signals.length - sigs.length;
  const pre = state.raw[0]?.prefilter && state.raw[0].prefilter !== "None" ? ` · prefilter "${state.raw[0].prefilter}"` : "";
  $("meta").textContent =
    `${rec.format} · ${state.raw.length} channels at ${sf.toFixed(sf % 1 ? 2 : 0)} Hz · ` +
    `${(state.n / sf).toFixed(1)} s · ${rec.annotations.length} annotation${rec.annotations.length === 1 ? "" : "s"}` +
    (skipped ? ` · ${skipped} channel(s) at other rates hidden` : "") + pre;
  const offsets = state.raw.map((c) => {
    let m = 0; for (let i = 0; i < c.data.length; i += 50) m += c.data[i];
    return m / Math.ceil(c.data.length / 50);
  });
  const maxOff = Math.max(...offsets.map(Math.abs));
  $("dc-note").hidden = !(maxOff > 1000 && +$("hp").value === 0);
  $("dc-note").textContent = `This file carries a DC offset of up to ${Math.round(maxOff).toLocaleString()} µV. ` +
    "Each trace is centred for display, but slow drift will dominate until you add a high-pass filter.";
  process();
}

// ---------------------------------------------------------------- processing

function process() {
  if (!state.rec) return;
  const t0 = performance.now();
  const sf = state.sf;
  const opts = { fs: sf, highpass: +$("hp").value, lowpass: +$("lp").value, notch: +$("notch").value };
  const sections = design(opts);
  const causal = $("phase").value === "causal";
  let chans = state.raw.map((c) => {
    if (!sections.length) return Float32Array.from(c.data);
    return causal ? filterCausal(c.data, sections) : filtfilt(c.data, sections, Math.round(3 * sf));
  });
  const ref = $("ref").value;
  if (ref === "average") {
    const avg = new Float32Array(state.n);
    for (const d of chans) for (let i = 0; i < state.n; i++) avg[i] += d[i] / chans.length;
    chans = chans.map((d) => d.map((v, i) => v - avg[i]));
  } else if (ref !== "device") {
    const r = chans[state.raw.findIndex((c) => c.label === ref)];
    if (r) chans = chans.map((d) => d.map((v, i) => v - r[i]));
  }
  state.view = chans;
  computeSpectrum();
  draw();
  setStatus(`Processed in ${Math.round(performance.now() - t0)} ms`);
}

function computeSpectrum() {
  const avg = $("avg").value;
  const whole = $("span").value === "whole";
  const sf = state.sf;
  const a = whole ? 0 : Math.floor(state.start * sf);
  const b = whole ? state.n : Math.min(state.n, Math.floor((state.start + state.dur) * sf));
  state.psd = state.view.map((d) => welch(d, sf, { nperseg: 2 * sf, average: avg, start: a, end: b }));
}

// ---------------------------------------------------------------- drawing

function setupCanvas(canvas, height) {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.parentElement.clientWidth;
  canvas.style.width = w + "px";
  canvas.style.height = height + "px";
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w, h: height };
}

function draw() {
  drawTraces();
  drawSpectrum();
  drawBands();
  drawHeadMap();
}

function drawTraces() {
  const canvas = $("traces");
  const nch = state.view.length;
  const rowH = Math.max(22, Math.min(40, 620 / nch));
  const { ctx, w, h } = setupCanvas(canvas, rowH * nch + 34);
  const left = 46, right = 12, top = 8;
  const sf = state.sf;
  const a = Math.floor(state.start * sf);
  const b = Math.min(state.n, Math.floor((state.start + state.dur) * sf));
  const scale = +$("scale").value; // µV per row height
  ctx.clearRect(0, 0, w, h);
  ctx.font = "11px Inter, sans-serif";

  // annotation spans
  ctx.fillStyle = css("--accent");
  ctx.globalAlpha = 0.16;
  for (const an of state.rec.annotations) {
    const s0 = an.span ? an.span.start : an.onset;
    const d0 = an.span ? an.span.duration : an.duration;
    const x0 = left + ((s0 - state.start) / state.dur) * (w - left - right);
    const x1 = left + ((s0 + Math.max(d0, 0.05) - state.start) / state.dur) * (w - left - right);
    if (x1 > left && x0 < w - right) ctx.fillRect(Math.max(left, x0), top, Math.min(w - right, x1) - Math.max(left, x0), rowH * nch);
  }
  ctx.globalAlpha = 1;

  // time grid
  ctx.strokeStyle = css("--line");
  ctx.fillStyle = css("--muted");
  ctx.lineWidth = 1;
  const step = state.dur > 20 ? 5 : state.dur > 5 ? 1 : 0.5;
  for (let t = Math.ceil(state.start / step) * step; t <= state.start + state.dur; t += step) {
    const x = left + ((t - state.start) / state.dur) * (w - left - right);
    ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, top + rowH * nch); ctx.stroke();
    ctx.fillText(t.toFixed(step < 1 ? 1 : 0) + " s", x - 10, top + rowH * nch + 16);
  }

  const ink = css("--ink"), accent = css("--accent");
  const pxPerSample = (w - left - right) / (b - a);
  for (let c = 0; c < nch; c++) {
    const d = state.view[c];
    const y0 = top + rowH * (c + 0.5);
    let mean = 0;
    for (let i = a; i < b; i++) mean += d[i];
    mean /= Math.max(1, b - a);
    const isSel = state.selected === state.raw[c].label;
    ctx.fillStyle = isSel ? accent : css("--ink-2");
    ctx.font = (isSel ? "600 " : "") + "11px Inter, sans-serif";
    ctx.fillText(state.raw[c].label, 4, y0 + 4);
    ctx.strokeStyle = isSel ? accent : ink;
    ctx.lineWidth = isSel ? 1.3 : 0.8;
    ctx.beginPath();
    const k = rowH / scale;
    if (pxPerSample >= 1) {
      for (let i = a; i < b; i++) {
        const x = left + (i - a) * pxPerSample;
        const y = y0 - (d[i] - mean) * k;
        i === a ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
    } else {
      // min/max decimation per pixel column keeps spikes visible
      const cols = Math.floor(w - left - right);
      for (let px = 0; px < cols; px++) {
        const i0 = a + Math.floor(px / pxPerSample), i1 = Math.min(b, a + Math.floor((px + 1) / pxPerSample));
        let lo = Infinity, hi = -Infinity;
        for (let i = i0; i < i1; i++) { if (d[i] < lo) lo = d[i]; if (d[i] > hi) hi = d[i]; }
        if (lo === Infinity) continue;
        // join columns so the trace stays continuous: draw toward whichever extreme comes first
        const first = d[i0] <= d[i1 - 1] ? lo : hi, second = first === lo ? hi : lo;
        if (px === 0) ctx.moveTo(left + px, y0 - (first - mean) * k);
        else ctx.lineTo(left + px, y0 - (first - mean) * k);
        ctx.lineTo(left + px + 0.5, y0 - (second - mean) * k);
      }
    }
    ctx.stroke();
  }
  // scale bar
  ctx.strokeStyle = accent; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(w - 6, top + rowH * nch - rowH); ctx.lineTo(w - 6, top + rowH * nch); ctx.stroke();
  $("scale-label").textContent = `Orange bar = ${scale} µV`;
}

function drawSpectrum() {
  const canvas = $("spectrum");
  const { ctx, w, h } = setupCanvas(canvas, 300);
  const left = 52, right = 12, top = 12, bottom = 34;
  const fmax = +$("fmax").value;
  ctx.clearRect(0, 0, w, h);
  if (!state.psd?.length || !state.psd[0].segments) {
    ctx.fillStyle = css("--muted");
    ctx.fillText("Window too short for a 2 s Welch segment. Lengthen the window or use the whole recording.", left, h / 2);
    return;
  }
  const { freqs } = state.psd[0];
  const kmax = freqs.findIndex((f) => f > fmax);
  const kEnd = kmax < 0 ? freqs.length : kmax;
  const kStart = freqs.findIndex((f) => f >= 0.5);
  const db = state.psd.map((p) => Array.from(p.psd.slice(kStart, kEnd), (v) => 10 * Math.log10(v + 1e-12)));
  let lo = Infinity, hi = -Infinity;
  for (const row of db) for (const v of row) { if (v < lo) lo = v; if (v > hi) hi = v; }
  lo = Math.max(lo, hi - 90);
  const X = (f) => left + (f / fmax) * (w - left - right);
  const Y = (v) => top + (1 - (v - lo) / (hi - lo || 1)) * (h - top - bottom);
  for (const [name, a, b, color] of BANDS) {
    if (a >= fmax) continue;
    ctx.fillStyle = css(color);
    ctx.globalAlpha = 0.09;
    ctx.fillRect(X(a), top, X(Math.min(b, fmax)) - X(a), h - top - bottom);
    ctx.globalAlpha = 1;
    ctx.font = "10px Inter, sans-serif";
    ctx.fillText(name, X(a) + 3, top + 11);
  }
  const mains = [50, 60].filter((f) => f < fmax);
  ctx.setLineDash([3, 3]); ctx.strokeStyle = css("--muted");
  for (const f of mains) { ctx.beginPath(); ctx.moveTo(X(f), top); ctx.lineTo(X(f), h - bottom); ctx.stroke(); }
  ctx.setLineDash([]);
  ctx.fillStyle = css("--muted");
  ctx.font = "11px Inter, sans-serif";
  for (let f = 0; f <= fmax; f += fmax > 60 ? 20 : 10) ctx.fillText(f + "", X(f) - 6, h - bottom + 16);
  ctx.fillText("Hz", w - right - 14, h - bottom + 16);
  const tick = (hi - lo) > 40 ? 20 : 10;
  for (let v = Math.ceil(lo / tick) * tick; v <= hi; v += tick) {
    ctx.fillText(v + " dB", 4, Y(v) + 4);
    ctx.strokeStyle = css("--line"); ctx.beginPath(); ctx.moveTo(left, Y(v)); ctx.lineTo(w - right, Y(v)); ctx.stroke();
  }
  const fs = Array.from(freqs.slice(kStart, kEnd));
  db.forEach((row, c) => {
    const sel = state.selected === state.raw[c].label;
    if (sel) return;
    ctx.strokeStyle = css("--ink");
    ctx.globalAlpha = state.selected ? 0.18 : 0.45;
    ctx.lineWidth = 0.9;
    ctx.beginPath();
    row.forEach((v, i) => (i ? ctx.lineTo(X(fs[i]), Y(v)) : ctx.moveTo(X(fs[i]), Y(v))));
    ctx.stroke();
    ctx.globalAlpha = 1;
  });
  const si = state.raw.findIndex((c) => c.label === state.selected);
  if (si >= 0) {
    ctx.strokeStyle = css("--accent"); ctx.lineWidth = 2;
    ctx.beginPath();
    db[si].forEach((v, i) => (i ? ctx.lineTo(X(fs[i]), Y(v)) : ctx.moveTo(X(fs[i]), Y(v))));
    ctx.stroke();
  }
  $("spec-label").textContent = `Welch, 2 s Hann windows, ${state.psd[0].segments} segments, ${$("avg").value} average · ` +
    (state.selected ? `${state.selected} highlighted` : "click a channel to highlight it");
}

function drawBands() {
  if (!state.psd?.length || !state.psd[0].segments) { $("bands").innerHTML = ""; return; }
  const rows = state.raw.map((c, i) => {
    const { freqs, psd } = state.psd[i];
    const total = bandPower(freqs, psd, 1, 45);
    const rel = BANDS.map(([, a, b]) => bandPower(freqs, psd, a, b) / total);
    let pk = 0, best = -1;
    for (let k = 0; k < freqs.length; k++) if (freqs[k] >= 7 && freqs[k] <= 14 && psd[k] > best) { best = psd[k]; pk = freqs[k]; }
    const line = (f) => {
      const k = freqs.findIndex((x) => x >= f);
      if (k < 0) return null;
      let base = 0, cnt = 0;
      for (let j = k - 8; j <= k + 8; j++) if (Math.abs(j - k) > 3 && psd[j]) { base += psd[j]; cnt++; }
      return 10 * Math.log10(psd[k] / (base / cnt));
    };
    return { label: c.label, rel, pk, l60: line(60), l50: line(50) };
  });
  const mains = rows.map((r) => r.l60 ?? -Infinity);
  const head = `<tr><th>Channel</th>${BANDS.map(([n, , , c]) => `<th style="color:var(${c})">${n}</th>`).join("")}<th>Alpha peak</th><th title="Height of the 60 Hz bin above its neighbours">60 Hz line</th></tr>`;
  const body = rows.map((r) => {
    const sel = r.label === state.selected ? ' class="sel"' : "";
    const cells = r.rel.map((v, j) => `<td><span class="bar" style="--w:${Math.min(100, v * 100).toFixed(0)}%;--c:var(${BANDS[j][3]})"></span>${(v * 100).toFixed(0)}%</td>`).join("");
    const ln = r.l60 == null ? "–" : `${r.l60.toFixed(0)} dB`;
    return `<tr data-ch="${esc(r.label)}"${sel}><td><strong>${esc(r.label)}</strong></td>${cells}<td>${r.pk.toFixed(1)} Hz</td><td>${ln}</td></tr>`;
  }).join("");
  $("bands").innerHTML = `<table>${head}${body}</table>`;
  $("bands").querySelectorAll("tr[data-ch]").forEach((tr) => tr.addEventListener("click", () => select(tr.dataset.ch)));
  const worst = Math.max(...mains);
  $("line-note").textContent = Number.isFinite(worst)
    ? (worst > 10
      ? `Line noise: the 60 Hz bin sits up to ${worst.toFixed(0)} dB above its neighbours.` +
        (+$("notch").value === 60 ? " That is what survives the notch: compare with the notch off." : " Try the 60 Hz notch.")
      : "No strong 60 Hz line noise in this view.")
    : "";
}

function drawHeadMap() {
  const names = state.raw.map((c) => c.label).filter((l) => canonical(l));
  const values = {};
  const band = $("mapband").value;
  const [_, a, b] = BANDS.find(([n]) => n === band);
  state.raw.forEach((c, i) => {
    if (!canonical(c.label) || !state.psd?.[i]?.segments) return;
    const { freqs, psd } = state.psd[i];
    values[c.label] = bandPower(freqs, psd, a, b) / bandPower(freqs, psd, 1, 45);
  });
  drawHead($("head"), names, { onClick: select, values, selected: state.selected, size: 260 });
  const note = state.selected && NOTES[canonical(state.selected)];
  $("head-note").textContent = note || `Shading = relative ${band} power. Click an electrode or a row to highlight that channel.`;
}

function select(label) {
  state.selected = state.selected === label ? null : label;
  draw();
}

function setStatus(msg) { $("status").textContent = msg; }

// ---------------------------------------------------------------- wiring

function init() {
  const sel = $("sample");
  const reprocess = () => process();
  ["hp", "lp", "notch", "phase", "ref"].forEach((id) => $(id).addEventListener("change", reprocess));
  ["avg", "span"].forEach((id) => $(id).addEventListener("change", () => { computeSpectrum(); draw(); }));
  ["scale", "fmax", "mapband"].forEach((id) => $(id).addEventListener("input", draw));
  $("dur").addEventListener("change", () => {
    state.dur = +$("dur").value;
    $("start").max = Math.max(0, state.n / state.sf - state.dur).toFixed(1);
    if ($("span").value === "window") computeSpectrum();
    draw();
  });
  let pending = null;
  $("start").addEventListener("input", () => {
    state.start = +$("start").value;
    $("start-label").textContent = `${state.start.toFixed(1)} s`;
    drawTraces();
    if ($("span").value === "window") {
      clearTimeout(pending);
      pending = setTimeout(() => { computeSpectrum(); drawSpectrum(); drawBands(); drawHeadMap(); }, 120);
    }
  });
  sel.addEventListener("change", () => {
    const opt = sel.selectedOptions[0];
    $("sample-note").textContent = opt.dataset.note || "";
    if (opt.dataset.preset) applyPreset(opt.dataset.preset);
    loadUrl(base + "data/samples/" + sel.value, sel.value).catch((e) => setStatus(e.message));
  });
  $("file").addEventListener("change", async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    try { loadBuffer(await f.arrayBuffer(), f.name); $("sample-note").textContent = `Your file (${f.name}) stays in this browser; nothing is uploaded.`; }
    catch (err) { setStatus("Could not read that file: " + err.message); }
  });
  document.addEventListener("keydown", (e) => {
    if (!state.rec || e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      const s = $("start");
      s.value = Math.min(+s.max, Math.max(0, +s.value + (e.key === "ArrowRight" ? 1 : -1) * state.dur * 0.8));
      s.dispatchEvent(new Event("input"));
    }
  });
  window.addEventListener("resize", () => state.rec && draw());
  document.addEventListener("themechange", () => state.rec && draw());
  $("traces").addEventListener("click", (e) => {
    const rect = e.target.getBoundingClientRect();
    const nch = state.view.length;
    const rowH = Math.max(22, Math.min(40, 620 / nch));
    const c = Math.floor((e.clientY - rect.top - 8) / rowH);
    if (c >= 0 && c < nch) select(state.raw[c].label);
  });
  sel.dispatchEvent(new Event("change"));
}

function applyPreset(p) {
  const presets = {
    raw: { hp: 0, lp: 0, notch: 0, ref: "device", scale: 100 },
    clean: { hp: 1, lp: 40, notch: 0, ref: "device", scale: 100 },
    noisy: { hp: 0, lp: 0, notch: 0, ref: "device", scale: 400 },
    drift: { hp: 0, lp: 40, notch: 0, ref: "device", scale: 400 },
  };
  const v = presets[p];
  if (!v) return;
  for (const [k, val] of Object.entries(v)) {
    const el = $(k);
    if (el) el.value = val;
  }
}

init();
