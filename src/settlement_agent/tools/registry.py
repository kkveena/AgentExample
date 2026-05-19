"""Tool registry.

The registry maps tool names (as referenced in YAML configs and future MCP
manifests) to their Python callables. Keeping a registry keeps the agent
code symmetric with how MCP toolsets will resolve tools by name in Phase 2.
"""
from __future__ import annotations

from typing import Callable

from ..domain.models import ToolCallResult
from .position_tool import TOOL_NAME as POSITION_TOOL, call_position_tool
from .reference_data_tool import (
    TOOL_NAME as REFERENCE_DATA_TOOL,
    call_reference_data_tool,
)
from .settlement_tool import TOOL_NAME as SETTLEMENT_TOOL, call_settlement_tool
from .trade_netting_tool import (
    TOOL_NAME as TRADE_NETTING_TOOL,
    call_trade_netting_tool,
)

ToolFn = Callable[..., ToolCallResult]

REGISTRY: dict[str, ToolFn] = {
    POSITION_TOOL: call_position_tool,
    SETTLEMENT_TOOL: call_settlement_tool,
    REFERENCE_DATA_TOOL: call_reference_data_tool,
    TRADE_NETTING_TOOL: call_trade_netting_tool,
}


def get_tool(name: str) -> ToolFn:
    if name not in REGISTRY:
        raise KeyError(f"Unknown tool: {name}")
    return REGISTRY[name]


def available_tools() -> list[str]:
    return sorted(REGISTRY.keys())
