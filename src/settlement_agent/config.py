"""Runtime configuration for the settlement_agent package.

Holds environment-driven defaults: data directory, feature flags for the
Phase 1 -> Phase 2 migration (LLM backend, REST/MCP tool backend, durable
session store), and any shared paths. Anything that varies between dev /
test / prod environments belongs here, not in YAML.
"""
from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT: Path = Path(__file__).resolve().parent
REPO_ROOT: Path = PACKAGE_ROOT.parents[1]
DATA_DIR: Path = Path(os.environ.get("SETTLEMENT_AGENT_DATA_DIR", REPO_ROOT / "data"))
CONFIG_DIR: Path = PACKAGE_ROOT / "config"

# Phase 2 feature flags (defaults keep Phase 1 behaviour).
USE_LLM_AGENTS: bool = os.environ.get("SETTLEMENT_AGENT_USE_LLM", "0") == "1"
TOOL_BACKEND: str = os.environ.get("SETTLEMENT_AGENT_TOOL_BACKEND", "csv")  # csv | rest | mcp
SESSION_STORE: str = os.environ.get("SETTLEMENT_AGENT_SESSION_STORE", "memory")  # memory | sqlite | redis
