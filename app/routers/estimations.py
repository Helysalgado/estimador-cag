"""Endpoints for the estimation API."""

from __future__ import annotations

import json
from typing import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.prompts import render_estimation_prompt
from app.schemas.estimation import EstimationRequest, EstimationResponse
from app.services.llm_service import PROMPT_VERSION, estimate_from_request
from app.services.llm_wrapper import complete_stream, get_default_wrapper_config

router = APIRouter(prefix="/api/v1", tags=["estimations"])


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/estimate", response_model=EstimationResponse)
def create_estimation(request: EstimationRequest) -> EstimationResponse:
    """Render the versioned prompt pair and return a full estimation."""
    try:
        return estimate_from_request(request, prompt_version=PROMPT_VERSION)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Upstream LLM call failed") from exc


@router.post("/estimate/stream")
def stream_estimation(request: EstimationRequest) -> StreamingResponse:
    """Stream the estimation as Server-Sent Events (LIDR session_4 format)."""
    system_prompt, user_message = render_estimation_prompt(request, version=PROMPT_VERSION)
    config = get_default_wrapper_config()

    def event_stream() -> Iterator[str]:
        yield _sse("status", {"phase": "preparing", "prompt_version": PROMPT_VERSION})
        yield _sse("status", {"phase": "calling_llm"})
        try:
            for chunk in complete_stream(
                system_prompt=system_prompt,
                user_message=user_message,
                config=config,
            ):
                if chunk:
                    yield _sse("token", {"chunk": chunk})
        except Exception:  # noqa: BLE001
            yield _sse("error", {"message": "Upstream LLM call failed"})
            return
        yield _sse("complete", {"prompt_version": PROMPT_VERSION})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
