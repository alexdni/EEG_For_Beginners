"""Shared setup for the lab scripts: import path, output folder, --show flag."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib  # noqa: E402

SHOW = "--show" in sys.argv
if not SHOW:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import mne  # noqa: E402

mne.set_log_level("ERROR")

_args = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = Path(_args[0] if _args else "lab_outputs")
OUT.mkdir(parents=True, exist_ok=True)


def finish(fig, name):
    """Save a figure into the output folder, and show it if --show was passed."""
    path = OUT / f"{name}.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    print(f"saved {path}")
    if SHOW:
        plt.show()
    plt.close(fig)
