"""HTTP schemas for the Session 12 agent endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AgentEstimateRequest(BaseModel):
    transcript: str = Field(min_length=20)
    model: str | None = None
    max_iterations: int = Field(default=12, ge=1, le=30)
    search_mode: Literal["vector", "hybrid"] = "hybrid"
    rerank: bool = False
    k: int = Field(default=5, ge=1, le=20)
    reasoning_effort: Literal["low", "medium", "high"] | None = None


class AgentEstimateResponse(BaseModel):
    estimate_text: str
    trace: list[str]
    trace_text: str
    iterations: int
    tool_calls: dict[str, int]
    model: str
    request_id: str
    stopped_reason: str
