"""Position Tool (CSV-backed mock).

Phase 1: reads from data/position_data.csv.
Phase 2: replace internals with a REST adapter; expose via MCP server. The
input/output Pydantic models must remain stable across that migration.
"""
from __future__ import annotations

from ..domain.models import PositionEvidence, PositionToolInput, ToolCallResult
from ..infrastructure.csv_loader import load_positions
from .base import filter_rows

TOOL_NAME = "position_tool"


def call_position_tool(
    payload: PositionToolInput | dict, base_dir: str | None = None
) -> ToolCallResult:
    """Return position evidence for the given account / security."""
    inp = (
        payload
        if isinstance(payload, PositionToolInput)
        else PositionToolInput(**payload)
    )
    rows = load_positions(base_dir)
    matches = filter_rows(
        rows,
        account_id=inp.account_id,
        security_id=inp.security_id,
        cusip=inp.cusip,
        settlement_location=inp.settlement_location,
    )
    evidence = [PositionEvidence(**row).model_dump() for row in matches]
    return ToolCallResult(
        tool_name=TOOL_NAME,
        input_payload=inp.model_dump(exclude_none=True),
        records=evidence,
        record_count=len(evidence),
    )
