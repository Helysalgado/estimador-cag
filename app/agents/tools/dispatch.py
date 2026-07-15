"""Dispatch parsed tool calls to local implementations."""

from __future__ import annotations

import json
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.calculate_estimate import calculate_estimate
from app.agents.tools.search_budgets import search_budgets


async def execute_tool(
    session: AsyncSession,
    name: str,
    arguments: dict[str, Any],
    *,
    k: int = 5,
    search_mode: Literal["vector", "hybrid"] = "hybrid",
    rerank: bool = False,
) -> dict[str, Any]:
    if name == "search_budgets":
        return await search_budgets(
            session,
            query=str(arguments["query"]),
            component_type=arguments.get("component_type", "other"),
            k=k,
            search_mode=search_mode,
            rerank=rerank,
        )
    if name == "calculate_estimate":
        return calculate_estimate(list(arguments.get("components") or []))
    return {"error": f"unknown_tool:{name}"}


def parse_tool_arguments(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    return json.loads(raw or "{}")
