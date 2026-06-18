from app.schemas.estimation import DetailLevel, EstimationRequest, OutputFormat, ProjectType
from app.services import llm_service


def _sample_request() -> EstimationRequest:
    return EstimationRequest(
        description=(
            "A small B2B SaaS to manage employee equipment loans across teams "
            "with role-based access and audit trail."
        ),
        project_type=ProjectType.WEB_SAAS,
        detail_level=DetailLevel.MEDIUM,
        output_format=OutputFormat.PHASES_TABLE,
    )


def test_estimate_from_request_uses_cache_hit_after_miss(monkeypatch):
    calls = {"count": 0}
    cache_store = {}

    class FakeCache:
        def get(self, key):
            return cache_store.get(key)

        def set(self, key, value, ttl_seconds=None):
            _ = ttl_seconds
            cache_store[key] = value

    def fake_generate_sync(**kwargs):  # noqa: ANN003
        calls["count"] += 1
        _ = kwargs
        return {
            "estimation": "| phase | cost |",
            "model": "gpt-4o-mini",
            "provider": "openai",
            "timestamp": "2026-01-01T00:00:00",
        }

    monkeypatch.setattr(llm_service, "cache", FakeCache())
    monkeypatch.setattr(llm_service, "generate_sync", fake_generate_sync)

    request = _sample_request()
    first = llm_service.estimate_from_request(request)
    second = llm_service.estimate_from_request(request)

    assert first.text == second.text == "| phase | cost |"
    assert first.prompt_version == "v1"
    assert calls["count"] == 1
