"""Endpoints for the estimation API."""

from __future__ import annotations

import json
from typing import Any, Iterator

import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.config import settings
from app.prompts import render_estimation_prompt
from app.schemas.estimation import EstimationRequest, EstimationResponse
from app.services.llm_service import PROMPT_VERSION, estimate_from_request
from app.services.llm_wrapper import complete_stream, get_default_wrapper_config

router = APIRouter(prefix="/api/v1", tags=["estimations"])
log = structlog.get_logger(__name__)

ALLOWED_PROMPT_VERSIONS = frozenset({"v1", "v2"})


def _normalize_prompt_version(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in ALLOWED_PROMPT_VERSIONS:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "unsupported_prompt_version",
                "allowed": sorted(ALLOWED_PROMPT_VERSIONS),
                "received": value,
            },
        )
    return normalized


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/estimate", response_model=EstimationResponse)
def create_estimation(
    request: EstimationRequest,
    prompt_version: str = Query(
        default=PROMPT_VERSION,
        description="Jinja template set under app/prompts/estimation/<version> (e.g. v1, v2).",
    ),
) -> EstimationResponse:
    """Render the versioned prompt pair and return a full estimation."""
    version = _normalize_prompt_version(prompt_version)
    try:
        return estimate_from_request(request, prompt_version=version)
    except Exception as exc:  # noqa: BLE001
        log.exception(
            "estimation_llm_failed",
            error_type=type(exc).__name__,
            prompt_version=version,
        )
        if settings.APP_ENV == "development":
            detail: str | dict[str, Any] = {
                "message": "Upstream LLM call failed",
                "error_type": type(exc).__name__,
                "hint": (
                    "Revisa OPENAI_API_KEY / ANTHROPIC_API_KEY en .env y que el proceso "
                    "uvicorn cargue ese archivo (reinicia tras editar). "
                    "LLM_PROVIDER y LLM_MODEL deben coincidir con una clave disponible."
                ),
                "error": str(exc)[:800],
            }
        else:
            detail = "Upstream LLM call failed"
        raise HTTPException(status_code=502, detail=detail) from exc


@router.post("/estimate/stream")
def stream_estimation(
    request: EstimationRequest,
    prompt_version: str = Query(
        default=PROMPT_VERSION,
        description="Jinja template set for streaming (same as blocking /estimate).",
    ),
) -> StreamingResponse:
    """Stream the estimation as Server-Sent Events (LIDR session_4 format)."""
    version = _normalize_prompt_version(prompt_version)
    system_prompt, user_message = render_estimation_prompt(request, version=version)
    config = get_default_wrapper_config()

    def event_stream() -> Iterator[str]:
        yield _sse("status", {"phase": "preparing", "prompt_version": version})
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
        yield _sse("complete", {"prompt_version": version})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
