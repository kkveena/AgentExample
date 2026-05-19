"""Trade / Netting Tool (CSV-backed mock).

Phase 1: reads from data/trade_netting_data.csv.
Phase 2: replace with a REST adapter exposed via MCP. Keep this contract.
"""
from __future__ import annotations

from ..models import (
    ToolCallResult,
    TradeNettingEvidence,
    TradeNettingToolInput,
)
from ...infrastructure.db.csv_loader import load_trade_netting
from .base import filter_rows

TOOL_NAME = "trade_netting_tool"


def call_trade_netting_tool(
    payload: TradeNettingToolInput | dict, base_dir: str | None = None
) -> ToolCallResult:
    inp = (
        payload
        if isinstance(payload, TradeNettingToolInput)
        else TradeNettingToolInput(**payload)
    )
    rows = load_trade_netting(base_dir)
    matches = filter_rows(
        rows,
        account_id=inp.account_id,
        security_id=inp.security_id,
        counterparty_id=inp.counterparty_id,
    )
    evidence = [TradeNettingEvidence(**row).model_dump() for row in matches]
    return ToolCallResult(
        tool_name=TOOL_NAME,
        input_payload=inp.model_dump(exclude_none=True),
        records=evidence,
        record_count=len(evidence),
    )
