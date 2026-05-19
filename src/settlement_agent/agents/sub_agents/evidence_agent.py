"""Evidence sub-agent.

Calls CSV-backed tools and assembles an ``EvidenceBundle``. In Phase 2
this becomes an ADK ``LlmAgent`` with the four MCP-backed tools attached
as its toolset; the bundle assembly stays the same.
"""
from __future__ import annotations

from ...domain.models import (
    EvidenceBundle,
    PositionEvidence,
    PositionToolInput,
    ReferenceDataToolInput,
    ReferenceEvidence,
    ScenarioClassification,
    SettlementEvidence,
    SettlementToolInput,
    TradeNettingEvidence,
    TradeNettingToolInput,
)
from ...tools.position_tool import call_position_tool
from ...tools.reference_data_tool import call_reference_data_tool
from ...tools.settlement_tool import call_settlement_tool
from ...tools.trade_netting_tool import call_trade_netting_tool
from .intake_agent import lookup_settlement_row

AGENT_ID = "evidence_agent"


def run(classification: ScenarioClassification) -> EvidenceBundle:
    bundle = EvidenceBundle(
        instruction_id=classification.instruction_id,
        case_id=classification.case_id,
    )

    settlement_row = (
        lookup_settlement_row(classification.instruction_id)
        if classification.instruction_id
        else None
    )

    # Settlement first — anchors the rest of the bundle.
    s_call = call_settlement_tool(
        SettlementToolInput(instruction_id=classification.instruction_id)
    )
    bundle.tool_calls.append(s_call)
    bundle.settlement = [SettlementEvidence(**r) for r in s_call.records]

    account_id = settlement_row.get("account_id") if settlement_row else None
    security_id = settlement_row.get("security_id") if settlement_row else None
    counterparty_id = settlement_row.get("counterparty_id") if settlement_row else None

    if account_id and security_id:
        p_call = call_position_tool(
            PositionToolInput(account_id=account_id, security_id=security_id)
        )
        bundle.tool_calls.append(p_call)
        bundle.position = [PositionEvidence(**r) for r in p_call.records]

    r_call = call_reference_data_tool(
        ReferenceDataToolInput(
            security_id=security_id,
            account_id=account_id,
            counterparty_id=counterparty_id,
        )
    )
    bundle.tool_calls.append(r_call)
    bundle.reference = [ReferenceEvidence(**r) for r in r_call.records]

    t_call = call_trade_netting_tool(
        TradeNettingToolInput(
            account_id=account_id,
            security_id=security_id,
            counterparty_id=counterparty_id,
        )
    )
    bundle.tool_calls.append(t_call)
    bundle.trade_netting = [TradeNettingEvidence(**r) for r in t_call.records]

    return bundle


def build_adk_agent():  # pragma: no cover - Phase 2 placeholder
    try:
        from google.adk.agents import LlmAgent  # type: ignore
    except Exception:
        return None
    return LlmAgent(
        name=AGENT_ID,
        instruction=(
            "Call position_tool, settlement_tool, reference_data_tool, and "
            "trade_netting_tool for the supplied instruction context. Store "
            "raw evidence rows in the evidence bundle; do not summarise."
        ),
    )
