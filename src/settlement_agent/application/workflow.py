"""Workflow entry point.

Thin wrapper around the root agent. Tries to mirror the run into a
Google ADK session when ADK is installed; otherwise stays on the local
deterministic root agent. Either path produces the same ``SessionState``.
"""
from __future__ import annotations

from typing import Optional

from ..agents.root_agent import run as run_root_agent
from ..domain.models import SessionState


def adk_available() -> bool:
    try:
        import google.adk  # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def run_workflow_local(
    instruction_id: str,
    approval_status: Optional[str] = None,
    reviewer: Optional[str] = None,
    comments: Optional[str] = None,
) -> SessionState:
    """Run the firm-short workflow using the local deterministic root agent."""
    return run_root_agent(instruction_id, approval_status, reviewer, comments)


def run_workflow(
    instruction_id: str,
    approval_status: Optional[str] = None,
    reviewer: Optional[str] = None,
    comments: Optional[str] = None,
    prefer_adk: bool = True,
) -> SessionState:
    """Public entry point. Uses ADK session bookkeeping when available."""
    state = run_workflow_local(instruction_id, approval_status, reviewer, comments)

    if prefer_adk and adk_available():
        try:
            _mirror_into_adk_session(state)
        except Exception:
            # ADK session bookkeeping is best-effort in Phase 1.
            pass
    return state


def _mirror_into_adk_session(state: SessionState) -> None:
    """Copy SessionState into a Google ADK in-memory session for inspection."""
    from google.adk.sessions import InMemorySessionService  # type: ignore

    svc = InMemorySessionService()
    session = svc.create_session(
        app_name="settlement_agent",
        user_id="phase1-runner",
        session_id=state.run_id,
    )
    adk_state = getattr(session, "state", None)
    if isinstance(adk_state, dict):
        adk_state.update(state.model_dump())
