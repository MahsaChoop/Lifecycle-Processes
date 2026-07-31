"""Portable paths and analysis constants shared by every dataset.

Dataset-specific values (database paths, event type ids, attribute ids, OCEL2
event tables, output folders) live in `functions/configs/<dataset>.py` and are
loaded with `functions.configs.load_dataset_config`.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
RESULTS_TABLES = PROJECT_ROOT / "results" / "tables"
RESULTS_FIGURES = PROJECT_ROOT / "results" / "figures"
COMPLEXITY_REPO = PROJECT_ROOT / "process-complexity"

IQR_CONFIG = {
    "window_size": 30,
    "min_periods": 8,
    "iqr_multiplier": 1.5,
}

# Utility experiment (unchanged values)
SEED = 40
MAX_REP = 5
REPRO_SEEDS = list(range(10))


def save_figure(fig, figures_dir, stem, dpi=300):
    """Save figure as both PNG and PDF at the given dpi."""
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".pdf"):
        fig.savefig(figures_dir / f"{stem}{ext}", dpi=dpi, bbox_inches="tight")
