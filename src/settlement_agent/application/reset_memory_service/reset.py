"""Reset Phase 1 in-memory caches.

Phase 2 will extend this to clear durable session and case-memory
stores as well.
"""
from __future__ import annotations

from ...infrastructure import config_loader
from ...infrastructure.db import csv_loader


def reset_memory() -> dict[str, int]:
    """Clear all in-memory caches used by Phase 1.

    Returns a dict reporting how many cache entries were cleared per
    layer so callers (CLI / test fixtures) can confirm the reset.
    """
    csv_cache_size = csv_loader.load_csv.cache_info().currsize
    cfg_cache_size = config_loader.load_yaml.cache_info().currsize

    csv_loader.load_csv.cache_clear()
    config_loader.load_yaml.cache_clear()

    return {
        "csv_entries_cleared": csv_cache_size,
        "config_entries_cleared": cfg_cache_size,
    }
