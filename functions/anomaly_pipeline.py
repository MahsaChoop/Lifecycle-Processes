"""Run rolling IQR anomaly detection and write the result table."""
from __future__ import annotations

from pathlib import Path

from functions.anomaly import rolling_iqr_detect
from functions.config import IQR_CONFIG


def run_rolling_iqr(weekly, cfg, tables_dir=None):
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)

    rolling_iqr_anomalies = rolling_iqr_detect(weekly[cfg.closed_event_type_id], **IQR_CONFIG)
    n_anomalies = int(rolling_iqr_anomalies["is_anomaly"].sum())
    print(f"Detected {n_anomalies} rolling-IQR anomalies for event_type_id={cfg.closed_event_type_id}.")

    out_path = tables_dir / "rolling_iqr_anomalies.csv"
    rolling_iqr_anomalies.to_csv(out_path, index=False)
    print(f"Saved rolling IQR anomalies to {out_path}")
    return rolling_iqr_anomalies
