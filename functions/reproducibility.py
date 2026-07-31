"""Multi-seed random-control reproducibility loop """
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from pm4py.algo.evaluation.precision import algorithm as precision_evaluator
from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator

from functions.complexity_metrics import (
    _gini,
    _variant_case_counts,
)
from functions.config import REPRO_SEEDS
from functions.discovery import (
    complexity_size_cfc_simplicity,
    compute_generalization,
    df_to_event_log,
    safe_f1,
)


def run_seed_reproducibility(
    flat_df_clean,
    all_cases_clean,
    num_vital_cases_clean,
    miners,
    consolidated_results_table_clean,
    cfg,
    repro_seeds=None,
    tables_dir=None,
):
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    if repro_seeds is None:
        repro_seeds = REPRO_SEEDS

    repro_discovery_rows = []
    repro_complexity_rows = []

    for seed in repro_seeds:
        local_rng = np.random.default_rng(seed)
        sampled = local_rng.choice(all_cases_clean, size=num_vital_cases_clean, replace=False)
        sample_df = (
            flat_df_clean[flat_df_clean["case:concept:name"].isin(sampled)]
            .copy()
            .sort_values(["case:concept:name", "time:timestamp"])
            .reset_index(drop=True)
        )
        elog = df_to_event_log(sample_df)

        for miner_name, miner_fn in miners.items():
            rec = {
                "seed": seed,
                "discovery_method": miner_name,
                "fitness": np.nan,
                "precision": np.nan,
                "f_score": np.nan,
                "generalization": np.nan,
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

            repro_discovery_rows.append(rec)

        crow = {"seed": seed}
        try:
            counts = _variant_case_counts(elog)
            total = counts.sum()
            crow["top1_variant_coverage"] = float(counts[0] / total) if counts.size else np.nan
            crow["top10_variant_coverage"] = float(counts[:10].sum() / total) if counts.size else np.nan
            crow["gini_variant_concentration"] = _gini(counts)
        except Exception as exc:
            print(f"[seed={seed}] similarity stats failed: {exc}")

        repro_complexity_rows.append(crow)

    repro_discovery_df = pd.DataFrame(repro_discovery_rows)
    repro_complexity_df = pd.DataFrame(repro_complexity_rows).set_index("seed")

    repro_discovery_df.to_csv(tables_dir / "repro_discovery_metrics.csv", index=False)
    repro_complexity_df.to_csv(tables_dir / "repro_complexity_similarity_metrics.csv")

    def _cv(series):
        m = series.mean()
        return series.std(ddof=1) / abs(m) if m not in (0, np.nan) and not pd.isna(m) and m != 0 else np.nan

    _disc_ok = repro_discovery_df[repro_discovery_df["status"] == "ok"]
    _disc_metrics = ["fitness", "precision", "f_score", "size", "cfc"]
    repro_discovery_summary = _disc_ok.groupby("discovery_method")[_disc_metrics].agg(
        ["mean", "std", _cv]
    )
    repro_discovery_summary.columns = [
        f"{metric}_{'cv' if stat == '_cv' else stat}" for metric, stat in repro_discovery_summary.columns
    ]
    repro_discovery_summary = repro_discovery_summary.reset_index()

    _num_cols = repro_complexity_df.select_dtypes("number").columns
    repro_complexity_summary = pd.DataFrame(
        {
            "mean": repro_complexity_df[_num_cols].mean(),
            "std": repro_complexity_df[_num_cols].std(ddof=1),
        }
    )
    repro_complexity_summary["cv"] = (
        repro_complexity_summary["std"] / repro_complexity_summary["mean"].abs()
    )
    repro_complexity_summary = repro_complexity_summary.sort_values("cv")

    repro_discovery_summary.to_csv(tables_dir / "repro_discovery_summary.csv", index=False)
    repro_complexity_summary.to_csv(tables_dir / "repro_complexity_summary.csv")

    print(f"Reproducibility over {len(repro_seeds)} seeds: {repro_seeds}")
    print("\nDiscovery metrics summary (mean/std/CV per miner):")
    print(repro_discovery_summary)
    print("\nWithin-log similarity summary (mean/std/CV per metric, sorted by CV):")
    print(repro_complexity_summary)

    seed_fscore_mean = (
        repro_discovery_df[repro_discovery_df["status"] == "ok"]
        .groupby("discovery_method")["f_score"]
        .mean()
    )

    consolidated_results_table_clean_repro = consolidated_results_table_clean.copy()
    mask = consolidated_results_table_clean_repro["log_name"] == "random_case_control"
    mapped_fscore = consolidated_results_table_clean_repro.loc[mask, "discovery_method"].map(
        seed_fscore_mean
    )
    consolidated_results_table_clean_repro.loc[mask, "f_score"] = mapped_fscore.fillna(
        consolidated_results_table_clean_repro.loc[mask, "f_score"]
    ).to_numpy()

    print(
        "Consolidated clean-log results (random_case_control f_score = mean over "
        f"{repro_discovery_df['seed'].nunique()} seeds):"
    )
    print(consolidated_results_table_clean_repro)
    consolidated_results_table_clean_repro.to_csv(
        tables_dir / "consolidated_results_table_clean_repro.csv", index=False
    )
    print(f"Saved {tables_dir / 'consolidated_results_table_clean_repro.csv'}")

    return {
        "repro_discovery_df": repro_discovery_df,
        "repro_complexity_df": repro_complexity_df,
        "repro_discovery_summary": repro_discovery_summary,
        "repro_complexity_summary": repro_complexity_summary,
        "consolidated_results_table_clean_repro": consolidated_results_table_clean_repro,
    }
