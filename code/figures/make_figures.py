"""Regenerate every figure in assets/figures/ from the course sample recordings.

Run from the repo root:  python code/figures/make_figures.py  [figure-name ...]
With no arguments every figure is rebuilt. Each figure is one function below,
so a module can point at the exact code that drew its pictures.
"""
import sys
import textwrap
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eeg101 import BANDS, load_sample, standard_montage  # noqa: E402

mne.set_log_level("ERROR")
warnings.filterwarnings("ignore", category=RuntimeWarning)

OUT = Path(__file__).resolve().parents[2] / "assets" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#1f2430"
MUTED = "#6b7280"
ACCENT = "#d9480f"
BAND_COLORS = {
    "delta": "#5f3dc4",
    "theta": "#1c7ed6",
    "alpha": "#2b8a3e",
    "beta": "#e67700",
    "gamma": "#c92a2a",
}
EC_COLOR, EO_COLOR = "#2b8a3e", "#868e96"

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "font.size": 10,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "axes.titleweight": "bold",
        "axes.titlesize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "text.color": INK,
        "legend.frameon": False,
    }
)

FIGURES = {}

# s05 and s06 end with a few seconds of saturated junk where the headset came off.
# Figures crop it; the lab notebooks leave it in so students can find it themselves.
TAIL_JUNK = {"artifacts_ec": 4.0, "pipeline_raw": 4.5}


def load(name):
    raw = load_sample(name)
    if name in TAIL_JUNK:
        raw.crop(0, raw.times[-1] - TAIL_JUNK[name])
    return raw


def figure(fn):
    FIGURES[fn.__name__] = fn
    return fn


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def stacked(ax, data, times, names, spacing, color=INK, lw=0.6, scalebar=True):
    """Plot channels as rows, top to bottom, like an EEG viewer."""
    for i, row in enumerate(data):
        ax.plot(times, row - i * spacing, color=color, lw=lw)
    ax.set_yticks(-np.arange(len(names)) * spacing)
    ax.set_yticklabels(names)
    ax.set_ylim(-(len(names) - 0.3) * spacing, spacing * 0.9)
    ax.set_xlim(times[0], times[-1])
    ax.set_xlabel("time (s)")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if scalebar:
        x = times[-1] + (times[-1] - times[0]) * 0.01
        y0 = -(len(names) - 1) * spacing
        ax.plot([x, x], [y0, y0 + spacing], color=ACCENT, lw=2, clip_on=False)
        ax.text(x, y0 + spacing / 2, f" {spacing:g} µV", color=ACCENT, va="center", fontsize=9)


def window(raw, start, dur, picks=None):
    sf = raw.info["sfreq"]
    a, b = int(start * sf), int((start + dur) * sf)
    data = raw.get_data(picks=picks)[:, a:b] * 1e6
    return data, np.arange(data.shape[1]) / sf + start


def psd_db(raw, picks=None, fmin=1, fmax=45, average="median"):
    sp = raw.compute_psd(
        method="welch", fmin=fmin, fmax=fmax, picks=picks,
        n_fft=int(raw.info["sfreq"] * 2), average=average,
    )
    psd, f = sp.get_data(return_freqs=True)
    return f, 10 * np.log10(psd * 1e12)  # dB re 1 µV²/Hz


def best_window(raw, dur, score, step=0.5, max_ptp=None, check=None):
    """Start time of the window that maximises score(data).

    max_ptp skips windows where any channel (of `check`, or the scored data) swings more
    than that many µV, so the search finds a typical artifact rather than a saturated one.
    """
    sf = raw.info["sfreq"]
    starts = np.arange(3, raw.times[-1] - dur - 3, step)
    data = raw.get_data() * 1e6
    ref = check.get_data() * 1e6 if check is not None else data
    best, best_s = -np.inf, float(starts[0])
    for s in starts:
        a, b = int(s * sf), int((s + dur) * sf)
        if max_ptp is not None and np.ptp(ref[:, a:b], axis=1).max() > max_ptp:
            continue
        v = score(data[:, a:b])
        if v > best:
            best, best_s = v, float(s)
    return best_s


# --------------------------------------------------------------------------
# Module 01-04: what the signal is
# --------------------------------------------------------------------------


@figure
def raw_trace_eyes_closed():
    raw = load_sample("rest_ec").filter(1, 40)
    data, t = window(raw, 60, 8)
    fig, ax = plt.subplots(figsize=(10, 7))
    stacked(ax, data, t, raw.ch_names, spacing=60)
    for name in ("O1", "O2", "Pz"):
        i = raw.ch_names.index(name)
        ax.plot(t, data[i] - i * 60, color=BAND_COLORS["alpha"], lw=0.8)
    ax.set_title("Eyes closed, 19 channels, 1-40 Hz. The green rows (O1, O2, Pz) carry the posterior alpha rhythm")
    save(fig, "raw_trace_eyes_closed")


@figure
def alpha_zoom():
    raw = load_sample("rest_ec").filter(1, 40)
    data, t = window(raw, 62, 2, picks=["O1"])
    fig, ax = plt.subplots(figsize=(10, 2.6))
    ax.plot(t, data[0], color=BAND_COLORS["alpha"], lw=1.2)
    peaks, _ = signal.find_peaks(data[0], distance=int(raw.info["sfreq"] / 14), prominence=8)
    ax.plot(t[peaks], data[0][peaks], "o", ms=3, color=INK)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("µV")
    ax.set_title(f"Two seconds of O1 with eyes closed: {len(peaks)} peaks ≈ {len(peaks) / 2:.0f} Hz")
    save(fig, "alpha_zoom")


