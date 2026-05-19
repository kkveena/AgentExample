"""Eval runner tests."""
from settlement_agent.application.evaluation_service.eval_runner import run_eval_suite


def test_eval_suite_runs_and_all_pass():
    results = run_eval_suite()
    assert results, "eval suite returned no results"
    failures = [
        (r.scenario_id, r.checks, r.notes) for r in results if not r.passed
    ]
    assert not failures, f"eval failures: {failures}"


def test_eval_suite_has_required_scenarios():
    results = run_eval_suite()
    ids = {r.scenario_id for r in results}
    assert {
        "eval_firm_short_confirmed",
        "eval_incoming_receive_covers",
        "eval_insufficient_evidence",
        "eval_counterparty_short",
        "eval_netting_mismatch",
    }.issubset(ids)
