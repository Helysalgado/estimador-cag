"""Heuristic anchor extraction for evicted conversation turns."""

from __future__ import annotations

import re

ANCHOR_PATTERN = re.compile(
    r"(must|cannot|can't|required|deadline|budget|team|stack|security|login)\b[^.\n!?]{0,140}",
    re.IGNORECASE,
)


def detect_anchor_candidates(text: str) -> list[str]:
    """Extract concise anchor-like facts from free text."""
    candidates: list[str] = []
    for match in ANCHOR_PATTERN.finditer(text):
        value = match.group(0).strip().rstrip(".,;")
        if value and value not in candidates:
            candidates.append(value)
    return candidates
