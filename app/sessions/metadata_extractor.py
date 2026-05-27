"""LLM-assisted extraction of ProjectMetadata updates per turn."""

from __future__ import annotations

import json

from app.config import settings
from app.services.llm_wrapper import WrapperConfig, generate_sync_messages
from app.services.sessions import ProjectMetadata


def merge_metadata(existing: ProjectMetadata, update: ProjectMetadata) -> ProjectMetadata:
    """Merge sparse updates into existing metadata."""
    if update.project_name:
        existing.project_name = update.project_name
    if update.assumed_team_size is not None:
        existing.assumed_team_size = update.assumed_team_size
    if update.agreed_scope:
        existing.agreed_scope = update.agreed_scope
    for item in update.mentioned_technologies:
        if item not in existing.mentioned_technologies:
            existing.mentioned_technologies.append(item)
    for item in update.explicit_constraints:
        if item not in existing.explicit_constraints:
            existing.explicit_constraints.append(item)
    for item in update.rejected_options:
        if item not in existing.rejected_options:
            existing.rejected_options.append(item)
    return existing


def _extract_with_llm(user_turn: str, assistant_text: str, config: WrapperConfig) -> ProjectMetadata:
    """Best-effort JSON extraction using a cheap model."""
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        return ProjectMetadata()
    extractor_config = WrapperConfig(
        provider=config.provider,
        model=settings.METADATA_EXTRACTOR_MODEL,
        max_tokens=300,
        temperature=0.0,
        fallback_provider=config.fallback_provider,
        fallback_model=config.fallback_model,
    )
    system = (
        "Extract JSON only with keys: project_name, assumed_team_size, "
        "mentioned_technologies, agreed_scope, explicit_constraints, rejected_options. "
        "Use null/[] when unknown."
    )
    user = f"USER:\n{user_turn}\n\nASSISTANT:\n{assistant_text}"
    try:
        result = generate_sync_messages(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            config=extractor_config,
        )
    except Exception:
        return ProjectMetadata()
    raw = (result.get("estimation") or "").strip()
    try:
        payload = json.loads(raw)
    except Exception:
        return ProjectMetadata()
    return ProjectMetadata(
        project_name=payload.get("project_name"),
        assumed_team_size=payload.get("assumed_team_size"),
        mentioned_technologies=list(payload.get("mentioned_technologies") or []),
        agreed_scope=payload.get("agreed_scope"),
        explicit_constraints=list(payload.get("explicit_constraints") or []),
        rejected_options=list(payload.get("rejected_options") or []),
    )


def extract_project_metadata_update(
    *,
    user_turn: str,
    assistant_text: str,
    config: WrapperConfig,
) -> ProjectMetadata:
    """Return sparse metadata update inferred from the latest completed turn."""
    return _extract_with_llm(user_turn, assistant_text, config)
