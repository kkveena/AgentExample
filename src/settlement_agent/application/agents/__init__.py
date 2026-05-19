"""ADK-style agent enclosure: root + sub-agents.

This package is the agentic engine. It is intentionally separate from
:mod:`settlement_agent.application.chat_service` so that any service
(chat, REST, CLI, batch, eval runner) can invoke the agents directly
without going through a chat-style entry point.

Layout::

    root_agent (SequentialAgent in Phase 2)
      ├── intake_agent
      ├── evidence_agent
      ├── diagnosis_agent
      ├── commentary_agent
      └── policy_hitl_agent
"""
from .root_agent import build_root_agent, run as run_root  # noqa: F401
