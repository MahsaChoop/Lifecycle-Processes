"""Schema validation, incomplete-trace removal, repetition filter, random control."""
from __future__ import annotations

import numpy as np
import pandas as pd

from functions.config import MAX_REP, SEED

required_cols = ["case:concept:name", "concept:name", "time:timestamp"]


def validate_and_standardize(df: pd.DataFrame, name: str) -> pd.DataFrame:
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"{name} is missing required columns: {missing_cols}")

    out = df[required_cols].copy()
    out["case:concept:name"] = out["case:concept:name"].astype(str)
    out["concept:name"] = out["concept:name"].astype(str)
    out["time:timestamp"] = pd.to_datetime(out["time:timestamp"], utc=True, errors="coerce")

    out = out.dropna(subset=required_cols)
    out = out.sort_values(["case:concept:name", "time:timestamp"]).reset_index(drop=True)

    if out.empty:
        raise ValueError(f"{name} is empty after cleaning.")

    return out


def remove_incomplete_traces_two_ends(
    df: pd.DataFrame,
    end_activity_1: str,
    end_activity_2: str,
) -> pd.DataFrame:
    """Keep cases whose last activity is end_activity_1 or end_activity_2."""
    if df.empty:
        return df.copy()

    ordered = df.sort_values(["case:concept:name", "time:timestamp"]).copy()
    last_events = ordered.groupby("case:concept:name", sort=False).tail(1)
    valid_cases = last_events[
        last_events["concept:name"].isin([end_activity_1, end_activity_2])
    ]["case:concept:name"]

    return (
        ordered[ordered["case:concept:name"].isin(valid_cases)]
        .copy()
        .reset_index(drop=True)
    )


def keep_traces_containing_end_activities(
    df: pd.DataFrame,
    end_activity_1: str,
    end_activity_2: str,
) -> pd.DataFrame:
    """Keep full traces that contain end_activity_1 or end_activity_2 anywhere."""
    if df.empty:
        return df.copy()

    ordered = df.sort_values(["case:concept:name", "time:timestamp"]).copy()
    ends = {end_activity_1, end_activity_2}
    has_end = ordered.groupby("case:concept:name")["concept:name"].transform(
        lambda s: s.isin(ends).any()
    )
    return ordered.loc[has_end].reset_index(drop=True)


