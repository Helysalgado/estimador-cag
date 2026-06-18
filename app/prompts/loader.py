"""Jinja2 loader for versioned prompt templates.

The on-disk layout is ``app/prompts/<use_case>/<version>/*.j2``. Versioning
is required from day one: switching prompts becomes a string change at the
call site (``version="v2"``), not a code refactor.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.config import settings
from app.schemas.estimation import EstimationRequest
from app.services.sessions import ProjectMetadata

_BASE_DIR = Path(__file__).resolve().parent

_env = Environment(
    loader=FileSystemLoader(_BASE_DIR),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    keep_trailing_newline=True,
)

log = structlog.get_logger(__name__)


def _project_metadata_for_template(
    project_metadata: ProjectMetadata | None,
) -> ProjectMetadata | None:
    if project_metadata is None or not project_metadata.has_content():
        return None
    return project_metadata


def render_estimation_prompt(
    request: EstimationRequest,
    version: str = "v1",
    *,
    project_metadata: ProjectMetadata | None = None,
) -> tuple[str, str]:
    """Render the system and user prompts for the estimation use case.

    Returns:
        A tuple ``(system_prompt, user_prompt)`` ready to be sent to the LLM
        as separate ``role: "system"`` and ``role: "user"`` messages.
    """
    context = {
        "description": request.description,
        "project_type": request.project_type.value,
        "detail_level": request.detail_level.value,
        "output_format": request.output_format.value,
        "reference_projects": request.reference_projects,
        "project_metadata": _project_metadata_for_template(project_metadata),
        "rolling_summary": None,
        "anchors": [],
        "tier": "default",
    }
    system = _env.get_template(f"estimation/{version}/system.j2").render(**context)
    user = _env.get_template(f"estimation/{version}/user.j2").render(**context)
    combined = (system + user).encode("utf-8")
    content_sha256 = hashlib.sha256(combined).hexdigest()
    log.info(
        "prompt_rendered",
        prompt_template_version=version,
        app_env=settings.APP_ENV,
        content_sha256=content_sha256,
        description_chars=len(request.description),
    )
    return system, user


def render_session_system_prompt(
    *,
    project_metadata: ProjectMetadata | None,
    rolling_summary: str | None = None,
    anchors: list[str] | None = None,
    tier: str = "default",
    version: str = "v1",
    project_type: str = "web_saas",
    detail_level: str = "medium",
    output_format: str = "phases_table",
) -> str:
    """Render only the system prompt for a conversational session turn.

    Uses the same ``system.j2`` as the stateless estimator, with neutral defaults
    for form fields that are not collected in the session UI yet.
    """
    context = {
        "project_type": project_type,
        "detail_level": detail_level,
        "output_format": output_format,
        "reference_projects": None,
        "project_metadata": _project_metadata_for_template(project_metadata),
        "rolling_summary": rolling_summary,
        "anchors": anchors or [],
        "tier": tier,
    }
    return _env.get_template(f"estimation/{version}/system.j2").render(**context)
