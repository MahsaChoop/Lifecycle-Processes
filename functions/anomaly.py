"""Rolling IQR anomaly detection."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _week_start(values):
    ts = pd.to_datetime(values)
    return (ts - pd.to_timedelta(ts.dt.weekday, unit="D")).dt.normalize()


def rolling_iqr_detect(series, window_size=30, min_periods=8, iqr_multiplier=1.5):
    """Detect point anomalies with a backward-looking rolling IQR window."""
    clean = pd.to_numeric(series, errors="coerce").sort_index()
    clean.index = pd.to_datetime(clean.index)
    clean = clean.groupby(clean.index).sum().sort_index()

    history = clean.shift(1).rolling(window=window_size, min_periods=min_periods)
    q1 = history.quantile(0.25)
    q3 = history.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - iqr_multiplier * iqr
    upper = q3 + iqr_multiplier * iqr

    is_low = clean < lower
    is_high = clean > upper
    nonzero_iqr = iqr.replace(0, np.nan)
    high_distance = (clean - upper).clip(lower=0)
    low_distance = (lower - clean).clip(lower=0)
    anomaly_score = ((high_distance + low_distance) / nonzero_iqr).fillna(0)

    return pd.DataFrame(
        {
            "week_start": clean.index,
            "value": clean.values,
            "rolling_q1": q1.values,
            "rolling_q3": q3.values,
            "iqr": iqr.values,
            "lower_bound": lower.values,
            "upper_bound": upper.values,
            "is_anomaly": (is_low | is_high).fillna(False).values,
            "anomaly_direction": np.select(
                [is_high.fillna(False), is_low.fillna(False)],
                ["high", "low"],
                default="normal",
            ),
            "anomaly_score": anomaly_score.values,
        }
    )
