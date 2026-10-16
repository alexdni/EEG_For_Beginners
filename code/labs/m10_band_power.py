"""Module 10: spectral features from the resting-state pair and the 4-channel headband.

Usage:  python code/labs/m10_band_power.py [output_dir] [--show]
"""
import numpy as np
from _common import finish, plt

from eeg101 import BANDS, load_sample


def band_table(raw, fmin=1.0, fmax=40.0, average="median"):
    """Absolute (µV²) and relative band power per channel, from a 2 s Welch spectrum.

    Relative power divides by total fmin-fmax power. Bands that extend past fmax
    (gamma, with fmax=40) are skipped, so the relative values do not sum to 100%.
    """
    sp = raw.compute_psd(method="welch", fmin=fmin, fmax=fmax, n_fft=int(raw.info["sfreq"] * 2), average=average)
    psd, f = sp.get_data(return_freqs=True)
    psd = psd * 1e12  # V²/Hz -> µV²/Hz
    df = f[1] - f[0]
    total = psd.sum(axis=1) * df
    absolute = {b: psd[:, (f >= lo) & (f < hi)].sum(axis=1) * df for b, (lo, hi) in BANDS.items() if hi <= fmax}
    relative = {b: v / total for b, v in absolute.items()}
    return f, psd, absolute, relative


ec = load_sample("rest_ec").filter(1, 40)
eo = load_sample("rest_eo").filter(1, 40)

for label, raw in (("eyes closed", ec), ("eyes open", eo)):
    f, psd, absolute, relative = band_table(raw)
    o1 = raw.ch_names.index("O1")
    print(f"\n{label}, O1:")
    for b in absolute:
        print(f"  {b:6s} absolute {absolute[b][o1]:7.1f} µV²   relative {relative[b][o1] * 100:5.1f} %")
    # peak alpha frequency: the biggest spectral value between 7 and 14 Hz, averaged over O1, O2, Pz
    post = [raw.ch_names.index(c) for c in ("O1", "O2", "Pz")]
    m = (f >= 7) & (f <= 14)
    paf = f[m][np.argmax(psd[post][:, m].mean(0))]
    print(f"  peak alpha frequency (O1/O2/Pz): {paf:.1f} Hz")
    print(f"  theta/beta ratio at Cz: {absolute['theta'][raw.ch_names.index('Cz')] / absolute['beta'][raw.ch_names.index('Cz')]:.2f}")

# Which channels have the most alpha with eyes closed?
f, psd, absolute, relative = band_table(ec)
order = np.argsort(absolute["alpha"])[::-1]
print("\nTop 5 channels by absolute alpha power, eyes closed:",
      ", ".join(f"{ec.ch_names[i]} {absolute['alpha'][i]:.0f}" for i in order[:5]))

# Median vs mean averaging on a recording with artifacts. Deliberately NOT cropped:
# the last seconds, where the headset came off, are left in to show what one bad window does.
art = load_sample("pipeline_raw").filter(1, 40)
for avg in ("mean", "median"):
    _, _, absolute, _ = band_table(art, average=avg)
    fp1 = art.ch_names.index("Fp1")
    print(f"pipeline_raw Fp1 delta power with Welch average='{avg}': {absolute['delta'][fp1]:7.1f} µV²")

# The 4-channel headband, three conditions
print("\n4-channel headband, O1 relative power:")
fig, ax = plt.subplots(figsize=(8, 4))
for name, label in (("headband_ec", "eyes closed"), ("headband_eo", "eyes open"), ("headband_task", "eyes open, task")):
    raw = load_sample(name).filter(1, 40)
    f, psd, absolute, relative = band_table(raw)
    o1 = raw.ch_names.index("O1")
    print(f"  {label:16s} theta {relative['theta'][o1] * 100:4.1f}%  alpha {relative['alpha'][o1] * 100:4.1f}%  beta {relative['beta'][o1] * 100:4.1f}%")
    ax.plot(f, 10 * np.log10(psd[o1]), label=label)
ax.set_xlabel("frequency (Hz)")
ax.set_ylabel("dB re 1 µV²/Hz")
ax.set_title("O1 on the 4-channel headband")
ax.legend()
finish(fig, "m10_headband_spectra")

fig = ec.compute_psd(fmin=1, fmax=40).plot_topomap(show=False)
finish(fig, "m10_band_topomaps_eyes_closed")
