"""Diagnosis sub-agent.

Applies firm-short business rules to the evidence bundle and emits a
``DiagnosisResult``. Phase 2: same logic invoked behind an ADK
``LlmAgent`` for natural-language outputs while keeping the reason-code
contract stable.
"""
from __future__ import annotations

from ....domain.models import (
    DiagnosisResult,
    EvidenceBundle,
    ScenarioClassification,
)

AGENT_ID = "diagnosis_agent"


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


def run(
    classification: ScenarioClassification, evidence: EvidenceBundle
) -> DiagnosisResult:
    delivery = next(
        (s for s in evidence.settlement if s.direction == "DELIVER"), None
    )
    receive = next(
        (s for s in evidence.settlement if s.direction == "RECEIVE"), None
    )

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
        and shortfall > 0
        and incoming_qty >= shortfall
    )

    refs = _evidence_refs(evidence)
    conf = _avg_confidence(evidence)

    if (
        classification.scenario_label == "counterparty_short"
        and receive
        and not delivery
    ):
        return DiagnosisResult(
            reason_code="COUNTERPARTY_SHORT",
            is_firm_short=False,
            free_position_qty=free_qty,
            recommended_action="Monitor incoming receive; do not describe as firm short.",
            evidence_refs=refs,
            confidence=conf,
            notes="Counterparty pending delivery on a receive instruction.",
        )

    if classification.scenario_label == "rejected_or_unalleged":
        return DiagnosisResult(
            reason_code="COUNTERPARTY_REJECT",
            is_firm_short=False,
            recommended_action="Route for manual review / re-instruction as needed.",
            evidence_refs=refs,
            confidence=conf,
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
            evidence_refs=refs,
            confidence=conf,
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
            recommended_action="Track internal receive dependency before delivery commentary.",
            evidence_refs=refs,
            confidence=conf,
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
            evidence_refs=refs,
            confidence=conf,
        )

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
            action = (
                "Desk to confirm cover or release/realignment; do not speculate "
                "beyond evidence."
            )

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
            evidence_refs=refs,
            confidence=conf,
        )

    return DiagnosisResult(
        reason_code="NO_POSITION_SHORT" if delivery else "INSUFFICIENT_EVIDENCE",
        is_firm_short=False,
        delivery_obligation_qty=delivery_qty,
        free_position_qty=free_qty,
        recommended_action=(
            "Flag as insufficient evidence for firm-short commentary; analyst review."
        ),
        evidence_refs=refs,
        confidence=conf,
        notes="No firm-short evidence detected from current bundle.",
    )


def build_adk_agent():  # pragma: no cover - Phase 2 placeholder
    try:
        from google.adk.agents import LlmAgent  # type: ignore
    except Exception:
        return None
    return LlmAgent(
        name=AGENT_ID,
        instruction=(
            "Compare delivery obligation vs free inventory; identify pledged / "
            "segregated / encumbered inventory; consider incoming receives and "
            "netting mismatch. Output reason_code, recommended_action, and "
            "evidence references. Prefer 'insufficient_evidence' over speculation."
        ),
    )
