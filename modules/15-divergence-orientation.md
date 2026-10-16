---
title: "Divergence orientation"
module: 15
week: 2
session: 8
time: "20 min to prepare, then the in-person walkthrough"
summary: "What to have ready before Alex walks you through the Divergence platform, and how the course samples connect to it."
---

# Divergence orientation

After this module you will be ready for the in-person platform walkthrough: you will know the vocabulary, know which parts of the course map to which parts of the platform, and have your questions written down.

Alex will walk you through the platform in person: the **Dive mobile app**, the **practitioner webapp**, the **hardware you will be loaned**, and **how protocols and sessions are set up**. This page does not try to replace that walkthrough. It makes sure the walkthrough goes fast.

## The vocabulary you need first

Before the session, make sure you can say, in a sentence each, what these are. Each links to where the course teaches it.

| Term | You should be able to say | Taught in |
| --- | --- | --- |
| 10-20 site | A standard electrode position named by region and side (Fz, Cz, O1…); odd = left, even = right, z = midline | [Module 03](03-electrodes-and-montages.md) |
| Band-power feature | The power of the signal in a frequency band (area under the spectrum), absolute or relative to total power | [Module 10](10-spectral-features.md) |
| Reward / inhibit threshold | The level a band must be above (reward) or below (inhibit) for feedback to be given; usually adaptive | [Module 13](13-neurofeedback-loop.md) |
| RMSSD | Root mean square of successive RR differences; a short-window index of vagal activity | [Module 14](14-hrv-basics.md) |
| LF/HF | Ratio of 0.04-0.15 Hz to 0.15-0.4 Hz power in the RR series; strongly affected by breathing rate | [Module 14](14-hrv-basics.md) |

The full self-assessment list is in [Checkpoints](../checkpoints.md).

## Where the course meets the platform

Several of the course samples came out of Divergence tools, so you have already seen what the platform produces:

- **The cleaning pipeline.** Sample `s04_linenoise_cleaned_19ch.edf` is the output of a cleaning pipeline whose header records its settings: 1 Hz high-pass, 45 Hz low-pass, 60 Hz notch, then artifact repair. Compare it with its raw input `s03` in [Module 07](07-filtering.md), and notice that a residual 60 Hz peak survived.
- **Measure exports and artifact profiles.** Samples `s06`, `s07` and `s08` are three exports of the same recording from a Divergence Measure session: raw, rejection only (bad segments cut, 75 s down to 46 s), and the full pipeline (segments repaired rather than cut, 74 s). The EDF headers name the pipeline profiles: *rejection-only* and *full*. [Module 09](09-artifact-handling.md) and [Lab 2](12-lab-2-clean-and-measure.md) use them.
- **Segment rejection with a record of what was cut.** `s10` stores every removed stretch as an annotation (`Noise removed 2.40 s at 00:00:51.823`), so the cleaning is auditable.
- **Consumer hardware.** The samples come from several headsets: 19-channel dry-electrode caps, an 8-channel headset and a 4-channel headband. Dry electrodes and consumer amplifiers mean large DC offsets, odd sampling rates (242-251 Hz), drift, and line noise. That is the data the platform has to cope with every day, and it is why the pipeline order matters: filter, re-reference, remove artifacts, then compute features.
- **The feedback loop.** Everything in [Module 13](13-neurofeedback-loop.md), from band power in a sliding window to reward/inhibit thresholds to artifact gates, is what a neurofeedback session runs in real time. The HRV Training modes (RSA amplitude, LF power, coherence) from [Module 14](14-hrv-basics.md) are the biofeedback side.

> [!TIP]
> Alex's open-source assessment tool, [Squiggly](https://github.com/alexdni/squiggly), runs a similar offline pipeline on 19-channel EO/EC recordings: filtering, ASR, ICA, then band power, ratios, asymmetry and connectivity. Its README is a useful map of what a full qEEG analysis contains, and its artifact profiles (*full*, *conservative*, *aggressive*, *rejection-only*) match the names in the `s07`/`s08` headers.

## What to bring

1. **Your notes file** ([template](../notes-template.md)), with every term you had to look up and your questions.
2. **Your Lab 1 and Lab 2 outputs**: the eyes-open vs eyes-closed spectra, a blink and a muscle screenshot, and your three-sentence ICA write-up.
3. **Your Checkpoints list** with anything you cannot do yet marked.
4. **Questions.** Some good ones to start from:
   - Which headsets will we be loaned, how many channels, and which sites?
   - What reference does each device use, and does the platform re-reference?
   - Which artifact handling runs online during a session, and which only offline?
   - How are reward and inhibit thresholds set at the start of a session, and how fast do they adapt? What success rate do they target?
   - How are protocols chosen for a client: from an assessment, from a template, or by the practitioner?
   - For HRV Training, how is each mode's score computed, and how is the breathing pacer set?
   - Where do Measure exports like `s06`-`s08` come from in the app, and who uses them?

## Self-check

<details><summary>Sample s07 is 46 s long and s08 is 74 s, but they come from the same 75 s recording. Why the difference?</summary>

s07 is the rejection-only profile: bad segments were cut out. s08 is the full pipeline: bad segments were repaired (ASR/ICA-style correction) and kept, so almost all of the recording survives.
</details>

<details><summary>Why does the order "filter, re-reference, remove artifacts, compute features" matter?</summary>

Drift and line noise distort the reference and confuse artifact detection, so filtering comes first. Re-referencing before ICA and feature extraction means every channel is on the same basis. Artifacts have to be dealt with before features are computed, or they become part of the features.
</details>

<details><summary>In one sentence each: 10-20 site, band-power feature, reward/inhibit threshold, RMSSD, LF/HF.</summary>

See the vocabulary table at the top of this page. If any of your sentences needed a second attempt, revisit the linked module before the meeting.
</details>

Back to the [course overview](../README.md) or on to the [Checkpoints](../checkpoints.md).
