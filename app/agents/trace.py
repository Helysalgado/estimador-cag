"""Format agent steps as readable STEP traces."""

from __future__ import annotations

import json
from typing import Any


def summarize_observation(result: Any, *, max_chars: int = 500) -> str:
    text = json.dumps(result, ensure_ascii=False, default=str)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def format_step(
    step_number: int,
    *,
    reasoning: str,
    action: str,
    observation: str,
) -> str:
    reason = reasoning.strip() or "(no reasoning summary emitted)"
    return (
        f"STEP {step_number}\n"
        f"reasoning: {reason}\n"
        f"action: {action}\n"
        f"observation: {observation}"
    )


def format_action(name: str, arguments: dict[str, Any]) -> str:
    try:
        args_repr = json.dumps(arguments, ensure_ascii=False, sort_keys=True)
    except TypeError:
        args_repr = str(arguments)
    return f"{name}({args_repr})"
