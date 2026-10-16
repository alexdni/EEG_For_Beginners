// Small DSP toolkit for the Signal Lab: Butterworth biquads, notch, filtfilt, FFT, Welch.

// RBJ audio-EQ cookbook biquads. Returns normalised [b0,b1,b2,a1,a2].
function biquad(type, f0, fs, Q) {
  const w = (2 * Math.PI * f0) / fs;
  const cw = Math.cos(w), sw = Math.sin(w), alpha = sw / (2 * Q);
  let b0, b1, b2;
  const a0 = 1 + alpha, a1 = -2 * cw, a2 = 1 - alpha;
  if (type === "lowpass") { b0 = (1 - cw) / 2; b1 = 1 - cw; b2 = (1 - cw) / 2; }
  else if (type === "highpass") { b0 = (1 + cw) / 2; b1 = -(1 + cw); b2 = (1 + cw) / 2; }
  else if (type === "notch") { b0 = 1; b1 = -2 * cw; b2 = 1; }
  else throw new Error(type);
  return [b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0];
}

// 4th-order Butterworth = two 2nd-order sections with Q = 0.5412 and 1.3066.
export function design({ fs, highpass, lowpass, notch }) {
  const sections = [];
  const qs = [0.5411961, 1.3065630];
  if (highpass > 0) qs.forEach((q) => sections.push(biquad("highpass", highpass, fs, q)));
  if (lowpass > 0 && lowpass < fs / 2) qs.forEach((q) => sections.push(biquad("lowpass", lowpass, fs, q)));
  if (notch > 0 && notch < fs / 2) sections.push(biquad("notch", notch, fs, 30));
  return sections;
}

function runSection(x, [b0, b1, b2, a1, a2]) {
  // Direct form II transposed, state primed to the first sample's steady state.
  const y = new Float32Array(x.length);
  const x0 = x[0];
  const y0 = x0 * ((b0 + b1 + b2) / (1 + a1 + a2)); // output for a constant input x0
  let z2 = b2 * x0 - a2 * y0;
  let z1 = b1 * x0 - a1 * y0 + z2;
  for (let i = 0; i < x.length; i++) {
    const xi = x[i];
    const yi = b0 * xi + z1;
    z1 = b1 * xi - a1 * yi + z2;
    z2 = b2 * xi - a2 * yi;
    y[i] = yi;
  }
  return y;
}

export function filterCausal(x, sections) {
  let y = x;
  for (const s of sections) y = runSection(y, s);
  return y;
}

// Zero-phase: odd-reflect pad, filter forward and backward, unpad (like scipy.signal.filtfilt).
export function filtfilt(x, sections, pad) {
  const n = x.length;
  const p = Math.min(pad, n - 1);
  const ext = new Float32Array(n + 2 * p);
  for (let i = 0; i < p; i++) ext[i] = 2 * x[0] - x[p - i];
  ext.set(x, p);
  for (let i = 0; i < p; i++) ext[p + n + i] = 2 * x[n - 1] - x[n - 2 - i];
  let y = filterCausal(ext, sections);
  y.reverse();
  y = filterCausal(y, sections);
  y.reverse();
  return y.slice(p, p + n);
}

// In-place iterative radix-2 FFT on separate real/imag arrays.
function fft(re, im) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    const wr = Math.cos(ang), wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let cr = 1, ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const ar = re[i + k + len / 2] * cr - im[i + k + len / 2] * ci;
        const ai = re[i + k + len / 2] * ci + im[i + k + len / 2] * cr;
        re[i + k + len / 2] = re[i + k] - ar; im[i + k + len / 2] = im[i + k] - ai;
        re[i + k] += ar; im[i + k] += ai;
        const t = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = t;
      }
    }
  }
}

// Welch PSD in µV²/Hz with a Hann window and 50% overlap. average: "mean" | "median".
export function welch(x, fs, { nperseg, average = "median", start = 0, end = x.length } = {}) {
  let n = 1;
  while (n < (nperseg || fs * 2)) n <<= 1;
  const win = new Float32Array(n);
  let wss = 0;
  for (let i = 0; i < n; i++) { win[i] = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (n - 1)); wss += win[i] * win[i]; }
  const nf = n / 2 + 1;
  const segs = [];
  for (let s = start; s + n <= end; s += n / 2) {
    let mean = 0;
    for (let i = 0; i < n; i++) mean += x[s + i];
    mean /= n;
    const re = new Float64Array(n), im = new Float64Array(n);
    for (let i = 0; i < n; i++) re[i] = (x[s + i] - mean) * win[i];
    fft(re, im);
    const p = new Float64Array(nf);
    for (let k = 0; k < nf; k++) {
      p[k] = (re[k] * re[k] + im[k] * im[k]) / (fs * wss) * (k === 0 || k === n / 2 ? 1 : 2);
    }
    segs.push(p);
  }
  const freqs = Float64Array.from({ length: nf }, (_, k) => (k * fs) / n);
  const psd = new Float64Array(nf);
  if (!segs.length) return { freqs, psd, segments: 0 };
  for (let k = 0; k < nf; k++) {
    if (average === "median") {
      const col = segs.map((s) => s[k]).sort((a, b) => a - b);
      const m = col.length >> 1;
      // scipy's median bias correction is small for many segments; skip it for clarity
      psd[k] = col.length % 2 ? col[m] : (col[m - 1] + col[m]) / 2;
    } else {
      let sum = 0;
      for (const s of segs) sum += s[k];
      psd[k] = sum / segs.length;
    }
  }
  return { freqs, psd, segments: segs.length };
}

export function bandPower(freqs, psd, lo, hi) {
  let sum = 0;
  const df = freqs[1] - freqs[0];
  for (let k = 0; k < freqs.length; k++) if (freqs[k] >= lo && freqs[k] < hi) sum += psd[k] * df;
  return sum;
}
