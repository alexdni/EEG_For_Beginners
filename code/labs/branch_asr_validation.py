"""Project branch: validate an artifact-cleaning method by injecting artifacts you control.

The trick from the syllabus: take real EEG, add artifacts whose exact shape and timing
you know, clean it, and measure (1) how much of each artifact is gone and (2) how much
of the brain signal survived. Because you kept the uncontaminated original ("truth"),
both questions have exact answers.

    python code/labs/branch_asr_validation.py [output_dir] [--show]

Methods compared (each is a function taking contaminated Raw -> cleaned Raw, kept-mask):
  - ICA: MNE ICA, blink components chosen by correlation with Fp1/Fp2
  - threshold: reject 0.5 s windows whose peak-to-peak exceeds 5x the channel's median
  - ASR (k=20 and k=10): mne-denoise's ASR, if installed (pip install mne-denoise)
Add your own method to METHODS and it gets the same report.
"""
import time

import numpy as np
from _common import finish, plt
from mne.preprocessing import ICA
from mne.time_frequency import psd_array_welch

from eeg101 import load_sample

RNG = np.random.default_rng(42)
START, DUR = 60.0, 120.0  # seconds of s01 to use
ALPHA = (8.0, 13.0)

# How strongly a frontal (eye) source shows up at each site, relative to Fp1/Fp2.
BLINK_WEIGHT = {"Fp1": 1.0, "Fp2": 1.0, "F7": 0.55, "F8": 0.55, "F3": 0.5, "F4": 0.5, "Fz": 0.5,
                "C3": 0.2, "C4": 0.2, "Cz": 0.2, "T3": 0.15, "T4": 0.15,
                "P3": 0.08, "P4": 0.08, "Pz": 0.08, "T5": 0.06, "T6": 0.06, "O1": 0.03, "O2": 0.03}
MUSCLE_SITES = ["T3", "T4", "T5", "T6", "F7", "F8"]


# --------------------------------------------------------------------------- data


def make_dataset():
    raw = load_sample("rest_ec").filter(1, 40).crop(START, START + DUR)
    raw.set_eeg_reference("average")
    sf = raw.info["sfreq"]
    truth = raw.get_data() * 1e6
    n_ch, n = truth.shape
    names = raw.ch_names
    t = np.arange(n) / sf

    # Non-overlapping event slots, 4 s apart with jitter, alternating blink / muscle.
    slots = np.arange(3, DUR - 3, 4.0) + RNG.uniform(-0.5, 0.5, size=len(np.arange(3, DUR - 3, 4.0)))
    blink_times, muscle_times = slots[0::2], slots[1::2]

    blink = np.zeros_like(truth)
    w = np.array([BLINK_WEIGHT.get(c, 0.0) for c in names])[:, None]
    for tc in blink_times:
        amp = RNG.uniform(120, 220)  # µV at Fp1/Fp2, a typical blink
        blink += w * amp * np.exp(-0.5 * ((t - tc) / 0.09) ** 2)[None, :]

    muscle = np.zeros_like(truth)
    from scipy.signal import butter, sosfiltfilt

    sos = butter(4, [20, 45], btype="bandpass", fs=sf, output="sos")
    for tc in muscle_times:
        a, b = int((tc - 0.5) * sf), int((tc + 0.5) * sf)
        env = np.hanning(b - a)
        for c in MUSCLE_SITES:
            i = names.index(c)
            burst = sosfiltfilt(sos, RNG.standard_normal(b - a + 200))[100:-100]
            muscle[i, a:b] += 25 * burst / burst.std() * env

    # Masks: where each artifact lives, and "clean" samples more than 1 s from any event.
    near = np.zeros(n, bool)
    for tc in np.r_[blink_times, muscle_times]:
        near[max(0, int((tc - 1.0) * sf)): int((tc + 1.0) * sf)] = True
    blink_mask = np.zeros(n, bool)
    for tc in blink_times:
        blink_mask[int((tc - 0.25) * sf): int((tc + 0.25) * sf)] = True
    muscle_mask = np.zeros(n, bool)
    for tc in muscle_times:
        muscle_mask[int((tc - 0.5) * sf): int((tc + 0.5) * sf)] = True

    contaminated = raw.copy()
    contaminated._data = (truth + blink + muscle) / 1e6
    return dict(raw=raw, contaminated=contaminated, truth=truth, blink=blink, muscle=muscle,
                clean_mask=~near, blink_mask=blink_mask, muscle_mask=muscle_mask, sf=sf,
                blink_times=blink_times, muscle_times=muscle_times)


