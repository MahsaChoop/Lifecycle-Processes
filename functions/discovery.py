"""Discovery miners and clean-log F1 evaluation (logic unchanged)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.evaluation.precision import algorithm as precision_evaluator
from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.objects.log.obj import Event, EventLog, Trace

from functions.config import RESULTS_TABLES

IMF_NOISE_THRESHOLDS = [0.3, 0.4, 0.5, 0.6]
HEURISTICS_DEP_THRESHOLDS = [0.6, 0.7, 0.8, 0.9]


def df_to_event_log(df: pd.DataFrame) -> EventLog:
    elog = EventLog()
    for case_id, grp in df.groupby("case:concept:name", sort=False):
        tr = Trace()
        tr.attributes["concept:name"] = str(case_id)
        for _, row in grp.iterrows():
            tr.append(
                Event(
                    {
                        "concept:name": row["concept:name"],
                        "time:timestamp": row["time:timestamp"],
                        "case:concept:name": row["case:concept:name"],
                    }
                )
            )
        elog.append(tr)
    return elog


def discover_alpha(elog: EventLog) -> Tuple[Any, Any, Any]:
    return alpha_miner.apply(elog, variant=alpha_miner.Variants.ALPHA_VERSION_CLASSIC)


def discover_heuristics(elog: EventLog, dep_thresh: float) -> Tuple[Any, Any, Any]:
    params = {
        "dependency_threshold": dep_thresh,
        "and_threshold": 0.65,
        "loop_two_threshold": dep_thresh,
    }
    if hasattr(heuristics_miner, "apply_petri"):
        return heuristics_miner.apply_petri(elog, parameters=params)
    if hasattr(heuristics_miner, "apply"):
        discovered = heuristics_miner.apply(elog, parameters=params)
        if isinstance(discovered, tuple) and len(discovered) == 3:
            return discovered
    raise RuntimeError("Heuristics miner did not return a Petri net in this PM4Py version.")


def discover_inductive(elog: EventLog, variant_name: str = "IM", noise_threshold: float = 0.0) -> Tuple[Any, Any, Any]:
    if variant_name == "IMf":
        try:
            discovered = inductive_miner.apply(
                elog,
                variant=inductive_miner.Variants.IMf,
                parameters={"noise_threshold": noise_threshold},
            )
        except Exception:
            discovered = inductive_miner.apply(
                elog,
                parameters={"noise_threshold": noise_threshold},
            )
    else:
        discovered = inductive_miner.apply(elog)

    if isinstance(discovered, tuple) and len(discovered) == 3:
        return discovered

    net, im, fm = pt_converter.apply(discovered)
    return net, im, fm


def safe_f1(fitness: float, precision: float) -> float:
    if pd.isna(fitness) or pd.isna(precision):
        return np.nan
    if (fitness + precision) == 0:
        return 0.0
    return 2 * fitness * precision / (fitness + precision)


def complexity_size_cfc_simplicity(net: Any) -> Dict[str, float]:
    places = list(getattr(net, "places", []))
    transitions = list(getattr(net, "transitions", []))
    arcs = list(getattr(net, "arcs", []))

    size = float(len(places) + len(transitions) + len(arcs))

    out_counts = {t: 0 for t in transitions}
    for a in arcs:
        src = getattr(a, "source", None)
        if src in out_counts:
            out_counts[src] += 1
    cfc = float(sum(max(v - 1, 0) for v in out_counts.values()))

    simplicity = np.nan
    try:
        from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator

        simplicity = float(simplicity_evaluator.apply(net))
    except Exception:
        pass

    return {"size": size, "cfc": cfc, "simplicity": simplicity}


def compute_generalization(elog: EventLog, net: Any, im: Any, fm: Any) -> float:
    try:
        from pm4py.algo.evaluation.generalization import algorithm as generalization_evaluator

        return float(generalization_evaluator.apply(elog, net, im, fm))
    except Exception:
        return np.nan


def build_miners(
    heuristics_dep_thresholds=None,
    imf_noise_thresholds=None,
):
    if heuristics_dep_thresholds is None:
        heuristics_dep_thresholds = HEURISTICS_DEP_THRESHOLDS
    if imf_noise_thresholds is None:
        imf_noise_thresholds = IMF_NOISE_THRESHOLDS

    miners = {
        "alpha_classic": lambda elog: discover_alpha(elog),
        "inductive_IM": lambda elog: discover_inductive(elog, "IM"),
    }

    for dep_thresh in heuristics_dep_thresholds:
        miners[f"heuristics_dep_{dep_thresh:.1f}"] = (
            lambda elog, d=dep_thresh: discover_heuristics(elog, d)
        )

    for noise_thr in imf_noise_thresholds:
        miners[f"inductive_IMf_noise_{noise_thr:.1f}"] = (
            lambda elog, n=noise_thr: discover_inductive(elog, "IMf", n)
        )
    return miners


def evaluate_clean_logs(clean_log_groups_df, miners=None, tables_dir=None):
    tables_dir = Path(tables_dir or RESULTS_TABLES)
    tables_dir.mkdir(parents=True, exist_ok=True)
    if miners is None:
        miners = build_miners()

    clean_log_groups_eventlog = {
        name: df_to_event_log(df) for name, df in clean_log_groups_df.items()
    }

    clean_records = []
    for group_name, elog in clean_log_groups_eventlog.items():
        distinct_traces = len({tuple(ev["concept:name"] for ev in tr) for tr in elog})

        for miner_name, miner_fn in miners.items():
            rec = {
                "log_name": group_name,
                "discovery_method": miner_name,
                "distinct_traces": distinct_traces,
                "generalization": np.nan,
                "fitness": np.nan,
                "precision": np.nan,
                "f_score": np.nan,
                "size": np.nan,
                "cfc": np.nan,
                "simplicity": np.nan,
                "status": "ok",
                "error": None,
            }
            try:
                net, im, fm = miner_fn(elog)

                fit_res = replay_fitness_evaluator.apply(
                    elog,
                    net,
                    im,
                    fm,
                    variant=replay_fitness_evaluator.Variants.TOKEN_BASED,
                )
                fitness = fit_res.get("log_fitness", np.nan)

                precision = precision_evaluator.apply(
                    elog,
                    net,
                    im,
                    fm,
                    variant=precision_evaluator.Variants.ETCONFORMANCE_TOKEN,
                )

                rec["fitness"] = fitness
                rec["precision"] = precision
                rec["f_score"] = safe_f1(fitness, precision)
                rec["generalization"] = compute_generalization(elog, net, im, fm)
                rec.update(complexity_size_cfc_simplicity(net))

            except Exception as exc:
                rec["status"] = "failed"
                rec["error"] = str(exc)

            clean_records.append(rec)

    results_df_clean = pd.DataFrame.from_records(clean_records)

    consolidated_results_table_clean = (
        results_df_clean[
            [
                "log_name",
                "discovery_method",
                "distinct_traces",
                "generalization",
                "fitness",
                "precision",
                "f_score",
                "size",
                "cfc",
                "simplicity",
                "status",
                "error",
            ]
        ]
        .sort_values(["discovery_method", "log_name"])
        .reset_index(drop=True)
    )

    print(
        f"Expected records: {len(clean_log_groups_eventlog) * len(miners)} | Observed: {len(results_df_clean)}"
    )
    print("\n7) Consolidated results table in clean logs")
    print(consolidated_results_table_clean)
    out_path = tables_dir / "consolidated_results_table_clean.csv"
    consolidated_results_table_clean.to_csv(out_path, index=False)
    print(f"Saved {out_path}")

    failed_rows_clean = consolidated_results_table_clean[
        consolidated_results_table_clean["status"] == "failed"
    ][["log_name", "discovery_method", "error"]]
    if not failed_rows_clean.empty:
        print("\nSome miner/log combinations failed on clean logs:")
        print(failed_rows_clean)

    return consolidated_results_table_clean, clean_log_groups_eventlog, miners
