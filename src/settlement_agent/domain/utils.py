"""Shared domain utilities (pure helpers, no I/O)."""
from __future__ import annotations

from typing import Iterable


def first(iterable: Iterable, default=None):
    """Return the first element of ``iterable`` or ``default`` if empty."""
    for item in iterable:
        return item
    return default
