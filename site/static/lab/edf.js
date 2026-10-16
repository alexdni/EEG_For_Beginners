// Minimal EDF / EDF+ reader for 16-bit files. Returns signals in microvolts.
// Spec: https://www.edfplus.info/specs/edf.html

const ascii = (bytes, a, n) => {
  let s = "";
  for (let i = a; i < a + n; i++) s += String.fromCharCode(bytes[i]);
  return s.trim();
};

const UNIT_TO_UV = { uv: 1, "µv": 1, "μv": 1, mv: 1e3, v: 1e6, nv: 1e-3 };

export function parseEDF(buffer) {
  const bytes = new Uint8Array(buffer);
  if (bytes.length < 256) throw new Error("File is too small to be an EDF.");
  const headerBytes = parseInt(ascii(bytes, 184, 8), 10);
  const reserved = ascii(bytes, 192, 44);
  let nRecords = parseInt(ascii(bytes, 236, 8), 10);
  const recordDuration = parseFloat(ascii(bytes, 244, 8));
  const ns = parseInt(ascii(bytes, 252, 4), 10);
  if (!ns || !recordDuration || !headerBytes) throw new Error("Not a valid EDF header.");

  const field = (offset, width) => {
    const out = [];
    for (let i = 0; i < ns; i++) out.push(ascii(bytes, 256 + offset * ns + i * width, width));
    return out;
  };
  // byte offsets of each per-signal field, in units of "ns * width"
  const labels = field(0, 16);
  let off = 16;
  off += 80; // transducer
  const dims = field(off, 8); off += 8;
  const pmin = field(off, 8).map(Number); off += 8;
  const pmax = field(off, 8).map(Number); off += 8;
  const dmin = field(off, 8).map(Number); off += 8;
  const dmax = field(off, 8).map(Number); off += 8;
  const prefilter = field(off, 80); off += 80;
  const nsamp = field(off, 8).map(Number);

  const recordSamples = nsamp.reduce((a, b) => a + b, 0);
  const recordBytes = recordSamples * 2;
  const available = Math.floor((bytes.length - headerBytes) / recordBytes);
  if (!(nRecords > 0) || nRecords > available) nRecords = available;

  const view = new DataView(buffer);
  const signals = [];
  const annotations = [];
  const annIdx = labels.findIndex((l) => l === "EDF Annotations");

  const offsets = [];
  let acc = 0;
  for (let s = 0; s < ns; s++) { offsets.push(acc); acc += nsamp[s]; }

  for (let s = 0; s < ns; s++) {
    if (s === annIdx) continue;
    const unit = UNIT_TO_UV[dims[s].toLowerCase()] ?? 1;
    const gain = ((pmax[s] - pmin[s]) / (dmax[s] - dmin[s])) * unit;
    const offset = (pmin[s] - gain / unit * dmin[s]) * unit;
    const data = new Float32Array(nRecords * nsamp[s]);
    for (let r = 0; r < nRecords; r++) {
      let p = headerBytes + r * recordBytes + offsets[s] * 2;
      const o = r * nsamp[s];
      for (let k = 0; k < nsamp[s]; k++, p += 2) data[o + k] = view.getInt16(p, true) * gain + offset;
    }
    signals.push({ label: labels[s], unit: dims[s], sfreq: nsamp[s] / recordDuration, prefilter: prefilter[s], data });
  }

  if (annIdx >= 0) {
    for (let r = 0; r < nRecords; r++) {
      const p = headerBytes + r * recordBytes + offsets[annIdx] * 2;
      const raw = ascii(bytes, p, nsamp[annIdx] * 2);
      // TALs: +onset[\x15duration]\x14text\x14...\x00
      for (const tal of raw.split("\x00")) {
        const parts = tal.split("\x14");
        if (parts.length < 2) continue;
        const [timing, ...texts] = parts;
        const [onset, duration] = timing.split("\x15");
        for (const text of texts) {
          if (text) annotations.push({ onset: parseFloat(onset), duration: parseFloat(duration || "0"), text });
        }
      }
    }
  }
  // Some exporters write cut segments as "Noise removed 2.40 s at 00:00:51.823": recover the span.
  for (const a of annotations) {
    const m = a.text.match(/([\d.]+)\s*s at (\d+):(\d+):([\d.]+)/);
    if (m) a.span = { start: +m[2] * 3600 + +m[3] * 60 + +m[4], duration: +m[1] };
  }

  const patient = ascii(bytes, 8, 80);
  const recording = ascii(bytes, 88, 80);
  return {
    format: reserved.startsWith("EDF+") ? reserved.slice(0, 5) : "EDF",
    patient, recording, recordDuration, nRecords, signals, annotations,
  };
}
