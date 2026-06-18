"""Boss decision policy for Actor-Critic-Boss mode."""

from __future__ import annotations


def boss_decide(*, critic: dict[str, object], iteration: int) -> tuple[str, str]:
    """Return (verdict, note) from critic payload."""
    verdict = str(critic.get("verdict") or "accept")
    issues = critic.get("issues") or []
    if verdict == "iterate":
        return "iterate", f"iteration_{iteration}: refine {len(issues)} issues"
    return "accept", f"iteration_{iteration}: accepted"
