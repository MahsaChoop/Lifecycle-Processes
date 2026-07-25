"""Anomaly and commit-context figures (logic unchanged; paths via RESULTS_FIGURES)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from functions.commits import CATEGORIES
from functions.config import RESULTS_FIGURES


def plot_weekly_event_counts(weekly, figures_dir=None, event_ids=None, show=True):
    figures_dir = Path(figures_dir or RESULTS_FIGURES)
    figures_dir.mkdir(parents=True, exist_ok=True)
    if event_ids is None:
        event_ids = [31, 105]
    event_labels = {
        31: "31: created issue",
        105: "105: closed issue",
    }
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
        ax.legend(title="Event type", ncol=2, fontsize=8)
    ax.set_xlabel("Week start (Monday)")
    ax.set_ylabel("Event count")
    ax.set_title("Weekly counts per event id")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(figures_dir / "weekly_event_counts.png", dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    return fig


def plot_anomaly_figures(weekly_105_anomaly_frame, anomaly_states, figures_dir=None, show=True):
    figures_dir = Path(figures_dir or RESULTS_FIGURES)
    figures_dir.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR = figures_dir

    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(
        weekly_105_anomaly_frame["week_start"],
        weekly_105_anomaly_frame["value"],
        marker="o",
        markersize=3,
        label="weekly rate of issue_closed",
    )
    ax.plot(weekly_105_anomaly_frame["week_start"], weekly_105_anomaly_frame["upper_bound"], linestyle="--", label="IQR upper")
    ax.plot(weekly_105_anomaly_frame["week_start"], weekly_105_anomaly_frame["lower_bound"], linestyle="--", label="IQR lower")
    if not anomaly_states.empty:
        ax.scatter(
            anomaly_states["week_start"],
            anomaly_states["value"],
            color="red",
            s=55,
            zorder=3,
            label="anomaly states",
        )
    ax.set_title("Rolling IQR anomalies with k=1.5")
    ax.set_xlabel("Week start")
    ax.set_ylabel("Closed issues/week")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "rolling_iqr_anomalies.png", dpi=150, bbox_inches="tight")
    plt.show()

    severity_order = ["P0", "P1", "P2", "P3", "P4"]
    severity_to_level = {severity: idx for idx, severity in enumerate(severity_order)}
    severity_colors = {
        "P0": "#8B0000",
        "P1": "#D62728",
        "P2": "#FF7F0E",
        "P3": "#1F77B4",
        "P4": "#2CA02C",
    }

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), gridspec_kw={"width_ratios": [2, 1]})
    if anomaly_states.empty:
        axes[0].text(0.5, 0.5, "No anomaly severity states", ha="center", va="center", transform=axes[0].transAxes)
        axes[1].text(0.5, 0.5, "No severity counts", ha="center", va="center", transform=axes[1].transAxes)
    else:
        severity_plot = anomaly_states.copy()
        severity_plot["severity_level"] = severity_plot["severity"].map(severity_to_level)
        axes[0].scatter(
            severity_plot["week_start"],
            severity_plot["severity_level"],
            s=90,
            c=severity_plot["severity"].map(severity_colors),
            edgecolor="black",
            linewidth=0.5,
        )
        axes[0].set_yticks(range(len(severity_order)))
        axes[0].set_yticklabels(severity_order)
        axes[0].invert_yaxis()
        axes[0].set_xlabel("Week start")
        axes[0].set_ylabel("Severity")
        axes[0].set_title("Anomaly severity over time")
        axes[0].grid(alpha=0.25)

        severity_counts = severity_plot["severity"].value_counts().reindex(severity_order, fill_value=0)
        axes[1].bar(
            severity_counts.index,
            severity_counts.values,
            color=[severity_colors[severity] for severity in severity_counts.index],
            edgecolor="black",
            linewidth=0.5,
        )
        axes[1].set_xlabel("Severity")
        axes[1].set_ylabel("Anomaly weeks")
        axes[1].set_title("Severity distribution")
        axes[1].grid(axis="y", alpha=0.25)

    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "anomaly_severity_overview.png", dpi=150, bbox_inches="tight")
    plt.show()

    severity_legend_labels = {
        "P0": "P0: complete outage",
        "P1": "P1: major impact",
        "P2": "P2: degraded",
        "P3": "P3: minor",
        "P4": "P4: cosmetic",
    }
    plot_frame = weekly_105_anomaly_frame.copy().sort_values("week_start")
    plot_frame["rolling_trend"] = plot_frame["value"].rolling(window=8, min_periods=2).mean()
    score_max = plot_frame["anomaly_score"].max()
    if pd.isna(score_max) or score_max <= 0:
        plot_frame["anomaly_score_scaled"] = 0.0
    else:
        plot_frame["anomaly_score_scaled"] = (plot_frame["anomaly_score"] / score_max).clip(0, 1)

    score_threshold = 0.45
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
        color="#9CC9F2",
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

    for severity in severity_order:
        subset = anomaly_states.loc[anomaly_states["severity"].eq(severity)].copy()
        if subset.empty:
            continue
        axes[0].scatter(
            subset["week_start"],
            subset["value"],
            color=severity_colors[severity],
            edgecolor="white",
            linewidth=0.8,
            s=95,
            zorder=4,
            label=severity_legend_labels[severity],
        )
        for _, row in subset.iterrows():
            label = f"{row['severity']}: {row['component']}"
            axes[0].annotate(
                label,
                xy=(row["week_start"], row["value"]),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color=severity_colors[severity],
                bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": severity_colors[severity], "alpha": 0.75},
            )

    axes[0].set_title("Engineering ticket volume - multimodal anomaly detection")
    axes[0].set_ylabel("Tickets per week")
    axes[0].grid(axis="y", alpha=0.2)
    axes[0].legend(loc="upper left", fontsize=8, frameon=True)

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
    axes[1].axhline(score_threshold, color="#777777", linestyle="--", linewidth=1, label=f"Threshold {score_threshold:.2f}")
    axes[1].set_ylim(0, 1.05)
    axes[1].set_ylabel("Anomaly score")
    axes[1].set_xlabel("Week")
    axes[1].grid(axis="y", alpha=0.2)
    axes[1].legend(loc="upper right", fontsize=8, frameon=True)

    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "ticket_volume_anomaly_detection.png", dpi=150, bbox_inches="tight")
    plt.show()


    with plt.rc_context({
        "font.family": "DejaVu Sans",
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
    }):
        fig, axes = plt.subplots(
            3,
            1,
            figsize=(14, 8.5),
            sharex=True,
            gridspec_kw={"height_ratios": [4, 1, 1.6], "hspace": 0.12},
        )

        metric_ax, severity_ax, score_ax = axes
        metric_ax.fill_between(
            plot_frame["week_start"],
            plot_frame["lower_bound"],
            plot_frame["upper_bound"],
            color="#B8D4E3",
            alpha=0.35,
            label="Rolling IQR band",
            linewidth=0,
        )
        metric_ax.plot(
            plot_frame["week_start"],
            plot_frame["value"],
            color="#1F3B5B",
            linewidth=1.6,
            label="Closed issues / week",
        )
        metric_ax.plot(
            plot_frame["week_start"],
            plot_frame["rolling_trend"],
            color="#5A7C9C",
            linestyle="--",
            linewidth=1.2,
            label="Rolling trend",
        )

        annotated_states = anomaly_states.dropna(subset=["week_start", "value"]).copy()
        annotated_states = annotated_states.sort_values("week_start")
        label_offsets = [(0, 16), (0, -22), (0, 28), (0, -34)]
        for plot_index, (_, row) in enumerate(annotated_states.iterrows()):
            severity = row["severity"]
            color = severity_colors.get(severity, "#444444")
            metric_ax.scatter(
                row["week_start"],
                row["value"],
                color=color,
                edgecolor="white",
                linewidth=0.9,
                s=85,
                zorder=4,
            )
            offset = label_offsets[plot_index % len(label_offsets)]
            metric_ax.annotate(
                f"{severity} | {row['component']}",
                xy=(row["week_start"], row["value"]),
                xytext=offset,
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color="#1F3B5B",
                arrowprops={"arrowstyle": "-", "color": color, "lw": 0.6},
                bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": color, "lw": 0.7, "alpha": 0.9},
            )

        metric_ax.set_title("Weekly closed issues with rolling-IQR anomalies and severity context")
        metric_ax.set_ylabel("Closed issues / week")
        metric_ax.grid(axis="y", alpha=0.2)
        handles, labels = metric_ax.get_legend_handles_labels()
        severity_handles = [
            plt.Line2D([0], [0], marker="o", linestyle="", color=severity_colors[s], markeredgecolor="white",
                       markersize=8, label=severity_legend_labels[s])
            for s in severity_order
            if s in set(annotated_states["severity"])
        ]
        metric_ax.legend(handles + severity_handles, labels + [h.get_label() for h in severity_handles],
                         loc="upper left", fontsize=8, ncol=2, frameon=True)

        severity_ax.set_yticks(range(len(severity_order)))
        severity_ax.set_yticklabels(severity_order)
        severity_ax.invert_yaxis()
        severity_ax.set_ylim(len(severity_order) - 0.5, -0.5)
        severity_ax.set_ylabel("Severity")
        severity_ax.grid(axis="x", alpha=0.15)
        if not annotated_states.empty:
            annotated_states["severity_level"] = annotated_states["severity"].map(severity_to_level)
            severity_ax.scatter(
                annotated_states["week_start"],
                annotated_states["severity_level"],
                c=annotated_states["severity"].map(severity_colors),
                edgecolor="white",
                linewidth=0.7,
                s=70,
            )

        score_ax.fill_between(
            plot_frame["week_start"],
            plot_frame["anomaly_score_scaled"],
            step="mid",
            color="#F3A6A6",
            alpha=0.4,
        )
        score_ax.plot(
            plot_frame["week_start"],
            plot_frame["anomaly_score_scaled"],
            color="#C0392B",
            linewidth=1.1,
            drawstyle="steps-mid",
        )
        score_ax.axhline(
            score_threshold,
            color="#666666",
            linestyle="--",
            linewidth=1,
            label=f"Alert threshold {score_threshold:.2f}",
        )
        score_ax.set_ylim(0, 1.05)
        score_ax.set_ylabel("Anomaly score")
        score_ax.set_xlabel("Week")
        score_ax.grid(axis="y", alpha=0.2)
        score_ax.legend(loc="upper right", fontsize=8, frameon=True)

        fig.suptitle("Anomaly summary: metric, severity timeline, and detector score", fontsize=14, y=0.995)
        fig.autofmt_xdate()
        plt.tight_layout(rect=[0, 0, 1, 0.985])
        fig.savefig(FIGURES_DIR / "anomaly_summary_dashboard.png", dpi=150, bbox_inches="tight")
        plt.show()
    return FIGURES_DIR


def plot_commit_category_stack(commit_context, commit_typeclass_per_week, figures_dir=None, show=True):
    figures_dir = Path(figures_dir or RESULTS_FIGURES)
    figures_dir.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR = figures_dir
    CATEGORY_COLORS = {
        "feature_work": "#2E5D8E",
        "bug_fixes":    "#C97B55",
        "tech_debt":    "#7B9EB8",
        "docs":         "#5B8C7A",
        "other":        "#A8A8A8",
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

    fig, ax = plt.subplots(figsize=(12, 4.8))

    bottom = np.zeros(len(ctx))
    for c in CATEGORIES:
        ax.bar(
            ctx["week_label"], ctx[f"cat_{c}_count"],
            bottom=bottom, color=CATEGORY_COLORS[c], label=c,
            edgecolor="white", linewidth=0.3,
        )
        bottom += ctx[f"cat_{c}_count"].values

    ymax = float(bottom.max()) if len(bottom) else 1.0
    for i, (x, total) in enumerate(zip(ctx["week_label"], ctx["commit_event_count"])):
        ax.text(
            x, bottom[i] + ymax * 0.01,
            str(int(total)), ha="center", va="bottom",
            fontsize=8, color="#333333",
        )

    dir_marker = {"high": "^", "low": "v"}
    for x, direction in zip(ctx["week_label"], ctx["anomaly_direction"]):
        m = dir_marker.get(str(direction))
        if m:
            ax.annotate(
                m, xy=(x, 0), xytext=(0, -28),
                textcoords="offset points", ha="center", va="top",
                fontsize=9, color="#555555", annotation_clip=False,
            )

    ax.set_ylim(0, ymax * 1.12 if ymax > 0 else 1)
    ax.set_ylabel("Commits")
    ax.set_title("Commit context: commits per anomaly week (stacked by category)")
    ax.tick_params(axis="x", rotation=45)
    for lbl in ax.get_xticklabels():
        lbl.set_ha("right")
    ax.legend(
        loc="upper center", bbox_to_anchor=(0.5, -0.28),
        ncol=len(CATEGORIES), frameon=False,
    )

    plt.tight_layout()
    fig.savefig(
        FIGURES_DIR / "commit_context_category_stack.png",
        dpi=150, bbox_inches="tight",
    )
    plt.show()
    return FIGURES_DIR
