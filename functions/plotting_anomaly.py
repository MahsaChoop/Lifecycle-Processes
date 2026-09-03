"""Anomaly and commit-context figures (paths via the dataset config)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from functions.commits import CATEGORIES
from functions.config import save_figure

FIGURE_FONT = {
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 10,
    "figure.titlesize": 15,
}


def _open_closed_weekly_series(weekly, cfg, created_col=None, closed_col=None):
    created_col = cfg.create_event_type_id if created_col is None else created_col
    closed_col = cfg.closed_event_type_id if closed_col is None else closed_col
    created_counts = weekly[created_col] if created_col in weekly.columns else pd.Series(dtype=int)
    closed_counts = weekly[closed_col] if closed_col in weekly.columns else pd.Series(dtype=int)
    return created_counts, closed_counts


def weekly_open_closed_summary_table(weekly, cfg, created_col=None, closed_col=None, tables_dir=None):
    """Table 1: summary statistics for weekly created (open) vs closed issue counts."""
    tables_dir = Path(tables_dir or cfg.tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    if weekly.empty:
        summary_table = pd.DataFrame()
    else:
        created_counts, closed_counts = _open_closed_weekly_series(weekly, cfg, created_col, closed_col)
        summary_table = pd.DataFrame({
            "Open issues (weekly created)": created_counts,
            "Closed issues (weekly closed)": closed_counts,
        }).describe().round(2)
    out_path = tables_dir / "weekly_open_closed_summary.csv"
    summary_table.to_csv(out_path)
    print(f"Saved {out_path}")
    return summary_table


def plot_weekly_open_vs_closed_histogram(
    weekly, cfg, created_col=None, closed_col=None, figures_dir=None, show=True,
):
    """Histogram: distribution of weekly created (open) vs closed issue counts."""
    figures_dir = Path(figures_dir or cfg.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    no_titles_dir = cfg.figures_no_titles_dir
    with plt.rc_context(FIGURE_FONT):
        fig, ax = plt.subplots(figsize=(10, 4.5))
        if weekly.empty:
            ax.text(
                0.5, 0.5, "No weekly data available",
                ha="center", va="center", transform=ax.transAxes,
            )
        else:
            created_counts, closed_counts = _open_closed_weekly_series(weekly, cfg, created_col, closed_col)
            ax.hist(
                created_counts, bins=20, alpha=0.6,
                label="Open issues (created per week)", edgecolor="black",
            )
            ax.hist(
                closed_counts, bins=20, alpha=0.6,
                label="Closed issues (closed per week)", edgecolor="black",
            )
            ax.legend()
        ax.set_xlabel("Count per week")
        ax.set_ylabel("Number of weeks")
        ax.set_title("Distribution of weekly open vs closed issues")
        plt.tight_layout()
        save_figure(
            fig, figures_dir, "weekly_open_vs_closed_issue_distribution",
            no_titles_dir=no_titles_dir,
        )
        if show:
            plt.show()
    return fig


def plot_weekly_event_counts(weekly, cfg, figures_dir=None, event_ids=None, show=True):
    figures_dir = Path(figures_dir or cfg.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    no_titles_dir = cfg.figures_no_titles_dir
    if event_ids is None:
        event_ids = [cfg.create_event_type_id, cfg.closed_event_type_id]
    event_labels = {
        cfg.create_event_type_id: f"{cfg.create_event_type_id}: created issue",
        cfg.closed_event_type_id: f"{cfg.closed_event_type_id}: closed issue",
    }
    with plt.rc_context(FIGURE_FONT):
        fig, ax = plt.subplots(figsize=(11, 4.5))
        if weekly.empty:
            ax.text(
                0.5, 0.5, "No rows for these event id values",
                ha="center", va="center", transform=ax.transAxes,
            )
        else:
            weeks = pd.date_range(weekly.index.min(), weekly.index.max(), freq="7D")
            for eid in event_ids:
                s = weekly[eid] if eid in weekly.columns else pd.Series(dtype=int)
                y = s.reindex(weeks, fill_value=0)
                ax.plot(weeks, y.values, marker="o", markersize=3, label=event_labels.get(eid, str(eid)))
            ax.legend(title="Event type", ncol=2, fontsize=10)
        ax.set_xlabel("Week start (Monday)")
        ax.set_ylabel("Event count")
        ax.set_title("Weekly counts per event id")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        plt.tight_layout()
        save_figure(fig, figures_dir, "weekly_event_counts", no_titles_dir=no_titles_dir)
        if show:
            plt.show()
    return fig


def plot_anomaly_figures(rolling_iqr_anomalies, cfg, figures_dir=None, show=True):
    figures_dir = Path(figures_dir or cfg.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR = figures_dir
    NO_TITLES_DIR = cfg.figures_no_titles_dir

    plot_frame = rolling_iqr_anomalies.copy().sort_values("week_start")
    flagged = plot_frame.loc[plot_frame["is_anomaly"]]
    score_max = plot_frame["anomaly_score"].max()
    if pd.isna(score_max) or score_max <= 0:
        plot_frame["anomaly_score_scaled"] = 0.0
    else:
        plot_frame["anomaly_score_scaled"] = (plot_frame["anomaly_score"] / score_max).clip(0, 1)

    with plt.rc_context(FIGURE_FONT):
        fig, ax = plt.subplots(figsize=(12, 4.5))
        ax.plot(
            plot_frame["week_start"],
            plot_frame["value"],
            marker="o",
            markersize=3,
            color="#1F3A5F", 
            label="weekly rate of issue_closed",
        )
        ax.plot(plot_frame["week_start"], plot_frame["upper_bound"], linestyle="--", label="IQR upper band")
        #ax.plot(plot_frame["week_start"], plot_frame["lower_bound"], linestyle="--", label="IQR lower band")
        if not flagged.empty:
            ax.scatter(
    
                flagged["week_start"],
                flagged["value"],
                color="red",
                s=55,
                zorder=3,
                label="anomalies",
            )
        ax.set_title("Finding anomalies with Rolling IQR method with k=1.5 for issue_closed rate")
        ax.set_xlabel("Week start")
        ax.set_ylabel("issue_closed rate (weekly)")
        ax.grid(alpha=0.25)
        ax.legend(frameon=False)
        fig.autofmt_xdate()
        plt.tight_layout()
        save_figure(fig, FIGURES_DIR, "rolling_iqr_anomalies", no_titles_dir=NO_TITLES_DIR)
        if show:
            plt.show()

        plot_frame["rolling_trend"] = plot_frame["value"].rolling(window=8, min_periods=2).mean()
        fig, axes = plt.subplots(
            2,
            1,
            figsize=(14, 7),
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1.25], "hspace": 0.05},
        )
        axes[0].bar(
            plot_frame["week_start"],
            plot_frame["value"],
            width=5,
            color="#1F3A5F",
            alpha=0.75,
            label="Tickets per week",
        )
        axes[0].plot(
            plot_frame["week_start"],
            plot_frame["rolling_trend"],
            color="#2E86AB",
            linestyle="--",
            linewidth=1.4,
            label="Rolling trend",
        )
        if not flagged.empty:
            axes[0].scatter(
                flagged["week_start"],
                flagged["value"],
                color="red",
                edgecolor="white",
                linewidth=0.8,
                s=95,
                zorder=4,
                label="anomalies",
            )
        axes[0].set_title("Weekly issue_closed rate with rolling-IQR anomalies")
        axes[0].set_ylabel("Tickets per week")
        axes[0].grid(axis="y", alpha=0.2)
        axes[0].legend(frameon=False)

        axes[1].fill_between(
            plot_frame["week_start"],
            plot_frame["anomaly_score_scaled"],
            step="mid",
            color="#F3A6A6",
            alpha=0.35,
        )
        axes[1].plot(
            plot_frame["week_start"],
            plot_frame["anomaly_score_scaled"],
            color="#D95F5F",
            linewidth=1.2,
            drawstyle="steps-mid",
        )
        axes[1].set_ylim(0, 1.05)
        axes[1].set_ylabel("Anomaly score")
        axes[1].set_xlabel("Week")
        axes[1].grid(axis="y", alpha=0.2)

        fig.autofmt_xdate()
        plt.tight_layout()
        save_figure(
            fig, FIGURES_DIR, "ticket_volume_anomaly_detection",
            no_titles_dir=NO_TITLES_DIR,
        )
        if show:
            plt.show()
    return FIGURES_DIR


def plot_commit_category_stack(commit_context, commit_typeclass_per_week, cfg, figures_dir=None, show=True):
    figures_dir = Path(figures_dir or cfg.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR = figures_dir
    NO_TITLES_DIR = cfg.figures_no_titles_dir
    CATEGORY_COLORS = {
        "feature_work": "#8FA6BF",
        "bug_fixes":    "#EF8A62",
        "tech_debt":    "#1F3A5F",
        "docs":         "#8C9B6E",
        "other":        "#D9D9D9",
    }

    cat_count_cols = [f"cat_{c}_count" for c in CATEGORIES]

    ctx = (
        commit_context[["week_start", "anomaly_direction", "commit_event_count"]]
        .merge(
            commit_typeclass_per_week[["week_start", *cat_count_cols]],
            on="week_start",
            how="left",
        )
        .sort_values("week_start")
        .reset_index(drop=True)
    )
    ctx["week_label"] = pd.to_datetime(ctx["week_start"]).dt.strftime("%Y-%m-%d")
    stack = ctx[cat_count_cols].fillna(0).sum(axis=1)
    commit_n = ctx["commit_event_count"].fillna(0).astype(float)
    scale = commit_n.div(stack.replace(0, np.nan)).fillna(0)
    for c in CATEGORIES:
        ctx[f"cat_{c}_plot"] = ctx[f"cat_{c}_count"].fillna(0) * scale
    no_mix = (stack <= 0) & (commit_n > 0)
    if no_mix.any():
        ctx.loc[no_mix, "cat_other_plot"] = commit_n.loc[no_mix]

    with plt.rc_context(FIGURE_FONT):
        fig, ax = plt.subplots(figsize=(12, 4.8))

        bottom = np.zeros(len(ctx))
        for c in CATEGORIES:
            ax.bar(
                ctx["week_label"], ctx[f"cat_{c}_plot"],
                bottom=bottom, color=CATEGORY_COLORS[c], label=c,
                edgecolor="white", linewidth=0.3,
            )
            bottom += ctx[f"cat_{c}_plot"].values

        ymax = float(np.nanmax(bottom)) if len(bottom) else 1.0
        for i, (x, total) in enumerate(zip(ctx["week_label"], ctx["commit_event_count"])):
            ax.text(
                x, bottom[i] + ymax * 0.01,
                str(int(total)), ha="center", va="bottom",
                fontsize=10, color="#333333",
            )

        ax.set_ylim(0, ymax * 1.12 if ymax > 0 else 1)
        ax.set_ylabel("Count of Commits")
        ax.set_title("Interventions context: commit categories on issues closed in each anomaly week")
        ax.tick_params(axis="x", rotation=45)
        for lbl in ax.get_xticklabels():
            lbl.set_ha("right")
        ax.legend(frameon=False)
        ax.grid(axis="y", alpha=0.2)

        plt.tight_layout()
        save_figure(
            fig, FIGURES_DIR, "commit_context_category_stack",
            no_titles_dir=NO_TITLES_DIR,
        )
        plt.show()
    return FIGURES_DIR
