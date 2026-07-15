"""HTTP endpoint for LangGraph-based estimation (Session 13)."""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from openai import OpenAIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.graph.runner import run_estimation_graph
from app.graph.schemas import GraphEstimateRequest, GraphEstimateResponse

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])
log = structlog.get_logger(__name__)


@router.post("/estimate", response_model=GraphEstimateResponse)
async def graph_estimate(
    request: GraphEstimateRequest,
    http_request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GraphEstimateResponse:
    graph = getattr(http_request.app.state, "estimation_graph", None)
    if graph is None:
        raise HTTPException(status_code=503, detail="Estimation graph is not ready")

    try:
        return await run_estimation_graph(
            graph=graph,
            session=session,
            transcript=request.transcript,
            estimation_id=request.estimation_id,
            k=request.k,
            search_mode=request.search_mode,
            rerank=request.rerank,
        )
    except OpenAIError as exc:
        log.exception("graph_openai_failed")
        raise HTTPException(
            status_code=500,
            detail="Graph LLM call failed. Please try again later.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        log.exception("graph_estimate_failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="Graph estimate failed. Please try again later.",
        ) from exc
