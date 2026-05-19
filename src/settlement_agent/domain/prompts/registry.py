"""Prompt registry backed by ``config/prompts/prompts.yaml``."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from ...infrastructure.config_loader import load_prompts


@lru_cache(maxsize=None)
def _index() -> dict[str, dict]:
    cfg = load_prompts()
    return {p["id"]: p for p in cfg.get("prompts", [])}


def get_prompt(prompt_id: str) -> Optional[dict]:
    """Return the prompt dict for ``prompt_id`` or ``None``."""
    return _index().get(prompt_id)


def list_prompts() -> list[str]:
    return sorted(_index().keys())
