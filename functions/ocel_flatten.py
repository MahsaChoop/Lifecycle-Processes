"""Flatten OCEL2 SQLite to an issue-centric event log DataFrame."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from functions.config import OBJECT_TYPE, OCEL2_SQLITE

SUBTABLES = [
    "event_assigned", "event_closed", "event_commented", "event_committed",
    "event_created", "event_cross_referenced", "event_labeled", "event_merged",
    "event_referenced", "event_renamed", "event_reopened", "event_reviewed",
    "event_review_requested", "event_subscribed", "event_head_ref_deleted",
    "event_head_ref_force_pushed", "event_ready_for_review",
    "event_convert_to_draft", "event_unlabeled", "event_milestoned",
    "event_demilestoned", "event_unassigned", "event_mentioned",
    "event_auto_merge_disabled", "event_auto_rebase_enabled",
    "event_auto_squash_enabled", "event_base_ref_changed",
    "event_base_ref_deleted", "event_base_ref_force_pushed",
    "event_connected", "event_converted_to_discussion",
    "event_copilot_work_finished", "event_copilot_work_started",
    "event_head_ref_restored", "event_issue_type_added",
    "event_issue_type_changed", "event_locked", "event_parent_issue_added",
    "event_pinned", "event_review_request_removed",
    "event_sub_issue_added", "event_unsubscribed", "event_unpinned",
]


def flatten_ocel2_issue_log(sqlite_path=None, object_type=OBJECT_TYPE):
    sqlite_path = Path(sqlite_path or OCEL2_SQLITE)
    CONN = sqlite3.connect(str(sqlite_path))

    union_sql = " UNION ALL ".join(
        f"SELECT ocel_id, ocel_time FROM {t}" for t in SUBTABLES
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
