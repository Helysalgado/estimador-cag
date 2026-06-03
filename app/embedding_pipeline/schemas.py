"""Pydantic models for budget ingest and embedded chunks."""

from typing import Literal

from pydantic import BaseModel, Field

ClientSector = Literal[
    "finance",
    "ecommerce",
    "healthcare",
    "industrial",
    "education",
    "logistics",
]

ComponentComplexity = Literal["low", "medium", "high"]


class ClientMetadata(BaseModel):
    name: str = Field(min_length=1)
    sector: ClientSector
    country: str = Field(min_length=2, max_length=2, description="ISO 3166-1 alpha-2")


class BudgetComponent(BaseModel):
    component_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    tech_stack: list[str] = Field(min_length=1)
    estimated_hours: int = Field(ge=0)
    complexity: ComponentComplexity
    dependencies: list[str] = Field(default_factory=list)


class Budget(BaseModel):
    budget_id: str = Field(min_length=1)
    client_metadata: ClientMetadata
    project_summary: str = Field(min_length=1)
    main_technology: str = Field(min_length=1)
    year: int = Field(ge=2000, le=2100)
    total_estimated_hours: int = Field(ge=0)
    components: list[BudgetComponent] = Field(min_length=1)


class ChunkMetadata(BaseModel):
    budget_id: str
    component_id: str
    client_sector: ClientSector
    main_technology: str
    year: int
    complexity: ComponentComplexity
    estimated_hours: int = Field(ge=0)


class Chunk(BaseModel):
    chunk_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    metadata: ChunkMetadata
    token_count: int = Field(ge=0)


class EmbeddedChunk(Chunk):
    embedding: list[float] = Field(min_length=1)


class IngestStats(BaseModel):
    total_budgets: int = Field(ge=0)
    total_chunks: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)


class IngestRequest(BaseModel):
    budgets: list[Budget] = Field(min_length=1)


class IngestResponse(BaseModel):
    chunks: list[EmbeddedChunk]
    stats: IngestStats
