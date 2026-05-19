"""Commentary sub-agent.

Drafts factual, evidence-grounded commentary. Phase 2: ADK ``LlmAgent``
that calls a prompt-grounded model with the same evidence bundle and
diagnosis as input.
"""
from __future__ import annotations

from ....domain.models import CommentaryDraft, DiagnosisResult, EvidenceBundle

AGENT_ID = "commentary_agent"


def run(diagnosis: DiagnosisResult, evidence: EvidenceBundle) -> CommentaryDraft:
    ref = evidence.reference[0] if evidence.reference else None
    security_desc = ref.security_description if ref else "the referenced security"

    delivery = next(
        (s for s in evidence.settlement if s.direction == "DELIVER"), None
    )
    timestamp = (
        delivery.last_status_ts
        if delivery and delivery.last_status_ts
        else (
            evidence.position[0].snapshot_ts
            if evidence.position
            else "the latest snapshot"
        )
    )

    rc = diagnosis.reason_code
    if rc in {
        "FIRM_SHORT_FREE_INVENTORY",
        "FREE_INVENTORY_ENCUMBERED",
        "REALIGNMENT_REQUIRED",
    }:
        text = (
            f"Delivery remains pending for {security_desc}. Free position is "
            f"below the pending delivery quantity as of {timestamp}. "
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


def build_adk_agent():  # pragma: no cover - Phase 2 placeholder
    try:
        from google.adk.agents import LlmAgent  # type: ignore
    except Exception:
        return None
    return LlmAgent(
        name=AGENT_ID,
        instruction=(
            "Generate concise factual commentary. Every material claim must "
            "reference retrieved evidence. Do not expose internal system "
            "names. Do not invent quantities, statuses, or timestamps. Prefer "
            "'insufficient evidence' when facts are missing. Do NOT send QMA."
        ),
    )
