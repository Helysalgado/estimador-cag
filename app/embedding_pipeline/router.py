"""HTTP endpoints for budget embedding ingest and semantic search."""

from __future__ import annotations

import asyncio
import time
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAIError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def _semantic_search(
    request: SearchRequest,
    session: AsyncSession,
) -> SearchResponse:
    started = time.perf_counter()
    embedder = OpenAIEmbedder()

    try:
        query_vector = await asyncio.to_thread(embedder.embed_one, request.query)
    except OpenAIError as exc:
        log.exception("embedding_search_failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="Embedding service failed. Please try again later.",
        ) from exc

    distance_expr = Chunk.embedding.cosine_distance(query_vector)
    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Chunk.chunk_type,
            Chunk.content,
            Chunk.metadata_,
            distance_expr.label("distance"),
        )
        .order_by(distance_expr)
        .limit(request.k)
    )
    rows = (await session.execute(stmt)).all()
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    return SearchResponse(
        query=request.query,
        k=request.k,
        search_time_ms=elapsed_ms,
        results=[
            SearchResultItem(
                chunk_id=row.id,
                document_id=row.document_id,
                chunk_type=row.chunk_type,
                content=row.content,
                distance=round(float(row.distance), 4),
                metadata=row.metadata_ or {},
            )
            for row in rows
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
    """Return top-k chunks closest to the query embedding by cosine distance."""
    return await _semantic_search(request, session)
