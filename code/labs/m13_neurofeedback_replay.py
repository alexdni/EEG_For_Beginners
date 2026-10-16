"""Module 13: replay a reward/inhibit neurofeedback protocol on a recorded file.

Usage:  python code/labs/m13_neurofeedback_replay.py [output_dir]

What it does
1. Loads one minute of eyes-open EEG (sample s02) and band-passes it 1-40 Hz.
2. Every 250 ms, takes the last 1 s at Cz and computes band power in a reward band
   (15-18 Hz) and two inhibit bands (4-7 Hz theta, 22-30 Hz high beta).
3. Sets thresholds from the data (reward at the 40th percentile, inhibits at the 80th)
   and reports how often all three conditions are met, i.e. how often feedback is ON.
4. Injects fake blinks and jaw clenches and shows how they change the numbers.
5. Adds two artifact gates that PAUSE feedback instead of scoring a failure: an amplitude
   gate (catches blinks) and a 30-40 Hz power gate (catches muscle). Success is then
   counted only over the windows that were actually scored.
"""
import sys
from pathlib import Path

import numpy as np
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eeg101 import load_sample  # noqa: E402

SITE = "Cz"
REWARD = (15, 18)
INHIBITS = {"theta": (4, 7), "high beta": (22, 30)}
WIN_S, STEP_S = 1.0, 0.25
START_S, DUR_S = 60, 60


def band_powers(x, sf):
    """Band power for each 1 s window, stepping every 250 ms. Only past samples are used."""
    win, step = int(WIN_S * sf), int(STEP_S * sf)
    out = {"reward": [], "theta": [], "high beta": [], "ptp": [], "emg": []}
    for end in range(win, len(x) + 1, step):
        seg = x[end - win:end]
        f, p = signal.welch(seg, fs=sf, nperseg=win)
        bp = lambda lo, hi: p[(f >= lo) & (f < hi)].sum()  # noqa: E731
        out["reward"].append(bp(*REWARD))
        for name, (lo, hi) in INHIBITS.items():
            out[name].append(bp(lo, hi))
        out["ptp"].append(np.ptp(seg))
        out["emg"].append(bp(30, 40))
    return {k: np.array(v) for k, v in out.items()}


def feedback(bp, thr):
    return (bp["reward"] > thr["reward"]) & (bp["theta"] < thr["theta"]) & (bp["high beta"] < thr["high beta"])


def paused(bp, gate):
    """Windows the artifact gates refuse to score: too big (blink) or too much 30-40 Hz (muscle)."""
    return (bp["ptp"] > gate["ptp"]) | (bp["emg"] > gate["emg"])


def add_blinks(x, sf, every_s=4.0, amp_uv=150.0, rng=None):
    """Add blink-shaped bumps (about 300 ms wide) every few seconds."""
    y = x.copy()
    t = np.arange(int(0.4 * sf)) / sf
    blink = amp_uv * np.exp(-((t - 0.2) ** 2) / (2 * 0.06 ** 2))
    for s in np.arange(1.0, len(x) / sf - 1, every_s):
        i = int(s * sf)
        y[i:i + len(blink)] += blink
    return y


def add_jaw_clenches(x, sf, every_s=7.0, dur_s=1.0, amp_uv=15.0, rng=None):
    """Add bursts of broadband 20-60 Hz 'muscle' noise, then low-pass at 40 Hz like the real chain."""
    rng = rng or np.random.default_rng(0)
    y = x.copy()
    sos = signal.butter(4, [20, 40], "bandpass", fs=sf, output="sos")
    for s in np.arange(3.0, len(x) / sf - dur_s, every_s):
        i, n = int(s * sf), int(dur_s * sf)
        burst = signal.sosfilt(sos, rng.standard_normal(n + 200))[200:] * amp_uv * 4
        y[i:i + n] += burst
    return y


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    raw = load_sample("rest_eo").filter(1, 40, verbose="error")
    sf = raw.info["sfreq"]
    a, b = int(START_S * sf), int((START_S + DUR_S) * sf)
    x = raw.get_data(picks=[SITE])[0][a:b] * 1e6

    clean = band_powers(x, sf)
    thr = {
        "reward": np.percentile(clean["reward"], 40),
        "theta": np.percentile(clean["theta"], 80),
        "high beta": np.percentile(clean["high beta"], 80),
    }
    gate = {"ptp": np.percentile(clean["ptp"], 99) * 1.5, "emg": np.percentile(clean["emg"], 99) * 2}

    print(f"Protocol at {SITE}: reward {REWARD[0]}-{REWARD[1]} Hz, inhibit theta 4-7 Hz and high beta 22-30 Hz")
    print(f"Thresholds from the clean minute: reward > {thr['reward']:.2f} µV², "
          f"theta < {thr['theta']:.2f} µV², high beta < {thr['high beta']:.2f} µV²")
    print(f"Artifact gates: pause when a 1 s window spans more than {gate['ptp']:.0f} µV, "
          f"or 30-40 Hz power exceeds {gate['emg']:.2f} µV²\n")

    rng = np.random.default_rng(1)
    cases = {
        "clean recording": x,
        "+ a blink every 4 s": add_blinks(x, sf),
        "+ a jaw clench every 7 s": add_jaw_clenches(x, sf, rng=rng),
    }
    print(f"{'condition':26s} {'feedback ON':>11s} {'theta>thr':>10s} {'hibeta>thr':>11s} "
          f"{'paused':>7s} {'ON of scored':>13s}")
    for name, sig in cases.items():
        bp = band_powers(sig, sf)
        on, skip = feedback(bp, thr), paused(bp, gate)
        print(f"{name:26s} {on.mean() * 100:10.0f}% {np.mean(bp['theta'] > thr['theta']) * 100:9.0f}% "
              f"{np.mean(bp['high beta'] > thr['high beta']) * 100:10.0f}% {skip.mean() * 100:6.0f}% "
              f"{on[~skip].mean() * 100:12.0f}%")

    print("\nRead it like this: without gates, artifacts push the inhibit bands over threshold and the person")
    print("is told they are failing for reasons that have nothing to do with their brain. With the gates,")
    print("those windows are paused instead, and the success rate over the scored windows recovers.")

    if out_dir:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        out_dir.mkdir(parents=True, exist_ok=True)
        t = np.arange(len(clean["reward"])) * STEP_S + WIN_S + START_S
        fig, ax = plt.subplots(figsize=(10, 3))
        bp = band_powers(cases["+ a blink every 4 s"], sf)
        ax.plot(t, clean["theta"], label="theta, clean")
        ax.plot(t, bp["theta"], label="theta, with blinks", alpha=0.8)
        ax.axhline(thr["theta"], color="k", ls="--", label="inhibit threshold")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("µV²")
        ax.legend()
        fig.savefig(out_dir / "m13_theta_with_blinks.png", dpi=120, bbox_inches="tight")
        print(f"\nwrote {out_dir / 'm13_theta_with_blinks.png'}")


if __name__ == "__main__":
    main()
