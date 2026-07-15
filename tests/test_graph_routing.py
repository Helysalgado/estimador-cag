"""Unit tests for Session 13 graph routing (no OpenAI / DB)."""

from app.graph.build import build_graph
from app.graph.routing import route_after_validation


def test_route_after_validation_needs_review() -> None:
    assert (
        route_after_validation(
            {
                "transcript": "x",
                "estimation_id": "t",
                "requirements": [],
                "components": [],
                "budget_matches": [],
                "errors": [],
                "status": "needs_review",
            }
        )
        == "needs_review"
    )


def test_route_after_validation_validated() -> None:
    assert (
        route_after_validation(
            {
                "transcript": "x",
                "estimation_id": "t",
                "requirements": [],
                "components": [],
                "budget_matches": [],
                "errors": [],
                "status": "validated",
            }
        )
        == "validated"
    )


def test_build_graph_compiles_without_checkpointer() -> None:
    graph = build_graph(checkpointer=None)
    assert graph is not None
