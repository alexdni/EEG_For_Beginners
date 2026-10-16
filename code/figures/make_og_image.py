"""Draw the 1200x630 link-preview image (Open Graph / Twitter card) for the site.

The traces are real: occipital channels from the rest_ec sample (s01, eyes closed), so the
alpha rhythm is what you see. Output: site/static/og-image.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from scipy.signal import butter, sosfiltfilt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eeg101 import load_sample  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "site" / "static" / "og-image.png"

BG, CYAN, VIOLET, TEXT, MUTED = "#05070d", "#22d3ee", "#a78bfa", "#f1f5f9", "#94a3b8"
CHANNELS = ["Fp1", "F3", "C3", "P3", "O1", "O2", "P4", "C4"]


def mono(weight="regular"):
    for f in font_manager.findSystemFonts():
        name = Path(f).name
        if name == ("JetBrainsMono-Bold.ttf" if weight == "bold" else "JetBrainsMono-Regular.ttf"):
            return font_manager.FontProperties(fname=f)
    return font_manager.FontProperties(family="monospace", weight=weight)


def main():
    raw = load_sample("rest_ec")
    sf = raw.info["sfreq"]
    picks = [c for c in CHANNELS if c in raw.ch_names] or raw.ch_names[:8]
    start = int(20 * sf)
    data = raw.get_data(picks=picks)[:, start:start + int(6 * sf)] * 1e6
    data = sosfiltfilt(butter(4, [1, 30], btype="band", fs=sf, output="sos"), data, axis=1)
    t = np.arange(data.shape[1]) / sf

    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=BG)
    ax.set_xlim(0, t[-1])
    n = len(picks)
    ax.set_ylim(-1.2, n + 0.2)
    ax.axis("off")
    scale = np.percentile(np.abs(data), 98) * 2.2
    for i, row in enumerate(data):
        color = VIOLET if i % 3 == 2 else CYAN
        alpha = 0.24 + 0.3 * (picks[i] in ("O1", "O2"))
        ax.plot(t, n - 1 - i + row / scale, color=color, lw=1.4, alpha=alpha)

    # darken the left side so the text reads
    grad = np.linspace(0.92, 0.0, 256)[None, :]
    ax.imshow(np.dstack([np.full((1, 256, 3), [5 / 255, 7 / 255, 13 / 255]), grad]),
              extent=(0, t[-1] * 0.85, -1.2, n + 0.2), aspect="auto", zorder=2)

    bold, reg = mono("bold"), mono()
    fig.text(0.06, 0.74, "EEG FOR BEGINNERS", color=CYAN, fontproperties=bold, fontsize=22)
    fig.text(0.06, 0.53, "Two weeks,\nreal signals.", color=TEXT, fontproperties=bold, fontsize=56,
             linespacing=1.05, va="center")
    fig.text(0.06, 0.25, "Artifacts · filtering · ICA · band power\nneurofeedback · HRV — with real EDF recordings",
             color=MUTED, fontproperties=reg, fontsize=19, linespacing=1.5, va="center")
    fig.text(0.06, 0.08, "16 modules  ·  13 sample recordings  ·  in-browser Signal Lab",
             color=VIOLET, fontproperties=reg, fontsize=16)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, facecolor=BG)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
