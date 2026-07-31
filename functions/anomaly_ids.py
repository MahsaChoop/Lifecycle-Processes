"""Export anomaly object/event ID tables."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_anomaly_object_ids(anomaly_context):
    return (
        anomaly_context[["week_start", "object_ids"]]
        .explode("object_ids")
        .rename(columns={"object_ids": "object_id"})
        .dropna(subset=["object_id"])
        .drop_duplicates()
        .reset_index(drop=True)
    )


def build_anomaly_event_ids(anomaly_context):
    return (
        anomaly_context[["week_start", "event_ids"]]
        .explode("event_ids")
        .rename(columns={"event_ids": "event_id"})
        .dropna(subset=["event_id"])
        .drop_duplicates()
        .reset_index(drop=True)
    )


def export_anomaly_ids(anomaly_context, cfg, tables_dir=None):
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    anomaly_object_ids = build_anomaly_object_ids(anomaly_context)
    anomaly_event_ids = build_anomaly_event_ids(anomaly_context)
    anomaly_object_ids.to_csv(tables_dir / "anomaly_object_ids.csv", index=False)
    anomaly_event_ids.to_csv(tables_dir / "anomaly_event_ids.csv", index=False)
    return anomaly_object_ids, anomaly_event_ids
