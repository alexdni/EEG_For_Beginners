---
title: "Glossary"
summary: "Every term the course uses, A to Z, in one or two plain sentences, with a link to the module that teaches it."
---

# Glossary

One or two plain sentences per term, with the module that teaches it. If a word in your notes file is not here, add it to your questions for Alex.

## A

**Absolute band power.** Power in a frequency band in µV², the area under the spectrum between the band edges. Depends on electrode contact and skull thickness as well as the brain. → [10](modules/10-spectral-features.md)

**Alpha (8-13 Hz).** The rhythm of relaxed wakefulness, strongest at the back of the head with eyes closed. The single most reliable thing in human EEG. → [02](modules/02-frequency-bands.md)

**Alpha blocking (alpha reactivity).** The drop in posterior alpha when the eyes open. In the course sample, O1 alpha is about 18 times stronger with eyes closed. → [06](modules/06-lab-1-find-the-alpha-peak.md)

**Amplitude.** How big a signal is, in microvolts (µV). Scalp EEG is typically tens of µV. → [01](modules/01-where-the-signal-comes-from.md)

**Annotation.** A labelled time span stored with a recording, such as a marked artifact or an event. Sample s10 stores each cut segment as one. → [09](modules/09-artifact-handling.md)

**Artifact.** Anything in the recording that does not come from the brain: eyes, muscle, heart, mains, electrodes, movement. → [05](modules/05-artifacts-field-guide.md)

**Artifact gate.** A rule that pauses feedback (or marks data bad) when a window looks like an artifact, for example when its amplitude is too large. → [13](modules/13-neurofeedback-loop.md)

**ASR (artifact subspace reconstruction).** A method that repairs short high-amplitude bursts by comparing each moment against a clean reference segment and reconstructing the parts that deviate. The standard choice for real-time use. → [09](modules/09-artifact-handling.md)

**Average reference.** Re-referencing each channel to the mean of all channels. A common default for dense montages. → [08](modules/08-re-referencing.md)

## B

**Band-pass filter.** A filter that keeps one range of frequencies, such as 1-40 Hz; a high-pass and a low-pass combined. → [07](modules/07-filtering.md)

**Band-power feature.** A number summarising the power in one band over a window of signal; the feature most neurofeedback protocols train on. → [10](modules/10-spectral-features.md)

**Beta (13-30 Hz).** Active thinking and motor activity. High beta (roughly 20-30 Hz) overlaps with muscle activity. → [02](modules/02-frequency-bands.md)

**Bipolar montage.** Displaying each channel as the difference between two neighbouring electrodes, which shows local activity and cancels what they share. → [03](modules/03-electrodes-and-montages.md), [08](modules/08-re-referencing.md)

**Blink.** A big, slow deflection largest at Fp1 and Fp2, fading toward the back. The eyeball is an electrical dipole and the lid moving over it changes the field. → [05](modules/05-artifacts-field-guide.md)

## C

**Causal filter.** A filter that only uses past samples, so it can run in real time. It delays and distorts the signal slightly. → [07](modules/07-filtering.md), [13](modules/13-neurofeedback-loop.md)

**Channel.** One recorded signal, usually one electrode against the reference, shown as one row in a raw plot. → [04](modules/04-reading-a-raw-trace.md)

**Coherence (HRV).** How much of the heart-rhythm spectrum is concentrated in one narrow peak; high when the RR curve is smooth and sine-like during paced breathing. One of the three HRV Training modes. → [14](modules/14-hrv-basics.md)

**Component (ICA).** One of the source signals ICA unmixes from the recording, with a scalp map and a time course. → [09](modules/09-artifact-handling.md)

## D

**DC offset.** A large constant voltage, often tens of thousands of µV in raw dry-electrode files, from the electrode-skin junction rather than the brain. A high-pass filter removes it. → [07](modules/07-filtering.md)

**Delta (0.5-4 Hz).** Slow waves of deep sleep. In awake recordings, large delta is often eye movement or drift. → [02](modules/02-frequency-bands.md)

**Drift.** A slowly wandering baseline from sweat, changing electrode contact or movement. → [05](modules/05-artifacts-field-guide.md)

## E

**ECG (electrocardiogram).** A recording of the heart's electrical activity; the source of R-peaks for HRV. Heartbeat can also leak into EEG as an artifact. → [14](modules/14-hrv-basics.md)

**EDF / EDF+ (European Data Format).** The standard file format for EEG and other physiological recordings. EDF+ adds annotations. → [06](modules/06-lab-1-find-the-alpha-peak.md)

**Electrode pop.** A sudden jump confined to one electrode when its contact changes abruptly. → [05](modules/05-artifacts-field-guide.md)

**EMG (electromyogram).** Electrical activity from muscles. In EEG, high-frequency fuzz, worst on temporal channels and with jaw clenching. → [05](modules/05-artifacts-field-guide.md)

