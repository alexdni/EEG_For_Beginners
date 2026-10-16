"""Lab 2: clean a recording with ICA, then compute alpha power per channel.

Part A uses s06 (pipeline_raw), which has clear blinks, and compares the result with the
platform's own exports of the same recording (s07 rejection-only, s08 full pipeline).
Part B uses s01 (rest_ec), eyes closed, to answer "which channels have the most alpha?"

Usage:  python code/labs/lab2_clean_and_measure.py [output_dir] [--show]
"""
import numpy as np
from _common import finish, plt
from mne.preprocessing import ICA

from eeg101 import load_sample


def frontal_summary(raw, label):
    """SD and median-Welch delta power at Fp1/Fp2: the two numbers blinks inflate most."""
    picks = ["Fp1", "Fp2"]
    sd = raw.get_data(picks=picks).std(axis=1) * 1e6
    sp = raw.compute_psd(fmin=1, fmax=4, picks=picks, n_fft=int(raw.info["sfreq"] * 2), average="median")
    psd, f = sp.get_data(return_freqs=True)
    delta = psd.sum(axis=1) * (f[1] - f[0]) * 1e12
    print(f"  {label:28s} SD Fp1 {sd[0]:5.1f} Fp2 {sd[1]:5.1f} µV   delta Fp1 {delta[0]:6.1f} Fp2 {delta[1]:6.1f} µV²")


# ---------------- Part A: ICA on a recording with blinks -----------------------------
raw = load_sample("pipeline_raw")
raw.crop(0, raw.times[-1] - 4.5)          # the headset came off in the last 4.5 s
raw.filter(1.0, 40.0)                      # ICA works best on data high-passed at ~1 Hz
raw.set_eeg_reference("average")

ica = ICA(n_components=15, random_state=97, max_iter="auto")
ica.fit(raw)

# Step 1: look. Which map is frontal and symmetric, and which time course spikes with blinks?
fig = ica.plot_components(show=False)
finish(fig[0] if isinstance(fig, list) else fig, "lab2_ica_components")
fig = ica.plot_sources(raw, show=False, start=20, stop=30)
finish(fig, "lab2_ica_sources")

# Step 2: confirm with numbers. Fp1/Fp2 stand in for an EOG channel this headset does not have.
eog_idx, scores = ica.find_bads_eog(raw, ch_name=["Fp1", "Fp2"], threshold=3.0)
blink = int(eog_idx[0]) if eog_idx else int(np.argmax(np.abs(scores).max(axis=0)))
print(f"blink component: ICA{blink:03d}")

ica.exclude = [blink]
clean = ica.apply(raw.copy())

print("\nFrontal channels before and after (A3: what changed?)")
frontal_summary(raw, "before ICA")
frontal_summary(clean, f"after removing ICA{blink:03d}")
full = load_sample("pipeline_full")
frontal_summary(full, "platform full pipeline (s08)")

# ---------------- Part B: alpha power per channel, eyes closed -----------------------
def alpha_per_channel(raw, average="mean"):
    spec = raw.compute_psd(fmin=1, fmax=40, method="welch", n_fft=int(raw.info["sfreq"] * 2), average=average)
    psd, freqs = spec.get_data(return_freqs=True)
    alpha = psd[:, (freqs >= 8) & (freqs <= 13)].mean(axis=1) * 1e12   # mean µV²/Hz in 8-13 Hz
    return sorted(zip(raw.ch_names, alpha), key=lambda x: -x[1]), spec


ec = load_sample("rest_ec").filter(1.0, 40.0).set_eeg_reference("average")

# First attempt: the straight recipe. Look at the top three.
ranked, _ = alpha_per_channel(ec)
print("\nB1. naive (mean Welch, nothing rejected). Top three:", ", ".join(f"{c} {a:,.0f}" for c, a in ranked[:3]))

# The fix: mark every 1 s window where any channel swings more than 200 µV as BAD.
# compute_psd skips BAD_ annotations by default (reject_by_annotation=True).
from mne import Annotations  # noqa: E402

sf = ec.info["sfreq"]
d = ec.get_data() * 1e6
bad = [s for s in range(int(np.ceil(ec.times[-1]))) if np.ptp(d[:, int(s * sf): int((s + 1) * sf)], axis=1).max() > 200]
ec.set_annotations(Annotations(bad, [1.0] * len(bad), ["BAD_ptp"] * len(bad)))
print(f"B2. marked {len(bad)} of {int(np.ceil(ec.times[-1]))} one-second windows as BAD (> 200 µV peak-to-peak)")
ranked, spec = alpha_per_channel(ec)
print("    after rejection, mean Welch. Top three:", ", ".join(f"{c} {a:.1f}" for c, a in ranked[:3]))
ranked_med, _ = alpha_per_channel(ec, average="median")
print("    median Welch (robust alternative). Top three:", ", ".join(f"{c} {a:.1f}" for c, a in ranked_med[:3]))
print("\nAlpha power per channel after rejection (µV²/Hz):")
print("  " + ", ".join(f"{ch} {a:.1f}" for ch, a in ranked))

fig, ax = plt.subplots(figsize=(9, 4))
ax.bar([c for c, _ in ranked], [a for _, a in ranked], color="#2b8a3e")
ax.set_ylabel("mean 8-13 Hz power (µV²/Hz)")
ax.set_title("Alpha power per channel, eyes closed (s01), average reference, bad seconds rejected")
finish(fig, "lab2_alpha_per_channel")

fig = spec.plot_topomap(bands={"Alpha (8-13 Hz)": (8, 13)}, show=False)
finish(fig, "lab2_alpha_topomap")
