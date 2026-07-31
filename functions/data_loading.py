"""Load DuckDB tables and build weekly issue counts """
from __future__ import annotations

import duckdb
import pandas as pd


def load_events_df(cfg):
    with duckdb.connect(str(cfg.duckdb_path), read_only=True) as con:
        events_df = con.sql("SELECT * FROM main.events").df()
    return events_df


def load_objects_attributes(cfg):
    with duckdb.connect(str(cfg.duckdb_path), read_only=True) as con:
        objects_attributes = con.sql("SELECT * FROM main.object_attribute_values").df()
    return objects_attributes


def load_events_per_obj(cfg):
    with duckdb.connect(str(cfg.duckdb_path), read_only=True) as con:
        eventsPerobj_df = con.sql("SELECT * FROM graph_data_prep.graph_base_table").df()
    return eventsPerobj_df


def build_weekly_issue_counts(eventsPerobj_df, cfg, event_ids=None, object_type=None):
    if event_ids is None:
        event_ids = [cfg.create_event_type_id, cfg.closed_event_type_id]
    if object_type is None:
        object_type = cfg.issue_object_type
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
