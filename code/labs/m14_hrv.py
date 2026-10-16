"""Module 14: heart rate variability metrics with NeuroKit2.

Usage:  python code/labs/m14_hrv.py [output_dir]

Part 1 simulates a 5-minute ECG, finds the R-peaks, and prints the standard HRV metrics.
Part 2 builds two beat sequences by hand (RR intervals modulated by breathing) to show
what slow paced breathing does to the spectrum. Everything here is SIMULATED: real
recordings come from your own ECG or PPG sensor, and the numbers will differ.
"""
import sys
from pathlib import Path

import numpy as np
from scipy import signal

try:
    import neurokit2 as nk
except ImportError:
    sys.exit("This lab needs NeuroKit2:  pip install neurokit2")

SF = 1000  # Hz, for the ECG simulation and for peak indices in Part 2


def band_powers_ms2(peaks, sf, fs_interp=4.0):
    """LF and HF power in ms², the textbook way: resample the RR series evenly, Welch, integrate.

    NeuroKit2's nk.hrv_frequency() does the same job; we do it by hand so every step is visible
    and the units are unambiguous.
    """
    t = peaks[1:] / sf
    rr = np.diff(peaks) / sf * 1000
    ti = np.arange(t[0], t[-1], 1 / fs_interp)
    rri = np.interp(ti, t, rr)
    f, p = signal.welch(rri - rri.mean(), fs=fs_interp, nperseg=min(len(rri), 256 * 2))
    df = f[1] - f[0]
    lf = p[(f >= 0.04) & (f < 0.15)].sum() * df
    hf = p[(f >= 0.15) & (f < 0.40)].sum() * df
    return lf, hf


def metrics(peaks, sf):
    """The handful of HRV numbers this course uses, from R-peak sample indices."""
    t = nk.hrv_time(peaks, sampling_rate=sf)
    rr = np.diff(peaks) / sf * 1000
    lf, hf = band_powers_ms2(peaks, sf)
    return {
        "mean HR (bpm)": 60000 / rr.mean(),
        "SDNN (ms)": float(t["HRV_SDNN"].iloc[0]),
        "RMSSD (ms)": float(t["HRV_RMSSD"].iloc[0]),
        "LF (ms²)": lf,
        "HF (ms²)": hf,
        "LF/HF": lf / hf,
    }


def rr_with_breathing(breaths_per_min, minutes=5, mean_rr_ms=900, rsa_ms=40, seed=0):
    """Beat-to-beat intervals where each breath speeds the heart up and slows it down (RSA).

    rsa_ms is the peak-to-peak swing. Slow breathing near 6/min lines up with the
    baroreflex rhythm, so the swing gets bigger: we model that by doubling it, which is
    roughly what resonance-breathing studies report, not a physiological law.
    """
    rng = np.random.default_rng(seed)
    f_breath = breaths_per_min / 60.0
    swing = rsa_ms * (2.0 if breaths_per_min <= 7 else 1.0)
    t, rr = 0.0, []
    while t < minutes * 60:
        r = mean_rr_ms + swing / 2 * np.sin(2 * np.pi * f_breath * t) + rng.normal(0, 8)
        rr.append(r)
        t += r / 1000
    peaks = np.cumsum(np.array(rr)) / 1000 * SF
    return peaks.astype(int)


def show(title, m):
    print(title)
    for k, v in m.items():
        print(f"  {k:14s} {v:10.2f}")
    print()


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None

    # Part 1: ECG -> R-peaks -> metrics
    ecg = nk.ecg_simulate(duration=300, sampling_rate=SF, heart_rate=65, heart_rate_std=4, random_state=3)
    signals, info = nk.ecg_process(ecg, sampling_rate=SF)
    peaks = info["ECG_R_Peaks"]
    print(f"Part 1: simulated 5-minute ECG, {len(peaks)} R-peaks detected\n")
    show("HRV metrics", metrics(peaks, SF))

    # Part 2: spontaneous breathing (15/min) vs resonance-frequency breathing (6/min)
    normal = metrics(rr_with_breathing(15), SF)
    paced = metrics(rr_with_breathing(6), SF)
    print("Part 2: hand-built RR series, same mean heart rate, different breathing rate")
    print(f"  {'metric':14s} {'15 breaths/min':>15s} {'6 breaths/min':>14s}")
    for k in normal:
        print(f"  {k:14s} {normal[k]:15.2f} {paced[k]:14.2f}")
    print("\nAt 15/min (0.25 Hz) the breathing rhythm sits in the HF band (0.15-0.4 Hz).")
    print("At 6/min (0.1 Hz) it moves into the LF band (0.04-0.15 Hz): LF jumps and LF/HF follows,")
    print("even though nothing about 'sympathetic balance' changed. That is why LF/HF needs care.")

    if out_dir:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        out_dir.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(10, 3))
        for bpm, color in ((15, "tab:blue"), (6, "tab:green")):
            p = rr_with_breathing(bpm)
            rr = np.diff(p) / SF * 1000
            ax.plot(np.cumsum(rr)[:120] / 1000, rr[:120], color=color, label=f"{bpm} breaths/min")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("RR interval (ms)")
        ax.legend()
        fig.savefig(out_dir / "m14_paced_breathing.png", dpi=120, bbox_inches="tight")
        print(f"\nwrote {out_dir / 'm14_paced_breathing.png'}")


if __name__ == "__main__":
    main()
