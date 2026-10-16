"""Module 13: a real-time loop on BrainFlow's synthetic board, no headset needed.

Usage:  python code/labs/m13_brainflow_stream.py [output_dir] [--show] [--seconds 10]

What it does
1. Starts BrainFlow's SYNTHETIC_BOARD, which streams 16 channels of generated EEG-like
   signal at 250 Hz through exactly the same API a real OpenBCI, Muse or BrainBit uses.
2. Every 0.5 s, pulls the most recent 2 s from the board's ring buffer (only the past,
   as in a live neurofeedback loop).
3. Filters that window causally (Butterworth, not zero-phase: real time has no future),
   then computes Welch band power for alpha (8-13 Hz) and beta (13-30 Hz) per channel.
4. Prints a live log for a few channels and saves a plot of band power over time.

Swap BoardIds.SYNTHETIC_BOARD for your device's id (and fill in BrainFlowInputParams,
e.g. serial_port or mac_address) and the rest of the loop stays the same.
"""
import sys
import time

import numpy as np

import _common  # noqa: F401  (sets the import path, output folder and --show)
from _common import finish, plt
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, DetrendOperations, FilterTypes, WindowOperations

BOARD = BoardIds.SYNTHETIC_BOARD.value
WINDOW_S = 2.0
STEP_S = 0.5
BANDS = {"theta": (4.0, 8.0), "alpha": (8.0, 13.0), "beta": (13.0, 30.0)}
# The synthetic board puts a sine of roughly 5 x n Hz on its n-th channel (plus noise), so
# Fz carries ~5 Hz (theta), C3 ~10 Hz (alpha) and Cz ~15 Hz (beta): a built-in answer key.
SHOW_CHANNELS = ["Fz", "C3", "Cz"]

seconds = 10.0
if "--seconds" in sys.argv:
    seconds = float(sys.argv[sys.argv.index("--seconds") + 1])


def band_powers(x, sf):
    """Causal filter + Welch band power for one channel window. Modifies a copy."""
    x = np.ascontiguousarray(x, dtype=np.float64).copy()
    DataFilter.detrend(x, DetrendOperations.CONSTANT.value)
    DataFilter.perform_bandpass(x, sf, 1.0, 40.0, 4, FilterTypes.BUTTERWORTH.value, 0)  # causal
    nfft = DataFilter.get_nearest_power_of_two(sf)  # 256 samples ≈ 1 s segments
    psd = DataFilter.get_psd_welch(x, nfft, nfft // 2, sf, WindowOperations.HANNING.value)
    return {name: DataFilter.get_band_power(psd, lo, hi) for name, (lo, hi) in BANDS.items()}


def main():
    BoardShim.disable_board_logger()
    sf = BoardShim.get_sampling_rate(BOARD)
    eeg_rows = BoardShim.get_eeg_channels(BOARD)
    names = BoardShim.get_eeg_names(BOARD)
    print(f"Synthetic board: {len(eeg_rows)} EEG channels at {sf} Hz: {', '.join(names)}")

    board = BoardShim(BOARD, BrainFlowInputParams())
    board.prepare_session()
    board.start_stream()
    history = {ch: {b: [] for b in BANDS} for ch in names}
    times = []
    try:
        time.sleep(WINDOW_S)  # fill the first window
        t0 = time.time()
        header = "  t (s)  " + "  ".join(f"{ch + ' theta/alpha/beta':>24}" for ch in SHOW_CHANNELS)
        print(header)
        while time.time() - t0 < seconds:
            data = board.get_current_board_data(int(WINDOW_S * sf))  # newest samples, buffer untouched
            if data.shape[1] < int(WINDOW_S * sf):
                time.sleep(STEP_S)
                continue
            t = time.time() - t0
            times.append(t)
            cells = []
            for row, ch in zip(eeg_rows, names):
                bp = band_powers(data[row], sf)
                for b in BANDS:
                    history[ch][b].append(bp[b])
                if ch in SHOW_CHANNELS:
                    cells.append(f"{bp['theta']:6.1f}/{bp['alpha']:6.1f}/{bp['beta']:6.1f}")
            print(f"{t:7.1f}  " + "  ".join(f"{c:>24}" for c in cells))
            time.sleep(STEP_S)
    finally:
        board.stop_stream()
        board.release_session()

    print("\nMean band power over the run (µV², synthetic signal):")
    for ch in SHOW_CHANNELS:
        means = {b: np.mean(history[ch][b]) for b in BANDS}
        top = max(means, key=means.get)
        print(f"  {ch:>3}: " + "  ".join(f"{b} {v:7.1f}" for b, v in means.items()) + f"   -> mostly {top}")
    print("\nThe synthetic board puts a ~5 Hz sine on Fz, ~10 Hz on C3 and ~15 Hz on Cz, so the")
    print("loop should report theta, alpha and beta respectively. The numbers mean nothing")
    print("physiologically; the point is the loop: pull the newest window, filter causally,")
    print("compute a feature, repeat every 0.5 s. That is the core of a neurofeedback engine.")

    fig, axes = plt.subplots(1, 3, figsize=(15, 3.8))
    for ax, b in zip(axes, BANDS):
        for ch in SHOW_CHANNELS:
            ax.plot(times, history[ch][b], label=ch)
    for ax, b in zip(axes, BANDS):
        ax.set_xlabel("time since start (s)")
        ax.set_ylabel("band power (µV²)")
        ax.set_title(f"{b} power, 2 s window updated every {STEP_S} s")
        ax.legend(fontsize=8)
    fig.suptitle("BrainFlow synthetic board: a live band-power loop", fontweight="bold")
    fig.tight_layout()
    finish(fig, "m13_brainflow_stream")


if __name__ == "__main__":
    main()
