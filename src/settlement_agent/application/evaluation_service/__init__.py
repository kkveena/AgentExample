"""Evaluation service.

Runs the Phase 1 eval suite over the firm-short workflow and reports
per-case pass/fail across scenario classification, reason code, tool
coverage, evidence fields, commentary constraints, no-auto-QMA, and
human-approval requirement.
"""
from .eval_runner import EvalResult, run_eval_case, run_eval_suite  # noqa: F401
