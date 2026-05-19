"""Domain prompt registry.

Phase 1 prompts live in ``settlement_agent/config/prompts/prompts.yaml``.
This module exposes a thin lookup over that YAML so Phase 2 LLM-backed
sub-agents can resolve prompts by id without hard-coding strings.
"""
from .registry import get_prompt, list_prompts  # noqa: F401
