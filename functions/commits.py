"""Commit-message context and Conventional Commit classification."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd

from functions.anomaly import _week_start

CONVENTIONAL_TYPES = [
    "feat", "fix", "chore", "docs", "style", "refactor",
    "test", "build", "ci", "perf", "revert", "bump", "wip",
]
CATEGORY_MAP = {
    "feat": "feature_work",
    "fix": "bug_fixes",
    "refactor": "tech_debt",
    "chore": "tech_debt",
    "style": "tech_debt",
    "build": "tech_debt",
    "ci": "tech_debt",
    "perf": "tech_debt",
    "revert": "tech_debt",
    "bump": "tech_debt",
    "test": "tech_debt",
    "wip": "tech_debt",
    "docs": "docs",
}
CATEGORIES = ["feature_work", "bug_fixes", "tech_debt", "docs", "other"]
CATEGORY_TIE_BREAK = ["feature_work", "bug_fixes", "tech_debt", "docs"]

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>feat|fix|chore|docs|style|refactor|test|build|ci|perf|revert|bump|wip)"
    r"(\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<body>.+)$",
    re.IGNORECASE,
)


def build_weekly_commit_messages(eventsPerobj_df, objects_attributes, cfg, event_type_id=None):
    event_type_id = cfg.commit_event_type_id if event_type_id is None else event_type_id
    commit_events_objects = eventsPerobj_df.loc[
        eventsPerobj_df["event_type_id"].eq(event_type_id) & eventsPerobj_df["object_type"].eq(cfg.commit_object_type)
    ].copy()
    commit_events_objects["week_start"] = _week_start(commit_events_objects["event_timestamp"])
    commit_events_objects["object_id_key"] = pd.to_numeric(
        commit_events_objects["object_id"], errors="coerce"
    ).astype("Int64")

    message_attributes = objects_attributes.loc[
        objects_attributes["object_attribute_id"].eq(cfg.commit_message_attribute_id)
    ].copy()
    message_attributes["object_id_key"] = pd.to_numeric(
        message_attributes["object_id"], errors="coerce"
    ).astype("Int64")
    msg_cols = ["object_id_key", "object_id", "object_attribute_id", "attribute_value"]
    if "timestamp" in message_attributes.columns:
        msg_cols.append("timestamp")

    joined = commit_events_objects.merge(
        message_attributes[msg_cols],
        on="object_id_key",
        how="left",
        suffixes=("_event_object", "_attribute"),
    )

    fallback_text = joined.get("object_description", pd.Series("", index=joined.index))
    joined["message_text"] = joined["attribute_value"].fillna(fallback_text)

    weekly_messages = (
        joined.groupby("week_start")
        .agg(
            commit_event_count=("event_id", "nunique"),
            message_count=("attribute_value", lambda s: s.dropna().nunique()),
            messages_in_week=("message_text", _unique_nonempty),
            commit_event_descriptions=("event_description", _unique_nonempty),
            commit_event_ids=("event_id", lambda s: sorted(pd.Series(s).dropna().unique().tolist())),
            commit_object_ids=("object_id_key", lambda s: sorted(pd.Series(s).dropna().unique().tolist())),
        )
        .reset_index()
    )
    weekly_messages["messages_text"] = weekly_messages["messages_in_week"].apply(lambda msgs: "\n".join(msgs))
    return weekly_messages, joined


def _unique_nonempty(values):
    seen = []
    for value in values.dropna().astype(str):
        value = value.strip()
        if value and value not in seen:
            seen.append(value)
    return seen


def classify_and_link_commits_to_issues(eventsPerobj_df, objects_attributes, cfg):
    """Classify commit messages and link each commit to issues that share the same event_id."""
    _, joined = build_weekly_commit_messages(
        eventsPerobj_df,
        objects_attributes,
        cfg,
        event_type_id=cfg.commit_event_type_id,
    )
    parsed = joined["message_text"].map(_classify_message)
    classified = joined.copy()
    classified["cm_type"] = parsed.map(lambda value: value[0])
    classified["cm_scope"] = parsed.map(lambda value: value[1])
    classified["cm_breaking"] = parsed.map(lambda value: value[2])
    classified["category"] = classified["cm_type"].map(
        lambda cm_type: None if cm_type is None else CATEGORY_MAP.get(cm_type, "other")
    )

    commit_classified_all = classified.loc[classified["object_id_key"].notna()].copy()
    commit_classified_all["commit_object_id"] = commit_classified_all["object_id_key"]
    commit_classified_all = (
        commit_classified_all[
            [
                "commit_object_id",
                "event_id",
                "message_text",
                "cm_type",
                "cm_scope",
                "cm_breaking",
                "category",
            ]
        ]
        .drop_duplicates(subset=["commit_object_id"])
        .reset_index(drop=True)
    )

    issue_links = eventsPerobj_df.loc[
        eventsPerobj_df["object_type"].eq(cfg.issue_object_type),
        ["event_id", "object_id"],
    ].rename(columns={"object_id": "issue_id"})
    commit_issue = classified.merge(issue_links, on="event_id", how="inner")
    per_commit_issue = (
        commit_issue.dropna(subset=["issue_id", "object_id_key", "category"])
        .drop_duplicates(subset=["issue_id", "object_id_key"])
    )
    per_commit_issue["issue_id"] = per_commit_issue["issue_id"].astype(str)
    return commit_classified_all, per_commit_issue, classified


def overlapping_issue_categories(per_commit_issue, case_ids):
    """Map issues to overlapping commit categories; leftover cases go to other."""
    case_ids = set(str(x) for x in case_ids)
    issue_commit_categories = (
        per_commit_issue.loc[per_commit_issue["issue_id"].isin(case_ids)]
        .groupby(["issue_id", "category"], as_index=False)
        .agg(commit_count=("object_id_key", "nunique"))
    )
    n_with_classified = int(issue_commit_categories["issue_id"].nunique())
    missing_ids = sorted(case_ids - set(issue_commit_categories["issue_id"]))
    if missing_ids:
        issue_commit_categories = pd.concat(
            [
                issue_commit_categories,
                pd.DataFrame(
                    {
                        "issue_id": missing_ids,
                        "category": "other",
                        "commit_count": 0,
                    }
                ),
            ],
            ignore_index=True,
        )
    return issue_commit_categories, n_with_classified, missing_ids


def subset_log_by_overlapping_categories(flat_df, issue_commit_categories, categories=None):
    """Subset a flat issue log: each case goes into every category log it belongs to."""
    categories = CATEGORIES if categories is None else categories
    logs = {}
    for category in categories:
        ids = issue_commit_categories.loc[
            issue_commit_categories["category"].eq(category),
            "issue_id",
        ]
        log_df = flat_df[
            flat_df["case:concept:name"].astype(str).isin(set(ids.astype(str)))
        ].copy()
        if log_df.empty:
            print(f"  {category}: empty — skipped")
            continue
        logs[category] = log_df
        print(
            f"  {category}: {log_df['case:concept:name'].nunique()} cases | "
            f"{len(log_df)} events"
        )
    return logs


def build_commit_context(
    rolling_iqr_anomalies,
    eventsPerobj_df,
    objects_attributes,
    cfg,
    anomaly_object_ids,
    tables_dir=None,
):
    """Weekly commit context for issues that closed in anomaly weeks, linked via event_id."""
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)

    commit_classified_all, per_commit_issue, classified = classify_and_link_commits_to_issues(
        eventsPerobj_df, objects_attributes, cfg
    )

    anomaly_ids = anomaly_object_ids.copy()
    anomaly_ids["issue_id"] = anomaly_ids["object_id"].astype(str)
    anomaly_ids["week_start"] = _week_start(anomaly_ids["week_start"])
    case_ids = set(anomaly_ids["issue_id"])

    linked = per_commit_issue.drop(columns=["week_start"], errors="ignore").merge(
        anomaly_ids[["issue_id", "week_start"]],
        on="issue_id",
        how="inner",
    )
    linked = linked.drop_duplicates(subset=["week_start", "object_id_key"])
    if "event_description" not in linked.columns:
        linked["event_description"] = ""

    if linked.empty:
        weekly_commit_messages = pd.DataFrame(
            columns=[
                "week_start",
                "commit_event_count",
                "message_count",
                "messages_in_week",
                "commit_event_descriptions",
                "commit_event_ids",
                "commit_object_ids",
                "messages_text",
            ]
        )
    else:
        weekly_commit_messages = (
            linked.groupby("week_start")
            .agg(
                commit_event_count=("event_id", "nunique"),
                message_count=("message_text", lambda s: s.dropna().nunique()),
                messages_in_week=("message_text", _unique_nonempty),
                commit_event_descriptions=("event_description", _unique_nonempty),
                commit_event_ids=("event_id", lambda s: sorted(pd.Series(s).dropna().unique().tolist())),
                commit_object_ids=("object_id_key", lambda s: sorted(pd.Series(s).dropna().unique().tolist())),
            )
            .reset_index()
        )
        weekly_commit_messages["messages_text"] = weekly_commit_messages["messages_in_week"].apply(
            lambda msgs: "\n".join(msgs)
        )

    anomaly_weeks = rolling_iqr_anomalies.loc[rolling_iqr_anomalies["is_anomaly"]].copy()
    anomaly_weeks["week_start"] = _week_start(anomaly_weeks["week_start"])
    if not weekly_commit_messages.empty:
        weekly_commit_messages["week_start"] = _week_start(weekly_commit_messages["week_start"])
    commit_context = anomaly_weeks.merge(weekly_commit_messages, on="week_start", how="left")
    commit_context["commit_event_count"] = commit_context["commit_event_count"].fillna(0).astype(int)
    commit_context["message_count"] = commit_context["message_count"].fillna(0).astype(int)
    commit_context["messages_in_week"] = commit_context["messages_in_week"].apply(
        lambda value: value if isinstance(value, list) else []
    )
    commit_context["commit_event_descriptions"] = commit_context["commit_event_descriptions"].apply(
        lambda value: value if isinstance(value, list) else []
    )
    commit_context["messages_text"] = commit_context["messages_text"].fillna("")

    commit_context.to_csv(tables_dir / "commit_context.csv", index=False)
    n_rows, n_cols = commit_context.shape
    print(f"commit_context summary: {n_rows} rows x {n_cols} columns")
    print(f"Saved commit_context to {tables_dir / 'commit_context.csv'}")

    anomaly_issue_commit_categories, n_with_classified, missing_ids = overlapping_issue_categories(
        per_commit_issue, case_ids
    )
    anomaly_cats_path = tables_dir / "anomaly_issue_commit_categories.csv"
    anomaly_issue_commit_categories.to_csv(anomaly_cats_path, index=False)
    n_multi = int(
        (anomaly_issue_commit_categories.groupby("issue_id")["category"].nunique() > 1).sum()
    )
    print("\n=== Anomaly issue commit categories (overlapping, event_id link) ===")
    print(f"Anomaly issues: {len(case_ids)}")
    print(f"Issues with classified commits: {n_with_classified}")
    print(f"Issues with no classified commit (assigned to other): {len(missing_ids)}")
    print(f"Issues in more than one category: {n_multi}")
    issue_counts = anomaly_issue_commit_categories.groupby("category")["issue_id"].nunique()
    for category in CATEGORIES:
        print(f"  {category:<13s} {int(issue_counts.get(category, 0))}")
    print(f"Saved {anomaly_cats_path}")

    return commit_context, classified, anomaly_issue_commit_categories


def _classify_message(message):
    if not isinstance(message, str):
        return None, None, False
    first_line = message.strip().splitlines()[0] if message.strip() else ""
    match = CONVENTIONAL_RE.match(first_line)
    if not match:
        return "other", None, False
    cm_type = match.group("type").lower()
    scope = match.group("scope")
    breaking = match.group("breaking") == "!"
    return cm_type, scope, breaking


def _classify_week(messages):
    if not isinstance(messages, list):
        messages = []
    type_counter = Counter()
    scope_counter = Counter()
    breaking_count = 0
    for msg in messages:
        cm_type, scope, breaking = _classify_message(msg)
        if cm_type is None:
            continue
        type_counter[cm_type] += 1
        if scope:
            scope_counter[scope.lower()] += 1
        if breaking:
            breaking_count += 1

    cm_total = sum(type_counter.values())

    type_counts = {f"cm_{t}_count": int(type_counter.get(t, 0)) for t in CONVENTIONAL_TYPES}
    type_counts["cm_other_count"] = int(type_counter.get("other", 0))

    cat_counts = {f"cat_{c}_count": 0 for c in CATEGORIES}
    for t, n in type_counter.items():
        cat = CATEGORY_MAP.get(t, "other")
        cat_counts[f"cat_{cat}_count"] += int(n)

    cat_ratios = {}
    for c in CATEGORIES:
        cnt = cat_counts[f"cat_{c}_count"]
        cat_ratios[f"cat_{c}_ratio"] = (cnt / cm_total) if cm_total else 0.0

    if cm_total == 0:
        dominant_category = None
        dominant_type = None
    else:
        best_cat, best_n = None, -1
        for c in CATEGORY_TIE_BREAK:
            n = cat_counts[f"cat_{c}_count"]
            if n > best_n:
                best_cat, best_n = c, n
        if cat_counts["cat_other_count"] > best_n:
            best_cat = "other"
        dominant_category = best_cat
        dominant_type = type_counter.most_common(1)[0][0] if type_counter else None

    top_scopes = [scope for scope, _ in scope_counter.most_common(3)]

    return {
        "cm_total": int(cm_total),
        "cm_breaking_count": int(breaking_count),
        **type_counts,
        **cat_counts,
        **cat_ratios,
        "dominant_category": dominant_category,
        "dominant_type": dominant_type,
        "top_scopes": top_scopes,
    }


def build_commit_typeclass(commit_context, cfg, tables_dir=None):
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)

    _typeclass_rows = commit_context.apply(
        lambda row: pd.Series(_classify_week(row.get("messages_in_week", []))),
        axis=1,
    )
    commit_typeclass_per_week = pd.concat(
        [
            commit_context[["week_start", "anomaly_direction", "anomaly_score", "commit_event_count"]].reset_index(drop=True),
            _typeclass_rows.reset_index(drop=True),
        ],
        axis=1,
    ).sort_values("week_start").reset_index(drop=True)

    commit_typeclass_per_week.to_csv(tables_dir / "commit_typeclass_per_week.csv", index=False)

    ratio_cols = [f"cat_{c}_ratio" for c in CATEGORIES]
    overall_means = commit_typeclass_per_week[ratio_cols].mean()

    n_rows, n_cols = commit_typeclass_per_week.shape
    print(f"commit_typeclass_per_week summary: {n_rows} rows x {n_cols} columns")
    print("\nMean category ratios across all anomaly weeks:")
    for c in CATEGORIES:
        print(f"  {c:<13s} {overall_means[f'cat_{c}_ratio']:.3f}")

    if "anomaly_direction" in commit_typeclass_per_week.columns and not commit_typeclass_per_week.empty:
        by_dir = commit_typeclass_per_week.groupby("anomaly_direction")[ratio_cols].mean()
        print("\nMean category ratios by anomaly_direction:")
        for direction, row in by_dir.iterrows():
            parts = "  ".join(f"{c}={row[f'cat_{c}_ratio']:.3f}" for c in CATEGORIES)
            print(f"  [{direction}] {parts}")

    print(f"\nSaved commit_typeclass_per_week to {tables_dir / 'commit_typeclass_per_week.csv'}")
    return commit_typeclass_per_week


def build_whole_commit_category_logs(
    flat_df_clean,
    eventsPerobj_df,
    objects_attributes,
    cfg,
    tables_dir=None,
):
    """Classify all commit messages and subset the preprocessed whole log by overlapping commit categories."""
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)

    commit_classified_all, per_commit_issue, _ = classify_and_link_commits_to_issues(
        eventsPerobj_df, objects_attributes, cfg
    )
    commit_classified_path = tables_dir / "commit_classified_all.csv"
    commit_classified_all.to_csv(commit_classified_path, index=False)

    clean_cases = set(flat_df_clean["case:concept:name"].astype(str))
    issue_commit_categories, n_with_classified, missing_ids = overlapping_issue_categories(
        per_commit_issue, clean_cases
    )
    issue_cats_path = tables_dir / "issue_commit_categories.csv"
    issue_commit_categories.to_csv(issue_cats_path, index=False)

    n_clean_cases = flat_df_clean["case:concept:name"].nunique()
    print("=== Commit message classification (preprocessed whole log) ===")
    print(f"Preprocessed whole-log cases: {n_clean_cases}")
    print(f"Classified unique commits: {len(commit_classified_all)}")
    category_counts = commit_classified_all["category"].value_counts(dropna=False)
    for category in CATEGORIES:
        print(f"  {category:<13s} {int(category_counts.get(category, 0))}")
    print(f"Saved {commit_classified_path}")

    n_issues_in_table = issue_commit_categories["issue_id"].nunique()
    n_multi = int(
        (issue_commit_categories.groupby("issue_id")["category"].nunique() > 1).sum()
    )
    print("\n=== Issue commit categories (overlapping, preprocessed whole log) ===")
    print(f"Whole-log cases: {n_clean_cases}")
    print(f"Issues with classified commits: {n_with_classified}")
    print(
        f"Issues with no classified commit (assigned to other): {len(missing_ids)}"
    )
    print(f"Issues in issue_commit_categories: {n_issues_in_table}")
    print(f"Issues in more than one category log: {n_multi}")
    issue_counts = issue_commit_categories.groupby("category")["issue_id"].nunique()
    for category in CATEGORIES:
        print(f"  {category:<13s} {int(issue_counts.get(category, 0))}")
    print(f"Saved {issue_cats_path}")

    print("\n=== Preprocessed-log commit-category subsets (overlapping) ===")
    logs = subset_log_by_overlapping_categories(flat_df_clean, issue_commit_categories)
    return logs, issue_commit_categories, commit_classified_all
