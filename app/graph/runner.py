"""Invoke the compiled estimation graph with DB session + thread_id."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.observability import begin_span_recording, get_recorded_spans
from app.graph.schemas import GraphEstimateResponse


async def run_estimation_graph(
    *,
    graph: Any,
    session: AsyncSession,
    transcript: str,
    estimation_id: str | None = None,
    k: int = 5,
    search_mode: Literal["vector", "hybrid"] = "hybrid",
    rerank: bool = False,
) -> GraphEstimateResponse:
    thread_id = estimation_id or str(uuid.uuid4())
    begin_span_recording()

    config = {
        "configurable": {
            "thread_id": thread_id,
            "db_session": session,
            "k": k,
            "search_mode": search_mode,
            "rerank": rerank,
        }
    }
    initial = {
        "transcript": transcript,
        "estimation_id": thread_id,
        "requirements": [],
        "components": [],
        "budget_matches": [],
        "errors": [],
    }
    result = await graph.ainvoke(initial, config)
    spans = get_recorded_spans()

    return GraphEstimateResponse(
        estimate=result.get("estimate") or {},
        status=str(result.get("status") or "needs_review"),
        thread_id=thread_id,
        errors=list(result.get("errors") or []),
        requirements=list(result.get("requirements") or []),
        components=list(result.get("components") or []),
        node_spans=spans,
    )
