"""Lexical (full-text) search over the Spanish ``content_tsv`` column."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk

# Sentinel cosine distance for chunks found only on the lexical branch.
NO_VECTOR_DISTANCE = 1.0


async def search_fulltext(
    session: AsyncSession,
    query_text: str,
    *,
    limit: int,
) -> list[Any]:
    """Return top-``limit`` chunks matching ``websearch_to_tsquery`` (spanish)."""
    ts_query = func.websearch_to_tsquery("spanish", query_text)
    rank_expr = func.ts_rank(Chunk.content_tsv, ts_query)
    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Chunk.chunk_type,
            Chunk.content,
            Chunk.metadata_,
            rank_expr.label("lexical_rank"),
        )
        .where(Chunk.content_tsv.op("@@")(ts_query))
        .order_by(rank_expr.desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).all())
