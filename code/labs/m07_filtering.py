"""Module 07: filtering a recording with heavy 60 Hz line noise.

Usage:  python code/labs/m07_filtering.py [output_dir] [--show]
"""
import numpy as np
from _common import finish, plt

from eeg101 import load_sample


def peak_db(raw, freq, picks=("T3", "Cz", "O1"), absolute=False):
    """Power at `freq` relative to the median of the 6 Hz either side, in dB.

    With absolute=True, return the power at `freq` in dB re 1 µV²/Hz instead.
    """
    sp = raw.compute_psd(fmin=40, fmax=80, picks=list(picks), n_fft=int(raw.info["sfreq"] * 2), average="median")
    psd, f = sp.get_data(return_freqs=True)
    p = psd.mean(0)
    at = p[np.argmin(np.abs(f - freq))]
    if absolute:
        return 10 * np.log10(at * 1e12)
    around = p[((f >= freq - 8) & (f <= freq - 2)) | ((f >= freq + 2) & (f <= freq + 8))]
    return 10 * np.log10(at / np.median(around))


raw = load_sample("linenoise_raw")
cleaned = load_sample("linenoise_cleaned")
sf = raw.info["sfreq"]
print(f"sampling rate {sf:g} Hz, Nyquist {sf / 2:g} Hz, {raw.times[-1]:.0f} s")

# 1. The DC offset: raw values sit far from zero before any filtering.
offsets = raw.get_data().mean(axis=1) * 1e6
print(f"median DC offset across channels: {np.median(np.abs(offsets)):,.0f} µV")

# 2. How big is the line noise peak, before and after each step?
hp = raw.copy().filter(l_freq=1.0, h_freq=None)
notched = hp.copy().notch_filter(freqs=60)
print("\n60 Hz line noise (mean of T3, Cz, O1)   absolute power   above neighbours")
for label, r in (("raw file", raw), ("+ 1 Hz high-pass", hp), ("+ 60 Hz notch (MNE)", notched), ("platform cleaned file", cleaned)):
    print(f"  {label:24s} {peak_db(r, 60, absolute=True):8.1f} dB      {peak_db(r, 60):8.1f} dB")
print("  (the cleaned file's neighbours were themselves cut by its 45 Hz low-pass, so compare absolute power)")
print(f"70 Hz peak in the raw file {peak_db(raw, 70):6.1f} dB (not mains: 70 is not a multiple of 60)")
print(f"70 Hz after notching 60   {peak_db(notched, 70):6.1f} dB (a 60 Hz notch does nothing to it)")

# 3. A notch only removes the frequency you name. The 40 Hz low-pass handles 70 Hz.
band = hp.copy().notch_filter(freqs=60).filter(l_freq=None, h_freq=40.0)

# 4. The filter MNE designed for the 1 Hz high-pass: how long is it?
from mne.filter import create_filter  # noqa: E402

h = create_filter(None, sf, l_freq=1.0, h_freq=None, verbose=False)
print(f"\n1 Hz high-pass FIR: {len(h)} taps = {len(h) / sf:.1f} s of signal per output sample")
h01 = create_filter(None, sf, l_freq=0.1, h_freq=None, verbose=False)
print(f"0.1 Hz high-pass FIR: {len(h01)} taps = {len(h01) / sf:.1f} s")

# 5. Plot the spectra and the same 2 s at every stage.
fig, axes = plt.subplots(2, 1, figsize=(10, 7))
for r, label in ((raw, "raw"), (notched, "HP 1 Hz + notch 60"), (band, "HP 1 + notch 60 + LP 40"), (cleaned, "platform cleaned")):
    sp = r.compute_psd(fmin=0.5, fmax=110, picks=["T3", "Cz", "O1"], n_fft=int(sf * 2), average="median")
    psd, f = sp.get_data(return_freqs=True)
    axes[0].plot(f, 10 * np.log10(psd.mean(0) * 1e12), label=label, lw=1)
axes[0].set_xlabel("frequency (Hz)")
axes[0].set_ylabel("dB re 1 µV²/Hz")
axes[0].legend()
start = int(120 * sf)
t = np.arange(int(2 * sf)) / sf
for k, (r, label) in enumerate(((hp, "HP 1 Hz"), (notched, "+ notch"), (band, "+ LP 40"))):
    x = r.get_data(picks=["O1"])[0][start: start + len(t)] * 1e6
    axes[1].plot(t, x - k * 150, lw=0.7, label=label)
axes[1].set_xlabel("time (s) from 120 s")
axes[1].set_ylabel("O1 (offset per row)")
axes[1].legend()
fig.tight_layout()
finish(fig, "m07_filtering")
