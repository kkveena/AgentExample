"""Settlement Tool (CSV-backed mock).

Phase 1: reads from data/settlement_data.csv.
Phase 2: replace with a REST adapter exposed via MCP. Keep this contract.
"""
from __future__ import annotations

from ..models import SettlementEvidence, SettlementToolInput, ToolCallResult
from ...infrastructure.db.csv_loader import load_settlements
from .base import filter_rows

TOOL_NAME = "settlement_tool"


def call_settlement_tool(
    payload: SettlementToolInput | dict, base_dir: str | None = None
) -> ToolCallResult:
    inp = (
        payload
        if isinstance(payload, SettlementToolInput)
        else SettlementToolInput(**payload)
    )
    rows = load_settlements(base_dir)
    matches = filter_rows(
        rows,
        instruction_id=inp.instruction_id,
        account_id=inp.account_id,
        security_id=inp.security_id,
    )
    evidence = [SettlementEvidence(**row).model_dump() for row in matches]
    return ToolCallResult(
        tool_name=TOOL_NAME,
        input_payload=inp.model_dump(exclude_none=True),
        records=evidence,
        record_count=len(evidence),
    )
