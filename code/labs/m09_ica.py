"""Module 09: three ways to handle artifacts on the same recording.

1. Mark bad segments by a peak-to-peak threshold (rejection).
2. ICA: find and remove the blink component.
3. Compare with the platform's own rejection-only and full-pipeline exports.

Usage:  python code/labs/m09_ica.py [output_dir] [--show]
"""
import numpy as np
from _common import finish, plt
from mne import Annotations
from mne.preprocessing import ICA

from eeg101 import load_sample

raw = load_sample("pipeline_raw")
print(f"pipeline_raw: {raw.times[-1]:.1f} s, {len(raw.ch_names)} channels")

# The headset came off at the end: look at peak-to-peak per second before cropping.
sf = raw.info["sfreq"]
filt = raw.copy().filter(1, 40)
d = filt.get_data() * 1e6
ptp = [np.ptp(d[:, int(s * sf): int((s + 1) * sf)], axis=1).max() for s in range(int(np.ceil(raw.times[-1])))]
print("worst-channel peak-to-peak, last 7 seconds (µV):", [f"{v:,.0f}" for v in ptp[-7:]])
raw.crop(0, raw.times[-1] - 4.5)
filt = raw.copy().filter(1, 40)
print(f"cropped to {raw.times[-1]:.1f} s")

# --- 1. threshold rejection: mark any 1 s window where a channel swings > 150 µV ----
threshold = 150.0
d = filt.get_data() * 1e6
onsets = [s for s in range(int(np.ceil(raw.times[-1]))) if np.ptp(d[:, int(s * sf): int((s + 1) * sf)], axis=1).max() > threshold]
filt.set_annotations(Annotations(onsets, [1.0] * len(onsets), ["BAD_threshold"] * len(onsets)))
print(f"\nthreshold {threshold:g} µV: {len(onsets)} of {int(np.ceil(raw.times[-1]))} one-second windows marked bad")
print("bad windows start at (s):", onsets)

# --- 2. ICA -------------------------------------------------------------------------
ica_raw = filt.copy().set_annotations(None).set_eeg_reference("average")
ica = ICA(n_components=15, random_state=97, max_iter="auto")
ica.fit(ica_raw)
fp = ica_raw.copy().pick(["Fp1", "Fp2"]).get_data().mean(0)
sources = ica.get_sources(ica_raw).get_data()
corr = np.array([np.corrcoef(s, fp)[0, 1] for s in sources])
blink = int(np.argmax(np.abs(corr)))
print(f"\nICA: component ICA{blink:03d} correlates r = {corr[blink]:+.2f} with the Fp1/Fp2 average")
print("next strongest:", ", ".join(f"ICA{i:03d} {corr[i]:+.2f}" for i in np.argsort(-np.abs(corr))[1:4]))

# MNE's own detector does the same thing using frontal channels as a stand-in EOG
eog_idx, scores = ica.find_bads_eog(ica_raw, ch_name=["Fp1", "Fp2"], threshold=3.0)
print(f"ica.find_bads_eog agrees: {sorted(set(eog_idx))}")

ica.exclude = [blink]
clean = ica.apply(ica_raw.copy())
before = ica_raw.get_data(picks=["Fp1", "Fp2", "O1"]).std(axis=1) * 1e6
after = clean.get_data(picks=["Fp1", "Fp2", "O1"]).std(axis=1) * 1e6
for ch, b, a in zip(("Fp1", "Fp2", "O1"), before, after):
    print(f"  {ch}: SD {b:5.1f} µV -> {a:5.1f} µV")

# Optional: ICLabel, if installed (pip install mne-icalabel onnxruntime)
try:
    from mne_icalabel import label_components

    labels = label_components(ica_raw, ica, method="iclabel")
    print("\nICLabel:")
    for i, (lab, p) in enumerate(zip(labels["labels"], labels["y_pred_proba"])):
        print(f"  ICA{i:03d} {lab:16s} {p:.2f}")
except ImportError:
    print("\n(mne-icalabel not installed; skipping automatic labels)")

# --- 3. the platform's own exports of the same recording -----------------------------
rej = load_sample("pipeline_rejection")
full = load_sample("pipeline_full")
print(f"\nplatform rejection-only export: {rej.times[-1]:.0f} s kept; full pipeline: {full.times[-1]:.0f} s")

# Cutting segments out and gluing the rest together leaves steps at every splice.
jumps = np.abs(np.diff(rej.get_data() * 1e6, axis=1)).max(axis=0)
splices = np.where(jumps > 200)[0] / rej.info["sfreq"]
print("sample-to-sample jumps > 200 µV in the rejection-only file at (s):", np.round(splices, 1))

print("\nmean delta (1-4 Hz) power, Welch with mean vs median averaging:")
for label, r in (("raw (cropped, 1-40 Hz)", filt), ("our ICA-cleaned", clean),
                 ("platform rejection only", rej.copy().filter(1, 40)), ("platform full", full)):
    row = []
    for avg in ("mean", "median"):
        sp = r.compute_psd(fmin=1, fmax=40, n_fft=int(sf * 2), average=avg, reject_by_annotation=False)
        psd, f = sp.get_data(return_freqs=True)
        row.append(psd[:, (f >= 1) & (f < 4)].sum(1).mean() * 1e12 * (f[1] - f[0]))
    print(f"  {label:26s} mean {row[0]:8.1f} µV²   median {row[1]:7.1f} µV²")

fig = ica.plot_components(show=False)
fig = fig[0] if isinstance(fig, list) else fig
finish(fig, "m09_ica_components")
fig = ica.plot_sources(ica_raw, picks=[blink], show=False, start=20, stop=30)
finish(fig, "m09_blink_source")
fig, ax = plt.subplots(figsize=(10, 3))
t0, t1 = int(20 * sf), int(30 * sf)
t = np.arange(t1 - t0) / sf + 20
ax.plot(t, ica_raw.get_data(picks=["Fp1"])[0][t0:t1] * 1e6, label="Fp1 before", lw=0.8)
ax.plot(t, clean.get_data(picks=["Fp1"])[0][t0:t1] * 1e6, label="Fp1 after", lw=0.8)
ax.set_xlabel("time (s)")
ax.set_ylabel("µV")
ax.legend()
finish(fig, "m09_fp1_before_after")
