"""Shared base utilities for CSV-backed tools.

Phase 1 implementations are deliberately thin so they can be replaced by
REST-backed adapters and ultimately exposed as MCP tools without changing
the tool input/output contracts.
"""
from __future__ import annotations

from typing import Iterable


def _eq(row_value: str | None, expected: str | None) -> bool:
    if expected is None:
        return True
    if row_value is None:
        return False
    return str(row_value).strip() == str(expected).strip()


def filter_rows(rows: Iterable[dict], **predicates: str | None) -> list[dict]:
    """Filter CSV rows where every non-None predicate matches exactly."""
    return [
        row
        for row in rows
        if all(_eq(row.get(k), v) for k, v in predicates.items())
    ]


def coerce_float(value: str | None, default: float = 0.0) -> float:
    if value in (None, "", "NA"):
        return default
    try:
        return float(value)
    except ValueError:
        return default


def coerce_int(value: str | None, default: int = 0) -> int:
    if value in (None, "", "NA"):
        return default
    try:
        return int(value)
    except ValueError:
        return default
