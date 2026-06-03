"""Multi-turn session estimation: LLM orchestration and metadata heuristics."""

from __future__ import annotations
import re

import structlog

from app.prompts.loader import render_session_system_prompt
from app.schemas.sessions import (
    ACBIterationView,
    ACBResponse,
    ProjectMetadataView,
    SessionEstimationResponse,
    TurnObservation,
)
from app.sessions.metadata_extractor import extract_project_metadata_update, merge_metadata
from app.sessions.tier_resolver import resolve_tier
from app.services.boss import boss_decide
from app.services.critic import critic_review
from app.services.llm_wrapper import WrapperConfig, generate_sync_messages, get_default_wrapper_config
from app.services.sessions import ProjectMetadata, Session

log = structlog.get_logger(__name__)

PROMPT_VERSION = "v1"

TECH_KEYWORDS: dict[str, str] = {
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "python": "Python",
    "django": "Django",
    "fastapi": "FastAPI",
    "node": "Node.js",
    "nodejs": "Node.js",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "flutter": "Flutter",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "java": "Java",
    "spring": "Spring",
    "docker": "Docker",
    "streamlit": "Streamlit",
}

_PROJECT_NAME_PATTERNS = (
    re.compile(
        r"project\s+(?:called|named)\s+[\"']?([A-Za-z0-9][A-Za-z0-9\-]{2,48})",
        re.IGNORECASE,
    ),
    re.compile(
        r"app\s+(?:called|named)\s+[\"']?([A-Za-z0-9][A-Za-z0-9\-]{2,48})",
        re.IGNORECASE,
    ),
    re.compile(
        r"proyecto\s+[\"']?([A-Za-z0-9][A-Za-z0-9\-]{2,48})",
        re.IGNORECASE,
    ),
)

_TEAM_SIZE_PATTERN = re.compile(
    r"team\s+of\s+(\d{1,2})|(\d{1,2})\s+developers?",
    re.IGNORECASE,
)

_REJECTED_PATTERN = re.compile(
    r"(?:don't want|do not want|not interested in|reject(?:ing)?|instead of)\s+([^.!?\n]{3,80})",
    re.IGNORECASE,
)


def update_metadata_from_turn(
    metadata: ProjectMetadata,
    user_turn: str,
    assistant_text: str,
) -> None:
    """Apply lightweight heuristics after each completed turn."""
    combined = f"{user_turn}\n{assistant_text}"
    combined_lower = combined.lower()

    for keyword, label in TECH_KEYWORDS.items():
        if keyword in combined_lower and label not in metadata.mentioned_technologies:
            metadata.mentioned_technologies.append(label)

    if metadata.project_name is None:
        for pattern in _PROJECT_NAME_PATTERNS:
            match = pattern.search(user_turn)
            if match:
                metadata.project_name = match.group(1).strip().rstrip(".,;")
                break

    team_match = _TEAM_SIZE_PATTERN.search(user_turn)
    if team_match:
        size = team_match.group(1) or team_match.group(2)
        if size:
            metadata.assumed_team_size = int(size)

    scope = user_turn.strip()
    if scope:
        metadata.agreed_scope = scope[:300] + ("…" if len(scope) > 300 else "")

    for sentence in re.split(r"[.!?\n]+", user_turn):
        lowered = sentence.lower()
        if "must " in lowered or "cannot " in lowered or "can't " in lowered:
            constraint = sentence.strip()
            if constraint and constraint not in metadata.explicit_constraints:
                metadata.explicit_constraints.append(constraint[:200])

    for match in _REJECTED_PATTERN.finditer(user_turn):
        option = match.group(1).strip().rstrip(".,;")
        if option and option not in metadata.rejected_options:
            metadata.rejected_options.append(option[:120])


