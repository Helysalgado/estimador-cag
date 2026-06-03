"""HTTP endpoints for budget embedding ingest."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException
from openai import OpenAIError

from app.embedding_pipeline.chunker import JSONStructuralChunker
from app.embedding_pipeline.embedder import (
    OpenAIEmbedder,
    estimate_embedding_cost_usd,
)
from app.embedding_pipeline.schemas import IngestRequest, IngestResponse, IngestStats

router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])
# Alias literal del material (mat-sesion7): POST /embeddings/ingest
material_router = APIRouter(prefix="/embeddings", tags=["embeddings"])
log = structlog.get_logger(__name__)


@router.post("/ingest", response_model=IngestResponse)
@material_router.post("/ingest", response_model=IngestResponse)
def ingest_embeddings(request: IngestRequest) -> IngestResponse:
    """Chunk budgets structurally, embed each component, return vectors in memory."""
    chunker = JSONStructuralChunker()
    embedder = OpenAIEmbedder()

    chunks = chunker.chunk(request.budgets)

    try:
        result = embedder.embed_many(chunks)
    except OpenAIError as exc:
        log.exception("embedding_ingest_failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="Embedding service failed. Please try again later.",
        ) from exc

    return IngestResponse(
        chunks=result.chunks,
        stats=IngestStats(
            total_budgets=len(request.budgets),
            total_chunks=len(result.chunks),
            total_tokens=result.total_tokens,
            estimated_cost_usd=estimate_embedding_cost_usd(result.total_tokens),
        ),
    )
