"""Typed shared state for the Session 13 estimation graph."""

from __future__ import annotations

import operator
from typing import Annotated, NotRequired, TypedDict


class Component(TypedDict):
    name: str
    category: str


class BudgetMatch(TypedDict):
    component: str
    reference_budget_id: str
    amount: float


class EstimationState(TypedDict):
    transcript: str
    estimation_id: str
    requirements: list[str]
    components: list[Component]
    # Accumulator: grows as each component is searched.
    budget_matches: Annotated[list[BudgetMatch], operator.add]
    estimate: NotRequired[dict | None]
    status: NotRequired[str | None]  # validated | needs_review
    errors: Annotated[list[str], operator.add]
