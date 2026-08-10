"""Utility-experiment comparison figures (paths via the dataset config)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from functions.config import RESULTS_FIGURES, RESULTS_FIGURES_NO_TITLES, save_figure

LOG_ORDER = ["vitalizing", "random_case_control", "whole"]
LOG_COLORS = {
    "vitalizing": "#2ca02c",
    "random_case_control": "#1f77b4",
    "whole": "#ff7f0e",
}
LOG_LABELS = {
    "vitalizing": "Vitalizing",
    "random_case_control": "Random control",
    "whole": "Whole",
}
LOG_MARKERS = {"vitalizing": "o", "random_case_control": "s", "whole": "^"}


def _style_axes(ax, ylim01=False):
    ax.grid(True, axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    if ylim01:
        ax.set_ylim(0, 1)


def plot_grouped_bars(wide_df, title, ylabel, ax, ylim01=False):
    wide_df = wide_df.reindex(LOG_ORDER).dropna(how="all")
    configs = list(wide_df.columns)
    x = np.arange(len(configs))
    width = 0.25

    for i, log_name in enumerate(LOG_ORDER):
        if log_name not in wide_df.index:
            continue
        values = wide_df.loc[log_name, configs].astype(float).values
        offset = (i - (len(LOG_ORDER) - 1) / 2) * width
        ax.bar(
            x + offset,
            values,
            width,
            label=log_name,
            color=LOG_COLORS.get(log_name),
        )

    ax.set_xticks(x)
    ax.set_xticklabels(configs, rotation=45, ha="right")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend()
    _style_axes(ax, ylim01=ylim01)


def plot_utility_figures(consolidated_results_table_clean, cfg, figures_dir=None, show=True):
    figures_dir = Path(figures_dir or cfg.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR = figures_dir
    NO_TITLES_DIR = cfg.figures_no_titles_dir

    plot_df = consolidated_results_table_clean[
        consolidated_results_table_clean["status"] == "ok"
    ].copy()

    if plot_df.empty:
        raise ValueError("No successful rows in consolidated_results_table_clean to plot.")

    wide_f_score_clean = (
        plot_df.pivot(index="log_name", columns="discovery_method", values="f_score")
        .sort_index(axis=1)
    )
    wide_fitness_clean = (
        plot_df.pivot(index="log_name", columns="discovery_method", values="fitness")
        .sort_index(axis=1)
    )
    wide_precision_clean = (
        plot_df.pivot(index="log_name", columns="discovery_method", values="precision")
        .sort_index(axis=1)
    )
    wide_size_clean = (
        plot_df.pivot(index="log_name", columns="discovery_method", values="size")
        .sort_index(axis=1)
    )
    wide_cfc_clean = (
        plot_df.pivot(index="log_name", columns="discovery_method", values="cfc")
        .sort_index(axis=1)
    )
    wide_simplicity_clean = (
        plot_df.pivot(index="log_name", columns="discovery_method", values="simplicity")
        .sort_index(axis=1)
    )

    print(f"Plotting from {len(plot_df)} successful rows")
    print(f"Miner configs: {list(wide_f_score_clean.columns)}")
    print(f"Log groups: {list(wide_f_score_clean.index)}")

    fig, ax = plt.subplots(figsize=(14, 5))
    plot_grouped_bars(
        wide_f_score_clean,
        "Clean logs: F-score by miner config and log group",
        "F-score",
        ax,
        ylim01=True,
    )
    plt.tight_layout()
    save_figure(
        fig, FIGURES_DIR, "clean_log_f_score_grouped_bars",
        no_titles_dir=NO_TITLES_DIR,
    )
    print(f"Saved {FIGURES_DIR / 'clean_log_f_score_grouped_bars'}.{{png,pdf}}")
    if show:
        plt.show()

    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    plot_grouped_bars(wide_fitness_clean, "Fitness", "Fitness", axes[0], ylim01=True)
    plot_grouped_bars(wide_precision_clean, "Precision", "Precision", axes[1], ylim01=True)
    plt.tight_layout()
    save_figure(
        fig, FIGURES_DIR, "clean_log_fitness_precision",
        no_titles_dir=NO_TITLES_DIR,
    )
    print(f"Saved {FIGURES_DIR / 'clean_log_fitness_precision'}.{{png,pdf}}")
    if show:
        plt.show()

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    plot_grouped_bars(wide_size_clean, "Size", "Size", axes[0])
    plot_grouped_bars(wide_cfc_clean, "CFC", "CFC", axes[1])
    plot_grouped_bars(wide_simplicity_clean, "Simplicity", "Simplicity", axes[2], ylim01=True)
    plt.tight_layout()
    save_figure(
        fig, FIGURES_DIR, "clean_log_complexity",
        no_titles_dir=NO_TITLES_DIR,
    )
    print(f"Saved {FIGURES_DIR / 'clean_log_complexity'}.{{png,pdf}}")
    if show:
        plt.show()

    heur_cols = [c for c in wide_f_score_clean.columns if c.startswith("heuristics_dep_")]
    imf_cols = [c for c in wide_f_score_clean.columns if c.startswith("inductive_IMf_noise_")]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for log_name in LOG_ORDER:
        if log_name not in wide_f_score_clean.index:
            continue

        heur_pairs = sorted(
            (float(c.replace("heuristics_dep_", "")), c) for c in heur_cols
        )
        heur_x = [p[0] for p in heur_pairs]
        heur_y = [wide_f_score_clean.loc[log_name, p[1]] for p in heur_pairs]
        axes[0].plot(heur_x, heur_y, marker="o", label=log_name, color=LOG_COLORS.get(log_name))

        imf_pairs = sorted(
            (float(c.replace("inductive_IMf_noise_", "")), c) for c in imf_cols
        )
        imf_x = [p[0] for p in imf_pairs]
        imf_y = [wide_f_score_clean.loc[log_name, p[1]] for p in imf_pairs]
        axes[1].plot(imf_x, imf_y, marker="o", label=log_name, color=LOG_COLORS.get(log_name))

    axes[0].set_title("Heuristics dependency threshold vs F-score")
    axes[0].set_xlabel("dependency_threshold")
    axes[0].set_ylabel("F-score")
    axes[0].legend()
    _style_axes(axes[0], ylim01=True)

    axes[1].set_title("Inductive IMf noise vs F-score")
    axes[1].set_xlabel("noise_threshold")
    axes[1].set_ylabel("F-score")
    axes[1].legend()
    _style_axes(axes[1], ylim01=True)

    plt.tight_layout()
    save_figure(
        fig, FIGURES_DIR, "clean_log_threshold_sensitivity",
        no_titles_dir=NO_TITLES_DIR,
    )
    print(f"Saved {FIGURES_DIR / 'clean_log_threshold_sensitivity'}.{{png,pdf}}")
    if show:
        plt.show()

    slope_data = wide_f_score_clean.reindex(LOG_ORDER)
    configs = list(slope_data.columns)
    x = np.arange(len(configs))

    fig, ax = plt.subplots(figsize=(14, 5))
    for cfg_idx in range(len(configs)):
        y_vals = slope_data.iloc[:, cfg_idx].astype(float).values
        ax.plot(
            [cfg_idx] * len(LOG_ORDER),
            y_vals,
            color="#cccccc",
            linewidth=1.2,
            zorder=1,
        )
        for log_idx, log_name in enumerate(LOG_ORDER):
            if log_name not in slope_data.index:
                continue
            ax.scatter(
                cfg_idx,
                slope_data.loc[log_name, configs[cfg_idx]],
                color=LOG_COLORS.get(log_name),
                s=60,
                zorder=2,
                label=log_name if cfg_idx == 0 else None,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(configs, rotation=45, ha="right")
    ax.set_ylabel("F-score")
    ax.set_title("Clean logs: F-score comparison across log groups")
    ax.legend(title="Log group")
    _style_axes(ax, ylim01=True)
    plt.tight_layout()
    save_figure(
        fig, FIGURES_DIR, "clean_log_f_score_slopegraph",
        no_titles_dir=NO_TITLES_DIR,
    )
    print(f"Saved {FIGURES_DIR / 'clean_log_f_score_slopegraph'}.{{png,pdf}}")
    if show:
        plt.show()

    return {
        "wide_f_score_clean": wide_f_score_clean,
        "wide_fitness_clean": wide_fitness_clean,
        "wide_precision_clean": wide_precision_clean,
    }


def plot_repro_slopegraph(consolidated_results_table_clean_repro, cfg, figures_dir=None, show=True):
    figures_dir = Path(figures_dir or cfg.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR = figures_dir
    NO_TITLES_DIR = cfg.figures_no_titles_dir

    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.labelsize": 11,
            "axes.titlesize": 13,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
        }
    )

    LOG_LABELS = {
        "vitalizing": "Vitalizing",
        "random_case_control": "Random control (seed mean)",
        "whole": "Whole",
    }

    plot_df_repro = consolidated_results_table_clean_repro[
        consolidated_results_table_clean_repro["status"] == "ok"
    ].copy()
    wide_f_score_repro = (
        plot_df_repro.pivot(index="log_name", columns="discovery_method", values="f_score")
        .reindex(LOG_ORDER)
        .sort_index(axis=1)
    )

    slope_data = wide_f_score_repro.reindex(LOG_ORDER)
    configs = list(slope_data.columns)
    x = np.arange(len(configs))

    fig, ax = plt.subplots(figsize=(12, 5.5))
    for cfg_idx in range(len(configs)):
        y_vals = slope_data.iloc[:, cfg_idx].astype(float).values
        ax.plot(
            [cfg_idx] * len(LOG_ORDER),
            y_vals,
            color="#d9d9d9",
            linewidth=1.0,
            zorder=1,
        )
        for log_name in LOG_ORDER:
            if log_name not in slope_data.index:
                continue
            ax.scatter(
                cfg_idx,
                slope_data.loc[log_name, configs[cfg_idx]],
                color=LOG_COLORS.get(log_name),
                s=72,
                zorder=2,
                edgecolors="white",
                linewidths=0.8,
                label=LOG_LABELS.get(log_name) if cfg_idx == 0 else None,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(configs, rotation=45, ha="right")
    ax.set_ylabel("F-score")
    ax.set_title("F1-Score Comparison Across Discovery Algorithms: Vitalizing Sublog vs. Baselines (Whole log; 10 Random sublogs)")
    ax.legend(title="Log group", frameon=True)
    _style_axes(ax, ylim01=True)
    plt.tight_layout()
    save_figure(
        fig, FIGURES_DIR, "clean_log_f_score_slopegraph_repro",
        no_titles_dir=NO_TITLES_DIR,
    )
    print(f"Saved {FIGURES_DIR / 'clean_log_f_score_slopegraph_repro'}.{{png,pdf}}")
    if show:
        plt.show()
    return fig


def plot_f_score_dotplot_by_miner_different_repos(
    f_score_comparison,
    repos=None,
    discovery_methods=None,
    ncols=3,
    figures_dir=None,
    stem="f_score_dotplot_by_miner",
    show=True,
):
    """One panel per discovery method; repos on x, F1 on y, one marker per log group.

    `f_score_comparison` is the cross-repo table with a (log_name, discovery_method)
    MultiIndex in either order and one column per repo.
    """
    figures_dir = Path(figures_dir or RESULTS_FIGURES)
    figures_dir.mkdir(parents=True, exist_ok=True)
    no_titles_dir = RESULTS_FIGURES_NO_TITLES

    long_df = f_score_comparison.reset_index().melt(
        id_vars=["log_name", "discovery_method"],
        var_name="repo",
        value_name="f_score",
    )

    available_repos = list(f_score_comparison.columns)
    if repos is None:
        repos = available_repos
    else:
        unknown = [r for r in repos if r not in available_repos]
        if unknown:
            raise ValueError(
                f"Unknown repos {unknown}; available repos are {available_repos}"
            )
    if not repos:
        raise ValueError("No repos to plot.")

    if discovery_methods is None:
        discovery_methods = sorted(long_df["discovery_method"].unique())
    else:
        available_methods = set(long_df["discovery_method"])
        unknown = [m for m in discovery_methods if m not in available_methods]
        if unknown:
            raise ValueError(
                f"Unknown discovery methods {unknown}; "
                f"available methods are {sorted(available_methods)}"
            )
    if not discovery_methods:
        raise ValueError("No discovery methods to plot.")

    log_groups = [g for g in LOG_ORDER if g in set(long_df["log_name"])]

    nrows = int(np.ceil(len(discovery_methods) / ncols))
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(3.6 * ncols, 4 * nrows),
        sharey=True,
        squeeze=False,
    )
    flat_axes = axes.ravel()
    x = np.arange(len(repos))

    for ax_idx, ax in enumerate(flat_axes):
        if ax_idx >= len(discovery_methods):
            ax.set_visible(False)
            continue

        method = discovery_methods[ax_idx]
        panel = (
            long_df[long_df["discovery_method"] == method]
            .pivot(index="log_name", columns="repo", values="f_score")
            .reindex(index=log_groups, columns=repos)
        )

        for repo_idx, repo in enumerate(repos):
            ax.plot(
                [repo_idx] * len(log_groups),
                panel[repo].astype(float).values,
                color="#d9d9d9",
                linewidth=1.0,
                zorder=1,
            )

        for log_name in log_groups:
            ax.scatter(
                x,
                panel.loc[log_name, repos].astype(float).values,
                color=LOG_COLORS.get(log_name),
                marker=LOG_MARKERS.get(log_name, "o"),
                s=60,
                alpha=0.85,
                zorder=2,
                edgecolors="white",
                linewidths=0.8,
                label=LOG_LABELS.get(log_name, log_name) if ax_idx == 0 else None,
            )

        ax.set_title(method)
        ax.set_xticks(x)
        ax.set_xticklabels(repos, rotation=45, ha="right")
        if ax_idx % ncols == 0:
            ax.set_ylabel("F1-score")
        _style_axes(ax, ylim01=True)

    handles, labels = flat_axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        title="Log group",
        ncol=len(log_groups),
        loc="lower center",
        frameon=True,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    save_figure(fig, figures_dir, stem, no_titles_dir=no_titles_dir)
    print(f"Saved {figures_dir / stem}.{{png,pdf}}")
    if show:
        plt.show()
    return fig
