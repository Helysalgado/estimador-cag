"""HTTP endpoints for budget embedding ingest and semantic / hybrid search."""

from __future__ import annotations

import asyncio
import time
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAIError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import (
    CHUNK_TYPE_BUDGET_COMPONENT,
    EMBEDDING_DIMENSION,
    Chunk,
    Document,
)
from app.db.session import get_db_session
from app.embedding_pipeline.chunker import JSONStructuralChunker
from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.errors import DuplicateDocumentError
from app.embedding_pipeline.retrieval.pipeline import retrieve
from app.embedding_pipeline.schemas import (
    PersistIngestRequest,
    PersistIngestResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)

router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])
search_router = APIRouter(prefix="/api/v1", tags=["search"])
# Alias literal del material: POST /embeddings/ingest, POST /search
material_router = APIRouter(prefix="/embeddings", tags=["embeddings"])
material_search_router = APIRouter(prefix="", tags=["search"])
log = structlog.get_logger(__name__)


def _budget_document_metadata(budget) -> dict:
    return {
        "budget_id": budget.budget_id,
        "client_sector": budget.client_metadata.sector,
        "client_name": budget.client_metadata.name,
        "main_technology": budget.main_technology,
        "year": budget.year,
        "total_estimated_hours": budget.total_estimated_hours,
    }


async def _persist_ingest(
    request: PersistIngestRequest,
    session: AsyncSession,
) -> PersistIngestResponse:
    started = time.perf_counter()
    existing = await session.scalar(
        select(Document).where(Document.source_path == request.source_path)
    )
    if existing is not None:
        raise DuplicateDocumentError(existing.id)

    document = Document(
        source_path=request.source_path,
        document_type=request.document_type,
        metadata_=_budget_document_metadata(request.content),
    )
    session.add(document)
    await session.flush()

    chunker = JSONStructuralChunker()
    chunks = chunker.chunk([request.content])
    embedder = OpenAIEmbedder()

    try:
        result = await asyncio.to_thread(embedder.embed_many, chunks)
    except OpenAIError as exc:
        await session.rollback()
        log.exception("embedding_ingest_failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="Embedding service failed. Please try again later.",
        ) from exc

    chunk_rows = [
        Chunk(
            document_id=document.id,
            chunk_type=CHUNK_TYPE_BUDGET_COMPONENT,
            content=embedded.text,
            embedding=embedded.embedding,
            metadata_=embedded.metadata.model_dump(),
        )
        for embedded in result.chunks
    ]
    session.add_all(chunk_rows)
    await session.commit()

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return PersistIngestResponse(
        document_id=document.id,
        chunks_created=len(chunk_rows),
        embedding_dimension=EMBEDDING_DIMENSION,
        ingestion_time_ms=elapsed_ms,
    )


async def _search(
    request: SearchRequest,
    session: AsyncSession,
) -> SearchResponse:
    started = time.perf_counter()
    embedder = OpenAIEmbedder()
    effective_rerank = (
        request.rerank if request.rerank is not None else settings.RERANKING_ENABLED
    )

    try:
        query_vector = await asyncio.to_thread(embedder.embed_one, request.query)
    except OpenAIError as exc:
        log.exception("embedding_search_failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="Embedding service failed. Please try again later.",
        ) from exc

    try:
        hits = await retrieve(
            session,
            query_text=request.query,
            query_vector=query_vector,
            search_mode=request.search_mode,
            rerank=effective_rerank,
            top_k=request.k,
            candidate_pool_size=request.candidate_pool_size,
        )
    except Exception as exc:  # noqa: BLE001 — surface retrieval failures as 500
        log.exception("retrieval_failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="Retrieval failed. Please try again later.",
        ) from exc

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return SearchResponse(
        query=request.query,
        k=request.k,
        search_time_ms=elapsed_ms,
        search_mode=request.search_mode,
        rerank=effective_rerank,
        results=[
            SearchResultItem(
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                chunk_type=hit.chunk_type,
                content=hit.content,
                distance=round(float(hit.distance), 4),
                metadata=hit.metadata,
            )
            for hit in hits
        ],
    )


@router.post("/ingest", response_model=PersistIngestResponse)
@material_router.post("/ingest", response_model=PersistIngestResponse)
async def ingest_embeddings(
    request: PersistIngestRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PersistIngestResponse:
    """Chunk a budget, embed components, and persist document + chunks in one transaction."""
    return await _persist_ingest(request, session)


@search_router.post("/search", response_model=SearchResponse)
@material_search_router.post("/search", response_model=SearchResponse)
async def search_chunks(
    request: SearchRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SearchResponse:
    """Retrieve top-k chunks (vector or hybrid), optionally reranked."""
    return await _search(request, session)
