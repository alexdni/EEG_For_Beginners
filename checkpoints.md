---
title: "Checkpoints"
summary: "A self-assessment list for the end of the two weeks: tick what you can do, mark what you cannot, and bring the list to the first meeting."
---

# Checkpoints

Go through this list before the first supervisor meeting. Tick everything you can do without looking it up. Mark anything you cannot do yet with a **?** and bring the list. The marks tell Alex where to start; nobody is expected to tick everything.

## Checkpoints before the first supervisor meeting

This is the canonical list from the syllabus. If you can do all of these without looking anything up, you are onboarded. Anything you cannot do goes on your question list.

### Explain (out loud, in under a minute each)

- [ ] Where scalp EEG comes from and why its spatial resolution is poor → [Module 01](modules/01-where-the-signal-comes-from.md)
- [ ] The five frequency bands, their approximate ranges, and one state each is associated with → [Module 02](modules/02-frequency-bands.md)
- [ ] What a reference electrode is and why changing it changes the recording → [Module 03](modules/03-electrodes-and-montages.md), [Module 08](modules/08-re-referencing.md)
- [ ] How to tell a blink, an eye movement, muscle, and 60 Hz noise apart on a raw trace → [Module 05](modules/05-artifacts-field-guide.md)
- [ ] What ICA does to a recording and what ASR does differently → [Module 09](modules/09-artifact-handling.md)
- [ ] What band power and relative band power are, and how a theta/beta ratio is computed → [Module 10](modules/10-spectral-features.md)
- [ ] The five steps of a neurofeedback loop and what a reward/inhibit threshold does → [Module 13](modules/13-neurofeedback-loop.md)
- [ ] What RMSSD, HF, and LF measure, and why LF rises during slow paced breathing → [Module 14](modules/14-hrv-basics.md)

### Do (with your own code, on the PhysioNet data)