# --------------------------------------------------------------------------- methods


def clean_ica(raw):
    ica = ICA(n_components=15, random_state=97, max_iter="auto")
    ica.fit(raw)
    src = ica.get_sources(raw).get_data()
    fp = raw.copy().pick(["Fp1", "Fp2"]).get_data().mean(0)
    corr = np.array([abs(np.corrcoef(s, fp)[0, 1]) for s in src])
    ica.exclude = [int(i) for i in np.where(corr > 0.7)[0]] or [int(np.argmax(corr))]
    out = ica.apply(raw.copy())
    return out, np.ones(len(raw.times), bool), f"removed ICA{ica.exclude}"


def clean_threshold(raw, win=0.5, factor=5.0):
    sf = raw.info["sfreq"]
    d = raw.get_data() * 1e6
    step = int(win * sf)
    n_win = d.shape[1] // step
    ptp = np.array([np.ptp(d[:, k * step:(k + 1) * step], axis=1) for k in range(n_win)])  # win x ch
    limit = factor * np.median(ptp, axis=0)
    bad = (ptp > limit).any(axis=1)
    kept = np.ones(d.shape[1], bool)
    for k in np.where(bad)[0]:
        kept[k * step:(k + 1) * step] = False
    return raw.copy(), kept, f"rejected {bad.sum()} of {n_win} windows"


def make_asr(cutoff):
    def clean_asr(raw):
        from mne_denoise.asr import ASR

        asr = ASR(sfreq=raw.info["sfreq"], cutoff=cutoff, random_state=0)
        out, diag = asr.fit_transform(raw.copy(), return_diagnostics=True)
        frac = 100 * diag["fraction_reconstructed_samples"]
        return out, np.ones(len(raw.times), bool), f"cutoff {cutoff} SD, reconstructed {frac:.0f}% of samples"

    clean_asr.__name__ = f"asr_k{cutoff}"
    return clean_asr


METHODS = {"ICA": clean_ica, "threshold": clean_threshold}
try:
    import mne_denoise.asr  # noqa: F401

    METHODS["ASR k=20"] = make_asr(20)
    METHODS["ASR k=10"] = make_asr(10)
except ImportError:
    print("mne-denoise not installed: ASR skipped (pip install mne-denoise to add it)")


# --------------------------------------------------------------------------- metrics


