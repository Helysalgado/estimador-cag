"""Retrieve → assemble → structured generate → verify (Session 11)."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Literal

import structlog
from openai import OpenAI, OpenAIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.generation.context_assembler import (
    assemble_context,
    chunk_ids_as_strings,
)
from app.embedding_pipeline.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from app.embedding_pipeline.generation.schemas import (
    Estimate,
    RagEstimateResponse,
    RetrievalMeta,
)
from app.embedding_pipeline.generation.verify import verify_citations
from app.embedding_pipeline.retrieval.pipeline import retrieve

log = structlog.get_logger(__name__)

SearchMode = Literal["vector", "hybrid"]


def _parse_estimate(*, query: str, context_block: str, model: str) -> Estimate:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    user_prompt = build_user_prompt(query=query, context_block=context_block)
    response = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        text_format=Estimate,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("Structured generation returned no parsed Estimate")
    return parsed


async def generate_rag_estimate(
    session: AsyncSession,
    *,
    query: str,
    k: int = 5,
    search_mode: SearchMode = "hybrid",
    rerank: bool = False,
    candidate_pool_size: int = 50,
    request_id: str | None = None,
) -> RagEstimateResponse:
    """Full RAG estimate path used by the HTTP endpoint and offline evals."""
    rid = request_id or str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=rid)
    started = time.perf_counter()

    embedder = OpenAIEmbedder()
    query_vector = await asyncio.to_thread(embedder.embed_one, query)
    hits = await retrieve(
        session,
        query_text=query,
        query_vector=query_vector,
        search_mode=search_mode,
        rerank=rerank,
        top_k=k,
        candidate_pool_size=candidate_pool_size,
    )
    search_time_ms = int((time.perf_counter() - started) * 1000)
    context_block = assemble_context(hits)
    chunk_ids = chunk_ids_as_strings(hits)

    model = settings.RAG_GENERATION_MODEL
    try:
        estimate = await asyncio.to_thread(
            _parse_estimate,
            query=query,
            context_block=context_block,
            model=model,
        )
    except OpenAIError:
        log.exception("rag_generate_openai_failed", request_id=rid)
        raise
    except Exception:
        log.exception("rag_generate_parse_failed", request_id=rid)
        raise

    report = verify_citations(estimate, chunk_ids)
    log.info(
        "rag_estimate_done",
        request_id=rid,
        citation_ok=report.ok,
        dangling_chunk_ids=report.dangling_chunk_ids,
        grounded_lines=report.grounded_lines,
        ungrounded_lines=report.ungrounded_lines,
        retrieved=len(chunk_ids),
        search_mode=search_mode,
        rerank=rerank,
        model=model,
    )

    return RagEstimateResponse(
        estimate=estimate,
        citation_report=report,
        retrieval=RetrievalMeta(
            search_mode=search_mode,
            rerank=rerank,
            chunk_ids=chunk_ids,
            contexts=[hit.content for hit in hits],
            search_time_ms=search_time_ms,
        ),
        request_id=rid,
    )
