"""Recall-then-rerank retrieval pipeline (Session 10).

Composes the four exercise configurations behind ``search_mode`` and ``rerank``.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Literal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.embedding_pipeline.retrieval.fulltext import NO_VECTOR_DISTANCE, search_fulltext
from app.embedding_pipeline.retrieval.fusion import reciprocal_rank_fusion
from app.embedding_pipeline.retrieval.reranker import CrossEncoderReranker, get_reranker
from app.embedding_pipeline.retrieval.vector import search_vector

log = structlog.get_logger(__name__)

SearchMode = Literal["vector", "hybrid"]


@dataclass(frozen=True)
class RetrievedChunk:
    """Internal retrieval hit used before mapping to the HTTP schema."""

    chunk_id: int
    document_id: int
    chunk_type: str
    content: str
    distance: float
    metadata: dict[str, Any]


def _row_to_chunk(row: Any, *, distance: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=row.id,
        document_id=row.document_id,
        chunk_type=row.chunk_type,
        content=row.content,
        distance=distance,
        metadata=row.metadata_ or {},
    )


async def retrieve(
    session: AsyncSession,
    *,
    query_text: str,
    query_vector: list[float],
    search_mode: SearchMode = "vector",
    rerank: bool = False,
    top_k: int = 5,
    candidate_pool_size: int | None = None,
    rrf_k: int | None = None,
    reranker: CrossEncoderReranker | None = None,
) -> list[RetrievedChunk]:
    """Run vector or hybrid retrieval with optional cross-encoder reranking."""
    pool_size = candidate_pool_size or settings.RETRIEVAL_CANDIDATE_POOL_SIZE
    fusion_k = rrf_k if rrf_k is not None else settings.RRF_SMOOTHING_K
    started = time.perf_counter()

    # Wide recall when a later stage will re-sort; exact top_k for plain vector.
    wide = rerank or search_mode == "hybrid"
    vector_limit = pool_size if wide else top_k
    lexical_limit = pool_size

    if search_mode == "hybrid":
        vector_rows, lexical_rows = await asyncio.gather(
            search_vector(session, query_vector, limit=vector_limit),
            search_fulltext(session, query_text, limit=lexical_limit),
        )
    else:
        vector_rows = await search_vector(session, query_vector, limit=vector_limit)
        lexical_rows = []

    candidates: dict[int, RetrievedChunk] = {}
    for row in vector_rows:
        candidates[row.id] = _row_to_chunk(row, distance=float(row.distance))
    for row in lexical_rows:
        candidates.setdefault(
            row.id,
            _row_to_chunk(row, distance=NO_VECTOR_DISTANCE),
        )

    if search_mode == "hybrid":
        fused = reciprocal_rank_fusion(
            [
                [row.id for row in vector_rows],
                [row.id for row in lexical_rows],
            ],
            k=fusion_k,
        )
        ordered = [candidates[chunk_id] for chunk_id, _score in fused if chunk_id in candidates]
    else:
        ordered = [candidates[row.id] for row in vector_rows]

    if rerank and ordered:
        active_reranker = reranker or get_reranker()
        recall_pool = ordered[:pool_size]
        final = await asyncio.to_thread(
            active_reranker.rerank,
            query_text,
            recall_pool,
            top_n=top_k,
        )
    else:
        final = ordered[:top_k]

    log.info(
        "retrieve_done",
        search_mode=search_mode,
        rerank=rerank,
        vector_hits=len(vector_rows),
        lexical_hits=len(lexical_rows),
        results=len(final),
        search_time_ms=int((time.perf_counter() - started) * 1000),
    )
    return final
