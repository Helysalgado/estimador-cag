"""Unit tests for Session 12 agent tools (no OpenAI calls)."""

from app.agents.tools.calculate_estimate import calculate_estimate
from app.agents.tools.dispatch import parse_tool_arguments
from app.agents.tools.schemas import AGENT_TOOLS
from app.agents.trace import format_action, format_step


def test_calculate_estimate_median_and_total() -> None:
    result = calculate_estimate(
        [
            {"name": "Checkout", "reference_amounts": [100, 120, 140]},
            {"name": "Admin", "reference_amounts": [80, 100]},
        ]
    )
    assert result["components"][0]["estimated_hours"] == 120.0
    assert result["components"][1]["estimated_hours"] == 90.0
    assert result["total_hours"] == 210.0


def test_calculate_estimate_insufficient_refs() -> None:
    result = calculate_estimate([{"name": "Loyalty", "reference_amounts": []}])
    assert result["components"][0]["estimated_hours"] is None
    assert result["components"][0]["method"] == "insufficient_refs"
    assert result["total_hours"] == 0.0


def test_tool_schemas_are_flat_responses_shape() -> None:
    names = {tool["name"] for tool in AGENT_TOOLS}
    assert names == {"search_budgets", "calculate_estimate"}
    for tool in AGENT_TOOLS:
        assert tool["type"] == "function"
        assert "function" not in tool
        assert tool.get("strict") is True
        assert "parameters" in tool


def test_parse_tool_arguments() -> None:
    assert parse_tool_arguments('{"query":"Stripe","component_type":"integration"}')[
        "query"
    ] == "Stripe"


def test_format_step_trace() -> None:
    step = format_step(
        1,
        reasoning="Need Stripe comps",
        action=format_action("search_budgets", {"query": "Stripe", "component_type": "integration"}),
        observation='{"count": 2}',
    )
    assert step.startswith("STEP 1")
    assert "reasoning: Need Stripe comps" in step
    assert "action: search_budgets(" in step
    assert "observation:" in step
