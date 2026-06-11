import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from openai import RateLimitError

from app.db.session import get_db_session
from app.embedding_pipeline.embedder import EmbedManyResult
from app.embedding_pipeline.schemas import EmbeddedChunk
from app.main import app


def _one_budget() -> dict:
    budgets = json.loads(Path("data/budgets_sample.json").read_text(encoding="utf-8"))
    return budgets[0]


def _persist_payload() -> dict:
    budget = _one_budget()
    return {
        "source_path": f"data/budgets/{budget['budget_id']}.json",
        "document_type": "historical_budget",
        "content": budget,
    }


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    return session


@pytest.fixture
def client_with_db(mock_session: AsyncMock) -> TestClient:
    async def _override_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = _override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_ingest_persists_and_returns_metrics(
    client_with_db: TestClient,
    mock_session: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.embedding_pipeline.chunker.count_tokens",
        lambda text: 42,
    )

    def fake_embed_many(self, chunks):
        embedded = [
            EmbeddedChunk(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                metadata=chunk.metadata,
                token_count=chunk.token_count,
                embedding=[0.1] * 1536,
            )
            for chunk in chunks
        ]
        return EmbedManyResult(chunks=embedded, total_tokens=sum(c.token_count for c in chunks))

    monkeypatch.setattr(
        "app.embedding_pipeline.router.OpenAIEmbedder.embed_many",
        fake_embed_many,
    )

    def assign_document_id(document):
        document.id = 42

    mock_session.add.side_effect = assign_document_id

    payload = _persist_payload()
    response = client_with_db.post("/api/v1/embeddings/ingest", json=payload)
    legacy = client_with_db.post("/embeddings/ingest", json=payload)

    assert response.status_code == 200
    assert legacy.status_code == 200
    body = response.json()
    assert body["document_id"] == 42
    assert body["chunks_created"] == 3
    assert body["embedding_dimension"] == 1536
    assert body["ingestion_time_ms"] >= 0
    assert mock_session.commit.await_count == 2


def test_ingest_duplicate_returns_409(
    client_with_db: TestClient,
    mock_session: AsyncMock,
) -> None:
    mock_session.scalar = AsyncMock(return_value=SimpleNamespace(id=99))

    response = client_with_db.post("/api/v1/embeddings/ingest", json=_persist_payload())

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Document already ingested",
        "document_id": 99,
    }


def test_ingest_openai_error_returns_500(
    client_with_db: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.embedding_pipeline.chunker.count_tokens",
        lambda text: 1,
    )

    def fail_embed_many(self, chunks):
        raise RateLimitError("rate limited", response=MagicMock(), body=None)

    monkeypatch.setattr(
        "app.embedding_pipeline.router.OpenAIEmbedder.embed_many",
        fail_embed_many,
    )

    response = client_with_db.post("/api/v1/embeddings/ingest", json=_persist_payload())

    assert response.status_code == 500
    assert response.json()["detail"] == "Embedding service failed. Please try again later."


def test_ingest_validation_error_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/embeddings/ingest",
        json={"source_path": "", "document_type": "historical_budget", "content": {}},
    )
    assert response.status_code == 422
