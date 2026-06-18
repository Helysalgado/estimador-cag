from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from openai import RateLimitError

from app.embedding_pipeline.embedder import (
    EMBED_BATCH_SIZE,
    OpenAIEmbedder,
    estimate_embedding_cost_usd,
)
from app.embedding_pipeline.schemas import Chunk, ChunkMetadata


def _chunk(chunk_id: str, text: str, token_count: int = 10) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        text=text,
        metadata=ChunkMetadata(
            budget_id="BUD-1",
            component_id=chunk_id.split("::")[-1],
            client_sector="finance",
            main_technology="python",
            year=2024,
            complexity="low",
            estimated_hours=10,
        ),
        token_count=token_count,
    )


def test_estimate_embedding_cost_usd() -> None:
    assert estimate_embedding_cost_usd(1_000_000) == pytest.approx(0.02)
    assert estimate_embedding_cost_usd(500_000) == pytest.approx(0.01)


def test_embed_many_batches_and_preserves_order() -> None:
    n = EMBED_BATCH_SIZE + 5
    chunks = [_chunk(f"BUD-1::C{i}", f"text-{i}", token_count=i + 1) for i in range(n)]
    call_inputs: list[list[str]] = []

    def fake_create(*, model: str, input: list[str]):
        call_inputs.append(list(input))
        data = [
            SimpleNamespace(index=i, embedding=[float(i)])
            for i in range(len(input))
        ]
        return SimpleNamespace(data=data)

    client = MagicMock()
    client.embeddings.create.side_effect = fake_create
    embedder = OpenAIEmbedder(client=client)

    result = embedder.embed_many(chunks)

    assert len(call_inputs) == 2
    assert len(call_inputs[0]) == EMBED_BATCH_SIZE
    assert len(call_inputs[1]) == 5
    assert len(result.chunks) == n
    assert result.chunks[0].chunk_id == "BUD-1::C0"
    assert result.chunks[0].embedding == [0.0]
    assert result.chunks[-1].chunk_id == f"BUD-1::C{n - 1}"
    assert result.chunks[-1].embedding == [4.0]
    assert result.total_tokens == sum(range(1, n + 1))


def test_embed_one_delegates_to_batch_api() -> None:
    client = MagicMock()
    client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(index=0, embedding=[0.1, 0.2])],
    )
    embedder = OpenAIEmbedder(client=client)
    assert embedder.embed_one("hello") == [0.1, 0.2]
    client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input=["hello"],
    )


def test_rate_limit_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(
        "app.embedding_pipeline.embedder.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )

    response = SimpleNamespace(
        data=[SimpleNamespace(index=0, embedding=[1.0])],
    )
    client = MagicMock()
    client.embeddings.create.side_effect = [
        RateLimitError("rate limited", response=MagicMock(), body=None),
        RateLimitError("rate limited", response=MagicMock(), body=None),
        response,
    ]
    embedder = OpenAIEmbedder(client=client)
    chunks = [_chunk("BUD-1::A", "one")]

    result = embedder.embed_many(chunks)

    assert result.chunks[0].embedding == [1.0]
    assert sleeps == [1, 2]
    assert client.embeddings.create.call_count == 3


def test_rate_limit_exhausted_raises() -> None:
    client = MagicMock()
    client.embeddings.create.side_effect = RateLimitError(
        "rate limited",
        response=MagicMock(),
        body=None,
    )
    embedder = OpenAIEmbedder(client=client)

    with pytest.raises(RateLimitError):
        embedder.embed_one("fail")

    assert client.embeddings.create.call_count == 4
