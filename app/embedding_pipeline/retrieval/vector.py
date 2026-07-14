"""Dense (vector) search over chunk embeddings."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk


async def search_vector(
    session: AsyncSession,
    query_vector: list[float],
    *,
    limit: int,
) -> list[Any]:
    """Return top-``limit`` chunks ordered by cosine distance (ascending)."""
    distance_expr = Chunk.embedding.cosine_distance(query_vector)
    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Chunk.chunk_type,
            Chunk.content,
            Chunk.metadata_,
            distance_expr.label("distance"),
        )
        .order_by(distance_expr)
        .limit(limit)
    )
    return list((await session.execute(stmt)).all())