def welch_alpha(x, sf, mask, picks):
    """Mean PSD of `picks` over 2 s windows lying entirely inside `mask`."""
    step = int(2 * sf)
    segs = [x[picks, a:a + step] for a in range(0, x.shape[1] - step, step // 2) if mask[a:a + step].all()]
    if not segs:
        return None, None
    psd, f = psd_array_welch(np.stack(segs), sf, fmin=1, fmax=40, n_fft=step, verbose=False)
    return psd.mean(axis=0), f


def report(ds, name, cleaned_uv, kept, seconds):
    sf, truth = ds["sf"], ds["truth"]
    names = ds["raw"].ch_names
    occ = [names.index("O1"), names.index("O2")]
    fp = [names.index("Fp1"), names.index("Fp2")]
    tmp = [names.index(c) for c in MUSCLE_SITES]
    contaminated = ds["contaminated"].get_data() * 1e6

    clean_kept = ds["clean_mask"] & kept
    p_true, f = welch_alpha(truth, sf, clean_kept, occ)
    p_clean, _ = welch_alpha(cleaned_uv, sf, clean_kept, occ)
    band = (f >= ALPHA[0]) & (f <= ALPHA[1])
    peak_true = f[band][np.argmax(p_true.mean(0)[band])]
    peak_clean = f[band][np.argmax(p_clean.mean(0)[band])]
    alpha_change = 100 * (p_clean[:, band].sum() / p_true[:, band].sum() - 1)

    def removal(mask, art, chans):
        # Rejected samples count as fully removed: the artifact is no longer in the output.
        resid = cleaned_uv[np.ix_(chans, mask)] - truth[np.ix_(chans, mask)]
        resid[:, ~kept[mask]] = 0.0
        a = np.sqrt(np.mean(art[np.ix_(chans, mask)] ** 2))
        r = np.sqrt(np.mean(resid ** 2))
        return 100 * (1 - r / a), 20 * np.log10(a / max(r, 1e-9))

    blink_removed, blink_db = removal(ds["blink_mask"], ds["blink"], fp)
    muscle_removed, muscle_db = removal(ds["muscle_mask"], ds["muscle"], tmp)
    blinks_dropped = 100 * (1 - (ds["blink_mask"] & kept).sum() / ds["blink_mask"].sum())
    muscle_dropped = 100 * (1 - (ds["muscle_mask"] & kept).sum() / ds["muscle_mask"].sum())

    changed = (np.abs(cleaned_uv - contaminated) > 1.0).any(axis=0) | ~kept
    # Median over channels: s01 has a few real frontal artifacts of its own, and a method that
    # (correctly) repairs those would otherwise look like it damaged the brain signal.
    per_ch = (np.sqrt(np.mean((cleaned_uv[:, clean_kept] - truth[:, clean_kept]) ** 2, axis=1))
              / truth[:, clean_kept].std(axis=1))
    brain_err = np.median(per_ch)
    return dict(
        method=name, peak_true=peak_true, peak_clean=peak_clean, alpha_change=alpha_change,
        brain_err=100 * brain_err, blink_removed=blink_removed, blink_db=blink_db,
        muscle_removed=muscle_removed, muscle_db=muscle_db, blinks_dropped=blinks_dropped,
        muscle_dropped=muscle_dropped, modified=100 * changed.mean(), ms_per_s=1000 * seconds / DUR,
    )


# --------------------------------------------------------------------------- run


def main():
    ds = make_dataset()
    print(f"s01 eyes closed, {DUR:.0f} s from t={START:.0f} s, 1-40 Hz, average reference")
    print(f"injected {len(ds['blink_times'])} blinks (120-220 µV at Fp1/Fp2) and "
          f"{len(ds['muscle_times'])} muscle bursts (1 s, 20-45 Hz, 25 µV SD at {', '.join(MUSCLE_SITES)})\n")

    rows, outputs = [], {}
    contaminated_uv = ds["contaminated"].get_data() * 1e6
    rows.append(report(ds, "no cleaning", contaminated_uv, np.ones(contaminated_uv.shape[1], bool), 0.0))
    rows[0]["control"] = 0.0
    for name, fn in METHODS.items():
        t0 = time.perf_counter()
        try:
            out, kept, note = fn(ds["contaminated"].copy())
        except Exception as err:  # keep the harness running if one method breaks
            print(f"{name}: failed ({err})")
            continue
        seconds = time.perf_counter() - t0
        cleaned = out.get_data() * 1e6
        outputs[name] = (cleaned, kept)
        r = report(ds, name, cleaned, kept, seconds)
        r["note"] = note
        # Control: run the same method on the original, which has no injected artifacts.
        # Whatever it changes there is either the recording's own artifacts or collateral damage.
        ctrl, ctrl_kept, _ = fn(ds["raw"].copy())
        diff = (np.abs(ctrl.get_data() * 1e6 - ds["truth"]) > 1.0).any(axis=0) | ~ctrl_kept
        r["control"] = 100 * diff.mean()
        rows.append(r)

    hdr = (f"{'method':<12} {'alpha peak':>10} {'alpha Δ':>8} {'brain err':>9} {'blink rm':>9} "
           f"{'muscle rm':>9} {'modified':>9} {'control':>8} {'ms per s':>8}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['method']:<12} {r['peak_clean']:>7.1f} Hz {r['alpha_change']:>+7.1f}% {r['brain_err']:>8.1f}% "
              f"{r['blink_removed']:>8.0f}% {r['muscle_removed']:>8.0f}% {r['modified']:>8.1f}% {r['control']:>7.1f}% {r['ms_per_s']:>8.1f}"
              + (f"   {r['note']}" if r.get("note") else ""))
    print(f"\ntrue alpha peak at O1/O2 on clean segments: {rows[0]['peak_true']:.1f} Hz")
    print("alpha Δ    = change in 8-13 Hz power at O1/O2 on clean segments vs the uncontaminated original")
    print("brain err  = RMS(cleaned - original) on clean segments as % of the original's SD, median over channels")
    print("blink rm / muscle rm = % of the injected artifact's RMS gone from the output (rejected samples count as gone)")
    print("modified   = % of samples changed by more than 1 µV on any channel, or rejected")
    print("control    = the same, when the method is run on the original with nothing injected")
    for r in rows:
        if r["blinks_dropped"] > 0 or r["muscle_dropped"] > 0:
            print(f"{r['method']}: rejected {r['blinks_dropped']:.0f}% of blink samples and "
                  f"{r['muscle_dropped']:.0f}% of muscle samples outright")

    plot(ds, rows, outputs)


def plot(ds, rows, outputs):
    sf, names = ds["sf"], ds["raw"].ch_names
    contaminated = ds["contaminated"].get_data() * 1e6
    colors = {"ICA": "#1c7ed6", "threshold": "#e67700", "ASR k=20": "#2b8a3e", "ASR k=10": "#5f3dc4"}
    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(2, 3)
    for k, (label, tc, ch) in enumerate((("blink", ds["blink_times"][3], "Fp1"),
                                         ("muscle burst", ds["muscle_times"][3], "T3"))):
        ax = fig.add_subplot(gs[k, :2])
        a, b = int((tc - 1.5) * sf), int((tc + 1.5) * sf)
        t = np.arange(a, b) / sf + START
        i = names.index(ch)
        ax.plot(t, contaminated[i, a:b], color="#adb5bd", lw=1, label="contaminated")
        ax.plot(t, ds["truth"][i, a:b], color="#1f2430", lw=1.4, label="original (truth)")
        for name, (cleaned, kept) in outputs.items():
            y = np.where(kept[a:b], cleaned[i, a:b], np.nan)
            ax.plot(t, y, color=colors.get(name, "#c92a2a"), lw=1, alpha=0.85, label=name)
        ax.set_title(f"{ch} around an injected {label}", loc="left")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("µV")
        if k == 0:
            ax.legend(fontsize=8, ncol=3)
    labels = [r["method"] for r in rows]
    ax = fig.add_subplot(gs[0, 2])
    x = np.arange(len(rows))
    ax.bar(x - 0.2, [r["blink_removed"] for r in rows], 0.4, label="blink", color="#1c7ed6")
    ax.bar(x + 0.2, [r["muscle_removed"] for r in rows], 0.4, label="muscle", color="#c92a2a")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("% of artifact removed")
    ax.set_title("Artifact removed", loc="left")
    ax.legend(fontsize=8)
    ax = fig.add_subplot(gs[1, 2])
    ax.bar(x - 0.2, [r["alpha_change"] for r in rows], 0.4, label="alpha power Δ %", color="#2b8a3e")
    ax.bar(x + 0.2, [r["modified"] for r in rows], 0.4, label="samples modified %", color="#868e96")
    ax.axhline(0, color="#1f2430", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_title("Cost: alpha change and data touched", loc="left")
    ax.legend(fontsize=8)
    fig.suptitle("Injected-artifact validation on s01 (eyes closed)", fontweight="bold")
    fig.tight_layout()
    finish(fig, "branch_asr_validation")


if __name__ == "__main__":
    main()
