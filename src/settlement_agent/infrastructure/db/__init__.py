"""Database / file-system adapters.

Phase 1: CSV files under ``data/`` via :mod:`csv_loader`.
Phase 2: REST endpoints + SQL connections will live here alongside.
"""
from . import csv_loader  # noqa: F401
