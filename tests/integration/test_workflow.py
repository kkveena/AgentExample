"""End-to-end workflow tests."""
from settlement_agent.application.workflow import run_workflow_local


def test_firm_short_workflow_produces_evidence_and_diagnosis():
    state = run_workflow_local("SI-DLV-1001")
    assert state.classification is not None
    assert state.classification.scenario_label == "firm_short"
    assert state.evidence is not None
    assert state.evidence.position, "expected position evidence"
    assert state.evidence.settlement, "expected settlement evidence"
    assert state.diagnosis is not None
    assert state.diagnosis.reason_code == "FIRM_SHORT_FREE_INVENTORY"
    assert state.diagnosis.is_firm_short is True
    assert state.commentary is not None
    assert state.commentary.evidence_refs
    # Not final until approval recorded.
    assert state.approval.status == "pending"
    assert state.is_final() is False


def test_human_approval_marks_final():
    state = run_workflow_local("SI-DLV-1001", approval_status="approved", reviewer="ops_user")
    assert state.approval.status == "approved"
    assert state.approval.reviewer == "ops_user"
    assert state.is_final() is True


def test_rejected_approval_does_not_finalize():
    state = run_workflow_local("SI-DLV-1001", approval_status="rejected")
    assert state.is_final() is False


def test_workflow_runs_for_counterparty_short_case():
    state = run_workflow_local("SI-REC-1008")
    assert state.classification.scenario_label == "counterparty_short"
    assert state.diagnosis.reason_code == "COUNTERPARTY_SHORT"
    assert state.diagnosis.is_firm_short is False


def test_session_state_has_required_fields():
    state = run_workflow_local("SI-DLV-1001")
    for attr in (
        "run_id",
        "use_case_id",
        "workflow_version",
        "instruction_id",
        "classification",
        "evidence",
        "diagnosis",
        "commentary",
        "policy",
        "approval",
    ):
        assert hasattr(state, attr)


def test_no_internal_system_names_in_commentary():
    state = run_workflow_local("SI-DLV-1001")
    text = state.commentary.text.lower()
    for forbidden in ("oracle", "mainframe", "snowflake-prod", "sourcesystema"):
        assert forbidden not in text