@figure
def frequency_bands():
    raw = load_sample("rest_ec")
    sf = raw.info["sfreq"]
    _, t = window(raw, 60, 4, picks=["O1"])
    broad = raw.copy().filter(1, 45).get_data(picks=["O1"])[0] * 1e6
    a, b = int(60 * sf), int(64 * sf)
    fig, axes = plt.subplots(6, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(t, broad[a:b], color=INK, lw=0.7)
    axes[0].set_ylabel("1-45 Hz", rotation=0, ha="right", va="center")
    for ax, (band, (lo, hi)) in zip(axes[1:], BANDS.items()):
        x = raw.copy().filter(lo, hi, picks=["O1"]).get_data(picks=["O1"])[0][a:b] * 1e6
        ax.plot(t, x, color=BAND_COLORS[band], lw=0.9)
        ax.set_ylabel(f"{band}\n{lo:g}-{hi:g} Hz", rotation=0, ha="right", va="center")
        ax.set_ylim(-30, 30)
    for ax in axes:
        ax.spines["left"].set_visible(False)
        ax.set_yticks([])
    axes[0].set_title("One channel (O1, eyes closed) split into the five conventional bands")
    axes[-1].set_xlabel("time (s); every band row is drawn on the same ±30 µV scale")
    save(fig, "frequency_bands")


@figure
def psd_eyes_closed_vs_open():
    ec, eo = load_sample("rest_ec"), load_sample("rest_eo")
    picks = ["O1", "O2", "Pz"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"width_ratios": [1.4, 1]})
    for raw, color, label in ((ec, EC_COLOR, "eyes closed"), (eo, EO_COLOR, "eyes open")):
        f, p = psd_db(raw.copy().filter(1, 45), picks=picks)
        axes[0].plot(f, p.mean(0), color=color, lw=2, label=label)
    for band, (lo, hi) in BANDS.items():
        axes[0].axvspan(lo, hi, color=BAND_COLORS[band], alpha=0.06)
        axes[0].text((lo + hi) / 2, axes[0].get_ylim()[1], band, ha="center", va="top", fontsize=8, color=BAND_COLORS[band])
    axes[0].set_xlabel("frequency (Hz)")
    axes[0].set_ylabel("power (dB re 1 µV²/Hz)")
    axes[0].set_title("Mean spectrum of O1, O2, Pz")
    axes[0].legend(loc="lower left")

    def alpha_power(raw):
        sp = raw.copy().filter(1, 45).compute_psd(fmin=8, fmax=13, n_fft=int(raw.info["sfreq"] * 2), average="median")
        return sp.get_data().mean(1) * 1e12

    ratio = alpha_power(ec) / alpha_power(eo)
    order = np.argsort(ratio)[::-1]
    axes[1].barh([ec.ch_names[i] for i in order][::-1], ratio[order][::-1], color=EC_COLOR)
    axes[1].axvline(1, color=MUTED, lw=1, ls="--")
    axes[1].set_xlabel("alpha power, closed ÷ open")
    axes[1].set_title("Alpha reactivity per channel")
    save(fig, "psd_eyes_closed_vs_open")


@figure
def alpha_topomaps():
    fig, axes = plt.subplots(1, 2, figsize=(7, 3.4))
    vals = []
    for name in ("rest_ec", "rest_eo"):
        raw = load_sample(name).filter(1, 45)
        sp = raw.compute_psd(fmin=8, fmax=13, n_fft=int(raw.info["sfreq"] * 2), average="median")
        vals.append((raw, 10 * np.log10(sp.get_data().mean(1) * 1e12)))
    vmin = min(v.min() for _, v in vals)
    vmax = max(v.max() for _, v in vals)
    for ax, (raw, v), title in zip(axes, vals, ("eyes closed", "eyes open")):
        im, _ = mne.viz.plot_topomap(v, raw.info, axes=ax, show=False, vlim=(vmin, vmax), cmap="viridis", names=raw.ch_names, sensors=True)
        ax.set_title(title)
    cb = fig.colorbar(im, ax=axes, shrink=0.7)
    cb.set_label("alpha power 8-13 Hz (dB)")
    fig.suptitle("Where the alpha is: same person, same session", fontweight="bold")
    save(fig, "alpha_topomaps")


@figure
def electrode_layout():
    raw = load_sample("rest_ec")
    pos = raw.get_montage().get_positions()["ch_pos"]
    fig, ax = plt.subplots(figsize=(6, 6.3))
    mne.viz.plot_sensors(raw.info, axes=ax, show_names=False, show=False, kind="topomap")
    ax.collections[0].set_sizes([0])
    lobes = {"Fp": "#e67700", "F": "#1c7ed6", "C": "#2b8a3e", "T": "#c92a2a", "P": "#5f3dc4", "O": "#0b7285"}
    from mne.channels.layout import _find_topomap_coords

    xy = _find_topomap_coords(raw.info, picks=list(range(len(raw.ch_names))))
    for (x, y), name in zip(xy, raw.ch_names):
        key = "Fp" if name.startswith("Fp") else name[0]
        ax.add_patch(plt.Circle((x, y), 0.012, color=lobes[key], zorder=3))
        ax.text(x, y, name, ha="center", va="center", color="white", fontsize=8, fontweight="bold", zorder=4)
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, label=lab) for lab, c in
               (("Fp prefrontal", lobes["Fp"]), ("F frontal", lobes["F"]), ("C central", lobes["C"]),
                ("T temporal", lobes["T"]), ("P parietal", lobes["P"]), ("O occipital", lobes["O"]))]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8)
    ax.set_title("The 19 electrodes used in the course recordings\nodd = left, even = right, z = midline; nose at top")
    del pos
    save(fig, "electrode_layout")


