"""Portable paths and shared constants """
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
RESULTS_TABLES = PROJECT_ROOT / "results" / "tables"
RESULTS_FIGURES = PROJECT_ROOT / "results" / "figures"

COMMITIZEN_DUCKDB = DATA_RAW / "commitizen.duckdb"
OCEL2_SQLITE = DATA_RAW / "ocel2_commitizen.sqlite"
COMPLEXITY_REPO = PROJECT_ROOT / "process-complexity"

# State extractor / anomaly (unchanged values)
ANOMALY_EVENT_TYPE_ID = 105
ANOMALY_OBJECT_TYPE = "issue"
CREATE_EVENT_TYPE_ID = 31
COMMIT_EVENT_TYPE_ID = 43
COMMIT_OBJECT_TYPE = "commit"
COMMIT_MESSAGE_ATTRIBUTE_ID = 18
TITLE_ATTRIBUTE_ID = 6

IQR_CONFIG = {
    "window_size": 30,
    "min_periods": 8,
    "iqr_multiplier": 1.5,
}

# Utility experiment (unchanged values)
SEED = 40
MAX_REP = 5
END_ACTIVITY_1 = "closed"
END_ACTIVITY_2 = "head_ref_deleted"
OBJECT_TYPE = "issue"
REPRO_SEEDS = list(range(10))

FIGURES_DIR = RESULTS_FIGURES


def save_figure(fig, figures_dir, stem, dpi=300):
    """Save figure as both PNG and PDF at the given dpi."""
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".pdf"):
        fig.savefig(figures_dir / f"{stem}{ext}", dpi=dpi, bbox_inches="tight")
