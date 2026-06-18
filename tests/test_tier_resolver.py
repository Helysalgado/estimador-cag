from app.services.sessions import ProjectMetadata
from app.sessions.tier_resolver import resolve_tier


def test_tier_override_wins():
    tier, rule = resolve_tier(user_turn="anything", metadata=ProjectMetadata(), tier_override="developer")
    assert tier == "developer"
    assert rule == "override"


def test_tier_resolver_detects_executive_audience():
    tier, rule = resolve_tier(user_turn="Need summary for CTO and board.", metadata=ProjectMetadata())
    assert tier == "executive"
    assert rule == "audience_executive"