**Epoch.** A fixed window of data cut around an event, such as -0.2 to 0.8 s around a stimulus. → [11](modules/11-epochs-and-erps.md)

**ERP (event-related potential).** The average response to a repeated event, revealed by averaging many epochs so background EEG cancels out. → [11](modules/11-epochs-and-erps.md)

**Eyes closed / eyes open (EC/EO).** The two standard resting conditions. Comparing them is the quickest test that a recording works. → [06](modules/06-lab-1-find-the-alpha-peak.md)

## F

**Feedback.** The tone, bar or game the trainee perceives when the protocol's conditions are met. → [13](modules/13-neurofeedback-loop.md)

**FIR / IIR filter.** Two families of digital filter. FIR filters (MNE's default) are stable and can be zero-phase; IIR filters (such as Butterworth) are shorter and common in real time. → [07](modules/07-filtering.md)

**fMRI / MEG.** Other ways to measure the brain. fMRI has good spatial but poor time resolution; MEG measures magnetic fields with millisecond resolution and less smearing than EEG, but needs a shielded room. → [01](modules/01-where-the-signal-comes-from.md)

**Frequency band.** A conventional range of frequencies (delta, theta, alpha, beta, gamma). Edges vary by author by a hertz or two. → [02](modules/02-frequency-bands.md)

## G

**Gamma (30+ Hz).** Fast activity, hard to separate from muscle at the scalp. → [02](modules/02-frequency-bands.md)

## H

**HF (high frequency, HRV).** Heart-rhythm power at 0.15-0.4 Hz, the breathing band; dominated by RSA. → [14](modules/14-hrv-basics.md)

**High-pass filter.** Removes frequencies below the cutoff, such as drift and DC offset with a 0.5-1 Hz high-pass. → [07](modules/07-filtering.md)

**HRV (heart rate variability).** Beat-to-beat variation in the interval between heartbeats. → [14](modules/14-hrv-basics.md)

## I

**ICA (independent component analysis).** Unmixes the recording into statistically independent components so blink, eye-movement, heartbeat and muscle components can be removed. → [09](modules/09-artifact-handling.md)

**ICLabel.** A classifier (in Python, `mne-icalabel`) that labels ICA components as brain, eye, muscle, heart, line noise or other. → [09](modules/09-artifact-handling.md)

**Inhibit band.** A band that must stay below its threshold for feedback to be given. → [13](modules/13-neurofeedback-loop.md)

## L

**Latency.** The delay between a brain event and the feedback it triggers, from filters, window length, smoothing and display. → [13](modules/13-neurofeedback-loop.md)

**LF (low frequency, HRV).** Heart-rhythm power at 0.04-0.15 Hz. Rises sharply with slow paced breathing near 6 breaths per minute. One of the three HRV Training modes. → [14](modules/14-hrv-basics.md)

**LF/HF ratio.** LF power divided by HF power. Widely reported, widely criticised, and heavily affected by breathing rate. → [14](modules/14-hrv-basics.md)

**Line noise (mains hum).** Interference at the mains frequency, 60 Hz in North America and 50 Hz in most other places, and its harmonics. → [05](modules/05-artifacts-field-guide.md), [07](modules/07-filtering.md)

**Linked mastoids.** A reference made from the average of electrodes behind both ears. → [08](modules/08-re-referencing.md)

**Low-pass filter.** Removes frequencies above the cutoff, such as muscle and high-frequency noise with a 40-45 Hz low-pass. → [07](modules/07-filtering.md)

## M

**Mean HR.** Average heart rate in beats per minute; 60 000 divided by the mean RR interval in ms. → [14](modules/14-hrv-basics.md)

**MNE-Python.** The standard open-source EEG/MEG analysis library in Python, used in every lab. → [06](modules/06-lab-1-find-the-alpha-peak.md)

**Montage.** Either the set of electrode positions (MNE's meaning) or the way channels are combined for display, such as referential or bipolar (the clinical meaning). → [03](modules/03-electrodes-and-montages.md)

## N

**Neurofeedback.** Training a person to change a feature of their own EEG by giving them real-time feedback when it moves the right way. → [13](modules/13-neurofeedback-loop.md)

**Notch filter.** Removes a narrow band around one frequency, usually the mains frequency. → [07](modules/07-filtering.md)

**Nyquist frequency.** Half the sampling rate; the highest frequency a recording can represent. 125 Hz for a 250 Hz recording. → [07](modules/07-filtering.md)

## O

**Operant conditioning.** Learning driven by reward: behaviour (here, a brain state) that is followed by reward becomes more likely. → [13](modules/13-neurofeedback-loop.md)

## P

**Post-synaptic potential.** The voltage change in a neuron when it receives input. Summed across millions of aligned pyramidal neurons, these produce scalp EEG. → [01](modules/01-where-the-signal-comes-from.md)

**PPG (photoplethysmography).** An optical sensor measuring the blood-volume pulse with each heartbeat; used by most wearables for HRV. → [14](modules/14-hrv-basics.md)

**Protocol.** The full specification of a neurofeedback exercise: site, reward band, inhibit bands and thresholds. → [13](modules/13-neurofeedback-loop.md)

**PSD (power spectral density).** How a signal's power is distributed across frequencies; "the spectrum". → [10](modules/10-spectral-features.md)

**Pyramidal neurons.** The large cortical neurons whose aligned dendrites make their summed activity visible at the scalp. → [01](modules/01-where-the-signal-comes-from.md)

## R

**R-peak.** The tall sharp spike of each heartbeat in the ECG, used to time beats precisely. → [14](modules/14-hrv-basics.md)

**Raw trace.** The time-domain plot of a recording: time across, one row per channel, a µV scale bar. → [04](modules/04-reading-a-raw-trace.md)

**Re-referencing.** Changing what every channel is measured against after recording, such as switching to an average reference. → [08](modules/08-re-referencing.md)

**Reference electrode.** The electrode every channel's voltage is measured against. Choosing it changes what you see. → [03](modules/03-electrodes-and-montages.md), [08](modules/08-re-referencing.md)

**Rejection.** Removing bad channels or bad time segments rather than repairing them. → [09](modules/09-artifact-handling.md)

**Relative band power.** Band power divided by total power over a broad range; removes overall scale differences between people and sessions. → [10](modules/10-spectral-features.md)

**Resonance frequency breathing.** Breathing at the rate (about 6 per minute, 0.1 Hz) where breathing and the baroreflex reinforce each other and heart-rate swings are largest. → [14](modules/14-hrv-basics.md)

**Reward band.** The band that must be above its threshold for feedback to be given. → [13](modules/13-neurofeedback-loop.md)

**RMSSD.** Root mean square of successive differences between RR intervals; a short-window index of vagal activity. → [14](modules/14-hrv-basics.md)

**RR interval (NN interval).** The time between successive heartbeats, in ms. → [14](modules/14-hrv-basics.md)

**RSA (respiratory sinus arrhythmia).** Heart rate rising on the in-breath and falling on the out-breath. RSA amplitude is one of the three HRV Training modes. → [14](modules/14-hrv-basics.md)

## S

**Sampling rate.** How many samples per second the amplifier records, in Hz. The course samples are 242-251 Hz; always read it from the file. → [04](modules/04-reading-a-raw-trace.md)

**SDNN.** Standard deviation of NN intervals; overall heart-rate variability. Depends on recording length. → [14](modules/14-hrv-basics.md)

**SMR (sensorimotor rhythm).** Roughly 12-15 Hz activity over the sensorimotor strip (C3, Cz, C4); a classic neurofeedback reward band. → [13](modules/13-neurofeedback-loop.md)

## T

**10-20 system.** The international scheme for naming and placing scalp electrodes at 10% and 20% distances between skull landmarks. Odd numbers left, even right, z midline. → [03](modules/03-electrodes-and-montages.md)

**Theta (4-8 Hz).** Drowsiness, memory, and frontal-midline theta during mental effort. Blinks and eye movements also land here. → [02](modules/02-frequency-bands.md)

**Theta/beta ratio.** Theta power divided by beta power, typically at frontal or central sites; a common neurofeedback and qEEG feature. → [10](modules/10-spectral-features.md)

**Threshold.** The level a band's power is compared against to decide whether to give feedback. Usually adaptive. → [13](modules/13-neurofeedback-loop.md)

**Topomap.** A head map colouring each point by a value such as alpha power, interpolated between electrodes. → [06](modules/06-lab-1-find-the-alpha-peak.md)

## V

**Vagal activity.** Parasympathetic activity carried by the vagus nerve, which slows the heart and drives RSA. → [14](modules/14-hrv-basics.md)

**Volume conduction.** The spread of electrical activity through brain, skull and scalp, which smears each source across many electrodes and limits spatial resolution. → [01](modules/01-where-the-signal-comes-from.md)

## W

**Welch's method.** Estimating a spectrum by cutting the signal into overlapping windows, tapering and transforming each, and averaging. → [10](modules/10-spectral-features.md)

**Window (analysis window).** The stretch of signal used to compute one feature value, such as the last 1 s in a neurofeedback loop. → [10](modules/10-spectral-features.md), [13](modules/13-neurofeedback-loop.md)

## Z

**Zero-phase filter.** A filter applied forwards and backwards so it does not shift the signal in time; needs the whole recording, so it is offline only. → [07](modules/07-filtering.md)
