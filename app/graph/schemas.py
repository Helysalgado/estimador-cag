"""HTTP schemas for the LangGraph estimation endpoint."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class GraphEstimateRequest(BaseModel):
    transcript: str = Field(min_length=20)
    estimation_id: str | None = None
    k: int = Field(default=5, ge=1, le=20)
    search_mode: Literal["vector", "hybrid"] = "hybrid"
    rerank: bool = False


class GraphEstimateResponse(BaseModel):
    estimate: dict[str, Any]
    status: str
    thread_id: str
    errors: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    components: list[dict[str, Any]] = Field(default_factory=list)
    node_spans: list[str] = Field(default_factory=list)
