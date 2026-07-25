"""Load DuckDB tables and build weekly issue counts (same as original notebooks)."""
from __future__ import annotations

import duckdb
import pandas as pd

from functions.config import (
    ANOMALY_EVENT_TYPE_ID,
    COMMITIZEN_DUCKDB,
    CREATE_EVENT_TYPE_ID,
)


def load_events_df(quack_db=None):
    quack_db = quack_db or COMMITIZEN_DUCKDB
    with duckdb.connect(str(quack_db), read_only=True) as con:
        events_df = con.sql("SELECT * FROM main.events").df()
    return events_df


def load_objects_attributes(quack_db=None):
    quack_db = quack_db or COMMITIZEN_DUCKDB
    with duckdb.connect(str(quack_db), read_only=True) as con:
        objects_attributes = con.sql("SELECT * FROM main.object_attribute_values").df()
    return objects_attributes


def load_events_per_obj(quack_db=None):
    quack_db = quack_db or COMMITIZEN_DUCKDB
    with duckdb.connect(str(quack_db), read_only=True) as con:
        eventsPerobj_df = con.sql("SELECT * FROM graph_data_prep.graph_base_table").df()
    return eventsPerobj_df


def build_weekly_issue_counts(eventsPerobj_df, event_ids=None, object_type="issue"):
    if event_ids is None:
        event_ids = [CREATE_EVENT_TYPE_ID, ANOMALY_EVENT_TYPE_ID]
    sub = eventsPerobj_df.loc[
        eventsPerobj_df["event_type_id"].isin(event_ids)
        & eventsPerobj_df["object_type"].eq(object_type)
    ].copy()
    ts = pd.to_datetime(sub["event_timestamp"])
    sub["week_start"] = (ts - pd.to_timedelta(ts.dt.weekday, unit="D")).dt.normalize()
    weekly = (
        sub.groupby(["week_start", "event_type_id"])
        .size()
        .unstack("event_type_id", fill_value=0)
    )
    return weekly
