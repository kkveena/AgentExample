"""Smoke tests for CSV loading and data_dictionary consistency."""
from settlement_agent.infrastructure import csv_loader


def test_positions_load():
    rows = csv_loader.load_positions()
    assert len(rows) > 0
    assert "free_position_qty" in rows[0]


def test_settlements_load():
    rows = csv_loader.load_settlements()
    assert any(r["instruction_id"] == "SI-DLV-1001" for r in rows)


def test_reference_load():
    rows = csv_loader.load_reference()
    assert any(r["security_id"] == "SEC-US-0001" for r in rows)


def test_trade_netting_load():
    rows = csv_loader.load_trade_netting()
    assert any(r["trade_id"] == "TRD-5001" for r in rows)


def test_scenario_manifest_load():
    rows = csv_loader.load_scenario_manifest()
    assert any(r["case_id"] == "UC-01-FIRM-SHORT" for r in rows)


def test_data_dictionary_lists_all_csvs():
    rows = csv_loader.load_data_dictionary()
    listed = {r["file"] for r in rows}
    required = {
        "position_data.csv",
        "settlement_data.csv",
        "reference_data.csv",
        "trade_netting_data.csv",
        "scenario_manifest.csv",
    }
    assert required.issubset(listed)
