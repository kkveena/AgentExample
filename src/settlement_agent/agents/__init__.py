"""Settlement-agent ADK-style agent tree.

Phase 1 layout mirrors a Google ADK root-agent / sub-agent enclosure:

    root_agent (SequentialAgent-like orchestrator)
      ├── intake_agent
      ├── evidence_agent
      ├── diagnosis_agent
      ├── commentary_agent
      └── policy_hitl_agent

Each sub-agent module exposes:
  - a deterministic ``run(...)`` function used by the local fallback runner
    and by tests / evals / notebook in Phase 1, and
  - an optional ADK ``Agent``/``LlmAgent`` placeholder for Phase 2 wire-up.
"""

from .root_agent import build_root_agent, run as run_root  # noqa: F401
