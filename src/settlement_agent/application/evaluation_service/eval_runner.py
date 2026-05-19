"""Eval runner for Phase 1 firm-short reference workflow."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any

from ...domain.models import SessionState
from ...infrastructure.config_loader import load_eval_suite
from ..chat_service.workflow import run_workflow_local


@dataclass
class EvalResult:
    scenario_id: str
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _evidence_field_present(state: SessionState, field_name: str) -> bool:
    """True if any record in the bundle exposes the requested field."""
    if not state.evidence:
        return False
    field_groups = [
        state.evidence.position,
        state.evidence.settlement,
        state.evidence.reference,
        state.evidence.trade_netting,
    ]
    for group in field_groups:
        for rec in group:
            if hasattr(rec, field_name) and getattr(rec, field_name) is not None:
                return True
    return False


def _has_unsupported_numbers(text: str, evidence_refs: list[str]) -> bool:
    """Phase 1 heuristic: any numeric token > 2 digits should map to evidence.

    The commentary template doesn't inject raw numbers in Phase 1, so we
    simply check that no large numeric tokens leak through without being
    bound to evidence_refs.
    """
    big_numbers = re.findall(r"\b\d{3,}\b", text)
    return bool(big_numbers) and not evidence_refs


def run_eval_case(case: dict[str, Any]) -> EvalResult:
    instruction_id = case["instruction_id"]
    expected = case["expected"]

    state = run_workflow_local(instruction_id, approval_status="approved")
    checks: dict[str, bool] = {}
    notes: list[str] = []

    # Scenario classification check.
    checks["scenario_label"] = (
        state.classification is not None
        and state.classification.scenario_label == expected["scenario_label"]
    )

    # Reason code check.
    checks["reason_code"] = (
        state.diagnosis is not None
        and state.diagnosis.reason_code == expected["reason_code"]
    )

    # Tools called.
    tools_called = state.evidence.tools_called() if state.evidence else []
    required_tools = expected.get("tools_called", [])
    checks["tools_called"] = all(t in tools_called for t in required_tools)
    if not checks["tools_called"]:
        notes.append(f"expected {required_tools}, got {tools_called}")

    # Evidence bundle exists.
    checks["evidence_bundle_present"] = state.evidence is not None and bool(
        tools_called
    )

    # Required evidence fields.
    required_fields = expected.get("evidence_fields_required", [])
    if required_fields:
        missing = [
            f for f in required_fields if not _evidence_field_present(state, f)
        ]
        checks["evidence_fields"] = not missing
        if missing:
            notes.append(f"missing evidence fields: {missing}")
    else:
        checks["evidence_fields"] = True

    # Commentary checks.
    if state.commentary:
        checks["commentary_has_evidence_refs"] = bool(state.commentary.evidence_refs)
        checks["commentary_no_unsupported_numbers"] = not _has_unsupported_numbers(
            state.commentary.text, state.commentary.evidence_refs
        )
    else:
        checks["commentary_has_evidence_refs"] = False
        checks["commentary_no_unsupported_numbers"] = False

    # QMA send must not be performed automatically: in Phase 1 we never have
    # a "qma_sent" flag, so presence of any such field would fail this.
    checks["no_auto_qma_send"] = "qma_sent" not in state.extras

    # Human approval required.
    checks["approval_required"] = state.policy is not None and state.policy.requires_human_approval

    passed = all(checks.values())
    return EvalResult(
        scenario_id=case["scenario_id"],
        passed=passed,
        checks=checks,
        notes=notes,
    )


def run_eval_suite(verbose: bool = False) -> list[EvalResult]:
    suite = load_eval_suite()
    results = [run_eval_case(c) for c in suite["cases"]]
    if verbose:
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            print(f"[{status}] {r.scenario_id}")
            for k, v in r.checks.items():
                print(f"   - {k}: {v}")
            for n in r.notes:
                print(f"   note: {n}")
    return results


def main() -> int:
    results = run_eval_suite(verbose=True)
    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
    }
    print("\nSummary:", json.dumps(summary))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
