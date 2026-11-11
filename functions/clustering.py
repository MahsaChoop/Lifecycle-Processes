"""Partition a flat event log with pm4py trace clustering."""
from __future__ import annotations

import pandas as pd
import pm4py
from sklearn.cluster import KMeans


def cluster_flat_log(flat_df: pd.DataFrame, n_clusters: int = 5, random_state: int = 42) -> dict:
    """Cluster traces with pm4py.cluster_log and return named dataframes.

    pm4py 2.7.23 yields EventLog objects (the dataframe conversion in that
    version is commented out). Names follow the yielded order, which is the
    KMeans label: cluster_01 is label 0. An empty cluster is skipped without
    renumbering the later names.
    """
    clusterer = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        init="random",
        n_init=1,
        max_iter=1,
    )
    cluster_logs = {}
    for i, clust in enumerate(pm4py.cluster_log(flat_df, sklearn_clusterer=clusterer)):
        name = f"cluster_{i + 1:02d}"
        if len(clust) == 0:
            print(f"{name}: empty, skipped")
            continue
        df = pm4py.convert_to_dataframe(clust)
        if df is None or df.empty:
            print(f"{name}: empty, skipped")
            continue
        cluster_logs[name] = df
        n_cases = df["case:concept:name"].nunique()
        print(f"{name}: {n_cases} cases | {len(df)} events")
    return cluster_logs
