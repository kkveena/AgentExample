"""Session memory.

Phase 1: ``SessionState`` is re-exported from ``domain.models`` so the
import path is stable for downstream code while the model definition
stays co-located with the other Pydantic types.

Phase 2: this module will grow real session-store interfaces and
adapters (in-memory / sqlite / redis) without changing the public
``SessionState`` shape.
"""
from __future__ import annotations

from ..models import SessionState  # noqa: F401
