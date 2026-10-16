"""Lab 1: find the alpha peak in eyes-closed vs eyes-open resting EEG.

Usage (from the repo root):
    python code/labs/lab1_alpha_peak.py [output_folder] [--show]

Saves a spectrum plot and a topomap to output_folder (default ./lab_outputs) and
prints the occipital alpha peak and the eyes-closed / eyes-open alpha ratio per channel.
Pass --show to also open MNE's interactive raw-data browser and the plots.
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np

SHOW = "--show" in sys.argv
if not SHOW:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mne  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eeg101 import load_sample  # noqa: E402

mne.set_log_level("ERROR")

args = [a for a in sys.argv[1:] if not a.startswith("--")]
out = Path(args[0]) if args else Path("lab_outputs")
out.mkdir(parents=True, exist_ok=True)

# 1. Load both conditions and band-pass 1-40 Hz (removes DC offset, drift, line noise, most muscle)
raw_closed = load_sample("rest_ec").filter(1.0, 40.0)
raw_open = load_sample("rest_eo").filter(1.0, 40.0)
for name, raw in (("eyes closed", raw_closed), ("eyes open", raw_open)):
    print(f"{name}: {len(raw.ch_names)} channels, {raw.info['sfreq']:g} Hz, {raw.times[-1]:.0f} s")

if SHOW:
    raw_closed.plot(duration=10, n_channels=19, scalings=dict(eeg=50e-6), block=False)

# 2. Power spectra (Welch, 2 s windows, median across windows so a few artifacts do not dominate)
def spectrum(raw):
    return raw.compute_psd(method="welch", fmin=1, fmax=40, n_fft=int(raw.info["sfreq"] * 2), average="median")


spec_closed, spec_open = spectrum(raw_closed), spectrum(raw_open)
psd_c, freqs = spec_closed.get_data(return_freqs=True)
psd_o, freqs_o = spec_open.get_data(return_freqs=True)

# 3. Occipital alpha peak: the frequency of maximum power between 7 and 14 Hz, averaged over O1 and O2
occ = [raw_closed.ch_names.index(c) for c in ("O1", "O2")]
search = (freqs >= 7) & (freqs <= 14)
peak_c = freqs[search][np.argmax(psd_c[occ][:, search].mean(0))]
search_o = (freqs_o >= 7) & (freqs_o <= 14)
peak_o = freqs_o[search_o][np.argmax(psd_o[occ][:, search_o].mean(0))]
print(f"\nOccipital (O1/O2) alpha peak: eyes closed {peak_c:.1f} Hz, eyes open {peak_o:.1f} Hz")

# 4. Alpha band power (8-13 Hz) per channel, and the closed/open ratio ("alpha reactivity")
alpha_c = psd_c[:, (freqs >= 8) & (freqs <= 13)].mean(1)
alpha_o = psd_o[:, (freqs_o >= 8) & (freqs_o <= 13)].mean(1)
ratio = alpha_c / alpha_o
print("\nAlpha power 8-13 Hz, eyes closed / eyes open (highest first):")
for i in np.argsort(ratio)[::-1]:
    print(f"  {raw_closed.ch_names[i]:>4}  {ratio[i]:5.1f}x")

top3 = [raw_closed.ch_names[i] for i in np.argsort(alpha_c)[::-1][:3]]
print(f"\nThree channels with the most eyes-closed alpha power: {', '.join(top3)}")

# 5. Plots: both spectra on one axis, and the eyes-closed alpha topomap
fig, ax = plt.subplots(figsize=(8, 4))
ax.semilogy(freqs, psd_c[occ].mean(0) * 1e12, label="eyes closed", color="#2b8a3e", lw=2)
ax.semilogy(freqs_o, psd_o[occ].mean(0) * 1e12, label="eyes open", color="#868e96", lw=2)
ax.axvspan(8, 13, color="#2b8a3e", alpha=0.08)
ax.set_xlabel("frequency (Hz)")
ax.set_ylabel("power (µV²/Hz)")
ax.set_title("O1/O2 spectrum")
ax.legend()
fig.savefig(out / "lab1_spectra.png", dpi=120, bbox_inches="tight")

fig_topo = spec_closed.plot_topomap(bands={"Alpha (8-13 Hz)": (8, 13)}, show=False)
fig_topo.savefig(out / "lab1_alpha_topomap.png", dpi=120, bbox_inches="tight")
print(f"\nSaved plots to {out.resolve()}")

if SHOW:
    plt.show()
