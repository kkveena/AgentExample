"""Root agent for the firm-short workflow.

Composes the five sub-agents into a sequential ADK-style tree. In Phase
1 the root is a deterministic orchestrator that writes each sub-agent's
output into ``SessionState``; in Phase 2 it becomes a Google ADK
``SequentialAgent`` whose ``sub_agents=[...]`` is exactly the list
built by :func:`build_root_agent`.
"""
from __future__ import annotations

import uuid
from typing import Optional

from ...domain.models import HumanApproval, SessionState
from ...infrastructure.config_loader import load_use_case, load_workflow
from .sub_agents import commentary_agent as commentary
from .sub_agents import diagnosis_agent as diagnosis
from .sub_agents import evidence_agent as evidence
from .sub_agents import intake_agent as intake
from .sub_agents import policy_hitl_agent as policy_hitl

ROOT_AGENT_ID = "firm_short_root_agent"


def _new_run_id() -> str:
    return f"run-{uuid.uuid4().hex[:12]}"


def run(
    instruction_id: str,
    approval_status: Optional[str] = None,
    reviewer: Optional[str] = None,
    comments: Optional[str] = None,
) -> SessionState:
    """Execute the firm-short workflow deterministically.

    The output ``SessionState`` shape is identical to what an ADK
    ``Session`` will carry once the root agent is migrated to a
    Google ADK ``SequentialAgent``.
    """
    use_case = load_use_case()
    workflow = load_workflow()

    state = SessionState(
        run_id=_new_run_id(),
        use_case_id=use_case["use_case_id"],
        workflow_version=workflow["workflow_version"],
        instruction_id=instruction_id,
    )

    state.classification = intake.run(instruction_id)
    state.evidence = evidence.run(state.classification)
    state.diagnosis = diagnosis.run(state.classification, state.evidence)
    state.commentary = commentary.run(state.diagnosis, state.evidence)
    state.policy = policy_hitl.run(state.commentary, state.evidence, state.diagnosis)

    if approval_status:
        state.approval = policy_hitl.apply_human_approval(
            approval_status, reviewer, comments
        )
    else:
        state.approval = HumanApproval(status="pending")

    return state


def build_root_agent():  # pragma: no cover - Phase 2 placeholder
    """Phase 2: returns an ADK ``SequentialAgent`` wrapping the sub-agents.

    Each sub-agent module exposes ``build_adk_agent()`` which returns an
    ``LlmAgent`` (or ``None`` when ADK isn't installed). This function
    composes them into a single root tree.
    """
    try:
        from google.adk.agents import SequentialAgent  # type: ignore
    except Exception:
        return None

    sub_agents = [
        a
        for a in (
            intake.build_adk_agent(),
            evidence.build_adk_agent(),
            diagnosis.build_adk_agent(),
            commentary.build_adk_agent(),
            policy_hitl.build_adk_agent(),
        )
        if a is not None
    ]
    if not sub_agents:
        return None
    return SequentialAgent(name=ROOT_AGENT_ID, sub_agents=sub_agents)