def blink_times(raw, min_uv=80, max_uv=400):
    """Peak times (s) of blink-like bumps in the mean of Fp1 and Fp2, 0.5-8 Hz."""
    slow = raw.copy().filter(0.5, 8).get_data(picks=["Fp1", "Fp2"]).mean(0) * 1e6
    sf = raw.info["sfreq"]
    peaks, props = signal.find_peaks(np.abs(slow), height=(min_uv, max_uv), distance=int(sf))
    return peaks / sf, props["peak_heights"]


# --------------------------------------------------------------------------
# Module 05: artifacts field guide
# --------------------------------------------------------------------------


def _artifact_panel(ax, raw, start, dur, picks, spacing, title, highlight=()):
    data, t = window(raw, start, dur, picks=picks)
    stacked(ax, data, t, picks, spacing=spacing)
    for name in highlight:
        i = picks.index(name)
        ax.plot(t, data[i] - i * spacing, color=ACCENT, lw=1.0)
    ax.set_title(textwrap.fill(title, 48), loc="left", fontsize=10)


@figure
def artifact_gallery():
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.ravel()

    # blink: a typical blink in s06, centred in the window
    raw = load("pipeline_raw").filter(0.5, 40)
    times, heights = blink_times(raw)
    t_blink = float(times[np.argsort(heights)[len(heights) // 2]])
    _artifact_panel(axes[0], raw, t_blink - 1.5, 3, ["Fp1", "Fp2", "F3", "F4", "Cz", "Pz", "O1", "O2"], 100,
                    "Eye blink: big, fast-rising, same sign at Fp1 and Fp2, fades toward the back", ("Fp1", "Fp2"))

    # lateral eye movement: F7 and F8 deflect in opposite directions
    raw = load_sample("rest_eo").filter(0.5, 40)
    # (s05 is full of slow rolling eye movements too: see the reference and ICA figures)
    f7, f8 = raw.ch_names.index("F7"), raw.ch_names.index("F8")
    slow = raw.copy().filter(None, 3)
    s = best_window(slow, 3, lambda d: np.ptp(d[f7] - d[f8]) - abs(np.ptp(d[f7] + d[f8])), max_ptp=350, check=raw)
    _artifact_panel(axes[1], raw, s, 3, ["Fp1", "Fp2", "F7", "F8", "T3", "T4", "O1", "O2"], 100,
                    "Lateral eye movement: F7 and F8 swing in opposite directions", ("F7", "F8"))

    # muscle: the window with the most 20-45 Hz power on temporal/frontal-lateral channels
    best = None
    for name in ("rest_eo", "pipeline_raw", "rest_ec", "artifacts_ec"):
        raw = load_sample(name).filter(1, 45)
        hf = raw.copy().filter(20, 45)
        lat = [hf.ch_names.index(c) for c in ("T3", "T4", "T5", "T6", "F7", "F8")]
        s = best_window(hf, 3, lambda d: np.median(np.std(d[lat], axis=1)), max_ptp=300, check=raw)
        score = np.median(np.std(window(hf, s, 3)[0][lat], axis=1))
        if best is None or score > best[0]:
            best = (score, raw, s)
    _, raw, s = best
    _artifact_panel(axes[2], raw, s, 3, ["F7", "F8", "T3", "T4", "T5", "T6", "Cz", "O1"], 80,
                    "Muscle (EMG): dense high-frequency fuzz, worst on temporal sites", ("T3", "T4", "T5", "T6"))

    # line noise: raw recording, only drift removed
    raw = load_sample("linenoise_raw").filter(1, None)
    _artifact_panel(axes[3], raw, 100, 0.25, ["Fp1", "T3", "O1"], 400,
                    "60 Hz line noise: a fixed-frequency hum, 15 cycles per quarter second", ("T3",))

    # slow rolling eye movements: s05 is eyes-closed, but the eyes keep drifting (common when drowsy)
    raw = load("artifacts_ec").filter(0.5, 40)
    _artifact_panel(axes[4], raw, 14, 8, ["Fp1", "Fp2", "F7", "F8", "Cz", "O1", "O2"], 200,
                    "Slow eye movements: rolling 0.3-1 Hz waves at Fp/F7/F8 while alpha carries on at O1/O2",
                    ("Fp1", "Fp2", "F7", "F8"))

    # slow drift: sweat / poor contact, shown with only a 0.05 Hz high-pass
    raw = load_sample("segments_original").filter(0.05, 40)
    sd = raw.copy().filter(None, 0.5)
    i = int(np.argmax(np.std(sd.get_data(), axis=1)))
    _artifact_panel(axes[5], raw, 5, 30, raw.ch_names, 300,
                    f"Slow drift: wandering baseline over tens of seconds (worst: {raw.ch_names[i]})", (raw.ch_names[i],))
    fig.tight_layout()
    save(fig, "artifact_gallery")


# --------------------------------------------------------------------------
# Module 07: filtering
# --------------------------------------------------------------------------


@figure
def line_noise_spectrum():
    raw = load_sample("linenoise_raw")
    clean = load_sample("linenoise_cleaned")
    picks = ["T3", "Cz", "O1"]
    fig, ax = plt.subplots(figsize=(10, 4))
    f, p = psd_db(raw, picks=picks, fmin=0.5, fmax=110)
    ax.plot(f, p.mean(0), color=INK, lw=1.2, label="raw file as recorded")
    notched = raw.copy().notch_filter([60], picks="eeg")
    f, p = psd_db(notched, picks=picks, fmin=0.5, fmax=110)
    ax.plot(f, p.mean(0), color=ACCENT, lw=1.2, label="after a 60 Hz notch")
    f, p = psd_db(clean, picks=picks, fmin=0.5, fmax=110)
    ax.plot(f, p.mean(0), color=EC_COLOR, lw=1.6, label="after the full pipeline (1 Hz HP, 45 Hz LP, 60 Hz notch, artifact repair)")
    ax.axvline(60, color=MUTED, ls=":", lw=1)
    ax.text(61, ax.get_ylim()[1] - 5, "60 Hz mains", color=MUTED, fontsize=9, va="top")
    ax.set_xlabel("frequency (Hz)")
    ax.set_ylabel("power (dB re 1 µV²/Hz)")
    ax.set_title("Same eyes-closed recording before and after cleaning (mean of T3, Cz, O1)")
    ax.legend(loc="lower left", fontsize=9)
    save(fig, "line_noise_spectrum")


@figure
def filter_steps_time_domain():
    raw = load_sample("linenoise_raw")
    steps = [
        ("as recorded (DC offset removed)", raw.copy()),
        ("+ high-pass 1 Hz", raw.copy().filter(1, None)),
        ("+ notch 60 Hz", raw.copy().filter(1, None).notch_filter(60)),
        ("+ low-pass 40 Hz", raw.copy().filter(1, 40).notch_filter(60)),
    ]
    fig, axes = plt.subplots(len(steps), 1, figsize=(10, 7.5), sharex=True)
    for ax, (label, r) in zip(axes, steps):
        d, t = window(r, 120, 1, picks=["T3", "O1"])
        d = d - d.mean(axis=1, keepdims=True)
        ax.plot(t, d[0] + 60, color=INK, lw=0.6)
        ax.plot(t, d[1] - 60, color=EC_COLOR, lw=0.6)
        lim = max(200, np.abs(d).max() * 1.05)
        off = lim * 0.3
        ax.lines[-2].set_ydata(d[0] + off)
        ax.lines[-1].set_ydata(d[1] - off)
        ax.set_yticks([off, -off])
        ax.set_yticklabels(["T3", "O1"])
        ax.set_ylim(-lim, lim)
        ax.set_title(f"{label}    (axis ±{lim:,.0f} µV)", loc="left", fontsize=10)
        ax.spines["left"].set_visible(False)
    axes[-1].set_xlabel("time (s); note how the vertical scale shrinks as each filter is added")
    fig.suptitle("Building up a filter chain on the same 1 second", fontweight="bold")
    fig.tight_layout()
    save(fig, "filter_steps_time_domain")


@figure
def filter_responses():
    sf = 250.0
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.8))
    designs = {
        "FIR, 1 Hz high-pass (MNE default)": mne.filter.create_filter(None, sf, l_freq=1, h_freq=None, verbose=False),
        "FIR, 0.1 Hz high-pass": mne.filter.create_filter(None, sf, l_freq=0.1, h_freq=None, verbose=False),
    }
    for (label, h), color in zip(designs.items(), (ACCENT, "#1c7ed6")):
        w, H = signal.freqz(h, worN=2 ** 16, fs=sf)
        axes[0].plot(w, 20 * np.log10(np.abs(H) + 1e-12), color=color, label=f"{label} ({len(h)} taps)")
    axes[0].set_xlim(0, 5)
    axes[0].set_ylim(-60, 5)
    axes[0].set_xlabel("frequency (Hz)")
    axes[0].set_ylabel("gain (dB)")
    axes[0].set_title("High-pass: what gets through")
    axes[0].legend(fontsize=8, loc="lower right")

    b, a = signal.iirnotch(60, 30, sf)
    w, H = signal.freqz(b, a, worN=2 ** 14, fs=sf)
    axes[1].plot(w, 20 * np.log10(np.abs(H) + 1e-12), color=ACCENT)
    axes[1].set_xlim(40, 80)
    axes[1].set_xlabel("frequency (Hz)")
    axes[1].set_title("Notch at 60 Hz (Q = 30)")

    # step response: why filters distort shape and timing
    t = np.arange(-1, 3, 1 / sf)
    x = (t >= 0).astype(float) * 50
    sos_causal = signal.butter(4, 1, "highpass", fs=sf, output="sos")
    axes[2].plot(t, x, color=MUTED, lw=1, label="input: a 50 µV step")
    axes[2].plot(t, signal.sosfilt(sos_causal, x), color="#1c7ed6", lw=1.4, label="causal (real-time) 1 Hz HP")
    axes[2].plot(t, signal.sosfiltfilt(sos_causal, x), color=ACCENT, lw=1.4, label="zero-phase (offline) 1 Hz HP")
    axes[2].set_xlabel("time (s)")
    axes[2].set_ylabel("µV")
    axes[2].set_title("Filters change shape and timing")
    axes[2].legend(fontsize=8)
    fig.tight_layout()
    save(fig, "filter_responses")


# --------------------------------------------------------------------------
# Module 08: re-referencing
# --------------------------------------------------------------------------


@figure
def reference_comparison():
    raw = load_sample("rest_ec").filter(1, 40)
    picks = ["Fp1", "F3", "C3", "P3", "O1", "Cz"]
    versions = [
        ("as recorded (device reference)", raw.copy()),
        ("average reference", raw.copy().set_eeg_reference("average")),
        ("Cz reference", raw.copy().set_eeg_reference(["Cz"])),
    ]
    start = 60
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.5))
    for ax, (label, r) in zip(axes[:3], versions):
        d, t = window(r, start, 3, picks=picks)
        stacked(ax, d, t, picks, spacing=60, scalebar=ax is axes[2])
        ax.set_title(label, loc="left", fontsize=10)
    # bipolar longitudinal chain on the left side
    pairs = [("Fp1", "F3"), ("F3", "C3"), ("C3", "P3"), ("P3", "O1")]
    bip = mne.set_bipolar_reference(raw.copy(), [a for a, _ in pairs], [b for _, b in pairs], verbose=False)
    names = [f"{a}-{b}" for a, b in pairs]
    d, t = window(bip, start, 3, picks=names)
    stacked(axes[3], d, t, names, spacing=60, scalebar=False)
    axes[3].set_title("bipolar chain (left side, front to back)", loc="left", fontsize=10)
    fig.suptitle("Same 3 seconds of eyes-closed EEG, four references. Cz goes flat when it is the reference; "
                 "bipolar pairs show only local differences", fontweight="bold")
    fig.tight_layout()
    save(fig, "reference_comparison")


