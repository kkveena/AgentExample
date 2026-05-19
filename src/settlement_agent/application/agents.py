"""Deterministic Phase 1 agent implementations.

These mirror the YAML-declared agents but stay deterministic so the
workflow can run end-to-end in tests / notebook without an LLM call.
When ADK is wired up, each function below maps to an ADK sub-agent's
tool-call / response handler.
"""
from __future__ import annotations

from typing import Optional

from ..domain.models import (
    CommentaryDraft,
    DiagnosisResult,
    EvidenceBundle,
    HumanApproval,
    PolicyResult,
    PositionToolInput,
    ReferenceDataToolInput,
    ScenarioClassification,
    SettlementToolInput,
    TradeNettingToolInput,
)
from ..infrastructure.csv_loader import load_scenario_manifest, load_settlements
from ..tools.position_tool import call_position_tool
from ..tools.reference_data_tool import call_reference_data_tool
from ..tools.settlement_tool import call_settlement_tool
from ..tools.trade_netting_tool import call_trade_netting_tool


# ---------------------------------------------------------------------------
# Intake
# ---------------------------------------------------------------------------


def _lookup_settlement_row(instruction_id: str) -> Optional[dict]:
    for row in load_settlements():
        if row.get("instruction_id") == instruction_id:
            return row
    return None


def _lookup_scenario(case_id: str) -> Optional[dict]:
    for row in load_scenario_manifest():
        if row.get("case_id") == case_id:
            return row
    return None


