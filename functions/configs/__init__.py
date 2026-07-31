"""Per-dataset configuration modules and the loader that packs them.

Every dataset-specific value (paths, event type ids, attribute ids, OCEL2 event
tables, output folders) lives in one module of this package, so wiring up a new
export or fixing an id is a one-file edit.

    from functions.configs import load_dataset_config
    cfg = load_dataset_config("commitizen")
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, fields
from pathlib import Path

# Normalised dataset name -> module in this package.
_DATASET_MODULES = {
    "commitizen": "commitizen",
    "tradingagents": "tradingagents",
    "trading_agents": "tradingagents",
    "fingpt": "fingpt",
    "finrl": "finrl",
    "fin_rl": "finrl",
    "vibe_trading": "vibe_trading",
    "vibetrading": "vibe_trading",
    "openbb": "openbb",
}


@dataclass(frozen=True)
class DatasetConfig:
    """Everything the analysis functions need to know about one dataset."""

    dataset_name: str
    duckdb_path: Path
    sqlite_path: Path
    closed_event_type_id: int
    create_event_type_id: int
    commit_event_type_id: int
    title_attribute_id: int
    commit_message_attribute_id: int
    issue_object_type: str
    commit_object_type: str
    end_activity_1: str
    end_activity_2: str
    tables_dir: Path
    figures_dir: Path
    event_subtables: tuple


def available_datasets():
    """Dataset names accepted by load_dataset_config, without the aliases."""
    return sorted(set(_DATASET_MODULES.values()))


def _normalise(name):
    return str(name).strip().lower().replace("-", "_").replace(" ", "_")


def load_dataset_config(name):
    """Load the config module for `name` and pack it into a DatasetConfig.

    Names are matched case-insensitively and dashes count as underscores, so
    "Vibe-Trading", "vibe_trading" and "VIBE-TRADING" all resolve to the same
    module.
    """
    key = _normalise(name)
    if key not in _DATASET_MODULES:
        raise ValueError(
            f"Unknown dataset {name!r}. Available datasets: "
            f"{', '.join(available_datasets())}."
        )

    module = importlib.import_module(f"{__name__}.{_DATASET_MODULES[key]}")

    values = {}
    for field in fields(DatasetConfig):
        constant = field.name.upper()
        if not hasattr(module, constant):
            raise AttributeError(
                f"Config module {module.__name__} is missing {constant}."
            )
        values[field.name] = getattr(module, constant)

    for path_field in ("duckdb_path", "sqlite_path", "tables_dir", "figures_dir"):
        values[path_field] = Path(values[path_field])
    values["event_subtables"] = tuple(values["event_subtables"])

    config = DatasetConfig(**values)

    for label, path in (("DuckDB", config.duckdb_path), ("SQLite", config.sqlite_path)):
        if not path.exists():
            raise FileNotFoundError(
                f"{label} file for dataset {config.dataset_name!r} not found: {path}"
            )

    return config


__all__ = ["DatasetConfig", "available_datasets", "load_dataset_config"]
