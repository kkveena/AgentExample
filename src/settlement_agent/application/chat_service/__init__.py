"""Chat service: the firm-short root agent and its sub-agents.

This is the ADK-style enclosure for the workflow:

    root_agent (SequentialAgent in Phase 2)
      |- intake_agent
      |- evidence_agent
      |- diagnosis_agent
      |- commentary_agent
      |- policy_hitl_agent
"""
from .root_agent import build_root_agent, run as run_root  # noqa: F401
from .workflow import adk_available, run_workflow, run_workflow_local  # noqa: F401
