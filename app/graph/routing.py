"""Level 3 — conditional routing after validation."""

from __future__ import annotations

from typing import Literal

from app.graph.state import EstimationState

RouteName = Literal["validated", "needs_review"]


def route_after_validation(state: EstimationState) -> RouteName:
    """Route to END labels based on status set by validate_and_consolidate."""
    if state.get("status") == "needs_review":
        return "needs_review"
    return "validated"
