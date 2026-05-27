"""Simple cumulative summarizer for evicted session turns."""

from __future__ import annotations


def append_summary(current_summary: str, chunk: str, *, max_chars: int) -> str:
    """Append an evicted chunk to running summary and trim."""
    chunk = chunk.strip()
    if not chunk:
        return current_summary
    if current_summary:
        merged = f"{current_summary}\n- {chunk}"
    else:
        merged = f"- {chunk}"
    if len(merged) <= max_chars:
        return merged
    return merged[-max_chars:]
