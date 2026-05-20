"""Request and response models for conversational session endpoints."""

from pydantic import BaseModel, ConfigDict, Field


class SessionCreateResponse(BaseModel):
    """Identifier for a new in-memory estimation session."""

    session_id: str = Field(
        description="UUID for the session; required on subsequent estimate calls.",
    )


class ProjectMetadataView(BaseModel):
    """Snapshot of stable project facts accumulated during a session."""

    model_config = ConfigDict(from_attributes=True)

    project_name: str | None = None
    assumed_team_size: int | None = None
    mentioned_technologies: list[str] = Field(default_factory=list)
    agreed_scope: str | None = None
    explicit_constraints: list[str] = Field(default_factory=list)
    rejected_options: list[str] = Field(default_factory=list)


class SessionEstimationResponse(BaseModel):
    """Estimation for one session turn, including memory snapshot for the UI."""

    text: str = Field(description="Estimation rendered by the LLM as free text.")
    prompt_version: str = Field(description="Jinja template version used for this turn.")
    turn_count: int = Field(ge=0, description="Completed user/assistant pairs in memory.")
    project_metadata: ProjectMetadataView
