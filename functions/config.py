"""Portable paths and analysis constants shared by every dataset.

Dataset-specific values (database paths, event type ids, attribute ids, OCEL2
event tables, output folders) live in `functions/configs/<dataset>.py` and are
loaded with `functions.configs.load_dataset_config`.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
RESULTS_TABLES = PROJECT_ROOT / "results" / "tables"
RESULTS_FIGURES = PROJECT_ROOT / "results" / "figures"
RESULTS_FIGURES_NO_TITLES = PROJECT_ROOT / "results" / "figures_no_titles"
COMPLEXITY_REPO = PROJECT_ROOT / "process-complexity"

IQR_CONFIG = {
    "window_size": 30,
    "min_periods": 8,
    "iqr_multiplier": 1.5,
}

# Utility experiment (unchanged values)
SEED = 40
MAX_REP = 5
REPRO_SEEDS = list(range(10))


def _write_figure(fig, figures_dir, stem, dpi):
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".pdf"):
        fig.savefig(figures_dir / f"{stem}{ext}", dpi=dpi, bbox_inches="tight")


def save_figure(fig, figures_dir, stem, dpi=300, no_titles_dir=None):
    """Save figure as both PNG and PDF at the given dpi.

    When ``no_titles_dir`` is set, also write a copy with axes titles and
    figure ``suptitle`` cleared, then restore them for notebook display.
    """
    _write_figure(fig, figures_dir, stem, dpi)

    if no_titles_dir is None:
        return

    title_artists = []
    for ax in fig.axes:
        title = ax.title
        title_artists.append((title, title.get_text(), title.get_visible()))
        title.set_text("")
        title.set_visible(False)

    st = fig._suptitle
    st_state = None
    if st is not None:
        st_state = (st.get_text(), st.get_visible())
        st.set_text("")
        st.set_visible(False)

    try:
        _write_figure(fig, no_titles_dir, stem, dpi)
    finally:
        for title, text, visible in title_artists:
            title.set_text(text)
            title.set_visible(visible)
        if st_state is not None:
            st.set_text(st_state[0])
            st.set_visible(st_state[1])