# --------------------------------------------------------------------------
# Module 09: artifact handling (rejection, ICA, ASR-style pipelines)
# --------------------------------------------------------------------------


@figure
def segment_rejection():
    raw = load_sample("segments_original").filter(1, 40)
    kept = load_sample("segments_removed")
    fig, axes = plt.subplots(2, 1, figsize=(12, 6.5), gridspec_kw={"height_ratios": [2, 1]})
    d, t = window(raw, 0, raw.times[-1], picks=raw.ch_names)
    stacked(axes[0], d, t, raw.ch_names, spacing=200, lw=0.3)
    # the cleaned file stores what it removed as annotations with timestamps in the description
    for desc in kept.annotations.description:
        parts = desc.split()
        dur = float(parts[2])
        h, m, s = parts[-1].split(":")
        onset = int(h) * 3600 + int(m) * 60 + float(s)
        axes[0].axvspan(onset, onset + dur, color=ACCENT, alpha=0.18, lw=0)
    axes[0].set_title(f"8-channel headset, {raw.times[-1]:.0f} s. Shaded: the {len(kept.annotations)} segments cut by automatic rejection", loc="left")
    # both files start with a filter edge and end with a large transient the rejection missed: trim them
    trimmed = []
    for r in (raw.copy(), kept.copy().filter(1, 40)):
        trimmed.append(r.crop(2, r.times[-1] - 3))
    powers = []
    for r, color, label in ((trimmed[0], MUTED, f"original ({raw.times[-1]:.0f} s)"),
                            (trimmed[1], EC_COLOR, f"after rejection ({kept.times[-1]:.0f} s)")):
        f, p = psd_db(r, average="mean")
        axes[1].plot(f, p.mean(0), color=color, lw=1.6, label=label)
        powers.append(p.mean())
    axes[1].set_xlabel("frequency (Hz)")
    axes[1].set_ylabel("dB")
    diff = powers[1] - powers[0]
    verdict = (f"{diff:.1f} dB HIGHER after rejection: each cut leaves a splice step that adds broadband power"
               if diff > 0 else f"{-diff:.1f} dB lower after rejection")
    axes[1].set_title(f"Mean-averaged spectrum (edges trimmed): {verdict}", loc="left", fontsize=10)
    axes[1].legend()
    fig.tight_layout()
    save(fig, "segment_rejection")


