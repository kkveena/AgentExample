"""Intake sub-agent.

Classifies the scenario for a given instruction_id. In Phase 1 this is
deterministic, driven by the scenario manifest. In Phase 2 this becomes
an ADK ``LlmAgent`` whose tool is a settlement-lookup MCP tool.
"""
from __future__ import annotations

from typing import Optional

from ...domain.models import ScenarioClassification
from ...infrastructure.csv_loader import load_scenario_manifest, load_settlements

AGENT_ID = "intake_agent"

SCENARIO_LABEL_BY_REASON: dict[str, str] = {
    "FIRM_SHORT_FREE_INVENTORY": "firm_short",
    "FREE_INVENTORY_ENCUMBERED": "firm_short",
    "REALIGNMENT_REQUIRED": "firm_short",
    "SHORT_PENDING_INCOMING_RECEIVE": "incoming_receive_covers",
    "COUNTERPARTY_SHORT": "counterparty_short",
    "COUNTERPARTY_REJECT": "rejected_or_unalleged",
    "DEPENDENT_ON_INTERNAL_RECEIVE": "intercompany_dependency",
    "NETTING_MISMATCH_GROSS_VS_NET": "netting_mismatch",
    "NO_POSITION_SHORT": "insufficient_information",
    "CONTROL_OK": "control_no_fail",
}


def lookup_settlement_row(instruction_id: str) -> Optional[dict]:
    for row in load_settlements():
        if row.get("instruction_id") == instruction_id:
            return row
    return None


def lookup_scenario(case_id: str) -> Optional[dict]:
    for row in load_scenario_manifest():
        if row.get("case_id") == case_id:
            return row
    return None


def run(instruction_id: str) -> ScenarioClassification:
    """Classify the scenario from the instruction id."""
    settlement_row = lookup_settlement_row(instruction_id)
    if not settlement_row:
        return ScenarioClassification(
            instruction_id=instruction_id,
            scenario_label="insufficient_information",
            is_firm_short_candidate=False,
            notes="Instruction not found in settlement data.",
        )
    case_id = settlement_row.get("case_id")
    scenario_row = lookup_scenario(case_id) if case_id else None
    reason_code = (scenario_row or {}).get("primary_reason_code", "")
    label = SCENARIO_LABEL_BY_REASON.get(reason_code, "insufficient_information")
    return ScenarioClassification(
        instruction_id=instruction_id,
        case_id=case_id,
        scenario_label=label,
        is_firm_short_candidate=label == "firm_short",
        notes=(scenario_row or {}).get("scenario_name"),
    )


def build_adk_agent():  # pragma: no cover - Phase 2 placeholder
    """Phase 2 placeholder for an ADK LlmAgent definition."""
    try:
        from google.adk.agents import LlmAgent  # type: ignore
    except Exception:
        return None
    return LlmAgent(
        name=AGENT_ID,
        instruction=(
            "Classify the inbound settlement instruction into one of the "
            "Phase 1 scenarios. Do not invent details. Prefer "
            "'insufficient_information' over speculation."
        ),
    )
