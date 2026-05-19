"""YAML configuration validation tests."""
from settlement_agent.infrastructure import config_loader as yaml_loader


def test_all_required_configs_present_and_valid():
    results = yaml_loader.validate_all_configs()
    for path, ok in results.items():
        assert ok, f"config invalid: {path}"


def test_workflow_steps_match_known_agents():
    workflow = yaml_loader.load_workflow()
    agents = {a["id"] for a in yaml_loader.load_agents()["agents"]}
    for step in workflow["steps"]:
        assert step["agent"] in agents


def test_tools_yaml_lists_phase1_tools():
    tools = yaml_loader.load_tools_config()["tools"]
    names = {t["name"] for t in tools}
    assert {
        "position_tool",
        "settlement_tool",
        "reference_data_tool",
        "trade_netting_tool",
    } == names


def test_use_case_phase_is_one():
    uc = yaml_loader.load_use_case()
    assert uc["phase"] == 1
    assert "automatic_qma_send" in uc.get("out_of_scope", [])


def test_policy_requires_human_approval():
    policy = yaml_loader.load_policy()
    assert policy["approval"]["required"] is True
    assert "approved" in policy["approval"]["allowed_states"]
    assert "rejected" in policy["approval"]["allowed_states"]
    assert "needs_edit" in policy["approval"]["allowed_states"]
