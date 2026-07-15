"""Compile the Session 13 estimation StateGraph (levels 1–3)."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    classify_components,
    extract_requirements,
    generate_estimate,
    search_budgets_node,
    validate_and_consolidate,
)
from app.graph.routing import route_after_validation
from app.graph.state import EstimationState


def build_graph(checkpointer: Any | None = None):
    """Wire the sequential graph; optional checkpointer enables persistence (N2)."""
    builder = StateGraph(EstimationState)
    builder.add_node("extract_requirements", extract_requirements)
    builder.add_node("classify_components", classify_components)
    builder.add_node("search_budgets", search_budgets_node)
    builder.add_node("generate_estimate", generate_estimate)
    builder.add_node("validate_and_consolidate", validate_and_consolidate)

    builder.add_edge(START, "extract_requirements")
    builder.add_edge("extract_requirements", "classify_components")
    builder.add_edge("classify_components", "search_budgets")
    builder.add_edge("search_budgets", "generate_estimate")
    builder.add_edge("generate_estimate", "validate_and_consolidate")
    # Level 3 — conditional edge (both paths terminate at END).
    builder.add_conditional_edges(
        "validate_and_consolidate",
        route_after_validation,
        {
            "validated": END,
            "needs_review": END,
        },
    )
    return builder.compile(checkpointer=checkpointer)
