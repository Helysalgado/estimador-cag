"""Graph nodes: state → partial update (Session 13)."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.runnables import RunnableConfig
from openai import OpenAI

from app.agents.tools.calculate_estimate import calculate_estimate
from app.agents.tools.search_budgets import search_budgets
from app.config import settings
from app.graph.observability import node_span
from app.graph.state import BudgetMatch, Component, EstimationState

_CATEGORY_ENUM = ["integration", "migration", "frontend", "backend", "mobile", "other"]


def _llm_json(system: str, user: str) -> Any:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.responses.create(
        model=settings.GRAPH_LLM_MODEL,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        text={"format": {"type": "json_object"}},
    )
    text = getattr(response, "output_text", None) or "{}"
    return json.loads(text)


async def extract_requirements(
    state: EstimationState,
    config: RunnableConfig,
) -> dict[str, Any]:
    with node_span("extract_requirements"):
        data = _llm_json(
            system=(
                "Extract atomic software requirements from a meeting transcript. "
                'Return JSON: {"requirements": ["..."]}.'
            ),
            user=state["transcript"],
        )
        requirements = [
            str(r).strip() for r in (data.get("requirements") or []) if str(r).strip()
        ]
        if not requirements:
            return {
                "requirements": ["Unspecified software delivery from transcript"],
                "errors": ["extract_requirements: empty list; used fallback"],
            }
        return {"requirements": requirements}


async def classify_components(
    state: EstimationState,
    config: RunnableConfig,
) -> dict[str, Any]:
    with node_span("classify_components"):
        payload = json.dumps(state.get("requirements") or [], ensure_ascii=False)
        data = _llm_json(
            system=(
                "Group requirements into estimable software components. "
                f"Each component needs name and category in {_CATEGORY_ENUM}. "
                'Return JSON: {"components": [{"name": "...", "category": "..."}]}.'
            ),
            user=payload,
        )
        components: list[Component] = []
        for raw in data.get("components") or []:
            name = str(raw.get("name") or "").strip()
            category = str(raw.get("category") or "other").strip().lower()
            if category not in _CATEGORY_ENUM:
                category = "other"
            if name:
                components.append({"name": name, "category": category})
        if not components:
            return {
                "components": [{"name": "General delivery", "category": "other"}],
                "errors": ["classify_components: empty list; used fallback"],
            }
        return {"components": components}


async def search_budgets_node(
    state: EstimationState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Sequential per-component retrieval (no Send API in pre-work)."""
    with node_span("search_budgets"):
        configurable = (config or {}).get("configurable") or {}
        session = configurable.get("db_session")
        if session is None:
            return {"errors": ["search_budgets: missing db_session in config"]}

        k = int(configurable.get("k") or 5)
        search_mode = configurable.get("search_mode") or "hybrid"
        rerank = bool(configurable.get("rerank") or False)

        matches: list[BudgetMatch] = []
        errors: list[str] = []
        for component in state.get("components") or []:
            result = await search_budgets(
                session,
                query=component["name"],
                component_type=component.get("category", "other"),  # type: ignore[arg-type]
                k=k,
                search_mode=search_mode,
                rerank=rerank,
            )
            items = result.get("items") or []
            if not items:
                errors.append(f"no_hits:{component['name']}")
                continue
            for item in items[:3]:
                hours = item.get("estimated_hours")
                if hours is None:
                    continue
                matches.append(
                    {
                        "component": component["name"],
                        "reference_budget_id": str(item.get("budget_id") or "unknown"),
                        "amount": float(hours),
                    }
                )
        return {"budget_matches": matches, "errors": errors}


async def generate_estimate(
    state: EstimationState,
    config: RunnableConfig,
) -> dict[str, Any]:
    with node_span("generate_estimate"):
        by_name: dict[str, list[float]] = {}
        for match in state.get("budget_matches") or []:
            by_name.setdefault(match["component"], []).append(float(match["amount"]))

        components_payload = [
            {"name": name, "reference_amounts": amounts}
            for name, amounts in by_name.items()
        ]
        if not components_payload:
            for component in state.get("components") or []:
                components_payload.append(
                    {"name": component["name"], "reference_amounts": []}
                )

        calc = calculate_estimate(components_payload)
        estimate = {
            "components": calc["components"],
            "total_hours": calc["total_hours"],
            "method": calc["method"],
            "budget_matches": state.get("budget_matches") or [],
        }
        return {"estimate": estimate}


async def validate_and_consolidate(
    state: EstimationState,
    config: RunnableConfig,
) -> dict[str, Any]:
    with node_span("validate_and_consolidate"):
        estimate = state.get("estimate") or {}
        issues: list[str] = []

        matches = state.get("budget_matches") or []
        if not matches:
            issues.append("no_budget_matches")

        total = float(estimate.get("total_hours") or 0)
        if total <= 0:
            issues.append("total_hours_non_positive")

        for line in estimate.get("components") or []:
            if line.get("estimated_hours") is None:
                issues.append(f"ungrounded:{line.get('name')}")

        if issues:
            return {"status": "needs_review", "errors": issues}

        return {"status": "validated"}
