// 10-20 electrode positions (EEGLAB-style polar coordinates) and what each site is known for.

// theta: degrees from the nose, positive to the right; radius: 0 at Cz, 0.511 on the head outline.
const POLAR = {
  Fp1: [-18, 0.511], Fpz: [0, 0.511], Fp2: [18, 0.511],
  F7: [-54, 0.511], F3: [-39, 0.333], Fz: [0, 0.256], F4: [39, 0.333], F8: [54, 0.511],
  T3: [-90, 0.511], C3: [-90, 0.256], Cz: [0, 0], C4: [90, 0.256], T4: [90, 0.511],
  T5: [-126, 0.511], P3: [-141, 0.333], Pz: [180, 0.256], P4: [141, 0.333], T6: [126, 0.511],
  O1: [-162, 0.511], Oz: [180, 0.511], O2: [162, 0.511],
  A1: [-108, 0.62], A2: [108, 0.62],
};
const ALIASES = { T7: "T3", T8: "T4", P7: "T5", P8: "T6", M1: "A1", M2: "A2" };

export const LOBES = {
  Fp: { name: "prefrontal", color: "var(--amber)" },
  F: { name: "frontal", color: "var(--blue)" },
  C: { name: "central", color: "var(--green)" },
  T: { name: "temporal", color: "var(--red)" },
  P: { name: "parietal", color: "var(--violet)" },
  O: { name: "occipital", color: "#0b7285" },
  A: { name: "ear / mastoid", color: "var(--muted)" },
};

export const NOTES = {
  Fp1: "Above the left eye. Blinks and eye movements are largest here.",
  Fp2: "Above the right eye. Blinks and eye movements are largest here.",
  Fpz: "Midline, just above the nasion. Often used as ground.",
  F7: "Left front-temporal. Swings opposite to F8 during left-right eye movements; picks up jaw muscle.",
  F8: "Right front-temporal. Swings opposite to F7 during left-right eye movements; picks up jaw muscle.",
  F3: "Left frontal. A common neurofeedback site for frontal asymmetry protocols.",
  F4: "Right frontal. Paired with F3 for asymmetry.",
  Fz: "Frontal midline. Frontal-midline theta during mental effort is strongest here.",
  T3: "Left temporal (T7 in the 10-10 system). Muscle artifact from the jaw and temples dominates.",
  T4: "Right temporal (T8). Muscle artifact from the jaw and temples dominates.",
  C3: "Over left sensorimotor cortex. Mu rhythm and SMR; right-hand movement suppresses it.",
  C4: "Over right sensorimotor cortex. Mu rhythm and SMR; left-hand movement suppresses it.",
  Cz: "The vertex, centre of the head. Classic SMR / beta neurofeedback site; often the recording reference.",
  T5: "Left posterior temporal (P7). Often shows alpha with eyes closed.",
  T6: "Right posterior temporal (P8). Often shows alpha with eyes closed.",
  P3: "Left parietal. Alpha is strong here with eyes closed.",
  P4: "Right parietal. Alpha is strong here with eyes closed.",
  Pz: "Parietal midline. Alpha with eyes closed; the P300 ERP peaks here.",
  O1: "Left occipital, over visual cortex. The posterior alpha rhythm is biggest here.",
  O2: "Right occipital, over visual cortex. The posterior alpha rhythm is biggest here.",
  Oz: "Occipital midline. Strong alpha and visual responses.",
  A1: "Left earlobe or mastoid. A classic reference site (linked ears = A1+A2).",
  A2: "Right earlobe or mastoid. A classic reference site.",
};

export function canonical(label) {
  const clean = label.replace(/^EEG\s+/i, "").replace(/-(REF|LE|AVG|A1|A2)$/i, "").trim();
  const hit = Object.keys(POLAR).find((k) => k.toLowerCase() === clean.toLowerCase());
  if (hit) return hit;
  const alias = Object.keys(ALIASES).find((k) => k.toLowerCase() === clean.toLowerCase());
  return alias ? ALIASES[alias] : null;
}

export function lobeOf(name) {
  if (name.startsWith("Fp")) return "Fp";
  return name[0];
}

// x right, y up (front), in units of head radius = 1.
export function position(name) {
  const p = POLAR[canonical(name) || name];
  if (!p) return null;
  const [theta, r] = p;
  const rr = (r / 0.511) * 0.86;
  const t = (theta * Math.PI) / 180;
  return { x: rr * Math.sin(t), y: rr * Math.cos(t) };
}

export const STANDARD_19 = ["Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "T3", "C3", "Cz", "C4", "T4", "T5", "P3", "Pz", "P4", "T6", "O1", "O2"];

// Draw a head with electrodes into an <svg>. onClick(name) is called on electrode click.
export function drawHead(svg, names, { onClick, values, selected, size = 300, showLabels = true } = {}) {
  const ns = "http://www.w3.org/2000/svg";
  svg.setAttribute("viewBox", "-1.25 -1.25 2.5 2.5");
  svg.setAttribute("width", size);
  svg.setAttribute("height", size);
  svg.innerHTML = "";
  const el = (tag, attrs, parent = svg) => {
    const e = document.createElementNS(ns, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    parent.appendChild(e);
    return e;
  };
  const stroke = "var(--muted)";
  el("circle", { cx: 0, cy: 0, r: 1, fill: "var(--surface)", stroke, "stroke-width": 0.02 });
  el("path", { d: "M -0.12 -0.99 L 0 -1.15 L 0.12 -0.99", fill: "none", stroke, "stroke-width": 0.02 });
  el("path", { d: "M -0.99 -0.15 Q -1.1 0 -0.99 0.15", fill: "none", stroke, "stroke-width": 0.02 });
  el("path", { d: "M 0.99 -0.15 Q 1.1 0 0.99 0.15", fill: "none", stroke, "stroke-width": 0.02 });
  const vmax = values ? Math.max(...Object.values(values)) : 0;
  for (const name of names) {
    const p = position(name);
    if (!p) continue;
    const key = canonical(name) || name;
    const lobe = LOBES[lobeOf(key)];
    let fill = lobe ? lobe.color : "var(--muted)";
    if (values && values[name] != null) {
      const v = values[name] / (vmax || 1);
      fill = `color-mix(in srgb, var(--accent) ${Math.round(15 + 85 * v)}%, var(--surface))`;
    }
    const g = el("g", { class: "electrode", tabindex: 0, role: "button", "aria-label": name, "data-name": name });
    el("circle", {
      cx: p.x, cy: -p.y, r: 0.115, fill,
      stroke: selected === name ? "var(--ink)" : "var(--surface)", "stroke-width": selected === name ? 0.035 : 0.015,
    }, g);
    if (showLabels) {
      const t = el("text", {
        x: p.x, y: -p.y + 0.035, "text-anchor": "middle", "font-size": 0.095, "font-weight": 600,
        fill: values ? "var(--ink)" : "#fff", "pointer-events": "none", "font-family": "Inter, sans-serif",
      }, g);
      t.textContent = name;
    }
    if (onClick) {
      g.style.cursor = "pointer";
      g.addEventListener("click", () => onClick(name));
      g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onClick(name); } });
    }
  }
}
