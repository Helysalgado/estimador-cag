"""Lightweight critic pass for Actor-Critic-Boss mode."""

from __future__ import annotations


def critic_review(*, user_turn: str, candidate_text: str) -> dict[str, object]:
    """Return deterministic critique signals for the boss."""
    issues: list[dict[str, str]] = []
    if len(candidate_text.strip()) < 40:
        issues.append({"severity": "high", "message": "Response too short for estimation quality."})
    if "Totals" not in candidate_text and "total" not in candidate_text.lower():
        issues.append({"severity": "medium", "message": "Missing explicit totals line."})
    if "phase" not in candidate_text.lower() and "discovery" not in candidate_text.lower():
        issues.append({"severity": "medium", "message": "Phase breakdown may be incomplete."})
    verdict = "accept" if not any(issue["severity"] == "high" for issue in issues) else "iterate"
    return {
        "verdict": verdict,
        "issues": issues,
        "confidence": 0.72 if verdict == "accept" else 0.61,
        "prompt_excerpt": user_turn[:120],
    }
