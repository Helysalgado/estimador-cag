from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from openai import RateLimitError

from app.db.session import get_db_session
from app.main import app


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client_with_db(mock_session: AsyncMock) -> TestClient:
    async def _override_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = _override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_search_returns_ranked_results(
    client_with_db: TestClient,
    mock_session: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.embedding_pipeline.router.OpenAIEmbedder.embed_one",
        lambda self, text: [0.2] * 1536,
    )

    row = SimpleNamespace(
        id=156,
        document_id=12,
        chunk_type="budget_component",
        content="Backend service implementation with JWT-based authentication",
        metadata_={"scope": "backend", "budget_id": "BUD-TEST"},
        distance=0.231,
    )
    mock_session.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[row])))

    response = client_with_db.post(
        "/api/v1/search",
        json={"query": "REST API with OAuth authentication for fintech sector", "k": 5},
    )
    alias = client_with_db.post(
        "/search",
        json={"query": "REST API with OAuth authentication for fintech sector", "k": 5},
    )

    assert response.status_code == 200
    assert alias.status_code == 200
    body = response.json()
    assert body["k"] == 5
    assert body["search_mode"] == "vector"
    assert body["rerank"] is False
    assert body["search_time_ms"] >= 0
    assert len(body["results"]) == 1
    assert body["results"][0]["chunk_id"] == 156
    assert body["results"][0]["distance"] == 0.231


def test_search_accepts_hybrid_mode_without_rerank(
    client_with_db: TestClient,
    mock_session: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.embedding_pipeline.router.OpenAIEmbedder.embed_one",
        lambda self, text: [0.1] * 1536,
    )
    row = SimpleNamespace(
        id=1,
        document_id=1,
        chunk_type="budget_component",
        content="Stripe checkout and webhooks",
        metadata_={"budget_id": "BUD-2023-008"},
        distance=0.4,
        lexical_rank=0.9,
    )
    mock_session.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[row])))

    response = client_with_db.post(
        "/api/v1/search",
        json={
            "query": "Stripe checkout",
            "k": 5,
            "search_mode": "hybrid",
            "rerank": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["search_mode"] == "hybrid"
    assert body["rerank"] is False
    assert len(body["results"]) == 1


def test_search_openai_error_returns_500(
    client_with_db: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_embed_one(self, text):
        raise RateLimitError("rate limited", response=MagicMock(), body=None)

    monkeypatch.setattr(
        "app.embedding_pipeline.router.OpenAIEmbedder.embed_one",
        fail_embed_one,
    )

    response = client_with_db.post(
        "/api/v1/search",
        json={"query": "integration with external system", "k": 3},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Embedding service failed. Please try again later."
