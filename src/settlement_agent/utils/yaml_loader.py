"""YAML config loading helpers."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_ROOT = Path(__file__).resolve().parents[1] / "config"


def config_root() -> Path:
    return CONFIG_ROOT


@lru_cache(maxsize=None)
def load_yaml(relative_path: str) -> Any:
    """Load a YAML file relative to settlement_agent/config/."""
    path = CONFIG_ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_use_case(use_case_filename: str = "uc01_firm_short.yaml") -> dict:
    return load_yaml(f"use_cases/{use_case_filename}")


def load_agents() -> dict:
    return load_yaml("agents/agents.yaml")


def load_workflow(filename: str = "firm_short_workflow.yaml") -> dict:
    return load_yaml(f"workflows/{filename}")


def load_prompts() -> dict:
    return load_yaml("prompts/prompts.yaml")


def load_tools_config() -> dict:
    return load_yaml("tools/tools.yaml")


def load_policy() -> dict:
    return load_yaml("policies/policy.yaml")


def load_eval_suite(filename: str = "eval_cases.yaml") -> dict:
    return load_yaml(f"evals/{filename}")


REQUIRED_TOP_LEVEL_KEYS = {
    "agents/agents.yaml": {"version", "agents"},
    "workflows/firm_short_workflow.yaml": {
        "workflow_id",
        "workflow_version",
        "use_case_id",
        "steps",
    },
    "prompts/prompts.yaml": {"version", "prompts"},
    "tools/tools.yaml": {"version", "tools"},
    "policies/policy.yaml": {"policy_id", "constraints", "approval"},
    "evals/eval_cases.yaml": {"eval_suite_id", "cases"},
}


def validate_all_configs() -> dict[str, bool]:
    """Validate that each config has its required top-level keys."""
    results: dict[str, bool] = {}
    for rel, required in REQUIRED_TOP_LEVEL_KEYS.items():
        cfg = load_yaml(rel)
        results[rel] = required.issubset(cfg.keys()) if isinstance(cfg, dict) else False
    return results
