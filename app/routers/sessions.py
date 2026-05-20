"""Endpoints for multi-turn estimation sessions."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.config import settings
from app.schemas.sessions import SessionCreateResponse, SessionEstimationResponse
from app.services.attachments import AttachmentError, build_user_turn, process_attachments
from app.services.session_estimation import PROMPT_VERSION, estimate_session_turn
from app.services.sessions import session_store

router = APIRouter(prefix="/api/v1", tags=["sessions"])
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


@router.post("/sessions", response_model=SessionCreateResponse)
def create_session() -> SessionCreateResponse:
    """Create a new in-memory session and return its identifier."""
    session_id = session_store.create()
    log.info("session_created", session_id=session_id)
    return SessionCreateResponse(session_id=session_id)


@router.post(
    "/sessions/{session_id}/estimate",
    response_model=SessionEstimationResponse,
)
async def estimate_session(
    session_id: str,
    transcript: str = Form(
        ...,
        min_length=1,
        description="User message or transcription for this turn.",
    ),
    attachments: list[UploadFile] = File(
        default=[],
        description="Optional PDF or DOCX files; text is extracted locally.",
    ),
    prompt_version: str = Query(
        default=PROMPT_VERSION,
        description="Jinja template set under app/prompts/estimation/<version>.",
    ),
) -> SessionEstimationResponse:
    """Run one session turn: transcript, optional attachments, LLM, memory update."""
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "session_not_found", "session_id": session_id},
        )

    version = _normalize_prompt_version(prompt_version)

    try:
        attachments_text = await process_attachments(attachments)
    except AttachmentError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": exc.error, "message": exc.message},
        ) from exc

    user_turn = build_user_turn(transcript, attachments_text)
    try:
        return estimate_session_turn(session, user_turn, prompt_version=version)
    except Exception as exc:  # noqa: BLE001
        log.exception(
            "session_estimation_llm_failed",
            session_id=session_id,
            error_type=type(exc).__name__,
            prompt_version=version,
        )
        if settings.APP_ENV == "development":
            detail: str | dict[str, Any] = {
                "message": "Upstream LLM call failed",
                "error_type": type(exc).__name__,
                "hint": (
                    "Revisa OPENAI_API_KEY / ANTHROPIC_API_KEY en .env y reinicia uvicorn "
                    "tras editar. LLM_PROVIDER y LLM_MODEL deben coincidir con una clave disponible."
                ),
                "error": str(exc)[:800],
            }
        else:
            detail = "Upstream LLM call failed"
        raise HTTPException(status_code=502, detail=detail) from exc
