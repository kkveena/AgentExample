"""Chat service.

The chat-interaction surface for the firm-short workflow. A chat turn is
a single instruction request that flows through the agentic engine in
:mod:`settlement_agent.application.agents` and returns a ``SessionState``.

Phase 1 exposes a single entry point (``run_workflow``); Phase 2 may grow
this into a multi-turn conversation handler, slot-filling for missing
fields, and follow-up prompts.
"""
from .workflow import adk_available, run_workflow, run_workflow_local  # noqa: F401
