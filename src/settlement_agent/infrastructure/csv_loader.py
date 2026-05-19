"""CSV loading helpers for Phase 1 mock data.

In Phase 2+ these CSV reads will be replaced by REST/MCP-backed adapters.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def data_dir() -> Path:
    return DEFAULT_DATA_DIR


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return [dict(row) for row in reader]


@lru_cache(maxsize=None)
def load_csv(filename: str, base_dir: str | None = None) -> tuple[dict, ...]:
    """Load a CSV as an immutable tuple of dicts (cache-friendly)."""
    base = Path(base_dir) if base_dir else DEFAULT_DATA_DIR
    rows = _read_csv(base / filename)
    return tuple(rows)


def load_positions(base_dir: str | None = None) -> list[dict]:
    return list(load_csv("position_data.csv", base_dir))


def load_settlements(base_dir: str | None = None) -> list[dict]:
    return list(load_csv("settlement_data.csv", base_dir))


def load_reference(base_dir: str | None = None) -> list[dict]:
    return list(load_csv("reference_data.csv", base_dir))


def load_trade_netting(base_dir: str | None = None) -> list[dict]:
    return list(load_csv("trade_netting_data.csv", base_dir))


def load_scenario_manifest(base_dir: str | None = None) -> list[dict]:
    return list(load_csv("scenario_manifest.csv", base_dir))


def load_data_dictionary(base_dir: str | None = None) -> list[dict]:
    return list(load_csv("data_dictionary.csv", base_dir))
