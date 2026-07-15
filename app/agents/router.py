"""HTTP endpoint for the Session 12 estimation agent."""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.loop import run_agent
from app.agents.schemas import AgentEstimateRequest, AgentEstimateResponse
from app.db.session import get_db_session

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])
log = structlog.get_logger(__name__)


@router.post("/estimate", response_model=AgentEstimateResponse)
async def agent_estimate(
    request: AgentEstimateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgentEstimateResponse:
    """Run the manual tool-calling agent on a meeting transcript."""
    request_id = str(uuid.uuid4())
    try:
        return await run_agent(
            session,
            transcript=request.transcript,
            model=request.model,
            max_iterations=request.max_iterations,
            search_mode=request.search_mode,
            rerank=request.rerank,
            k=request.k,
            reasoning_effort=request.reasoning_effort,
            request_id=request_id,
        )
    except OpenAIError as exc:
        log.exception("agent_openai_failed", request_id=request_id)
        raise HTTPException(
            status_code=500,
            detail="Agent LLM call failed. Please try again later.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        log.exception("agent_failed", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="Agent estimate failed. Please try again later.",
        ) from exc
