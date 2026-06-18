"""Structural chunking: one budget component becomes one embeddable chunk."""

from __future__ import annotations

import tiktoken

from app.embedding_pipeline.schemas import Budget, BudgetComponent, Chunk, ChunkMetadata

EMBEDDING_MODEL = "text-embedding-3-small"


def count_tokens(text: str, *, model: str = EMBEDDING_MODEL) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def build_chunk_text(budget: Budget, component: BudgetComponent) -> str:
    sector = budget.client_metadata.sector
    tech_stack = ", ".join(component.tech_stack)
    return (
        f"[Project: {budget.project_summary}]\n"
        f"[Client sector: {sector} | Year: {budget.year} | "
        f"Main tech: {budget.main_technology}]\n"
        f"\n"
        f"Component: {component.name}\n"
        f"Description: {component.description}\n"
        f"Tech stack: {tech_stack}\n"
        f"Complexity: {component.complexity}\n"
        f"Estimated hours: {component.estimated_hours}"
    )


class JSONStructuralChunker:
    """One BudgetComponent maps to exactly one Chunk (no overlap or size splitting)."""

    def chunk(self, budgets: list[Budget]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for budget in budgets:
            sector = budget.client_metadata.sector
            for component in budget.components:
                text = build_chunk_text(budget, component)
                chunks.append(
                    Chunk(
                        chunk_id=f"{budget.budget_id}::{component.component_id}",
                        text=text,
                        metadata=ChunkMetadata(
                            budget_id=budget.budget_id,
                            component_id=component.component_id,
                            client_sector=sector,
                            main_technology=budget.main_technology,
                            year=budget.year,
                            complexity=component.complexity,
                            estimated_hours=component.estimated_hours,
                        ),
                        token_count=count_tokens(text),
                    )
                )
        return chunks
