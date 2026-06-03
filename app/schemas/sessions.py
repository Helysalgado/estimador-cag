"""Request and response models for conversational session endpoints."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SessionCreateResponse(BaseModel):
    """Identifier for a new in-memory estimation session."""

    session_id: str = Field(
        description="UUID for the session; required on subsequent estimate calls.",
    )


class AnchorView(BaseModel):
    text: str
    source_turn: int
    confidence: float


class ProjectMetadataView(BaseModel):
    """Snapshot of stable project facts accumulated during a session."""

    model_config = ConfigDict(from_attributes=True)

    project_name: str | None = None
    assumed_team_size: int | None = None
    mentioned_technologies: list[str] = Field(default_factory=list)
    agreed_scope: str | None = None
    explicit_constraints: list[str] = Field(default_factory=list)
    rejected_options: list[str] = Field(default_factory=list)


class TurnObservation(BaseModel):
    """Per-turn telemetry for stress evals and observability."""

    turn_index: int = Field(ge=1)
    session_id: str
    enriched_transcript_chars: int = Field(ge=0)
    attachments_total_chars: int = Field(ge=0)
    messages_in_window: int = Field(ge=0)
    anchors_count: int = Field(ge=0)
    summary_chars: int = Field(ge=0)
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cache_hit_kind: Literal["none", "exact", "semantic"] = "none"
    last_resolved_tier: str | None = None


class SessionEstimationResponse(BaseModel):
    """Estimation for one session turn, including memory snapshot for the UI."""

    text: str = Field(description="Estimation rendered by the LLM as free text.")
    prompt_version: str = Field(description="Jinja template version used for this turn.")
    turn_count: int = Field(ge=0, description="Completed user/assistant pairs in memory.")
    tier: str = Field(default="default", description="Tier resolved for this response.")
    tier_rule: str = Field(default="default_rule", description="Rule used to resolve tier.")
    project_metadata: ProjectMetadataView
    observation: TurnObservation | None = Field(
        default=None,
        description="Per-turn telemetry; populated on every conversational estimate.",
    )


class SessionDebugResponse(BaseModel):
    session_id: str
    message_count: int = Field(ge=0)
    anchors_count: int = Field(ge=0)
    summary_chars: int = Field(ge=0)
    last_resolved_tier: str
    last_tier_rule: str
    project_metadata: ProjectMetadataView
    anchors: list[AnchorView] = Field(default_factory=list)
    rolling_summary: str = ""
    last_turn_observed: dict[str, object] | None = None


class ACBIterationView(BaseModel):
    iteration: int
    verdict: str
    notes: str


class ACBResponse(BaseModel):
    text: str
    prompt_version: str
    turn_count: int
    tier: str
    tier_rule: str
    project_metadata: ProjectMetadataView
    trace: list[ACBIterationView] = Field(default_factory=list)
