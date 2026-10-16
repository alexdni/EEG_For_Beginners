---
title: "Lab 2: clean a recording and measure alpha"
module: 12
week: 2
session: 6
time: "60-90 min hands-on"
summary: "Remove the blink component with ICA, compare your result with the platform's own pipeline, and find which channels carry the most alpha, then explain what you did in three sentences."
---

# Lab 2: clean a recording and measure alpha

This is the Week 2 hands-on session. It turns "I can see alpha" into "I can clean a recording and compute numbers from it". Budget 60-90 minutes. Pair up if you can: one person drives, the other reads the docs and keeps notes.

By the end you will have:

- identified and removed a blink component with ICA, and checked the result with numbers;
- compared your cleaning with the Divergence platform's exports of the same recording;
- computed alpha power per channel on an eyes-closed recording, and found out what goes wrong if you skip rejection;
- written the three-sentence summary for your notes file.

**Before you start:** finish [Lab 1](06-lab-1-find-the-alpha-peak.md) and read Modules [07](07-filtering.md), [08](08-re-referencing.md), [09](09-artifact-handling.md) and [10](10-spectral-features.md). You need the course environment from Lab 1 (`pip install -r code/requirements.txt`).

The whole lab is also one script:

```bash
python code/labs/lab2_clean_and_measure.py            # plots go to ./lab_outputs
python code/labs/lab2_clean_and_measure.py --show     # and open on screen
```

Run it once at the end to check your answers. Work through the steps by hand first, in a notebook.

## Part A: remove the blinks (30-40 min)

We use `s06_pipeline_stage0_raw_19ch.edf` because it has clear, frequent blinks, and because the platform's own cleaned versions of the same recording exist for comparison (s07 and s08).

### A1. Load, crop, filter, re-reference

```python
from mne.preprocessing import ICA
from eeg101 import load_sample

raw = load_sample("pipeline_raw")
raw.plot(duration=10, n_channels=19)       # scroll to the end first. What happens there?
raw.crop(0, raw.times[-1] - 4.5)          # the headset came off in the last 4.5 s
raw.filter(1.0, 40.0)
raw.set_eeg_reference("average")
```

### A2. Fit ICA and find the blink

```python
ica = ICA(n_components=15, random_state=97, max_iter="auto")
ica.fit(raw)
ica.plot_components()                 # find the blink component (frontal, symmetric map)
ica.plot_sources(raw)                 # confirm it tracks the blinks in time
```

What to look for, in order:

1. **Map**: strongly one colour at Fp1 and Fp2, fading smoothly toward the back. Frontal and symmetric.
2. **Time course**: a sharp spike at every blink you can see in the raw Fp1/Fp2 traces, and quiet in between.
3. **Numbers**: confirm with MNE's detector, using Fp1 and Fp2 as a stand-in for the EOG channel this headset does not have:

```python
eog_idx, scores = ica.find_bads_eog(raw, ch_name=["Fp1", "Fp2"], threshold=3.0)
print(eog_idx)
```

**Expected:** ICA001 (index 1). Its map matches the description, and its time course correlates about r = 0.97 with the Fp1/Fp2 average. If you installed `mne-icalabel`, ICLabel calls it "eye blink" with probability 0.98. With the same settings and `random_state=97` you should get exactly this; with a different seed or MNE version the index may change, but there will be one obvious blink component.

### A3. Remove it and check what changed

```python
ica.exclude = [1]                     # replace with the index you identified
clean = ica.apply(raw.copy())
raw.plot(duration=10, n_channels=19)
clean.plot(duration=10, n_channels=19)
```

Then put numbers on it. The script prints the standard deviation and median-Welch delta (1-4 Hz) power at Fp1 and Fp2:

```text
Frontal channels before and after (A3: what changed?)
  before ICA                   SD Fp1  15.6 Fp2  17.5 µV   delta Fp1   62.6 Fp2   68.7 µV²
  after removing ICA001        SD Fp1  10.3 Fp2   9.9 µV   delta Fp1   38.5 Fp2   40.2 µV²
  platform full pipeline (s08) SD Fp1  18.7 Fp2  15.6 µV   delta Fp1  116.8 Fp2   30.5 µV²
```