SCENARIO_LABEL_BY_REASON = {
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


def intake_agent(instruction_id: str) -> ScenarioClassification:
    """Classify the scenario from the instruction id."""
    settlement_row = _lookup_settlement_row(instruction_id)
    if not settlement_row:
        return ScenarioClassification(
            instruction_id=instruction_id,
            scenario_label="insufficient_information",
            is_firm_short_candidate=False,
            notes="Instruction not found in settlement data.",
        )
    case_id = settlement_row.get("case_id")
    scenario_row = _lookup_scenario(case_id) if case_id else None
    reason_code = (scenario_row or {}).get("primary_reason_code", "")
    label = SCENARIO_LABEL_BY_REASON.get(reason_code, "insufficient_information")
    return ScenarioClassification(
        instruction_id=instruction_id,
        case_id=case_id,
        scenario_label=label,
        is_firm_short_candidate=label == "firm_short",
        notes=(scenario_row or {}).get("scenario_name"),
    )


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


def evidence_agent(classification: ScenarioClassification) -> EvidenceBundle:
    """Call CSV-backed tools and assemble an evidence bundle."""
    bundle = EvidenceBundle(
        instruction_id=classification.instruction_id,
        case_id=classification.case_id,
    )

    settlement_row = (
        _lookup_settlement_row(classification.instruction_id)
        if classification.instruction_id
        else None
    )

    # Always call settlement tool first to anchor the bundle.
    s_call = call_settlement_tool(
        SettlementToolInput(instruction_id=classification.instruction_id)
    )
    bundle.tool_calls.append(s_call)
    bundle.settlement = [
        __safe_settlement(r) for r in s_call.records if r is not None
    ]

    account_id = settlement_row.get("account_id") if settlement_row else None
    security_id = settlement_row.get("security_id") if settlement_row else None
    counterparty_id = settlement_row.get("counterparty_id") if settlement_row else None

    # Position tool: applies when we have an account/security context.
    if account_id and security_id:
        p_call = call_position_tool(
            PositionToolInput(account_id=account_id, security_id=security_id)
        )
        bundle.tool_calls.append(p_call)
        bundle.position = [__safe_position(r) for r in p_call.records]

    # Reference data tool.
    r_call = call_reference_data_tool(
        ReferenceDataToolInput(
            security_id=security_id,
            account_id=account_id,
            counterparty_id=counterparty_id,
        )
    )
    bundle.tool_calls.append(r_call)
    bundle.reference = [__safe_reference(r) for r in r_call.records]

    # Trade / netting tool.
    t_call = call_trade_netting_tool(
        TradeNettingToolInput(
            account_id=account_id,
            security_id=security_id,
            counterparty_id=counterparty_id,
        )
    )
    bundle.tool_calls.append(t_call)
    bundle.trade_netting = [__safe_trade(r) for r in t_call.records]

    return bundle


# Small helpers to convert dicts back to Pydantic instances safely.
from ..domain.models import (  # noqa: E402  (kept here to avoid circular tangles)
    PositionEvidence,
    ReferenceEvidence,
    SettlementEvidence,
    TradeNettingEvidence,
)


def __safe_position(d: dict) -> PositionEvidence:
    return PositionEvidence(**d)


def __safe_settlement(d: dict) -> SettlementEvidence:
    return SettlementEvidence(**d)


def __safe_reference(d: dict) -> ReferenceEvidence:
    return ReferenceEvidence(**d)


def __safe_trade(d: dict) -> TradeNettingEvidence:
    return TradeNettingEvidence(**d)


# ---------------------------------------------------------------------------
# Diagnosis
# ---------------------------------------------------------------------------


def diagnosis_agent(
    classification: ScenarioClassification, evidence: EvidenceBundle
) -> DiagnosisResult:
    """Apply firm-short business rules to the evidence bundle."""

    # Locate the delivery settlement record (if any) for this instruction.
    delivery = next(
        (s for s in evidence.settlement if s.direction == "DELIVER"),
        None,
    )
    receive = next(
        (s for s in evidence.settlement if s.direction == "RECEIVE"),
        None,
    )

    # Pick the position record for the firm delivery account.
    delivery_account = delivery.account_id if delivery else None
    position = next(
        (p for p in evidence.position if p.account_id == delivery_account),
        evidence.position[0] if evidence.position else None,
    )

    delivery_qty = delivery.pending_qty if delivery else None
    free_qty = position.free_position_qty if position else None
    pledged_qty = position.pledged_qty if position else None
    segregated_qty = position.segregated_qty if position else None
    incoming_qty = position.pending_receive_qty if position else None
    shortfall = (
        max(0.0, (delivery_qty or 0.0) - (free_qty or 0.0))
        if delivery_qty is not None and free_qty is not None
        else None
    )
    incoming_covers = (
        incoming_qty is not None
        and shortfall is not None
        and incoming_qty >= shortfall
        and shortfall > 0
    )

    # Counterparty short on receive: no position record needed.
    if (
        classification.scenario_label == "counterparty_short"
        and receive
        and not delivery
    ):
        return DiagnosisResult(
            reason_code="COUNTERPARTY_SHORT",
            is_firm_short=False,
            delivery_obligation_qty=None,
            free_position_qty=free_qty,
            recommended_action=(
                "Monitor incoming receive; do not describe as firm short."
            ),
            evidence_refs=_evidence_refs(evidence),
            confidence=_avg_confidence(evidence),
            notes="Counterparty pending delivery on a receive instruction.",
        )

    if classification.scenario_label == "rejected_or_unalleged":
        return DiagnosisResult(
            reason_code="COUNTERPARTY_REJECT",
            is_firm_short=False,
            recommended_action=(
                "Route for manual review / re-instruction as needed."
            ),
            evidence_refs=_evidence_refs(evidence),
            confidence=_avg_confidence(evidence),
            notes="Instruction reported as unmatched or rejected.",
        )

    if classification.scenario_label == "netting_mismatch":
        return DiagnosisResult(
            reason_code="NETTING_MISMATCH_GROSS_VS_NET",
            is_firm_short=False,
            delivery_obligation_qty=delivery_qty,
            recommended_action=(
                "Validate gross vs net obligations before drafting external commentary."
            ),
            evidence_refs=_evidence_refs(evidence),
            confidence=_avg_confidence(evidence),
            notes="Gross vs netted quantity mismatch on the netting group.",
        )

    if classification.scenario_label == "intercompany_dependency":
        return DiagnosisResult(
            reason_code="DEPENDENT_ON_INTERNAL_RECEIVE",
            is_firm_short=True,
            delivery_obligation_qty=delivery_qty,
            free_position_qty=free_qty,
            shortfall_qty=shortfall,
            incoming_receive_qty=incoming_qty,
            incoming_receive_covers=incoming_covers,
            recommended_action=(
                "Track internal receive dependency before delivery commentary."
            ),
            evidence_refs=_evidence_refs(evidence),
            confidence=_avg_confidence(evidence),
        )

    if classification.scenario_label == "incoming_receive_covers":
        return DiagnosisResult(
            reason_code="SHORT_PENDING_INCOMING_RECEIVE",
            is_firm_short=True,
            delivery_obligation_qty=delivery_qty,
            free_position_qty=free_qty,
            pledged_qty=pledged_qty,
            segregated_qty=segregated_qty,
            shortfall_qty=shortfall,
            incoming_receive_qty=incoming_qty,
            incoming_receive_covers=incoming_covers,
            recommended_action=(
                "Link incoming receive; monitor settlement before external commentary."
            ),
            evidence_refs=_evidence_refs(evidence),
            confidence=_avg_confidence(evidence),
        )

    # Firm-short paths (encumbered, realignment, plain firm short). Use the
    # inventory_status flag from position evidence as the discriminator so
    # diagnosis stays consistent with the scenario manifest.
    if classification.scenario_label == "firm_short" and delivery and position:
        status = (position.inventory_status or "").upper()
        if status == "FREE_INVENTORY_ENCUMBERED":
            reason = "FREE_INVENTORY_ENCUMBERED"
            action = "Request release from pledge/segregation or alternate cover."
        elif status == "REALIGNMENT_REQUIRED":
            reason = "REALIGNMENT_REQUIRED"
            action = "Initiate or recommend realignment instruction."
        else:
            reason = "FIRM_SHORT_FREE_INVENTORY"
            action = "Desk to confirm cover or release/realignment; do not speculate beyond evidence."

        return DiagnosisResult(
            reason_code=reason,
            is_firm_short=True,
            delivery_obligation_qty=delivery_qty,
            free_position_qty=free_qty,
            pledged_qty=pledged_qty,
            segregated_qty=segregated_qty,
            shortfall_qty=shortfall,
            incoming_receive_qty=incoming_qty,
            incoming_receive_covers=incoming_covers,
            recommended_action=action,
            evidence_refs=_evidence_refs(evidence),
            confidence=_avg_confidence(evidence),
        )

    # Default / insufficient evidence path.
    return DiagnosisResult(
        reason_code="NO_POSITION_SHORT" if delivery else "INSUFFICIENT_EVIDENCE",
        is_firm_short=False,
        delivery_obligation_qty=delivery_qty,
        free_position_qty=free_qty,
        recommended_action=(
            "Flag as insufficient evidence for firm-short commentary; analyst review."
        ),
        evidence_refs=_evidence_refs(evidence),
        confidence=_avg_confidence(evidence),
        notes="No firm-short evidence detected from current bundle.",
    )


def _evidence_refs(evidence: EvidenceBundle) -> list[str]:
    refs: list[str] = []
    refs.extend(p.position_evidence_id for p in evidence.position)
    refs.extend(s.settlement_evidence_id for s in evidence.settlement)
    refs.extend(r.ref_id for r in evidence.reference)
    refs.extend(t.trade_evidence_id for t in evidence.trade_netting)
    return refs


def _avg_confidence(evidence: EvidenceBundle) -> float:
    scores: list[float] = []
    for p in evidence.position:
        if p.confidence_score is not None:
            scores.append(p.confidence_score)
    for s in evidence.settlement:
        if s.confidence_score is not None:
            scores.append(s.confidence_score)
    return round(sum(scores) / len(scores), 4) if scores else 0.0


# ---------------------------------------------------------------------------
# Commentary
# ---------------------------------------------------------------------------


def commentary_agent(
    diagnosis: DiagnosisResult, evidence: EvidenceBundle
) -> CommentaryDraft:
    """Build factual draft commentary tied to retrieved evidence."""
    ref = evidence.reference[0] if evidence.reference else None
    security_desc = ref.security_description if ref else "the referenced security"
    delivery = next(
        (s for s in evidence.settlement if s.direction == "DELIVER"),
        None,
    )
    timestamp = (
        delivery.last_status_ts
        if delivery and delivery.last_status_ts
        else (evidence.position[0].snapshot_ts if evidence.position else "the latest snapshot")
    )

    rc = diagnosis.reason_code
    if rc in {"FIRM_SHORT_FREE_INVENTORY", "FREE_INVENTORY_ENCUMBERED", "REALIGNMENT_REQUIRED"}:
        text = (
            f"Delivery remains pending for {security_desc}. Free position is below "
            f"the pending delivery quantity as of {timestamp}. "
            f"{'Pledged or segregated inventory is reducing free availability. ' if rc == 'FREE_INVENTORY_ENCUMBERED' else ''}"
            f"Incoming receives do not currently cover the shortfall. "
            f"Desk action required: confirm cover, realignment, or release instruction."
        )
    elif rc == "SHORT_PENDING_INCOMING_RECEIVE":
        text = (
            f"Delivery remains pending for {security_desc}. A linked incoming "
            f"receive is expected and may cover the shortfall once settled "
            f"(as of {timestamp}). Monitor receive settlement before external commentary."
        )
    elif rc == "COUNTERPARTY_SHORT":
        text = (
            f"Receive instruction for {security_desc} remains pending with the "
            f"counterparty (as of {timestamp}). No firm short condition identified."
        )
    elif rc == "COUNTERPARTY_REJECT":
        text = (
            f"Instruction for {security_desc} is reported as unmatched or "
            f"rejected as of {timestamp}. Manual review or re-instruction is required."
        )
    elif rc == "DEPENDENT_ON_INTERNAL_RECEIVE":
        text = (
            f"Delivery for {security_desc} depends on an internal receive that "
            f"has not yet settled (as of {timestamp}). Track internal dependency."
        )
    elif rc == "NETTING_MISMATCH_GROSS_VS_NET":
        text = (
            f"Pending delivery for {security_desc} shows a gross vs netted "
            f"quantity mismatch (as of {timestamp}). Validate net obligation "
            f"before external commentary."
        )
    else:
        text = (
            f"Insufficient evidence to confirm a firm-short condition for "
            f"{security_desc} as of {timestamp}. Analyst review recommended."
        )

    return CommentaryDraft(
        text=text,
        reason_code=rc,
        evidence_refs=diagnosis.evidence_refs,
        contains_unsupported_claims=False,
        grounded=True,
    )


# ---------------------------------------------------------------------------
# Policy / HITL
# ---------------------------------------------------------------------------


FORBIDDEN_TOKENS = (
    # Generic placeholders for internal source-system names. Add real names
    # here if they ever leak into prompts/tests so this gate catches them.
    "SourceSystemA",
    "SourceSystemB",
    "ProdDB",
)


def policy_agent(
    commentary: CommentaryDraft, evidence: EvidenceBundle, diagnosis: DiagnosisResult
) -> PolicyResult:
    findings: list[str] = []

    if not commentary.evidence_refs:
        findings.append("commentary has no linked evidence references")

    for tok in FORBIDDEN_TOKENS:
        if tok.lower() in commentary.text.lower():
            findings.append(f"commentary references forbidden token: {tok}")

    if diagnosis.is_firm_short and not evidence.position:
        findings.append("firm-short claim without position evidence")

    if commentary.contains_unsupported_claims:
        findings.append("commentary contains unsupported claims")

    return PolicyResult(
        passed=len(findings) == 0,
        findings=findings,
        requires_human_approval=True,
    )


def apply_human_approval(
    status: str, reviewer: Optional[str] = None, comments: Optional[str] = None
) -> HumanApproval:
    if status not in {"approved", "rejected", "needs_edit", "pending"}:
        raise ValueError(f"Unsupported approval status: {status}")
    from datetime import datetime

    return HumanApproval(
        status=status,  # type: ignore[arg-type]
        reviewer=reviewer,
        comments=comments,
        decided_at=datetime.utcnow() if status != "pending" else None,
    )
