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


class PersistIngestRequest(BaseModel):
    source_path: str = Field(min_length=1)
    document_type: str = Field(min_length=1)
    content: Budget


class PersistIngestResponse(BaseModel):
    document_id: int = Field(ge=1)
    chunks_created: int = Field(ge=0)
    embedding_dimension: int = Field(ge=1)
    ingestion_time_ms: int = Field(ge=0)


class DuplicateDocumentDetail(BaseModel):
    detail: str
    document_id: int


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=100)
    search_mode: Literal["vector", "hybrid"] = "vector"
    # None → use settings.RERANKING_ENABLED; explicit bool overrides settings.
    rerank: bool | None = None
    candidate_pool_size: int = Field(default=50, ge=1, le=100)


class SearchResultItem(BaseModel):
    chunk_id: int
    document_id: int
    chunk_type: str
    content: str
    distance: float
    metadata: dict


class SearchResponse(BaseModel):
    query: str
    k: int
    search_time_ms: int
    search_mode: Literal["vector", "hybrid"] = "vector"
    rerank: bool = False
    results: list[SearchResultItem]
