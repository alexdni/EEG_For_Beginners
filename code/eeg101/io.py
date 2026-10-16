"""Load the course sample recordings with consistent names and electrode positions."""
from pathlib import Path

import mne

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"

# Short name -> file. See data/README.md for what each recording is for.
SAMPLES = {
    "rest_ec": "s01_rest_eyes-closed_19ch.edf",
    "rest_eo": "s02_rest_eyes-open_19ch.edf",
    "linenoise_raw": "s03_linenoise_raw_19ch.edf",
    "linenoise_cleaned": "s04_linenoise_cleaned_19ch.edf",
    "artifacts_ec": "s05_artifacts_eyes-closed_19ch.edf",
    "pipeline_raw": "s06_pipeline_stage0_raw_19ch.edf",
    "pipeline_rejection": "s07_pipeline_stage1_rejection_19ch.edf",
    "pipeline_full": "s08_pipeline_stage2_full_19ch.edf",
    "segments_original": "s09_segments_original_8ch.edf",
    "segments_removed": "s10_segments_removed_8ch.edf",
    "headband_ec": "s11_4ch_eyes-closed.edf",
    "headband_eo": "s12_4ch_eyes-open.edf",
    "headband_task": "s13_4ch_eyes-open_task.edf",
}

# The 10-10 system renamed four 10-20 sites. Most course files use the old names;
# load_sample() converts the few that use the new ones so every sample matches.
NEW_TO_OLD = {"T7": "T3", "T8": "T4", "P7": "T5", "P8": "T6"}

# Conventional band edges in Hz. Authors disagree by a hertz or two; treat these as conventions.
BANDS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}


def sample_path(name: str) -> Path:
    """Return the path of a sample by short name (see SAMPLES) or file name."""
    fname = SAMPLES.get(name, name)
    path = DATA_DIR / fname
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Known samples: {', '.join(SAMPLES)}")
    return path


def load_sample(name: str, montage: bool = True) -> mne.io.Raw:
    """Read a sample EDF into memory and attach standard 10-20 electrode positions.

    Channel names are normalised to the older 10-20 temporal names (T3, T4, T5, T6)
    because that is what most of the files and many clinical tools use. MNE's
    template montage knows both spellings.
    """
    raw = mne.io.read_raw_edf(sample_path(name), preload=True, verbose="error")
    raw.rename_channels({new: old for new, old in NEW_TO_OLD.items() if new in raw.ch_names})
    raw.set_channel_types({ch: "eeg" for ch in raw.ch_names})
    if montage:
        raw.set_montage(standard_montage(), on_missing="warn")
    return raw


def standard_montage() -> str:
    """Name of MNE's template 10-20 montage (renamed to colin27_1020 in MNE 1.13)."""
    builtin = mne.channels.get_builtin_montages()
    return "colin27_1020" if "colin27_1020" in builtin else "standard_1020"