@figure
def pipeline_stages():
    stages = [
        ("stage 0: raw export", load("pipeline_raw").filter(1, 40), MUTED),
        ("stage 1: bad-segment rejection only", load_sample("pipeline_rejection").filter(1, 40), "#1c7ed6"),
        ("stage 2: full pipeline (rejection + ASR/ICA repair)", load_sample("pipeline_full"), EC_COLOR),
    ]
    picks = ["Fp1", "Fp2", "F7", "F8", "T3", "T4", "Cz", "O1", "O2"]
    fig = plt.figure(figsize=(15, 8))
    gs = fig.add_gridspec(2, 3, height_ratios=[2.2, 1])
    for k, (label, r, color) in enumerate(stages):
        ax = fig.add_subplot(gs[0, k])
        d, t = window(r, 10, 6, picks=picks)
        stacked(ax, d, t, picks, spacing=100, color=color, scalebar=k == 2)
        ax.set_title(f"{label}\n{r.times[-1]:.0f} s long", loc="left", fontsize=10)
    ax = fig.add_subplot(gs[1, :])
    for label, r, color in stages:
        f, p = psd_db(r, average="mean")
        ax.plot(f, p.mean(0), color=color, lw=1.8, label=label)
    ax.set_xlabel("frequency (Hz)")
    ax.set_ylabel("dB")
    ax.legend(fontsize=9)
    ax.set_title("Mean spectra. Stage 1 cuts bad segments but leaves sharp splice steps where the pieces join "
                 "(e.g. at 7.7 s), adding power;\nstage 2 repairs instead of cutting and matches raw above ~3 Hz, removing mostly slow eye/drift power", loc="left", fontsize=10)
    fig.suptitle("Three exports of the same recording from the Divergence artifact pipeline", fontweight="bold")
    fig.tight_layout()
    save(fig, "pipeline_stages")


