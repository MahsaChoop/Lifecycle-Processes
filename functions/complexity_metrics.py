"""EPA / process-complexity wrappers and log complexity table."""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pm4py

from functions.config import COMPLEXITY_REPO

LOG_ORDER = ["vitalizing", "random_case_control", "whole"]


def ensure_complexity_deps():
    for _pkg, _mod in [("BitVector", "BitVector"), ("lempel_ziv_complexity", "lempel_ziv_complexity")]:
        try:
            importlib.import_module(_mod)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", _pkg])

    repo = Path(COMPLEXITY_REPO).resolve()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    import Complexity  # noqa: F401
    return Complexity


def _variant_case_counts(elog):
    variants = pm4py.get_variants(elog)
    counts = [len(v) if hasattr(v, "__len__") else int(v) for v in variants.values()]
    return np.array(sorted(counts, reverse=True), dtype=float)


def _gini(counts):
    if counts.size == 0 or counts.sum() == 0:
        return np.nan
    x = np.sort(counts)
    n = x.size
    total = x.sum()
    return float((2 * np.sum(np.arange(1, n + 1) * x) - (n + 1) * total) / (n * total))


def compute_log_complexity_table(clean_log_groups_eventlog, cfg, log_order=None, tables_dir=None):
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    if log_order is None:
        log_order = LOG_ORDER

    Complexity = ensure_complexity_deps()

    rows = []
    for name in log_order:
        pm_log = clean_log_groups_eventlog[name]
        row = {"log_name": name}
        try:
            plain = Complexity.generate_log(pm_log)
            pa = Complexity.build_graph(plain)

            var_ent, var_ent_norm = Complexity.graph_complexity(pa)
            seq_ent, seq_ent_norm = Complexity.log_complexity(pa)
            row.update(
                {
                    "variant_entropy": var_ent,
                    "norm_variant_entropy": var_ent_norm,
                    "sequence_entropy": seq_ent,
                    "norm_sequence_entropy": seq_ent_norm,
                }
            )

            measures = Complexity.perform_measurements(
                ["all"], log=plain, pm4py_log=pm_log, pa=pa, quiet=True
            )
            for key, value in measures.items():
                if isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        row[f"{key} ({sub_key})"] = sub_val
                else:
                    row[key] = value
        except Exception as exc:
            row["error"] = str(exc)
            print(f"[{name}] complexity computation failed: {exc}")

        try:
            counts = _variant_case_counts(pm_log)
            total = counts.sum()
            row["top1_variant_coverage"] = float(counts[0] / total) if counts.size else np.nan
            row["top10_variant_coverage"] = float(counts[:10].sum() / total) if counts.size else np.nan
            row["gini_variant_concentration"] = _gini(counts)
        except Exception as exc:
            print(f"[{name}] similarity stats failed: {exc}")

        rows.append(row)

    log_complexity_similarity_table = (
        pd.DataFrame(rows).set_index("log_name").reindex(log_order)
    )

    print("Log complexity + within-log similarity metrics:")
    print(log_complexity_similarity_table)
    out_path = tables_dir / "log_complexity_similarity_metrics.csv"
    log_complexity_similarity_table.to_csv(out_path)
    print(f"Saved {out_path}")
    return log_complexity_similarity_table
