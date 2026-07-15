"""HTTP endpoint for structured RAG estimates (Session 11)."""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db_session
from app.embedding_pipeline.generation.generate import generate_rag_estimate
from app.embedding_pipeline.generation.schemas import (
    RagEstimateRequest,
    RagEstimateResponse,
)

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])
log = structlog.get_logger(__name__)


@router.post("/estimate", response_model=RagEstimateResponse)
async def rag_estimate(
    request: RagEstimateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RagEstimateResponse:
    """Retrieve context (hybrid by default) and return a citation-checked estimate."""
    request_id = str(uuid.uuid4())
    effective_rerank = (
        request.rerank if request.rerank is not None else settings.RERANKING_ENABLED
    )
    try:
        return await generate_rag_estimate(
            session,
            query=request.query,
            k=request.k,
            search_mode=request.search_mode,
            rerank=effective_rerank,
            candidate_pool_size=request.candidate_pool_size,
            request_id=request_id,
        )
    except OpenAIError as exc:
        log.exception("rag_estimate_openai_failed", request_id=request_id)
        raise HTTPException(
            status_code=500,
            detail="Generation service failed. Please try again later.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        log.exception("rag_estimate_failed", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="RAG estimate failed. Please try again later.",
        ) from exc