def _fit_ica():
    from mne.preprocessing import ICA

    raw = load("pipeline_raw").filter(1, 40).set_eeg_reference("average")
    ica = ICA(n_components=15, random_state=97, max_iter="auto")
    ica.fit(raw)
    fp = raw.copy().pick(["Fp1", "Fp2"]).get_data().mean(0)
    src = ica.get_sources(raw).get_data()
    corr = np.array([abs(np.corrcoef(s, fp)[0, 1]) for s in src])
    return raw, ica, int(np.argmax(corr)), corr


@figure
def ica_components():
    raw, ica, blink, corr = _fit_ica()
    figs = ica.plot_components(show=False)
    fig = figs[0] if isinstance(figs, list) else figs
    for ax, c in zip(fig.axes, corr):
        ax.set_title(ax.get_title() + f"\nr={c:.2f}", fontsize=8)
    fig.suptitle(f"15 ICA components; r = correlation with the Fp1/Fp2 signal. ICA{blink:03d} is the blink.", fontweight="bold")
    fig.savefig(OUT / "ica_components.png", facecolor="white", dpi=130)
    plt.close(fig)
    print("wrote ica_components")


@figure
def ica_before_after():
    raw, ica, blink, _ = _fit_ica()
    ica.exclude = [blink]
    clean = ica.apply(raw.copy())
    times, heights = blink_times(raw)
    s = float(times[np.argsort(heights)[len(heights) // 2]]) - 2
    picks = ["Fp1", "Fp2", "F3", "F4", "Cz", "O1", "O2"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), gridspec_kw={"width_ratios": [1, 1, 0.7]})
    for ax, r, label, color in ((axes[0], raw, "before: average reference, 1-40 Hz", INK),
                                (axes[1], clean, f"after removing ICA{blink:03d}", EC_COLOR)):
        d, t = window(r, s, 4, picks=picks)
        stacked(ax, d, t, picks, spacing=100, color=color, scalebar=ax is axes[1])
        ax.set_title(label, loc="left", fontsize=10)
    src = ica.get_sources(raw).get_data(picks=[blink])[0]
    sf = raw.info["sfreq"]
    tt = np.arange(int(4 * sf)) / sf + s
    seg = src[int(s * sf): int(s * sf) + len(tt)]
    axes[2].plot(tt, seg / np.abs(seg).max(), color=ACCENT)
    axes[2].set_title(f"ICA{blink:03d} time course", loc="left", fontsize=10)
    axes[2].set_yticks([])
    axes[2].set_xlabel("time (s)")
    fig.tight_layout()
    save(fig, "ica_before_after")


# --------------------------------------------------------------------------
# Module 10: spectral features
# --------------------------------------------------------------------------


@figure
def welch_explainer():
    raw = load_sample("rest_ec").filter(1, 45)
    sf = raw.info["sfreq"]
    x = raw.get_data(picks=["O1"])[0][int(60 * sf): int(68 * sf)] * 1e6
    t = np.arange(len(x)) / sf
    nper = int(2 * sf)
    fig, axes = plt.subplots(1, 3, figsize=(15, 3.8), gridspec_kw={"width_ratios": [1.4, 1, 1]})
    axes[0].plot(t, x, color=INK, lw=0.6)
    colors = plt.cm.viridis(np.linspace(0, 0.9, 7))
    starts = np.arange(0, len(x) - nper + 1, nper // 2)
    for k, st in enumerate(starts):
        axes[0].axvspan(st / sf, (st + nper) / sf, ymin=0.02 + 0.02 * k, ymax=0.06 + 0.02 * k, color=colors[k % 7])
    axes[0].set_title("1. Cut 8 s of O1 into 2 s windows, 50% overlap", loc="left")
    axes[0].set_xlabel("time (s)")
    axes[0].set_ylabel("µV")
    win = signal.get_window("hann", nper)
    specs = []
    for k, st in enumerate(starts):
        f, p = signal.periodogram(x[st: st + nper], fs=sf, window=win)
        specs.append(p)
        axes[1].plot(f, p, color=colors[k % 7], lw=0.8)
    axes[1].set_xlim(1, 30)
    axes[1].set_title("2. Taper each window, take its spectrum", loc="left")
    axes[1].set_xlabel("frequency (Hz)")
    axes[1].set_ylabel("µV²/Hz")
    f, p = signal.welch(x, fs=sf, nperseg=nper)
    axes[2].plot(f, p, color=EC_COLOR, lw=2)
    lo, hi = BANDS["alpha"]
    m = (f >= lo) & (f <= hi)
    axes[2].fill_between(f[m], p[m], color=EC_COLOR, alpha=0.25)
    bp = np.trapezoid(p[m], f[m]) if hasattr(np, "trapezoid") else np.trapz(p[m], f[m])
    axes[2].text(hi + 1, p.max() * 0.7, f"alpha band power\n= area = {bp:.0f} µV²", color=EC_COLOR)
    axes[2].set_xlim(1, 30)
    axes[2].set_title("3. Average them: the Welch spectrum", loc="left")
    axes[2].set_xlabel("frequency (Hz)")
    fig.tight_layout()
    save(fig, "welch_explainer")


@figure
def band_power_topomaps():
    raw = load_sample("rest_ec").filter(1, 45).set_eeg_reference("average")
    sp = raw.compute_psd(fmin=1, fmax=45, n_fft=int(raw.info["sfreq"] * 2), average="median")
    psd, f = sp.get_data(return_freqs=True)
    total = psd.sum(1)
    fig, axes = plt.subplots(1, 5, figsize=(14, 3.2))
    for ax, (band, (lo, hi)) in zip(axes, BANDS.items()):
        rel = psd[:, (f >= lo) & (f < hi)].sum(1) / total
        im, _ = mne.viz.plot_topomap(rel * 100, raw.info, axes=ax, show=False, cmap="magma")
        ax.set_title(f"{band} {lo:g}-{hi:g} Hz\n{rel.min() * 100:.0f}-{rel.max() * 100:.0f}% of total", color=BAND_COLORS[band])
        fig.colorbar(im, ax=ax, shrink=0.6, format="%.0f%%")
    fig.suptitle("Relative band power, eyes closed, average reference (each map has its own scale)", fontweight="bold")
    save(fig, "band_power_topomaps")


@figure
def headband_conditions():
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
    conds = (("headband_ec", "eyes closed", EC_COLOR), ("headband_eo", "eyes open", EO_COLOR),
             ("headband_task", "eyes open, mental task", "#e67700"))
    rows = []
    for name, label, color in conds:
        raw = load_sample(name).filter(1, 40)
        f, p = psd_db(raw, picks=["O1"])
        axes[0].plot(f, p[0], color=color, lw=1.8, label=label)
        sp = raw.compute_psd(fmin=1, fmax=40, n_fft=int(raw.info["sfreq"] * 2), average="median")
        psd, ff = sp.get_data(return_freqs=True)
        band = {b: psd[:, (ff >= lo) & (ff < hi)].sum(1) for b, (lo, hi) in BANDS.items() if hi <= 40}
        tot = psd.sum(1)
        rows.append((label, color, {b: v / tot for b, v in band.items()}, raw.ch_names))
    axes[0].set_xlabel("frequency (Hz)")
    axes[0].set_ylabel("dB")
    axes[0].set_title("O1 spectrum on a 4-channel headband", loc="left")
    axes[0].legend()
    width = 0.27
    bands = ["theta", "alpha", "beta"]
    x = np.arange(len(bands))
    for k, (label, color, rel, names) in enumerate(rows):
        o1 = names.index("O1")
        axes[1].bar(x + (k - 1) * width, [rel[b][o1] * 100 for b in bands], width, color=color, label=label)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(bands)
    axes[1].set_ylabel("% of 1-40 Hz power at O1")
    axes[1].set_title("Relative band power is the feature most protocols use", loc="left")
    fig.tight_layout()
    save(fig, "headband_conditions")


# --------------------------------------------------------------------------
# Module 11: epochs and ERPs (synthetic, clearly labelled)
# --------------------------------------------------------------------------


@figure
def erp_averaging():
    rng = np.random.default_rng(7)
    sf = 250
    t = np.arange(-0.2, 0.8, 1 / sf)
    erp = 6 * np.exp(-((t - 0.3) ** 2) / (2 * 0.06 ** 2)) - 3 * np.exp(-((t - 0.1) ** 2) / (2 * 0.02 ** 2))
    bg = load_sample("rest_eo").filter(1, 30).get_data(picks=["Pz"])[0] * 1e6
    n_max = 160
    starts = rng.integers(0, len(bg) - len(t), n_max)
    trials = np.array([bg[s: s + len(t)] + erp for s in starts])
    trials -= trials[:, t < 0].mean(axis=1, keepdims=True)  # baseline correction
    trials = trials[np.ptp(trials, axis=1) < 80]  # drop epochs hit by blinks or drift
    fig, axes = plt.subplots(1, 4, figsize=(15, 3.4), sharey=True)
    for ax, n in zip(axes, (1, 10, 40, min(100, len(trials)))):
        if n > 1:
            for tr in trials[:min(n, 20)]:
                ax.plot(t, tr, color=MUTED, lw=0.3, alpha=0.4)
        ax.plot(t, trials[:n].mean(0), color=ACCENT, lw=1.8, label="average")
        ax.plot(t, erp, color=INK, lw=1, ls="--", label="true response")
        ax.axvline(0, color=MUTED, lw=0.8)
        ax.set_title(f"{n} trial{'s' if n > 1 else ''}")
        ax.set_xlabel("time from stimulus (s)")
        ax.set_ylim(-40, 40)
    axes[0].set_ylabel("µV")
    axes[0].legend(fontsize=8, loc="lower right")
    fig.suptitle("Averaging epochs: a 6 µV response buried in real background EEG (Pz) emerges as trials accumulate. The response is simulated.", fontweight="bold")
    fig.tight_layout()
    save(fig, "erp_averaging")


# --------------------------------------------------------------------------
# Module 13: neurofeedback (computed on the real recording)
# --------------------------------------------------------------------------


@figure
def neurofeedback_simulation():
    raw = load_sample("rest_eo").filter(1, 40)
    sf = raw.info["sfreq"]
    x = raw.get_data(picks=["Cz"])[0] * 1e6
    win, step = int(1 * sf), int(0.25 * sf)
    times, reward, inhibit_theta, inhibit_hibeta = [], [], [], []
    for st in range(0, len(x) - win, step):
        f, p = signal.welch(x[st: st + win], fs=sf, nperseg=win)
        bp = lambda lo, hi: p[(f >= lo) & (f < hi)].sum()
        times.append((st + win) / sf)
        reward.append(bp(15, 18))
        inhibit_theta.append(bp(4, 7))
        inhibit_hibeta.append(bp(22, 30))
    times, reward, it, ih = map(np.array, (times, reward, inhibit_theta, inhibit_hibeta))
    sl = slice(int(60 / 0.25), int(120 / 0.25))
    t = times[sl]
    thr_r = np.percentile(reward[sl], 40)
    thr_t = np.percentile(it[sl], 80)
    thr_h = np.percentile(ih[sl], 80)
    ok = (reward[sl] > thr_r) & (it[sl] < thr_t) & (ih[sl] < thr_h)
    fig, axes = plt.subplots(4, 1, figsize=(12, 7), sharex=True)
    for ax, y, thr, label, color, above in (
        (axes[0], reward[sl], thr_r, "reward: 15-18 Hz (SMR/low beta)", EC_COLOR, True),
        (axes[1], it[sl], thr_t, "inhibit: 4-7 Hz theta (blinks land here)", BAND_COLORS["theta"], False),
        (axes[2], ih[sl], thr_h, "inhibit: 22-30 Hz high beta (jaw clench lands here)", BAND_COLORS["gamma"], False),
    ):
        ax.plot(t, y, color=color, lw=1)
        ax.axhline(thr, color=INK, ls="--", lw=1)
        ax.set_ylabel("µV²", fontsize=8)
        ax.set_title(label + ("  — must be ABOVE the line" if above else "  — must be BELOW the line"), loc="left", fontsize=10)
    axes[3].fill_between(t, 0, ok.astype(float), step="post", color=ACCENT, alpha=0.7)
    axes[3].set_yticks([])
    axes[3].set_title(f"feedback ON (all three conditions met): {ok.mean() * 100:.0f}% of the time", loc="left", fontsize=10)
    axes[3].set_xlabel("time (s); band power from a 1 s window updated every 250 ms at Cz")
    fig.suptitle("A reward/inhibit protocol replayed on one minute of real eyes-open EEG", fontweight="bold")
    fig.tight_layout()
    save(fig, "neurofeedback_simulation")


# --------------------------------------------------------------------------
# Module 14: HRV (NeuroKit2 simulated ECG)
# --------------------------------------------------------------------------


@figure
def hrv_basics():
    try:
        import neurokit2 as nk
    except ImportError:
        print("skip hrv_basics: pip install neurokit2")
        return
    sf = 250
    ecg = nk.ecg_simulate(duration=300, sampling_rate=sf, heart_rate=65, heart_rate_std=4, random_state=3)
    signals, info = nk.ecg_process(ecg, sampling_rate=sf)
    peaks = info["ECG_R_Peaks"]
    rr = np.diff(peaks) / sf * 1000
    fig, axes = plt.subplots(1, 3, figsize=(15, 3.6), gridspec_kw={"width_ratios": [1.3, 1.3, 1]})
    t = np.arange(len(ecg)) / sf
    m = t < 5
    axes[0].plot(t[m], signals["ECG_Clean"][m], color=INK, lw=0.8)
    pk = peaks[peaks < 5 * sf]
    axes[0].plot(pk / sf, signals["ECG_Clean"].iloc[pk], "o", color=ACCENT, ms=5)
    for a, b in zip(pk[:-1], pk[1:]):
        axes[0].annotate("", xy=(b / sf, 1.25), xytext=(a / sf, 1.25), arrowprops=dict(arrowstyle="<->", color=ACCENT, lw=1))
        axes[0].text((a + b) / 2 / sf, 1.32, f"{(b - a) / sf * 1000:.0f}", ha="center", fontsize=7, color=ACCENT)
    axes[0].set_ylim(None, 1.45)
    axes[0].set_title("1. Find R-peaks; RR interval in ms", loc="left")
    axes[0].set_xlabel("time (s)")
    axes[0].set_yticks([])
    axes[1].plot(np.cumsum(rr) / 1000, rr, color=INK, lw=0.9)
    rmssd = np.sqrt(np.mean(np.diff(rr) ** 2))
    axes[1].set_title(f"2. RR series (tachogram): SDNN {rr.std():.0f} ms, RMSSD {rmssd:.0f} ms", loc="left")
    axes[1].set_xlabel("time (s)")
    axes[1].set_ylabel("RR (ms)")
    rr_t = np.cumsum(rr) / 1000
    ti = np.arange(rr_t[0], rr_t[-1], 0.25)
    rr_i = np.interp(ti, rr_t, rr)
    f, p = signal.welch(rr_i - rr_i.mean(), fs=4, nperseg=256)
    axes[2].plot(f, p, color=INK, lw=1)
    for lo, hi, c, lab in ((0.04, 0.15, BAND_COLORS["beta"], "LF"), (0.15, 0.4, BAND_COLORS["theta"], "HF")):
        mm = (f >= lo) & (f < hi)
        axes[2].fill_between(f[mm], p[mm], color=c, alpha=0.35, label=lab)
    axes[2].set_xlim(0, 0.5)
    axes[2].set_title("3. Spectrum of the RR series", loc="left")
    axes[2].set_xlabel("frequency (Hz)")
    axes[2].legend()
    fig.suptitle("HRV from a simulated 5-minute ECG (NeuroKit2)", fontweight="bold")
    fig.tight_layout()
    save(fig, "hrv_basics")


if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGURES)
    for n in names:
        FIGURES[n]()
