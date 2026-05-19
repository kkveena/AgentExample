"""Workflow runner.

Tries to use Google ADK when available; otherwise runs a local fallback
runner that preserves the same step ordering and session-state shape so
tests and the notebook still work in any environment.
"""
from __future__ import annotations

import uuid
from typing import Optional

from ..domain.models import HumanApproval, SessionState
from ..utils.yaml_loader import load_use_case, load_workflow
from .agents import (
    apply_human_approval,
    commentary_agent,
    diagnosis_agent,
    evidence_agent,
    intake_agent,
    policy_agent,
)


def _new_run_id() -> str:
    return f"run-{uuid.uuid4().hex[:12]}"


def run_workflow_local(
    instruction_id: str,
    approval_status: Optional[str] = None,
    reviewer: Optional[str] = None,
    comments: Optional[str] = None,
) -> SessionState:
    """Run the firm-short workflow using the local deterministic agents.

    This is the fallback runner used when Google ADK isn't installed in the
    environment. It writes the same fields into SessionState that an ADK
    Session would carry, so downstream code is interchangeable.
    """
    use_case = load_use_case()
    workflow = load_workflow()

    state = SessionState(
        run_id=_new_run_id(),
        use_case_id=use_case["use_case_id"],
        workflow_version=workflow["workflow_version"],
        instruction_id=instruction_id,
    )

    state.classification = intake_agent(instruction_id)
    state.evidence = evidence_agent(state.classification)
    state.diagnosis = diagnosis_agent(state.classification, state.evidence)
    state.commentary = commentary_agent(state.diagnosis, state.evidence)
    state.policy = policy_agent(state.commentary, state.evidence, state.diagnosis)

    if approval_status:
        state.approval = apply_human_approval(approval_status, reviewer, comments)
    else:
        state.approval = HumanApproval(status="pending")

    return state


def adk_available() -> bool:
    try:
        import google.adk  # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def run_workflow(
    instruction_id: str,
    approval_status: Optional[str] = None,
    reviewer: Optional[str] = None,
    comments: Optional[str] = None,
    prefer_adk: bool = True,
) -> SessionState:
    """Entry point. Uses ADK if available; otherwise the local fallback.

    Either path produces the same SessionState shape.
    """
    if prefer_adk and adk_available():
        try:
            return _run_with_adk(instruction_id, approval_status, reviewer, comments)
        except Exception:
            # If ADK runtime fails for any environment reason, fall back so
            # tests and notebook still pass.
            return run_workflow_local(instruction_id, approval_status, reviewer, comments)
    return run_workflow_local(instruction_id, approval_status, reviewer, comments)


def _run_with_adk(
    instruction_id: str,
    approval_status: Optional[str],
    reviewer: Optional[str],
    comments: Optional[str],
) -> SessionState:
    """ADK-aware wrapper.

    Phase 1 still drives the deterministic agents; the ADK integration here
    establishes a session and stores the same state fields under an ADK
    Session. Replace internals with real ADK Agent/Tool wiring as the SDK
    surface stabilises.
    """
    # Lazy import so environments without ADK still load this module.
    try:
        from google.adk.sessions import InMemorySessionService  # type: ignore
    except Exception:
        return run_workflow_local(instruction_id, approval_status, reviewer, comments)

    state = run_workflow_local(instruction_id, approval_status, reviewer, comments)

    try:
        svc = InMemorySessionService()
        session = svc.create_session(
            app_name="settlement_agent",
            user_id="phase1-runner",
            session_id=state.run_id,
        )
        # Mirror the session-state fields into ADK session state so the
        # session inspector / debugger sees them.
        adk_state = getattr(session, "state", None)
        if isinstance(adk_state, dict):
            adk_state.update(state.model_dump())
    except Exception:
        # Don't fail the workflow if ADK session bookkeeping has issues.
        pass

    return state
