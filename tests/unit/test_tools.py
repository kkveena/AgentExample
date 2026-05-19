"""Tool-level unit tests."""
from settlement_agent.domain.models import (
    PositionToolInput,
    ReferenceDataToolInput,
    SettlementToolInput,
    TradeNettingToolInput,
)
from settlement_agent.domain.tools.position_tool import call_position_tool
from settlement_agent.domain.tools.reference_data_tool import call_reference_data_tool
from settlement_agent.domain.tools.registry import REGISTRY, available_tools
from settlement_agent.domain.tools.settlement_tool import call_settlement_tool
from settlement_agent.domain.tools.trade_netting_tool import call_trade_netting_tool


def test_position_tool_returns_firm_short_record():
    result = call_position_tool(
        PositionToolInput(account_id="ACC-DLV-001", security_id="SEC-US-0001")
    )
    assert result.record_count == 1
    rec = result.records[0]
    assert rec["free_position_qty"] == 85000.0
    assert rec["pending_delivery_qty"] == 150000.0


def test_settlement_tool_by_instruction_id():
    result = call_settlement_tool(
        SettlementToolInput(instruction_id="SI-DLV-1001")
    )
    assert result.record_count == 1
    assert result.records[0]["direction"] == "DELIVER"


def test_reference_data_tool_by_security():
    result = call_reference_data_tool(
        ReferenceDataToolInput(security_id="SEC-US-0001")
    )
    assert result.record_count >= 1
    assert result.records[0]["security_description"].startswith("Alpha")


def test_trade_netting_tool_filters():
    result = call_trade_netting_tool(
        TradeNettingToolInput(account_id="ACC-DLV-001", security_id="SEC-US-0001")
    )
    assert result.record_count >= 1


def test_registry_lists_all_phase1_tools():
    tools = available_tools()
    assert {
        "position_tool",
        "settlement_tool",
        "reference_data_tool",
        "trade_netting_tool",
    }.issubset(set(tools))
    for name in tools:
        assert callable(REGISTRY[name])
