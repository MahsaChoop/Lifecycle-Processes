"""Rolling IQR anomaly detection and weekly title bags."""
from __future__ import annotations

import numpy as np
import pandas as pd

from functions.config import IQR_CONFIG

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


def build_weekly_titles(eventsPerobj_df, objects_attributes, cfg, event_type_id=None):
    event_type_id = cfg.closed_event_type_id if event_type_id is None else event_type_id
    closed_events_objects = eventsPerobj_df.loc[
        eventsPerobj_df["event_type_id"].eq(event_type_id) & eventsPerobj_df["object_type"].eq(cfg.issue_object_type)
    ].copy()
    closed_events_objects["week_start"] = _week_start(closed_events_objects["event_timestamp"])
    closed_events_objects["object_id_key"] = pd.to_numeric(
        closed_events_objects["object_id"], errors="coerce"
    ).astype("Int64")

    title_attributes = objects_attributes.loc[
        objects_attributes["object_attribute_id"].eq(cfg.title_attribute_id)
    ].copy()
    title_attributes["object_id_key"] = pd.to_numeric(
        title_attributes["object_id"], errors="coerce"
    ).astype("Int64")
    title_cols = ["object_id_key", "object_id", "object_attribute_id", "attribute_value"]
    if "timestamp" in title_attributes.columns:
        title_cols.append("timestamp")

    joined = closed_events_objects.merge(
        title_attributes[title_cols],
        on="object_id_key",
        how="left",
        suffixes=("_event_object", "_attribute"),
    )

    fallback_text = joined.get("object_description", pd.Series("", index=joined.index))
    joined["title_text"] = joined["attribute_value"].fillna(fallback_text)

    def unique_nonempty(values):
        seen = []
        for value in values.dropna().astype(str):
            value = value.strip()
            if value and value not in seen:
                seen.append(value)
        return seen

    weekly_text = (
        joined.groupby("week_start")
        .agg(
            event_count=("event_id", "nunique"),
            title_count=("attribute_value", lambda s: s.dropna().nunique()),
            titles_in_week=("title_text", unique_nonempty),
            event_descriptions=("event_description", unique_nonempty),
            event_ids=("event_id", lambda s: sorted(pd.Series(s).dropna().unique().tolist())),
            object_ids=("object_id_key", lambda s: sorted(pd.Series(s).dropna().unique().tolist())),
        )
        .reset_index()
    )
    weekly_text["titles_text"] = weekly_text["titles_in_week"].apply(lambda titles: "\n".join(titles))
    return weekly_text, joined


