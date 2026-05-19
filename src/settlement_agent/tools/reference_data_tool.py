"""Reference Data Tool (CSV-backed mock).

Phase 1: reads from data/reference_data.csv.
Phase 2: replace with a REST adapter exposed via MCP. Keep this contract.
"""
from __future__ import annotations

from ..domain.models import (
    ReferenceDataToolInput,
    ReferenceEvidence,
    ToolCallResult,
)
from ..infrastructure.csv_loader import load_reference
from .base import filter_rows

TOOL_NAME = "reference_data_tool"


def call_reference_data_tool(
    payload: ReferenceDataToolInput | dict, base_dir: str | None = None
) -> ToolCallResult:
    inp = (
        payload
        if isinstance(payload, ReferenceDataToolInput)
        else ReferenceDataToolInput(**payload)
    )
    rows = load_reference(base_dir)
    matches = filter_rows(
        rows,
        security_id=inp.security_id,
        cusip=inp.cusip,
        isin=inp.isin,
        account_id=inp.account_id,
        counterparty_id=inp.counterparty_id,
    )
    evidence = [ReferenceEvidence(**row).model_dump() for row in matches]
    return ToolCallResult(
        tool_name=TOOL_NAME,
        input_payload=inp.model_dump(exclude_none=True),
        records=evidence,
        record_count=len(evidence),
    )
