"""EPA log-complexity metrics via MaxVidgof/process-complexity."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from functions.config import COMPLEXITY_REPO
from functions.discovery import df_to_event_log

EPA_MEASURES = ["magnitude", "variety", "affinity"]

RESULT_COLUMNS = [
    "log_name",
    "n_cases",
    "variant_entropy",
    "normalized_variant_entropy",
    "sequence_entropy",
    "normalized_sequence_entropy",
    "magnitude",
    "variety",
    "affinity",
    "status",
    "error",
]


def import_complexity():
    """Import Complexity.py from the cloned process-complexity directory."""
    if not COMPLEXITY_REPO.exists():
        raise FileNotFoundError(
            f"process-complexity not found at {COMPLEXITY_REPO}. "
            "Clone https://github.com/MaxVidgof/process-complexity into that path."
        )
    path = str(COMPLEXITY_REPO)
    if path not in sys.path:
        sys.path.insert(0, path)
    import Complexity

    return Complexity


def _empty_record(log_name, n_cases=0, status="failed", error=None):
    return {
        "log_name": log_name,
        "n_cases": n_cases,
        "variant_entropy": np.nan,
        "normalized_variant_entropy": np.nan,
        "sequence_entropy": np.nan,
        "normalized_sequence_entropy": np.nan,
        "magnitude": np.nan,
        "variety": np.nan,
        "affinity": np.nan,
        "status": status,
        "error": error,
    }


def _metrics_for_log(Complexity, df):
    elog = df_to_event_log(df)
    log = Complexity.generate_log(elog)
    epa = Complexity.build_graph(log)

    variant_entropy, normalized_variant_entropy = Complexity.graph_complexity(epa)
    sequence_entropy, normalized_sequence_entropy = Complexity.log_complexity(epa)
    extra = Complexity.perform_measurements(
        EPA_MEASURES,
        log=log,
        pm4py_log=elog,
        pa=epa,
        quiet=True,
    )
    return {
        "variant_entropy": variant_entropy,
        "normalized_variant_entropy": normalized_variant_entropy,
        "sequence_entropy": sequence_entropy,
        "normalized_sequence_entropy": normalized_sequence_entropy,
        "magnitude": extra.get("Magnitude", np.nan),
        "variety": extra.get("Variety", np.nan),
        "affinity": extra.get("Affinity", np.nan),
    }


def evaluate_epa_complexity(
    log_groups_df,
    cfg,
    tables_dir=None,
    out_filename="epa_complexity.csv",
):
    """Compute EPA entropy plus magnitude, variety, and affinity for each log group."""
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    Complexity = import_complexity()

    records = []
    for log_name, df in log_groups_df.items():
        n_cases = 0 if df is None or df.empty else int(df["case:concept:name"].nunique())
        rec = _empty_record(log_name, n_cases=n_cases, status="ok", error=None)
        if df is None or df.empty:
            rec["status"] = "failed"
            rec["error"] = "empty log"
            records.append(rec)
            continue
        try:
            rec.update(_metrics_for_log(Complexity, df))
        except Exception as exc:
            rec["status"] = "failed"
            rec["error"] = str(exc)
        records.append(rec)

    results = (
        pd.DataFrame.from_records(records, columns=RESULT_COLUMNS)
        .sort_values("log_name")
        .reset_index(drop=True)
    )
    out_path = tables_dir / out_filename
    results.to_csv(out_path, index=False)
    print(f"Saved {out_path}")

    failed = results[results["status"] == "failed"][["log_name", "error"]]
    if not failed.empty:
        print("\nSome log groups failed EPA complexity:")
        print(failed)

    return results