- [ ] Load a run, attach a montage, band-pass filter, and plot the raw trace → [Module 06, Part B](modules/06-lab-1-find-the-alpha-peak.md#part-b-the-physionet-version-extension)
- [ ] Produce eyes-open and eyes-closed spectra and point to the alpha peak on a topomap → [Module 06, Part B](modules/06-lab-1-find-the-alpha-peak.md#part-b-the-physionet-version-extension)
- [ ] Run ICA, identify the blink component, remove it, and show the frontal channels before and after → [Module 12, PhysioNet alternative](modules/12-lab-2-clean-and-measure.md#alternative-the-original-syllabus-version-physionet-data)
- [ ] Compute alpha power per channel and name the three highest → [Module 12, PhysioNet alternative](modules/12-lab-2-clean-and-measure.md#alternative-the-original-syllabus-version-physionet-data)

> [!TIP]
> The PhysioNet runs load with `mne.datasets.eegbci` (the extension in Lab 1 and the alternative in Lab 2). The course's own [sample recordings](data/README.md) work for every "Do" item too, and are what the main path of both labs uses. Doing each item on both is the best proof that your code is yours.

### Have ready

- [ ] Your notes file with the artifact cheat sheet, the sketched 10-20 head, and the three Week 2 answers → [notes template](notes-template.md)
- [ ] A list of terms you looked up and a list of questions for Alex
- [ ] A working Python environment with MNE installed, committed `requirements.txt` or environment file in the project repo → [Module 00](modules/00-start-here.md)

## Module by module

The rest of this page breaks the same ground into smaller "I can…" steps, module by module. Use it to find exactly where a gap is.

### The five words Alex will use on day one

If you can only prepare one thing, prepare these. Say each in one sentence, out loud.

- [ ] **10-20 site**: a standard electrode position named by region and side (Fp, F, C, T, P, O; odd = left, even = right, z = midline). → [Module 03](modules/03-electrodes-and-montages.md)
- [ ] **Band-power feature**: the power of the signal in a frequency band, the area under the spectrum between two frequencies; absolute or relative to total power. → [Module 10](modules/10-spectral-features.md)
- [ ] **Reward / inhibit threshold**: the level a band must be above (reward) or below (inhibit) for feedback to be given; adapts so the person succeeds a target fraction of the time. → [Module 13](modules/13-neurofeedback-loop.md)
- [ ] **RMSSD**: root mean square of successive differences between heartbeats; a short-window index of vagal activity. → [Module 14](modules/14-hrv-basics.md)
- [ ] **LF/HF**: ratio of low-frequency (0.04-0.15 Hz) to high-frequency (0.15-0.4 Hz) power in the heartbeat series; heavily affected by breathing rate. → [Module 14](modules/14-hrv-basics.md)

### Week 1: what EEG is

**[Module 01, Where the signal comes from](modules/01-where-the-signal-comes-from.md)**
- [ ] I can explain that scalp EEG is the summed post-synaptic potentials of millions of aligned cortical pyramidal neurons.
- [ ] I can explain volume conduction and why it makes EEG's spatial resolution poor.
- [ ] I can give typical EEG amplitudes (tens of microvolts) and say why EEG has millisecond time resolution.
- [ ] I can compare EEG with fMRI and MEG in one sentence each.

**[Module 02, Frequency bands](modules/02-frequency-bands.md)**
- [ ] I can list delta, theta, alpha, beta and gamma with approximate edges and one state each is associated with.
- [ ] I can explain why band edges vary between authors and why gamma is hard to separate from muscle.

**[Module 03, Electrodes and montages](modules/03-electrodes-and-montages.md)**
- [ ] I can sketch the 19 standard sites from memory, including T3/T7 and T4/T8.
- [ ] I can explain what a reference electrode is, and the difference between a referential and a bipolar montage.

**[Module 04, Reading a raw trace](modules/04-reading-a-raw-trace.md)**
- [ ] I can read a multichannel plot: time axis, one row per channel, scale bar in µV.
- [ ] I can spot eyes-closed posterior alpha in a raw trace (a ~10 Hz ripple over O1, O2, Pz).

**[Module 05, Artifacts field guide](modules/05-artifacts-field-guide.md)**
- [ ] I can recognise a blink (big, slow, largest at Fp1/Fp2).
- [ ] I can recognise a lateral eye movement (opposite sign at F7 and F8).
- [ ] I can recognise muscle (high-frequency fuzz, temporal channels and jaw), heartbeat, 60 Hz line noise, an electrode pop, sweat drift and movement.
- [ ] I have a one-page artifact cheat sheet in my notes.

**[Module 06, Lab 1: find the alpha peak](modules/06-lab-1-find-the-alpha-peak.md)**
- [ ] I have MNE-Python installed and can load an EDF file.
- [ ] I can plot a raw trace and a power spectrum, and show the alpha peak appear with eyes closed.
- [ ] I can draw a topomap of alpha power and check it is at the back of the head.
- [ ] I have screenshots of a blink and a muscle burst in my notes.

### Week 2: working with the signal

**[Module 07, Filtering](modules/07-filtering.md)**
- [ ] I can say what a 1 Hz high-pass removes (drift, DC offset) and what a 40-45 Hz low-pass removes.
- [ ] I can explain why a 60 Hz notch is needed in Toronto, and when you would use 50 Hz.
- [ ] I can explain at least one way filters distort the signal (ringing, phase shift, smearing in time).

**[Module 08, Re-referencing](modules/08-re-referencing.md)**
- [ ] I can explain why every channel is a difference against a reference.
- [ ] I can apply an average reference in MNE and say how average, linked-mastoid and Cz references differ.

**[Module 09, Artifact handling](modules/09-artifact-handling.md)**
- [ ] I can describe the three families: rejecting bad channels and segments, ICA, and ASR.
- [ ] I can fit ICA, find the blink component from its scalp map and time course, and remove it.
- [ ] I can say why ASR is the standard choice for real-time use.

**[Module 10, Spectral features](modules/10-spectral-features.md)**
- [ ] I can explain Welch's method in three steps (window, taper and transform, average).
- [ ] I can compute absolute and relative band power and a ratio such as theta/beta.

**[Module 11, Epochs and ERPs](modules/11-epochs-and-erps.md)**
- [ ] I can explain what an epoch is and why averaging epochs reveals an event-related potential.

**[Module 12, Lab 2: clean and measure](modules/12-lab-2-clean-and-measure.md)**
- [ ] I have written the three sentences: which component I removed and how I knew, what changed in the frontal channels, and which three channels have the highest alpha power.
- [ ] If my top alpha channels were not occipital or parietal, I know to re-check the montage and reference.

**[Module 13, The neurofeedback loop](modules/13-neurofeedback-loop.md)**
- [ ] I can draw the five-step loop from memory.
- [ ] I can read a protocol (site, reward band, inhibit bands, thresholds) and say when feedback is given.
- [ ] I can explain why thresholds adapt, and why neurofeedback is operant conditioning.
- [ ] I can explain why a blink floods theta and a jaw clench raises high beta, and why that matters more online than offline.

**[Module 14, HRV basics](modules/14-hrv-basics.md)**
- [ ] I can explain RR intervals and how they come from ECG R-peaks or a PPG pulse wave.
- [ ] I can say what RMSSD, SDNN, LF, HF and LF/HF index.
- [ ] I can explain RSA and resonance-frequency breathing near 6 breaths per minute.
- [ ] I can name the three HRV Training targets: RSA amplitude, LF power, coherence.

**[Module 15, Divergence orientation](modules/15-divergence-orientation.md)**
- [ ] I have my notes file, lab outputs and questions ready for the walkthrough.

## Bring to the meeting

- [ ] This list, with **?** marks.
- [ ] Your [notes file](notes-template.md).
- [ ] Lab 1 spectra and screenshots; Lab 2 three-sentence write-up.
- [ ] Your questions for Alex.
