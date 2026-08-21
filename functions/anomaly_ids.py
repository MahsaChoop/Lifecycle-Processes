"""Export anomaly object/event ID tables from flagged IQR weeks."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from functions.anomaly import _week_start


def _closed_events_in_anomaly_weeks(rolling_iqr_anomalies, eventsPerobj_df, cfg):
    anomaly_weeks = pd.to_datetime(
        rolling_iqr_anomalies.loc[rolling_iqr_anomalies["is_anomaly"], "week_start"]
    ).dt.normalize()
    closed = eventsPerobj_df.loc[
        eventsPerobj_df["event_type_id"].eq(cfg.closed_event_type_id)
        & eventsPerobj_df["object_type"].eq(cfg.issue_object_type)
    ].copy()
    if closed.empty or anomaly_weeks.empty:
        closed["week_start"] = pd.NaT
        return closed.iloc[0:0]
    closed["week_start"] = _week_start(closed["event_timestamp"])
    return closed.loc[closed["week_start"].isin(anomaly_weeks)].copy()


def build_anomaly_object_ids(rolling_iqr_anomalies, eventsPerobj_df, cfg):
    closed = _closed_events_in_anomaly_weeks(rolling_iqr_anomalies, eventsPerobj_df, cfg)
    closed["object_id"] = pd.to_numeric(closed["object_id"], errors="coerce").astype("Int64")
    return (
        closed[["week_start", "object_id"]]
        .dropna(subset=["object_id"])
        .drop_duplicates()
        .reset_index(drop=True)
    )


def build_anomaly_event_ids(rolling_iqr_anomalies, eventsPerobj_df, cfg):
    closed = _closed_events_in_anomaly_weeks(rolling_iqr_anomalies, eventsPerobj_df, cfg)
    return (
        closed[["week_start", "event_id"]]
        .dropna(subset=["event_id"])
        .drop_duplicates()
        .reset_index(drop=True)
    )


def export_anomaly_ids(rolling_iqr_anomalies, eventsPerobj_df, cfg, tables_dir=None):
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    anomaly_object_ids = build_anomaly_object_ids(rolling_iqr_anomalies, eventsPerobj_df, cfg)
    anomaly_event_ids = build_anomaly_event_ids(rolling_iqr_anomalies, eventsPerobj_df, cfg)
    anomaly_object_ids.to_csv(tables_dir / "anomaly_object_ids.csv", index=False)
    anomaly_event_ids.to_csv(tables_dir / "anomaly_event_ids.csv", index=False)
    return anomaly_object_ids, anomaly_event_ids
