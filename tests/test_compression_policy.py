"""Tests for summary growth and anchor promotion on eviction."""

from __future__ import annotations

from types import SimpleNamespace

from app.sessions.compression.policy import compress_evicted_pairs
from app.sessions.compression.summarizer import append_summary


def test_append_summary_respects_max_chars():
    summary = append_summary("", "first chunk", max_chars=40)
    summary = append_summary(summary, "second chunk that makes the summary longer", max_chars=40)
    assert len(summary) <= 40
    assert summary.endswith("longer")


def test_compress_evicted_pairs_promotes_anchors_and_summary():
    evicted = [
        (
            SimpleNamespace(content="Budget must stay under 80k EUR for phase one."),
            SimpleNamespace(content="Acknowledged; we will size phases accordingly."),
        )
    ]
    summary, anchors = compress_evicted_pairs(
        evicted,
        current_summary="",
        max_summary_chars=500,
        max_anchors=5,
        current_turn=4,
    )
    assert "Budget must" in summary
    assert anchors
    assert any("budget" in str(anchor["text"]).lower() for anchor in anchors)
