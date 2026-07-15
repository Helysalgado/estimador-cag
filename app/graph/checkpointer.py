"""Postgres checkpointer helpers for LangGraph (Session 13)."""

from __future__ import annotations

from app.config import settings


def checkpoint_postgres_uri() -> str:
    """Derive a psycopg-compatible URI from SQLAlchemy DATABASE_URL."""
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url.removeprefix("postgresql+asyncpg://")
    if url.startswith("postgres+asyncpg://"):
        return "postgresql://" + url.removeprefix("postgres+asyncpg://")
    return url