def remove_traces_with_high_activity_repetition(
    df: pd.DataFrame,
    max_rep: int = MAX_REP,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    ordered = df.sort_values(["case:concept:name", "time:timestamp"]).copy()
    valid_cases = []

    for case_id, grp in ordered.groupby("case:concept:name", sort=False):
        activity_counts = grp["concept:name"].value_counts()
        if activity_counts.max() <= max_rep:
            valid_cases.append(case_id)

    return (
        ordered[ordered["case:concept:name"].isin(valid_cases)]
        .copy()
        .reset_index(drop=True)
    )


def build_preprocessed_logs(
    flat,
    anomaly_events_df,
    cfg,
    seed=SEED,
    end_activity_1=None,
    end_activity_2=None,
    max_rep=MAX_REP,
):
    """Validate, keep traces containing end activities, filter high repetition, sample random control."""
    end_activity_1 = cfg.end_activity_1 if end_activity_1 is None else end_activity_1
    end_activity_2 = cfg.end_activity_2 if end_activity_2 is None else end_activity_2
    rng = np.random.default_rng(seed)

    flat_df = validate_and_standardize(flat.copy(), "flat")
    vitalizing_df = validate_and_standardize(anomaly_events_df.copy(), "anomaly_events_df")

    flat_df = keep_traces_containing_end_activities(flat_df, end_activity_1, end_activity_2)
    vitalizing_df = keep_traces_containing_end_activities(
        vitalizing_df, end_activity_1, end_activity_2
    )

    if flat_df.empty or vitalizing_df.empty:
        raise ValueError("Preprocessing removed all traces from whole or vitalizing log.")

    vitalizing_df_clean = remove_traces_with_high_activity_repetition(vitalizing_df, max_rep)
    flat_df_clean = remove_traces_with_high_activity_repetition(flat_df, max_rep)

    if vitalizing_df_clean.empty or flat_df_clean.empty:
        raise ValueError("Repetition cleaning removed all traces from vitalizing or whole log.")

    num_vital_cases_clean = vitalizing_df_clean["case:concept:name"].nunique()
    all_cases_clean = flat_df_clean["case:concept:name"].drop_duplicates().to_numpy()

    if num_vital_cases_clean > len(all_cases_clean):
        raise ValueError(
            f"Clean vitalizing cases ({num_vital_cases_clean}) exceed clean whole-log cases ({len(all_cases_clean)})."
        )

    sampled_cases_clean = rng.choice(all_cases_clean, size=num_vital_cases_clean, replace=False)
    random_case_control_df_clean = (
        flat_df_clean[flat_df_clean["case:concept:name"].isin(sampled_cases_clean)]
        .copy()
        .sort_values(["case:concept:name", "time:timestamp"])
        .reset_index(drop=True)
    )

    print(f"=== Repetition cleaning summary (MAX_REP = {max_rep}) ===")
    print(
        f"Vitalizing: {vitalizing_df['case:concept:name'].nunique()} -> "
        f"{vitalizing_df_clean['case:concept:name'].nunique()} cases | "
        f"{len(vitalizing_df)} -> {len(vitalizing_df_clean)} events"
    )
    print(
        f"Whole: {flat_df['case:concept:name'].nunique()} -> "
        f"{flat_df_clean['case:concept:name'].nunique()} cases | "
        f"{len(flat_df)} -> {len(flat_df_clean)} events"
    )
    print(
        f"Random control (rebuilt): {random_case_control_df_clean['case:concept:name'].nunique()} cases | "
        f"{len(random_case_control_df_clean)} events"
    )

    clean_log_groups_df = {
        "vitalizing": vitalizing_df_clean,
        "whole": flat_df_clean,
        "random_case_control": random_case_control_df_clean,
    }

    return {
        "flat_df": flat_df,
        "vitalizing_df": vitalizing_df,
        "flat_df_clean": flat_df_clean,
        "vitalizing_df_clean": vitalizing_df_clean,
        "random_case_control_df_clean": random_case_control_df_clean,
        "clean_log_groups_df": clean_log_groups_df,
        "all_cases_clean": all_cases_clean,
        "num_vital_cases_clean": num_vital_cases_clean,
        "rng": rng,
    }


def preprocess_flat_log(flat, cfg, max_rep=7, end_activity_1=None, end_activity_2=None):
    """Validate, keep traces containing end activities, and filter high repetition."""
    end_activity_1 = cfg.end_activity_1 if end_activity_1 is None else end_activity_1
    end_activity_2 = cfg.end_activity_2 if end_activity_2 is None else end_activity_2

    n_cases_raw = flat["case:concept:name"].nunique()
    n_events_raw = len(flat)

    out = validate_and_standardize(flat.copy(), "flat")
    out = keep_traces_containing_end_activities(out, end_activity_1, end_activity_2)
    n_cases_complete = out["case:concept:name"].nunique()
    n_events_complete = len(out)

    out = remove_traces_with_high_activity_repetition(out, max_rep)
    if out.empty:
        raise ValueError("Category-log preprocessing removed all traces from the flat log.")

    print(
        f"=== Category-log preprocess "
        f"(contain={end_activity_1}/{end_activity_2}, max_rep={max_rep}) ==="
    )
    print(
        f"Raw: {n_cases_raw} cases | {n_events_raw} events"
    )
    print(
        f"After contain-end filter: {n_cases_complete} cases | {n_events_complete} events"
    )
    print(
        f"After max_rep={max_rep}: {out['case:concept:name'].nunique()} cases | {len(out)} events"
    )
    return out
