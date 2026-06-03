"""OpenAI embedding client with batching, retries, and cost estimation."""

from __future__ import annotations

import time
from dataclasses import dataclass

import structlog
from openai import OpenAI, RateLimitError

from app.config import settings
from app.embedding_pipeline.chunker import EMBEDDING_MODEL
from app.embedding_pipeline.schemas import Chunk, EmbeddedChunk

log = structlog.get_logger(__name__)

# text-embedding-3-small input pricing (USD per 1M tokens); update when OpenAI changes rates.
EMBEDDING_INPUT_USD_PER_MILLION_TOKENS = 0.02

EMBED_BATCH_SIZE = 100
_RETRY_DELAYS_SECONDS = (1, 2, 4)


def estimate_embedding_cost_usd(total_tokens: int) -> float:
    return (total_tokens / 1_000_000) * EMBEDDING_INPUT_USD_PER_MILLION_TOKENS


@dataclass(frozen=True)
class EmbedManyResult:
    chunks: list[EmbeddedChunk]
    total_tokens: int


class OpenAIEmbedder:
    """Embeds chunk text via OpenAI text-embedding-3-small (1536 dimensions)."""

    def __init__(self, client: OpenAI | None = None, *, model: str = EMBEDDING_MODEL) -> None:
        self._client = client or OpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = model

    def embed_one(self, text: str) -> list[float]:
        vectors = self._create_embeddings([text])
        return vectors[0]

    def embed_many(self, chunks: list[Chunk]) -> EmbedManyResult:
        if not chunks:
            return EmbedManyResult(chunks=[], total_tokens=0)

        embedded: list[EmbeddedChunk] = []
        total_tokens = 0

        for batch_start in range(0, len(chunks), EMBED_BATCH_SIZE):
            batch = chunks[batch_start : batch_start + EMBED_BATCH_SIZE]
            texts = [chunk.text for chunk in batch]
            batch_tokens = sum(chunk.token_count for chunk in batch)
            started = time.perf_counter()

            vectors = self._create_embeddings(texts)
            latency_ms = int((time.perf_counter() - started) * 1000)

            log.info(
                "embedding_batch_complete",
                model=self._model,
                chunks=len(batch),
                tokens=batch_tokens,
                latency_ms=latency_ms,
            )

            for chunk, embedding in zip(batch, vectors, strict=True):
                embedded.append(
                    EmbeddedChunk(
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        metadata=chunk.metadata,
                        token_count=chunk.token_count,
                        embedding=embedding,
                    )
                )
            total_tokens += batch_tokens

        return EmbedManyResult(chunks=embedded, total_tokens=total_tokens)

    def _create_embeddings(self, texts: list[str]) -> list[list[float]]:
        last_error: RateLimitError | None = None
        attempts = len(_RETRY_DELAYS_SECONDS) + 1

        for attempt in range(attempts):
            try:
                response = self._client.embeddings.create(
                    model=self._model,
                    input=texts,
                )
                ordered = sorted(response.data, key=lambda item: item.index)
                return [item.embedding for item in ordered]
            except RateLimitError as exc:
                last_error = exc
                if attempt < len(_RETRY_DELAYS_SECONDS):
                    delay = _RETRY_DELAYS_SECONDS[attempt]
                    log.warning(
                        "embedding_rate_limited",
                        attempt=attempt + 1,
                        delay_seconds=delay,
                    )
                    time.sleep(delay)
                    continue
                raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("embedding request failed without response")
