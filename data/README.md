---
title: "Sample recordings"
summary: "Thirteen real EDF recordings used throughout the course, what each one is for, and how to load them."
---

# Sample recordings

These are real recordings from consumer and research-grade headsets, exported as EDF. They were picked because each one shows something specific: a clean alpha rhythm, line noise, blinks, or the same recording before and after cleaning. Nothing here is a textbook-perfect lab recording, and that is deliberate. This is what EEG looks like when you record it.

All files are **anonymised**: the patient and recording fields in each EDF header have been blanked, and the start date is set to 01.01.85, the EDF convention for "anonymised". The signals themselves are unchanged.

## Loading a sample

From Python, with the course helpers on your path (run from the `code/` folder or add it to `sys.path`):

```python
from eeg101 import load_sample

raw = load_sample("rest_ec")      # short name, or the file name
raw.plot(duration=10)
```

`load_sample` reads the file, marks every channel as EEG, renames the four 10-10 temporal sites to their older 10-20 names (T7→T3, T8→T4, P7→T5, P8→T6) so all files match, and attaches template 10-20 electrode positions.

Without the helpers, plain MNE works too:

```python
import mne
raw = mne.io.read_raw_edf("data/samples/s01_rest_eyes-closed_19ch.edf", preload=True)
```

## The catalogue

| File | Short name | Channels | Rate (Hz) | Length (s) | Size |
| --- | --- | --- | --- | --- | --- |
| `s01_rest_eyes-closed_19ch.edf` | `rest_ec` | 19 | 250 | 310 | 2.9 MB |
| `s02_rest_eyes-open_19ch.edf` | `rest_eo` | 19 | 249 | 308 | 2.9 MB |
| `s03_linenoise_raw_19ch.edf` | `linenoise_raw` | 19 | 250 | 410 | 3.9 MB |
| `s04_linenoise_cleaned_19ch.edf` | `linenoise_cleaned` | 19 | 250 | 410 | 3.8 MB |
| `s05_artifacts_eyes-closed_19ch.edf` | `artifacts_ec` | 19 | 250 | 73 | 0.7 MB |
| `s06_pipeline_stage0_raw_19ch.edf` | `pipeline_raw` | 19 | 250 | 75 | 0.7 MB |
| `s07_pipeline_stage1_rejection_19ch.edf` | `pipeline_rejection` | 19 | 250 | 46 | 0.4 MB |
| `s08_pipeline_stage2_full_19ch.edf` | `pipeline_full` | 19 | 250 | 74 | 0.7 MB |
| `s09_segments_original_8ch.edf` | `segments_original` | 8 | 251 | 122 | 0.5 MB |
| `s10_segments_removed_8ch.edf` | `segments_removed` | 8 | 251 | 98 | 0.4 MB |
| `s11_4ch_eyes-closed.edf` | `headband_ec` | 4 | 250 | 52 | 0.1 MB |
| `s12_4ch_eyes-open.edf` | `headband_eo` | 4 | 250 | 59 | 0.1 MB |
| `s13_4ch_eyes-open_task.edf` | `headband_task` | 4 | 250 | 48 | 0.1 MB |

The 19-channel files use the standard clinical 10-20 set: Fp1, Fp2, F7, F3, Fz, F4, F8, T3, C3, Cz, C4, T4, T5, P3, Pz, P4, T6, O1, O2. The 8-channel files have Cz, F3, F4, O1, O2, Pz, T3, T4; the 4-channel headband has F3, F4, Cz, O1.

### Resting state pair (s01, s02)

The same adult, same session, five minutes eyes closed then five minutes eyes open, on a 19-channel dry-electrode headset. **This is the pair to start with.** Eyes closed shows a strong 10 Hz posterior alpha rhythm; at O1 and O2 alpha power is about 18 times higher with eyes closed than open. Used in Modules 02, 03, 04, 06, 08, 10 and 13.

### Line noise, before and after (s03, s04)

One eyes-closed recording made somewhere with heavy mains interference. The raw file (s03) has a 60 Hz peak about 60 dB (a million times in power) above the surrounding spectrum, and a second, smaller peak at 70 Hz that is not mains (most likely the hardware itself). s04 is the same 410 seconds after the platform's cleaning pipeline (1 Hz high-pass, 45 Hz low-pass, 60 Hz notch, artifact repair). A residual 60 Hz peak survives, which is a lesson in its own right. Used in Module 07.

### Eye artifacts (s05)

Eyes closed, but the eyes keep rolling: large slow waves at Fp1, Fp2, F7 and F8 while alpha carries on at the back. The last four seconds are saturated junk where the headset came off; find it before you analyse anything. Used in Modules 05 and 09.

### Pipeline stages (s06, s07, s08)

Three exports of the same 75-second recording from the Divergence artifact pipeline:

- **s06**: the raw export. Contains a series of classic sharp blinks, which makes it the best file for practising ICA. Also ends with a few seconds of junk.
- **s07**: rejection only. Bad segments have been cut out, leaving 46 seconds.
- **s08**: the full pipeline. Segments are repaired rather than cut (ASR/ICA-style correction), so the length is back to 74 seconds.

Comparing the three is the clearest way to see what "cleaning" actually does. Used in Module 09 and Lab 2.

### Segment rejection (s09, s10)

An 8-channel headset recording (122 s) and the same file after automatic rejection cut 15 noisy segments (98 s). s10 stores each cut as an annotation such as `Noise removed 2.40 s at 00:00:51.823`, so you can see exactly what went. The original also has strong slow drift. Used in Modules 05 and 09.

### Four-channel headband (s11, s12, s13)

A low-cost 4-channel headband, about a minute each of eyes closed, eyes open, and eyes open during a mental task. Even with four channels, the eyes-closed alpha peak at O1 is obvious: alpha is about 38% of 1-40 Hz power with eyes closed against about 8% with eyes open. Used in Module 10 and the neurofeedback module.

## Things these files will teach you whether you like it or not

- **Sampling rates are not always round.** Some files say 249 or 251 Hz. Always read `raw.info["sfreq"]` instead of assuming 250.
- **Raw files carry a large DC offset.** Unfiltered values sit tens of thousands of microvolts from zero. That is the electrode, not the brain. A high-pass filter removes it.
- **Recordings end badly.** People take headsets off before the recording stops. Look at the last few seconds before computing anything.
- **Old and new electrode names coexist.** T3/T4/T5/T6 in one file, T7/T8/P7/P8 in another. Same places.

## Public datasets

For more data, see the [resource library](../resources.md#datasets). The [PhysioNet EEG Motor Movement/Imagery](https://physionet.org/content/eegmmidb/1.0.0/) dataset loads directly through `mne.datasets.eegbci` and is what Lab 1's optional extension uses.
