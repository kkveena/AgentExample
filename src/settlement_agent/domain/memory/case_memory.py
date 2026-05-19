"""Case-memory interface (Phase 1 placeholder).

Phase 1 stores illustrative cases in ``experience.md``. This module
defines the interface that the Phase 2 key-value (and later
pgvector-backed) case-memory adapter will implement.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CaseMemory(Protocol):
    """Read/write interface for durable case memory."""

    def get(self, case_id: str) -> dict | None: ...

    def put(self, case_id: str, payload: dict) -> None: ...

    def search(self, query: str, k: int = 5) -> list[dict]: ...
