"""Portable paths and shared constants (values match the original notebooks)."""
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
    # #region agent log
    import json as _json, time as _time
    _log_path = Path(__file__).resolve().parent.parent / "debug-2650fc.log"
    def _dbg(hypothesis_id, message, data, run_id="pre-fix"):
        with open(_log_path, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps({
                "sessionId": "2650fc", "runId": run_id, "hypothesisId": hypothesis_id,
                "location": "config.py:save_figure", "message": message, "data": data,
                "timestamp": int(_time.time() * 1000),
            }) + "\n")
    # #endregion
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    # #region agent log
    _dbg("A", "save_figure entered", {
        "stem": stem, "dpi": dpi, "figures_dir": str(figures_dir.resolve()),
        "expected_root": str(RESULTS_FIGURES.resolve()),
        "same_as_RESULTS_FIGURES": str(figures_dir.resolve()) == str(RESULTS_FIGURES.resolve()),
    })
    # #endregion
    for ext in (".png", ".pdf"):
        out = figures_dir / f"{stem}{ext}"
        try:
            fig.savefig(out, dpi=dpi, bbox_inches="tight")
            # #region agent log
            _dbg("B", "savefig ok", {
                "ext": ext, "path": str(out.resolve()),
                "exists": out.exists(), "size": out.stat().st_size if out.exists() else None,
            })
            # #endregion
        except Exception as e:
            # #region agent log
            _dbg("B", "savefig failed", {
                "ext": ext, "path": str(out), "error_type": type(e).__name__, "error": str(e),
            })
            # #endregion
            raise
    # #region agent log
    png_p = figures_dir / f"{stem}.png"
    pdf_p = figures_dir / f"{stem}.pdf"
    _dbg("D", "save_figure done", {
        "stem": stem, "png_exists": png_p.exists(), "pdf_exists": pdf_p.exists(),
        "dir_listing_pdfs": [p.name for p in figures_dir.glob(f"{stem}.*")],
    })
    # #endregion
