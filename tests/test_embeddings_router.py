import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from openai import RateLimitError

from app.embedding_pipeline.embedder import EmbedManyResult
from app.embedding_pipeline.schemas import EmbeddedChunk


def _one_budget_payload() -> dict:
    budgets = json.loads(Path("data/budgets_sample.json").read_text(encoding="utf-8"))
    return {"budgets": [budgets[0]]}


def test_ingest_returns_chunks_and_stats(
    client: TestClient,
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
                embedding=[0.1, 0.2, 0.3],
            )
            for chunk in chunks
        ]
        total_tokens = sum(c.token_count for c in chunks)
        return EmbedManyResult(chunks=embedded, total_tokens=total_tokens)

    monkeypatch.setattr(
        "app.embedding_pipeline.router.OpenAIEmbedder.embed_many",
        fake_embed_many,
    )

    payload = _one_budget_payload()
    response = client.post("/api/v1/embeddings/ingest", json=payload)
    legacy = client.post("/embeddings/ingest", json=payload)

    assert response.status_code == 200
    assert legacy.status_code == 200
    assert legacy.json()["stats"] == response.json()["stats"]
    body = response.json()
    assert len(body["chunks"]) == 3
    assert body["chunks"][0]["chunk_id"] == "BUD-2024-014::AUTH-001"
    assert body["chunks"][0]["embedding"] == [0.1, 0.2, 0.3]
    assert body["stats"] == {
        "total_budgets": 1,
        "total_chunks": 3,
        "total_tokens": 126,
        "estimated_cost_usd": pytest.approx(126 / 1_000_000 * 0.02),
    }


def test_ingest_openai_error_returns_500(
    client: TestClient,
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

    response = client.post("/api/v1/embeddings/ingest", json=_one_budget_payload())

    assert response.status_code == 500
    assert response.json()["detail"] == "Embedding service failed. Please try again later."


def test_ingest_validation_error_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/embeddings/ingest", json={"budgets": []})
    assert response.status_code == 422
