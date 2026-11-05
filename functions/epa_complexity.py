"""EPA log-complexity metrics via MaxVidgof/process-complexity."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from functions.config import COMPLEXITY_REPO
from functions.discovery import df_to_event_log

EPA_MEASURES = ["magnitude", "variety", "affinity"]
EPA_MEASURE_KEYS = {
    "magnitude": "Magnitude",
    "variety": "Variety",
    "affinity": "Affinity",
}
VARIANT_METRICS = ("variant_entropy", "normalized_variant_entropy")
SEQUENCE_METRICS = ("sequence_entropy", "normalized_sequence_entropy")

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
ALL_METRICS = [column for column in RESULT_COLUMNS if column not in {"log_name", "n_cases", "status", "error"}]


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


def _resolve_metrics(metrics):
    if metrics is None:
        return list(ALL_METRICS)
    resolved = list(metrics)
    unknown = [name for name in resolved if name not in ALL_METRICS]
    if unknown:
        raise ValueError(f"Unknown EPA metrics: {unknown}")
    return resolved


def _result_columns(metrics):
    return ["log_name", "n_cases", *metrics, "status", "error"]


def _empty_record(log_name, metrics, n_cases=0, status="failed", error=None):
    record = {
        "log_name": log_name,
        "n_cases": n_cases,
        "status": status,
        "error": error,
    }
    for name in metrics:
        record[name] = np.nan
    return record


def _metrics_for_log(Complexity, df, metrics):
    wanted = set(metrics)
    elog = df_to_event_log(df)
    out = {}

    need_variant = bool(wanted.intersection(VARIANT_METRICS))
    need_sequence = bool(wanted.intersection(SEQUENCE_METRICS))
    epa_measures = [name for name in EPA_MEASURES if name in wanted]

    log = None
    epa = None
    if need_variant or need_sequence or "magnitude" in wanted:
        log = Complexity.generate_log(elog)
    if need_variant or need_sequence:
        epa = Complexity.build_graph(log)

    if need_variant:
        variant_entropy, normalized_variant_entropy = Complexity.graph_complexity(epa)
        if "variant_entropy" in wanted:
            out["variant_entropy"] = variant_entropy
        if "normalized_variant_entropy" in wanted:
            out["normalized_variant_entropy"] = normalized_variant_entropy

    if need_sequence:
        sequence_entropy, normalized_sequence_entropy = Complexity.log_complexity(epa)
        if "sequence_entropy" in wanted:
            out["sequence_entropy"] = sequence_entropy
        if "normalized_sequence_entropy" in wanted:
            out["normalized_sequence_entropy"] = normalized_sequence_entropy

    if epa_measures:
        extra = Complexity.perform_measurements(
            epa_measures,
            log=log,
            pm4py_log=elog,
            pa=epa,
            quiet=True,
        )
        for name in epa_measures:
            out[name] = extra.get(EPA_MEASURE_KEYS[name], np.nan)
    return out


def evaluate_epa_complexity(
    log_groups_df,
    cfg,
    tables_dir=None,
    out_filename="epa_complexity.csv",
    metrics=None,
):
    """Compute EPA metrics for each log group.

    metrics selects which values to compute and return. The default is every
    metric: variant and sequence entropy, magnitude, variety, and affinity.
    """
    metrics = _resolve_metrics(metrics)
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    Complexity = import_complexity()

    records = []
    for log_name, df in log_groups_df.items():
        n_cases = 0 if df is None or df.empty else int(df["case:concept:name"].nunique())
        rec = _empty_record(log_name, metrics, n_cases=n_cases, status="ok", error=None)
        if df is None or df.empty:
            rec["status"] = "failed"
            rec["error"] = "empty log"
            records.append(rec)
            continue
        try:
            rec.update(_metrics_for_log(Complexity, df, metrics))
        except Exception as exc:
            rec["status"] = "failed"
            rec["error"] = str(exc)
        records.append(rec)

    results = (
        pd.DataFrame.from_records(records, columns=_result_columns(metrics))
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
