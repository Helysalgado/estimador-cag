"""Synthetic multi-turn scenarios for stress evaluation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioTurn:
    turn_index: int
    transcript: str
    fact_to_remember: str


@dataclass(frozen=True)
class StressScenario:
    name: str
    turns: list[ScenarioTurn]


SCENARIOS: dict[str, StressScenario] = {
    "growing": StressScenario(
        name="growing",
        turns=[
            ScenarioTurn(1, "Project name is Nimbus. Build a SaaS CRM MVP.", "project name: Nimbus"),
            ScenarioTurn(2, "Add authentication and role permissions.", "feature: authentication"),
            ScenarioTurn(3, "Need multi-tenant support for agencies.", "feature: multi-tenant"),
            ScenarioTurn(4, "Add audit log for all account actions.", "feature: audit log"),
            ScenarioTurn(5, "Add CSV export for reports.", "feature: CSV export"),
            ScenarioTurn(6, "Need dashboard analytics and alerts.", "feature: dashboard analytics"),
        ],
    ),
    "pivot": StressScenario(
        name="pivot",
        turns=[
            ScenarioTurn(1, "Project Atlas starts with React web app.", "stack includes React"),
            ScenarioTurn(2, "Backend with FastAPI and PostgreSQL.", "stack includes FastAPI"),
            ScenarioTurn(3, "Team asks for mobile-first roadmap.", "strategy: mobile-first"),
            ScenarioTurn(4, "Drop React frontend for Flutter.", "stack includes Flutter"),
            ScenarioTurn(5, "Keep API backend and add push notifications.", "feature: push notifications"),
            ScenarioTurn(6, "Prioritize app store launch.", "milestone: app store launch"),
        ],
    ),
    "contradiction": StressScenario(
        name="contradiction",
        turns=[
            ScenarioTurn(1, "Project Orion budget is 30000 EUR.", "budget locked: 30000 EUR"),
            ScenarioTurn(2, "Must include secure login and GDPR controls.", "constraint: secure login"),
            ScenarioTurn(3, "Timeline target is 10 weeks.", "timeline: 10 weeks"),
            ScenarioTurn(4, "Actually budget can be 80000 EUR if needed.", "budget locked: 80000 EUR"),
            ScenarioTurn(5, "Reduce scope to keep critical features only.", "scope: critical features"),
            ScenarioTurn(6, "Final decision still expects security and audit trail.", "constraint: audit trail"),
        ],
    ),
}


def resolve_scenarios(names: list[str]) -> list[StressScenario]:
    return [SCENARIOS[name] for name in names]
