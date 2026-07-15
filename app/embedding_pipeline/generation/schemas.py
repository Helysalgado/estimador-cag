"""Structured RAG estimate schemas with line-level citation integrity (Session 11)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SourceReference(BaseModel):
    chunk_id: str = Field(min_length=1)
    document_id: str | None = None
    evidence: str = Field(min_length=1, description="Verbatim fragment from the chunk")


class EstimateLineItem(BaseModel):
    description: str = Field(min_length=1)
    hours: float | None = Field(default=None, ge=0)
    role: str | None = None
    grounded: bool
    sources: list[SourceReference] = Field(default_factory=list)
    assumption: str | None = None

    @model_validator(mode="after")
    def _grounding_integrity(self) -> EstimateLineItem:
        """Enforce citation integrity; coerce common LLM slips on ungrounded lines."""
        if self.grounded:
            if not self.sources:
                raise ValueError("grounded=True requires at least one source")
            return self

        if self.sources:
            self.sources = []
        # Untethered positive hours are inventions — drop them.
        if self.hours is not None and self.hours > 0:
            self.hours = None
        if not (self.assumption or "").strip():
            self.assumption = "Not supported by retrieved context"
        return self


class Estimate(BaseModel):
    summary: str | None = None
    line_items: list[EstimateLineItem] = Field(min_length=1)
    total_hours: float | None = Field(default=None, ge=0)
    notes: str | None = None


class CitationReport(BaseModel):
    ok: bool
    dangling_chunk_ids: list[str] = Field(default_factory=list)
    grounded_lines: int = Field(ge=0)
    ungrounded_lines: int = Field(ge=0)
    details: list[str] | None = None


class RagEstimateRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=100)
    search_mode: Literal["vector", "hybrid"] = "hybrid"
    rerank: bool | None = False
    candidate_pool_size: int = Field(default=50, ge=1, le=100)


class RetrievalMeta(BaseModel):
    search_mode: Literal["vector", "hybrid"]
    rerank: bool
    chunk_ids: list[str]
    contexts: list[str] = Field(
        default_factory=list,
        description="Chunk texts in the same order as chunk_ids (for evals)",
    )
    search_time_ms: int = Field(ge=0)


class RagEstimateResponse(BaseModel):
    estimate: Estimate
    citation_report: CitationReport
    retrieval: RetrievalMeta
    request_id: str
