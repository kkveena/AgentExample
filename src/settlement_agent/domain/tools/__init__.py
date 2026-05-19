"""Domain tool contracts and Phase 1 CSV-backed implementations.

Phase 2 will plug REST / MCP adapters behind these same Pydantic
contracts via the registry; agents should never call adapters directly.
"""
from .registry import REGISTRY, available_tools, get_tool  # noqa: F401
