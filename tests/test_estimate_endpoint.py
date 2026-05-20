"""Tests for POST /api/v1/estimate."""

from __future__ import annotations

from typing import Any

import pytest

from app.schemas.estimation import EstimationResponse

VALID_PAYLOAD = {
    "description": "A small B2B SaaS to manage employee equipment loans across teams.",
    "project_type": "web_saas",
    "detail_level": "medium",
    "output_format": "phases_table",
}


class FakeEstimateFromRequest:
    """Records calls and returns a canned EstimationResponse."""

    def __init__(self, response_text: str = "fake estimation") -> None:
        self.response_text = response_text
        self.calls: list[dict[str, Any]] = []

    def __call__(self, request, **kwargs: Any) -> EstimationResponse:  # noqa: ANN001
        self.calls.append({"request": request, **kwargs})
        return EstimationResponse(text=self.response_text, prompt_version="v1")


@pytest.fixture
def fake_estimate(monkeypatch):
    fake = FakeEstimateFromRequest()
    monkeypatch.setattr(
        "app.routers.estimations.estimate_from_request",
        fake,
    )
    return fake


def test_valid_payload_returns_text_and_prompt_version(client, fake_estimate) -> None:
    response = client.post("/api/v1/estimate", json=VALID_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "fake estimation"
    assert body["prompt_version"] == "v1"


def test_endpoint_receives_typed_request(client, fake_estimate) -> None:
    client.post("/api/v1/estimate", json=VALID_PAYLOAD)
    assert len(fake_estimate.calls) == 1
    request = fake_estimate.calls[0]["request"]
    assert request.description == VALID_PAYLOAD["description"]
    assert request.project_type.value == "web_saas"


def test_missing_project_type_returns_422(client, fake_estimate) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "project_type"}
    response = client.post("/api/v1/estimate", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(err["loc"][-1] == "project_type" for err in detail)


def test_invalid_enum_value_returns_422(client, fake_estimate) -> None:
    payload = {**VALID_PAYLOAD, "project_type": "not_a_real_enum"}
    response = client.post("/api/v1/estimate", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(err["loc"][-1] == "project_type" for err in detail)


def test_short_description_returns_422(client, fake_estimate) -> None:
    payload = {**VALID_PAYLOAD, "description": "too short"}
    response = client.post("/api/v1/estimate", json=payload)
    assert response.status_code == 422


def test_endpoint_passes_separate_system_and_user_via_service(client, monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_generate_sync(**kwargs):  # noqa: ANN003
        captured["system_prompt"] = kwargs["system_prompt"]
        captured["user_message"] = kwargs["user_message"]
        return {
            "estimation": "from llm",
            "model": "gpt-4o-mini",
            "provider": "openai",
            "timestamp": "2026-01-01T00:00:00",
        }

    class FakeCache:
        def get(self, key):  # noqa: ANN001
            return None

        def set(self, key, value, ttl_seconds=None):  # noqa: ANN001
            pass

    monkeypatch.setattr("app.services.llm_service.generate_sync", fake_generate_sync)
    monkeypatch.setattr("app.services.llm_service.cache", FakeCache())

    response = client.post("/api/v1/estimate", json=VALID_PAYLOAD)
    assert response.status_code == 200
    assert VALID_PAYLOAD["description"] in captured["user_message"]
    assert VALID_PAYLOAD["description"] not in captured["system_prompt"]
    assert "senior project estimator" in captured["system_prompt"].lower()