def estimate_session_turn(
    session: Session,
    user_turn: str,
    *,
    prompt_version: str = PROMPT_VERSION,
    tier_override: str | None = None,
    attachments_total_chars: int = 0,
    cache_hit_kind: str = "none",
    config: WrapperConfig | None = None,
) -> SessionEstimationResponse:
    """Run one conversational turn: LLM call, history update, metadata refresh."""
    config = config or get_default_wrapper_config()
    tier, rule = resolve_tier(
        user_turn=user_turn,
        metadata=session.metadata,
        tier_override=tier_override,
    )
    session.last_resolved_tier = tier
    session.last_tier_rule = rule
    system_prompt = render_session_system_prompt(
        project_metadata=session.metadata,
        rolling_summary=session.rolling_summary,
        anchors=[anchor.text for anchor in session.anchors[-8:]],
        tier=tier,
        version=prompt_version,
    )
    messages = session.history.build_messages(
        system_prompt,
        current_user=user_turn,
    )
    result = generate_sync_messages(messages=messages, config=config)
    assistant_text = result.get("estimation") or ""

    session.add_turn(user_turn, assistant_text)
    update_metadata_from_turn(session.metadata, user_turn, assistant_text)
    llm_metadata = extract_project_metadata_update(
        user_turn=user_turn,
        assistant_text=assistant_text,
        config=config,
    )
    merge_metadata(session.metadata, llm_metadata)

    log.info(
        "session_turn_completed",
        session_id=session.session_id,
        prompt_version=prompt_version,
        history_turns=session.history.turn_count,
        metadata_populated=session.metadata.has_content(),
    )
    observation = TurnObservation(
        turn_index=session.history.turn_count,
        session_id=session.session_id,
        enriched_transcript_chars=len(user_turn),
        attachments_total_chars=attachments_total_chars,
        messages_in_window=len(session.history._messages),  # noqa: SLF001
        anchors_count=len(session.anchors),
        summary_chars=len(session.rolling_summary),
        tokens_in=int(result.get("tokens_in") or 0),
        tokens_out=int(result.get("tokens_out") or 0),
        cost_usd=float(result.get("cost_usd") or 0.0),
        latency_ms=int(result.get("latency_ms") or 0),
        cache_hit_kind=cache_hit_kind if cache_hit_kind in {"none", "exact", "semantic"} else "none",
        last_resolved_tier=session.last_resolved_tier,
    )
    session.last_turn_observed = observation.model_dump()
    log.info("turn_observed", **session.last_turn_observed)

    return SessionEstimationResponse(
        text=assistant_text,
        prompt_version=prompt_version,
        turn_count=session.history.turn_count,
        tier=tier,
        tier_rule=rule,
        project_metadata=ProjectMetadataView.model_validate(session.metadata),
        observation=observation,
    )


def estimate_session_turn_acb(
    session: Session,
    user_turn: str,
    *,
    prompt_version: str = PROMPT_VERSION,
    tier_override: str | None = None,
    config: WrapperConfig | None = None,
    max_iterations: int = 2,
) -> ACBResponse:
    """Run optional Actor-Critic-Boss loop and return trace."""
    _ = config or get_default_wrapper_config()
    trace: list[ACBIterationView] = []
    actor = estimate_session_turn(
        session,
        user_turn,
        prompt_version=prompt_version,
        tier_override=tier_override,
        config=config,
    )
    candidate_text = actor.text
    for iteration in range(1, max_iterations + 1):
        critic = critic_review(user_turn=user_turn, candidate_text=candidate_text)
        verdict, note = boss_decide(critic=critic, iteration=iteration)
        trace.append(ACBIterationView(iteration=iteration, verdict=verdict, notes=note))
        if verdict == "accept":
            break
        # Keep first actor response as persisted truth in this simplified ACB.
        candidate_text = actor.text
    return ACBResponse(
        text=candidate_text,
        prompt_version=prompt_version,
        turn_count=session.history.turn_count,
        tier=session.last_resolved_tier,
        tier_rule=session.last_tier_rule,
        project_metadata=ProjectMetadataView.model_validate(session.metadata),
        trace=trace,
    )
