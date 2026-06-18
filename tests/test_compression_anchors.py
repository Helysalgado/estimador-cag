"""Tests for heuristic anchor extraction on evicted turns."""

from app.sessions.compression.anchors import detect_anchor_candidates


def test_detect_anchor_candidates_finds_budget_and_stack():
    text = "Budget is locked at 80k EUR. Stack must include PostgreSQL and Redis."
    candidates = detect_anchor_candidates(text)
    assert candidates
    joined = " ".join(candidates).lower()
    assert "budget" in joined
    assert "stack" in joined or "postgresql" in joined


def test_detect_anchor_candidates_ignores_generic_feature_chatter():
    text = "Polish the dashboard widgets and refine the colour palette next sprint."
    candidates = detect_anchor_candidates(text)
    assert not candidates
