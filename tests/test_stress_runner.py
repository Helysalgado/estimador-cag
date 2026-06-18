"""Smoke tests for the stress runner CSV orchestration (no real LLM)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from app.schemas.estimation import DetailLevel, OutputFormat, ProjectType

from evals.stress.metrics import CostBudgetMetric, LatencyBudgetMetric
from evals.stress.run import _run_one_session
from evals.stress.schema import CSV_COLUMNS
from app.services.sessions import ProjectMetadata
from evals.stress.scenarios import Scenario, ScenarioTurn


def _tiny_scenario(*, turn_count: int = 3) -> Scenario:
    turns = [
        ScenarioTurn(
            transcript=(
                "We want a B2B SaaS called Nimbus for procurement teams. "
                "Stack: React + Postgres. Team of 3."
            ),
            fact_introduced="Nimbus",
            fact_field="project_name",
        ),
        ScenarioTurn(
            transcript="Turn 2: add SSO with Okta for employees and vendor users.",
            fact_introduced="Okta",
            fact_field="technologies",
        ),
        ScenarioTurn(
            transcript="Turn 3: confirmed budget 60k EUR; team stays at 3 developers.",
            fact_introduced="60",
            fact_field="any",
        ),
    ]
    for index in range(4, 21):
        turns.append(
            ScenarioTurn(
                transcript=f"Turn {index}: expand scope with another integration point.",
                fact_introduced=None,
            )
        )
    scenario = Scenario(
        name="growing",
        project_type=ProjectType.WEB_SAAS,
        detail_level=DetailLevel.MEDIUM,
        output_format=OutputFormat.PHASES_TABLE,
        turns=turns,
    )
    object.__setattr__(scenario, "turns", scenario.turns[:turn_count])
    return scenario


@pytest.fixture
def stress_llm_stub(monkeypatch):
    def fake_generate_sync_messages(*, messages, config):  # noqa: ANN001, ARG001
        user_text = messages[-1]["content"]
        return {
            "estimation": f"Estimate for Nimbus mentioning: {user_text[:80]}",
            "tokens_in": 120,
            "tokens_out": 60,
            "cost_usd": 0.002,
            "latency_ms": 1500,
        }

    monkeypatch.setattr(
        "app.services.session_estimation.generate_sync_messages",
        fake_generate_sync_messages,
    )
    monkeypatch.setattr(
        "app.services.session_estimation.render_session_system_prompt",
        lambda **kwargs: "SYSTEM-STUB",
    )
    monkeypatch.setattr(
        "app.services.session_estimation.extract_project_metadata_update",
        lambda **kwargs: ProjectMetadata(),
    )


def test_runner_writes_csv_with_expected_columns(client, stress_llm_stub, tmp_path: Path):
    scenario = _tiny_scenario()
    csv_path = tmp_path / "smoke.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        written, errors = _run_one_session(
            client,
            scenario,
            0,
            1,
            LatencyBudgetMetric(budget_ms=60_000),
            CostBudgetMetric(budget_usd=10.0),
            tmp_path,
            writer,
            mode="actor",
            allow_fallback=False,
        )

    assert errors == 0
    assert written == 3
    with csv_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    turn_indices = [int(row["turn_index"]) for row in rows]
    assert turn_indices == [1, 2, 3]
    for row in rows:
        assert row["scenario"] == "growing"
        assert row["error"] == ""
        assert int(row["tokens_in"]) > 0
    assert rows[0]["memory_drift_passed"] == ""
    assert rows[1]["memory_drift_passed"] in {"True", "False"}
    assert rows[0]["attachment_recall_passed"] == ""


def test_runner_records_error_row_on_validation_failure(client, stress_llm_stub, tmp_path: Path):
    scenario = _tiny_scenario(turn_count=20)
    bad_turns = [scenario.turns[0], ScenarioTurn(transcript="", fact_introduced=None)]
    object.__setattr__(scenario, "turns", bad_turns)

    csv_path = tmp_path / "errors.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        written, errors = _run_one_session(
            client,
            scenario,
            0,
            1,
            LatencyBudgetMetric(budget_ms=60_000),
            CostBudgetMetric(budget_usd=10.0),
            tmp_path,
            writer,
            mode="actor",
            allow_fallback=False,
        )

    assert written == 2
    assert errors == 1
    with csv_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[-1]["error"].startswith("HTTPStatusError") or "422" in rows[-1]["error"]
