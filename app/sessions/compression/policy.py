"""Compression policy for evicted conversational turns."""

from __future__ import annotations

from app.sessions.compression.anchors import detect_anchor_candidates
from app.sessions.compression.summarizer import append_summary


def compress_evicted_pairs(
    evicted_pairs: list[tuple[object, object]],
    *,
    current_summary: str,
    max_summary_chars: int,
    max_anchors: int,
    current_turn: int,
) -> tuple[str, list[dict[str, object]]]:
    """Promote anchor facts and append summary for evicted turns."""
    summary = current_summary
    anchors: list[dict[str, object]] = []
    for user_msg, assistant_msg in evicted_pairs:
        user_text = getattr(user_msg, "content", "")
        assistant_text = getattr(assistant_msg, "content", "")
        summary = append_summary(
            summary,
            f"user: {user_text[:240]} | assistant: {assistant_text[:240]}",
            max_chars=max_summary_chars,
        )
        for candidate in detect_anchor_candidates(f"{user_text}\n{assistant_text}"):
            anchors.append(
                {
                    "text": candidate,
                    "source_turn": max(current_turn - 1, 0),
                    "confidence": 0.55,
                }
            )
    if len(anchors) > max_anchors:
        anchors = anchors[-max_anchors:]
    return summary, anchors
