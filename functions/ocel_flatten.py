"""Flatten OCEL2 SQLite to an issue-centric event log DataFrame."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def flatten_ocel2_issue_log(cfg, sqlite_path=None, object_type=None):
    sqlite_path = Path(sqlite_path or cfg.sqlite_path)
    object_type = object_type or cfg.issue_object_type
    CONN = sqlite3.connect(str(sqlite_path))

    union_sql = " UNION ALL ".join(
        f"SELECT ocel_id, ocel_time FROM {t}" for t in cfg.event_subtables
    )
    times_df = pd.read_sql(union_sql, CONN)

    events_df = pd.read_sql(
        "SELECT e.ocel_id, em.ocel_type_map AS activity, eo.ocel_object_id "
        "FROM event e "
        "JOIN event_map_type em ON e.ocel_type = em.ocel_type "
        "JOIN event_object eo ON e.ocel_id = eo.ocel_event_id",
        CONN,
    )
    case_ids = pd.read_sql(
        f"SELECT ocel_id FROM object WHERE ocel_type = '{object_type}'", CONN
    )["ocel_id"]

    flat = (
        events_df
        .merge(times_df, on="ocel_id", how="left")
        .loc[lambda df: df["ocel_object_id"].isin(case_ids)]
        .dropna(subset=["ocel_time"])
        .rename(columns={"ocel_object_id": "case:concept:name",
                         "activity":       "concept:name",
                         "ocel_time":      "time:timestamp"})
        .sort_values(["case:concept:name", "time:timestamp"])
        .reset_index(drop=True)
    )
    flat["time:timestamp"] = pd.to_datetime(flat["time:timestamp"], utc=True)
    CONN.close()

    print(f"Flattened log: {len(flat)} events, {flat['case:concept:name'].nunique()} cases")
    print(flat[["case:concept:name", "concept:name", "time:timestamp"]].head(10))
    return flat


def build_vitalizing_subset(flat, anomaly_object_ids):
    """Keep flat events whose case id is in the anomaly object-id list."""
    anomaly_df = anomaly_object_ids.copy()
    anomaly_df["object_id"] = anomaly_df["object_id"].astype(str)
    anomaly_events_df = flat[
        flat["case:concept:name"].isin(anomaly_df["object_id"])
    ].copy()
    print(
        f"Anomaly events df: {len(anomaly_events_df)} rows, "
        f"{anomaly_events_df['case:concept:name'].nunique()} cases"
    )
    return anomaly_events_df, anomaly_df


def build_commit_category_logs(
    vitalizing_df_clean,
    anomaly_object_ids,
    commit_typeclass_per_week,
    categories=("feature_work", "tech_debt"),
):
    """Subset the clean vitalizing log by week-level commit dominant_category."""
    def _week_key(series):
        return pd.to_datetime(series, utc=True).dt.tz_localize(None).dt.normalize()

    labeled = anomaly_object_ids.copy()
    labeled["week_start"] = _week_key(labeled["week_start"])
    labeled["object_id"] = labeled["object_id"].astype(str)

    typeclass = commit_typeclass_per_week[["week_start", "dominant_category"]].copy()
    typeclass["week_start"] = _week_key(typeclass["week_start"])
    labeled = labeled.merge(typeclass, on="week_start", how="left")

    logs = {}
    print("=== Commit-category log subsets ===")
    for category in categories:
        n_weeks = typeclass.loc[typeclass["dominant_category"].eq(category), "week_start"].nunique()
        ids = labeled.loc[labeled["dominant_category"].eq(category), "object_id"]
        log_df = vitalizing_df_clean[
            vitalizing_df_clean["case:concept:name"].astype(str).isin(ids)
        ].copy()
        logs[category] = log_df
        print(
            f"{category}: {n_weeks} weeks | "
            f"{log_df['case:concept:name'].nunique()} cases | "
            f"{len(log_df)} events"
        )
    return logs
