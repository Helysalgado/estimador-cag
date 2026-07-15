"""Wrap Session 10 retrieval as the agent tool ``search_budgets``."""

from __future__ import annotations

import asyncio
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.retrieval.pipeline import retrieve

ComponentType = Literal[
    "integration",
    "migration",
    "frontend",
    "backend",
    "mobile",
    "other",
]


async def search_budgets(
    session: AsyncSession,
    *,
    query: str,
    component_type: ComponentType = "other",
    k: int = 5,
    search_mode: Literal["vector", "hybrid"] = "hybrid",
    rerank: bool = False,
    candidate_pool_size: int = 50,
) -> dict[str, Any]:
    """Retrieve compact historical budget snippets for one component focus."""
    focused = f"{component_type}: {query.strip()}"
    embedder = OpenAIEmbedder()
    query_vector = await asyncio.to_thread(embedder.embed_one, focused)
    hits = await retrieve(
        session,
        query_text=focused,
        query_vector=query_vector,
        search_mode=search_mode,
        rerank=rerank,
        top_k=k,
        candidate_pool_size=candidate_pool_size,
    )

    items: list[dict[str, Any]] = []
    for hit in hits:
        meta = hit.metadata or {}
        hours = meta.get("estimated_hours")
        items.append(
            {
                "chunk_id": str(hit.chunk_id),
                "document_id": str(hit.document_id),
                "budget_id": meta.get("budget_id"),
                "component_id": meta.get("component_id"),
                "estimated_hours": hours,
                "complexity": meta.get("complexity"),
                "client_sector": meta.get("client_sector"),
                "distance": round(float(hit.distance), 4),
                "snippet": hit.content[:400],
            }
        )

    return {
        "query": query,
        "component_type": component_type,
        "count": len(items),
        "items": items,
        "note": (
            "Use estimated_hours from items as reference_amounts for calculate_estimate. "
            "If results look weak, reformulate query and search again."
        ),
    }
