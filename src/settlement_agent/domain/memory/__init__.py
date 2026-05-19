"""Domain memory layer.

Phase 1 exposes only ``SessionState`` (in-memory, per-run). Phase 2 will
add a durable session store and a case-memory store behind these same
interfaces.
"""
from .session import SessionState  # noqa: F401
