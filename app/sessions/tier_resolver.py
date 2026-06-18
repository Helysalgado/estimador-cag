"""Resolve conversational response tier with explainable rules."""

from __future__ import annotations

from app.services.sessions import ProjectMetadata

ALLOWED_TIERS = frozenset({"default", "executive", "pm", "developer"})


def resolve_tier(
    *,
    user_turn: str,
    metadata: ProjectMetadata,
    tier_override: str | None = None,
) -> tuple[str, str]:
    """Return tier and rule id used to resolve it."""
    if tier_override and tier_override in ALLOWED_TIERS:
        return tier_override, "override"
    text = user_turn.lower()
    if "cto" in text or "board" in text or "executive" in text:
        return "executive", "audience_executive"
    if "technical" in text or "api" in text or "architecture" in text:
        return "developer", "audience_technical"
    if metadata.assumed_team_size is not None and metadata.assumed_team_size <= 4:
        return "pm", "small_team_pm"
    return "default", "default_rule"
