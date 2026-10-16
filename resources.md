---
title: "Resource library"
summary: "Everything the modules point at, plus the next layer down, grouped by type. All free and open without a login unless marked."
---

# Resource library

Everything the modules point at, plus the next layer down. All free and open without a login unless marked. "Time" is how long the useful part takes, not the whole thing. You do not need to finish every resource: the [schedule](schedule.md) says what to read, watch or run, and this page is the longer menu for when you want more.

## Videos

| Resource | Time | Use it for | Modules |
| --- | --- | --- | --- |
| [2-Minute Neuroscience: EEG](https://neuroscientificallychallenged.com/posts/2-minute-neuroscience-electroencephalography-eeg) | 2 min | Day-one orientation | [01](modules/01-where-the-signal-comes-from.md) |
| [Mike X Cohen, ANTS lecture playlist](https://www.youtube.com/watch?v=ukjuFUghieg&list=PLn0OLiymPak0t1moK3sn4Sl1seXlEOPHT) | 30 min each | Intro to EEG time series, filtering, static spectral analysis; the go-to for understanding why the math works. Cohen is the clearest explainer of why EEG looks the way it does | [01](modules/01-where-the-signal-comes-from.md), [07](modules/07-filtering.md), [10](modules/10-spectral-features.md) |
| [FieldTrip video lectures](https://www.fieldtriptoolbox.org/video/) (Donders) | 30-60 min each | Robert Oostenveld's "Introduction to EEG, MEG and analysis", Julian Keil's six-part "EEG Data Analysis" basics series, frequency analysis | [01](modules/01-where-the-signal-comes-from.md), [05](modules/05-artifacts-field-guide.md) |
| [Online EEGLAB Workshop](https://www.sccn.ucsd.edu/wiki/Online_EEGLAB_Workshop) (UCSD) | 15-40 min each | Preprocessing, ICA, "Removing Artifactual Components" (Delorme); EEGLAB is MATLAB but the concepts transfer | [05](modules/05-artifacts-field-guide.md), [09](modules/09-artifact-handling.md) |
| [Neural Data Science in Python videos](https://www.youtube.com/playlist?list=PLtfEWMIgWS22MMZjPIzBRE2cHhMcvEKwp) (Newman) | varies | Video companion to the textbook below | [06](modules/06-lab-1-find-the-alpha-peak.md) |

## Decks and courses

| Resource | Time | Use it for | Modules |
| --- | --- | --- | --- |
| [PURSUE EEG/ERP teaching modules](https://pursue.richmond.edu/teaching-modules/full-semester-course/module-1-overview-of-eeg-erp) (University of Richmond) | 45 min for Module 1 | The best plain-language intro deck: what EEG measures, how it compares to fMRI and MEG, strengths and limits. Later modules cover recording, artifacts and ERP analysis | [01](modules/01-where-the-signal-comes-from.md), [03](modules/03-electrodes-and-montages.md) |
| [SPM for EEG/MEG course materials](https://www.fil.ion.ucl.ac.uk/spm/docs/courses/eeg_meg) (UCL) | Optional | A second set of intro decks on preprocessing and source analysis | — |
| [Neural Data Science in Python](https://neuraldatascience.io) (Newman, Dalhousie) | 2-4 h for the EEG chapter | Free online textbook with notebooks; a slower, more complete path through MNE, starting from zero Python | [06](modules/06-lab-1-find-the-alpha-peak.md), [12](modules/12-lab-2-clean-and-measure.md) |
| [Python for the practicing neuroscientist](https://elifesciences.org/labs/f779833b/python-for-the-practicing-neuroscientist-an-online-educational-resource) (Kramer and Eden) | 1-2 h per notebook | Case-study notebooks; spectral analysis of EEG rhythms (notebooks 3-4) from first principles | [10](modules/10-spectral-features.md) |
| [Introduction to ERPs](https://erpinfo.org/the-erp-boot-camp) (Luck and Kappenman, ERP Boot Camp) | 3-5 h | Only if your project needs event-related analysis; free, but it needs an account on their course site | [11](modules/11-epochs-and-erps.md) |
| [10-20 system (EEG)](<https://en.wikipedia.org/wiki/10%E2%80%9320_system_(EEG)>), Wikipedia | 15 min | Electrode names and positions | [03](modules/03-electrodes-and-montages.md) |

## Hands-on documentation

| Resource | Time | Use it for | Modules |
| --- | --- | --- | --- |
| [MNE-Python install guide](https://mne.tools/stable/install/index.html) | 15 min | Fresh virtual environment plus `pip install mne matplotlib jupyter` | [06](modules/06-lab-1-find-the-alpha-peak.md) |
| [MNE-Python tutorials](https://mne.tools/stable/auto_tutorials/index.html) | 20-40 min each | The spine of the hands-on sessions; ordered so a new user can go top to bottom | all labs |
| [MNE: Overview of MEG/EEG analysis](https://mne.tools/stable/auto_tutorials/intro/10_overview.html) | 20 min | One dataset from raw file to plot | [06](modules/06-lab-1-find-the-alpha-peak.md) |
| [MNE: Filtering and resampling](https://mne.tools/stable/auto_tutorials/preprocessing/30_filtering_resampling.html) | 30 min | What filters do and what they cost | [07](modules/07-filtering.md) |
| [MNE: Setting the EEG reference](https://mne.tools/stable/auto_tutorials/preprocessing/55_setting_eeg_reference.html) | 20 min | Average, linked mastoid, single-channel references | [08](modules/08-re-referencing.md) |
| [MNE: Preprocessing overview](https://mne.tools/stable/auto_tutorials/preprocessing/10_preprocessing_overview.html) | 20 min | Survey of artifact types and tools | [09](modules/09-artifact-handling.md) |
| [MNE: Repairing artifacts with ICA](https://mne.tools/stable/auto_tutorials/preprocessing/40_artifact_correction_ica.html) | 40 min | The ICA workflow end to end | [09](modules/09-artifact-handling.md), [12](modules/12-lab-2-clean-and-measure.md) |
| [MNE: The Spectrum class](https://mne.tools/stable/auto_tutorials/time-freq/10_spectrum_class.html) | 20 min | `compute_psd`, Welch, band power | [10](modules/10-spectral-features.md) |
| [MNE: Epochs overview](https://mne.tools/stable/auto_tutorials/epochs/10_epochs_overview.html) | 30 min | Cutting continuous data around events | [11](modules/11-epochs-and-erps.md) |
| [EEGLAB quick tutorial on ICA rejection](https://sccn.ucsd.edu/wiki/A12:_Quick_Tutorial_on_Rejection) | 20 min | Recognising and rejecting artifact components | [09](modules/09-artifact-handling.md) |
| [EEGLAB tutorial outline](https://sccn.ucsd.edu/wiki/EEGLAB_TUTORIAL_OUTLINE) | Reference | The canonical step list for single-subject EEG processing | [09](modules/09-artifact-handling.md) |
| [Python EEG Handbook](https://github.com/ZitongLu1996/Python-EEG-Handbook) (Lu et al.) | Reference | A standardised single-subject preprocessing recipe in MNE to compare your pipeline against | [12](modules/12-lab-2-clean-and-measure.md) |

## Libraries

| Resource | Time | Use it for | Modules |
| --- | --- | --- | --- |
| [MNE-Python](https://mne.tools) | — | The standard open-source EEG/MEG library in Python; used in every lab | all |
| [mne-icalabel](https://mne.tools/mne-icalabel/stable/index.html) | 15 min | Auto-labels ICA components as brain, eye, muscle, heart, line noise | [09](modules/09-artifact-handling.md) |
| [clean_rawdata](https://github.com/sccn/clean_rawdata) | 30 min | EEGLAB plugin; its README explains how ASR works | [09](modules/09-artifact-handling.md) |
| [mne-denoise ASR](https://mne.tools/mne-denoise/asr.html) | 30 min | A Python implementation of ASR to experiment with | [09](modules/09-artifact-handling.md) |
| [NeuroKit2](https://neuropsychology.github.io/NeuroKit/) | 30 min | ECG/PPG processing and the full set of HRV metrics in a few lines; includes an HRV tutorial | [14](modules/14-hrv-basics.md) |
| [MNE-BIDS](https://mne.tools/mne-bids/stable/index.html) | 20 min | Reading and writing BIDS-formatted datasets, such as those on OpenNeuro | — |
| [specparam (formerly FOOOF)](https://github.com/fooof-tools/fooof) | 30 min | Separates the 1/f background of a spectrum from oscillatory peaks; a better way to measure an alpha peak than raw band power | [10](modules/10-spectral-features.md) |
| [BrainFlow](https://brainflow.org) | 30 min | Device-agnostic streaming from consumer EEG hardware; useful for real-time experiments | [13](modules/13-neurofeedback-loop.md) |
| [Lab Streaming Layer (LSL)](https://labstreaminglayer.org) | 30 min | The common protocol for streaming and synchronising EEG, markers and other signals in real time | [13](modules/13-neurofeedback-loop.md) |
| [Squiggly](https://github.com/alexdni/squiggly) | 20 min | Alex's open-source 19-channel EEG assessment tool; its README maps out a full qEEG analysis | [15](modules/15-divergence-orientation.md) |

## Papers

| Resource | Time | Use it for | Modules |
| --- | --- | --- | --- |
| [Enriquez-Geppert, Huster and Herrmann (2017)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5319996/), *EEG-Neurofeedback as a Tool to Modulate Cognition and Behavior: A Review Tutorial* | 60 min | How a neurofeedback study and system are built, step by step; Figure 2 is the whole field on one page | [13](modules/13-neurofeedback-loop.md) |
| [Shaffer and Ginsberg (2017)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5624990/), *An Overview of Heart Rate Variability Metrics and Norms* | 45 min | HRV metrics, what they mean, and published norms | [14](modules/14-hrv-basics.md) |

## Datasets

| Resource | Size | Use it for |
| --- | --- | --- |
| [Course sample recordings](data/README.md) | 13 EDF files, 17 MB | Every figure and lab in this course; anonymised real recordings chosen to show specific signals and artifacts |
| [PhysioNet EEG Motor Movement/Imagery](https://physionet.org/content/eegmmidb/1.0.0/) | 109 subjects, 64 ch, 160 Hz | Loads directly through `mne.datasets.eegbci`; runs 1 and 2 are one-minute eyes-open and eyes-closed baselines |
| [OpenNeuro](https://openneuro.org) | Hundreds of datasets | BIDS-formatted EEG datasets, no registration; resting-state sets are useful for band-power practice |
| [PhysioNet](https://physionet.org) | Large | Many physiological datasets beyond EEG, including ECG collections for HRV practice |

## Open-source projects

EEG 101 itself is retired: NeuroTechX archived the app in 2021 after InterAxon closed the Muse SDK, and its README now points to EEGEdu as the successor. Everything below is open source or openly licensed, and nothing here asks for an account; where a site has a request form for part of its material, the table says so. The [open-source projects page](open-source.md) has a "try it in 10 minutes" step for each.

| Project or deck | What it is | Login? | Why it is on this map |
| --- | --- | --- | --- |
| [EEG 101](https://github.com/NeuroTechX/eeg-101) (NeuroTechX) | Archived interactive Android tutorial (React Native + Java) that walked a Muse wearer through EEG neurophysiology, hardware, filtering, spectra, and a simple BCI classifier | No | The source is still readable: the tutorial text in `src` is a well-paced five-screen intro, and the signal classes show real-time filtering and plotting in a mobile app. Useful reference for the game-design team |
| [EEGEdu](https://github.com/kylemath/EEGEdu) (Mathewson lab, University of Alberta) | Browser-based successor to EEG 101: interactive modules on raw signal, filtering, spectra, bands, and evoked responses, streaming live from a Muse over Web Bluetooth. MIT licence, used in a 100-student undergraduate course | No | If a Muse 2 or Muse S is available, this is the fastest hands-on orientation there is; no install, just a browser |
| [EEG-ExPy](https://github.com/NeuroTechX/eeg-expy) (formerly eeg-notebooks, NeuroTechX) | Python library of classic EEG experiments (visual N170, P300, SSVEP, alpha) built on BrainFlow, PsychoPy and MNE, with [documentation](https://neurotechx.github.io/EEG-ExPy/) and bundled example datasets | No | The analysis notebooks run on the bundled data without any hardware, so you can see a full experiment-to-plot pipeline in MNE; maintained from Toronto (John Griffiths, U of T) |
| [BrainFlow](https://brainflow.readthedocs.io/en/stable/SupportedBoards.html) | Open-source SDK that streams from OpenBCI, Muse, BrainBit, Callibri, Unicorn and many other boards through one API, with Python, Node, Java and more bindings, plus a synthetic board and a playback-file board | No | The device layer under most open EEG tooling; the synthetic and playback boards let you test a real-time pipeline with no headset. Several of the boards it supports are ones Divergence integrates |
| [Introduction to Modern BCI Design](https://sccn.ucsd.edu/wiki/Introduction_To_Modern_Brain-Computer_Interface_Design) (Christian Kothe, SCCN/UCSD) | Ten recorded lectures with downloadable slide PDFs: EEG basics, signal processing in BCIs, ERP processing, oscillatory processes, machine learning, plus Lab Streaming Layer and BCILAB tutorials | No | The best open deck set on EEG basics and signal processing for engineers. Kothe is the author of ASR, so his lectures are also background reading for the de-noising project |
| [NeuroTechX awesome-bci](https://github.com/NeuroTechX/awesome-bci) | Curated list of open-source software, hardware, datasets, courses and communities | No | The index to go to when this map runs out |
| [NeuroTechEDU lessons](http://learn.neurotechedu.com/lessons/) (NeuroTechX) | Free written lessons on EEG, BCI and neurotech basics | No | Short written primers; community-maintained, so expect a few stale links |
| [OpenBCI docs: EEG setup](https://docs.openbci.com/GettingStarted/Biosensing-Setups/EEGSetup/) | Electrode wiring, reference and bias, 10-20 placement, and a walk-through of recording your own alpha waves | No | The most practical "what is a reference electrode" page on the web, and the whole [docs site](https://docs.openbci.com/) is MIT licensed |
| [Brainstorm introduction tutorials](https://neuroimage.usc.edu/brainstorm/Tutorials/AllIntroduction) (USC and McGill) | Free GUI application for MEG/EEG analysis; a compiled version runs without a MATLAB licence; step-by-step intro tutorials on a provided dataset, plus an EEG-specific tutorial | No | A no-code way to see filtering, artifact rejection, spectra and source maps before writing any Python |
| [PURSUE course modules](https://pursue.richmond.edu/teaching-modules/full-semester-course/) (University of Richmond) | Thirteen-module undergraduate EEG/ERP course, CC BY-NC-SA 4.0 | Decks on the module pages; data-processing labs and ERP datasets by request form | Already the Week 1 deck; the full module list covers signal generation, recording procedure, and processing labs |
| [Introductory Neuroscience and Neuro-Instrumentation](https://onlinecourses.nptel.ac.in/noc20_ee95/preview) (NPTEL, IISc Bangalore) | University lecture series; weeks 2-4 cover EEG recording systems, waveforms, and signal conditioning, with EEGLAB demos | No for the YouTube lectures; free enrolment only if you want certification | An engineering-flavoured alternative to the psychology-flavoured decks above |

Already in the library and also login-free: MNE tutorials, the FieldTrip and EEGLAB workshop videos, the EEGLAB wiki, Neural Data Science in Python, the Python EEG Handbook, and all the open-access papers.

## Paid options

Paid options exist (Cohen's Udemy courses, a few EEG intro courses on Udemy, the live SPM and ERP Boot Camp workshops, and Cohen's book *Analyzing Neural Time Series Data*, MIT Press, 2014, which is the long form of the ANTS lectures), but nothing in this course depends on them.