Frontal variability drops by about a third to a half, and frontal delta (where blinks put most of their energy) by about 40%. Occipital channels hardly change: O1's SD goes from 12.0 to 11.2 µV (from `code/labs/m09_ica.py`).

### A4. Compare with the platform

Load the platform's exports of the same recording and look at the same ten seconds:

```python
rej = load_sample("pipeline_rejection")    # s07: bad segments cut out (46 s left)
full = load_sample("pipeline_full")        # s08: segments repaired (74 s)
full.plot(duration=10, n_channels=19)
```

Questions for your notes:

- The platform's full pipeline leaves *more* Fp1 delta than your ICA (116.8 vs 38.5 µV²) but *less* at Fp2 (30.5 vs 40.2). Look at Fp1 in s08: what is still there?
- Your file and s08 are cleaned by different methods with different goals. The platform has to work in real time and automatically; you had a person looking at components. Which differences follow from that?
- s07 has steps at 7.7, 12.7, 26.8 and 32.0 s where segments were glued together ([Module 09](09-artifact-handling.md#putting-it-together-three-exports-of-one-recording)). Find one in the plot.

## Part B: alpha power per channel (20-30 min)

Now the measurement. Use the eyes-closed resting recording, `s01_rest_eyes-closed_19ch.edf`, where alpha should dominate at the back of the head.

### B1. The straight recipe

```python
ec = load_sample("rest_ec").filter(1.0, 40.0).set_eeg_reference("average")
spec = ec.compute_psd(fmin=1, fmax=40, method="welch", n_fft=int(2 * ec.info["sfreq"]))
psd, freqs = spec.get_data(return_freqs=True)
alpha = psd[:, (freqs >= 8) & (freqs <= 13)].mean(axis=1) * 1e12    # µV²/Hz
print(sorted(zip(ec.ch_names, alpha.round(1)), key=lambda x: -x[1])[:3])
```

**Expected:** `Fp1 90,671, Fp2 87,904, Pz 33,039` µV²/Hz. The top three are frontal. The syllabus says: *if the answer is not occipital or parietal, re-check your montage and reference.* Do that. Then look at the data:

```python
ec.plot(duration=20, n_channels=19)       # look at the start and the very end
```

The montage and reference are fine. The problem is **artifacts**: s01 contains a handful of large transients, the largest swinging about 170,000 µV peak-to-peak (after average referencing) in the final partial second of the file. The mean-averaged Welch spectrum is dominated by them, and the average reference spreads them to every channel.

### B2. Reject, then measure

Mark every second where any channel swings more than 200 µV peak-to-peak as bad, then recompute. `compute_psd` skips `BAD_` annotations by default.

```python
import numpy as np
from mne import Annotations

sf = ec.info["sfreq"]
d = ec.get_data() * 1e6
n_sec = int(np.ceil(ec.times[-1]))        # ceil, not int: the last partial second is where the worst junk is
bad = [s for s in range(n_sec) if np.ptp(d[:, int(s * sf): int((s + 1) * sf)], axis=1).max() > 200]
ec.set_annotations(Annotations(bad, [1.0] * len(bad), ["BAD_ptp"] * len(bad)))

spec = ec.compute_psd(fmin=1, fmax=40, method="welch", n_fft=int(2 * sf))
psd, freqs = spec.get_data(return_freqs=True)
alpha = psd[:, (freqs >= 8) & (freqs <= 13)].mean(axis=1) * 1e12
print(dict(zip(ec.ch_names, alpha.round(2))))      # alpha power per channel
spec.plot_topomap(bands={"Alpha (8-13 Hz)": (8, 13)})
```

**Expected:** 25 of 310 seconds marked bad. The top three become **O2 50.2, O1 49.7, T6 27.2** µV²/Hz, followed by T5 27.1, P4 16.3 and P3 15.5. Median averaging (`average="median"`) without any rejection gives the same ranking (O2 57.3, O1 56.1, T6 30.3). The topomap should be bright at the back of the head.

T5 and T6 are posterior temporal sites (called P7 and P8 in the newer 10-10 naming), sitting just beside the parietal and occipital electrodes, so "occipital, parietal and posterior temporal" is exactly the expected alpha pattern.

> [!NOTE]
> A spectrum plotted on a dB scale can still show a convincing alpha peak while a few huge windows inflate every channel's absolute power. A single number per channel hides what went into it. Look at the data before you average it.

## Part C: write it up (10 min)

Write three sentences in your notes file:

1. **Which component you removed and how you knew.** (Map, time course, and a number: correlation or `find_bads_eog` or ICLabel.)
2. **What changed in the frontal channels after removal.** (Use the SD or delta-power numbers from A3.)
3. **Which three channels have the highest alpha power**, and whether that matches where alpha should be. If the answer is not occipital or parietal, say what you checked: montage, reference, *and* artifacts.

Add one more line: one question about this lab you want to ask Alex.

## Alternative: the original syllabus version (PhysioNet data)

If you ran Lab 1 on the PhysioNet EEG Motor Movement/Imagery data, you can do Part A and B on its eyes-closed run instead. This is the syllabus's original code; it continues from the `raw_closed` object you built in Lab 1 (64 channels, 160 Hz, already filtered 1-40 Hz with the `standard_1005` montage attached):

```python
from mne.preprocessing import ICA

raw = raw_closed.copy().set_eeg_reference("average")
ica = ICA(n_components=20, random_state=97)
ica.fit(raw)
ica.plot_components()                 # find the blink component (frontal, bipolar-looking map)
ica.plot_sources(raw)                 # confirm it tracks the blinks in time
ica.exclude = [0]                     # replace 0 with the index you identified
clean = ica.apply(raw.copy())

spec = clean.compute_psd(fmin=1, fmax=40, method="welch")
psd, freqs = spec.get_data(return_freqs=True)
alpha = psd[:, (freqs >= 8) & (freqs <= 13)].mean(axis=1)
print(dict(zip(clean.ch_names, alpha.round(2))))   # alpha power per channel
```

Two differences from the course version: `alpha` here is in V²/Hz (tiny numbers like `1e-11`; multiply by `1e12` for µV²/Hz, or `.round(2)` will print zeros), and the PhysioNet recording is a lab recording with gel electrodes, so it is far cleaner than the course samples. Eyes-closed subjects in a quiet lab blink less, so the blink component may be weaker or absent; say so in your notes if you cannot find one.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Several components each contain one giant spike near the end | the headset-off junk is still in the data | crop it (`raw.crop(0, raw.times[-1] - 4.5)`) and refit |
| No obvious blink component | different seed or MNE version; or too few blinks | set `random_state=97`; use `find_bads_eog`; try `n_components=18` |
| Warning about rank or too many components | asking for more components than the data's rank | after average reference, use at most 18 for 19 channels |
| Alpha highest at Fp1/Fp2 | artifacts dominate the mean spectrum | reject bad seconds (B2) or use `average="median"` |
| All alpha values print as `0.0` | values are in V²/Hz | multiply by `1e12` before rounding |
| `plot_topomap` complains about positions | montage not attached | use `load_sample`, or `raw.set_montage("standard_1020")` |
| Plots do not appear | non-interactive backend | run with `--show`, or use Jupyter with `%matplotlib inline` |

## Check yourself

<details><summary>Why fit ICA on data high-passed at 1 Hz?</summary>

Slow drift is large and non-stationary, which violates ICA's assumptions and wastes components. A 1 Hz high-pass removes it, and the solution can still be applied to a less aggressively filtered copy of the same data.
</details>

<details><summary>The straight recipe put Fp1 and Fp2 on top for alpha. Name three things that could cause that, and which one it was here.</summary>

Wrong montage (channel positions swapped), an unusual reference, or artifacts dominating the average. Here it was artifacts: a few huge transients, the largest about 170,000 µV in the last partial second. Rejecting 25 bad seconds, or using median averaging, puts O2 and O1 on top.
</details>

<details><summary>Your ICA-cleaned Fp1 has less delta power than the platform's full pipeline. Does that make yours better?</summary>

Not necessarily. Lower frontal delta is consistent with better blink removal, but it is also what over-cleaning looks like. You chose one component by eye with full hindsight; the platform runs automatically and has to work live. The comparison is useful for understanding what each method removes, not for declaring a winner.
</details>
