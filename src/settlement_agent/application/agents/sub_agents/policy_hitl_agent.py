"""Policy / Human-in-the-Loop sub-agent.

Validates evidence grounding and routes the draft to a human reviewer.
Phase 1 keeps approval as a simple parameter; Phase 2 will plug this
into a Control-Plane policy registry.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from ....domain.models import (
    CommentaryDraft,
    DiagnosisResult,
    EvidenceBundle,
    HumanApproval,
    PolicyResult,
)

AGENT_ID = "policy_hitl_agent"


FORBIDDEN_TOKENS: tuple[str, ...] = (
    # Generic placeholders for internal source-system names. Add real names
    # here if they ever leak into prompts/tests so this gate catches them.
    "SourceSystemA",
    "SourceSystemB",
    "ProdDB",
)


def run(
    commentary: CommentaryDraft,
    evidence: EvidenceBundle,
    diagnosis: DiagnosisResult,
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
    status: str,
    reviewer: Optional[str] = None,
    comments: Optional[str] = None,
) -> HumanApproval:
    if status not in {"approved", "rejected", "needs_edit", "pending"}:
        raise ValueError(f"Unsupported approval status: {status}")
    return HumanApproval(
        status=status,  # type: ignore[arg-type]
        reviewer=reviewer,
        comments=comments,
        decided_at=datetime.utcnow() if status != "pending" else None,
    )


def build_adk_agent():  # pragma: no cover - Phase 2 placeholder
    try:
        from google.adk.agents import LlmAgent  # type: ignore
    except Exception:
        return None
    return LlmAgent(
        name=AGENT_ID,
        instruction=(
            "Validate that every claim in the draft commentary maps to "
            "evidence. Reject unsupported numeric claims. Confirm human "
            "approval is required before this commentary is treated as "
            "final. QMA send remains human-controlled."
        ),
    )
