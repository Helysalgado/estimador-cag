"""Stress metrics for latency, cost, and memory drift."""

from __future__ import annotations

import json
from typing import Any, Literal

from app.schemas.sessions import TurnObservation
from evals.metrics import MetricResult
from evals.stress.schema import STRESS_MARKER

FactField = Literal["project_name", "technologies", "scope", "summary", "any"]


class LatencyBudgetMetric:
    """1.0 if latency_ms <= budget_ms, else 0.0."""

    name = "latency_budget"

    def __init__(self, budget_ms: int) -> None:
        if budget_ms <= 0:
            raise ValueError("budget_ms must be positive")
        self.budget_ms = budget_ms

    def evaluate(self, observation: TurnObservation) -> MetricResult:
        passed = observation.latency_ms <= self.budget_ms
        return MetricResult(
            name=self.name,
            score=1.0 if passed else 0.0,
            passed=passed,
            details=f"{observation.latency_ms} ms vs budget {self.budget_ms} ms",
        )


class CostBudgetMetric:
    """1.0 if cost_usd <= budget_usd, else 0.0."""

    name = "cost_budget"

    def __init__(self, budget_usd: float) -> None:
        if budget_usd <= 0:
            raise ValueError("budget_usd must be positive")
        self.budget_usd = budget_usd

    def evaluate(self, observation: TurnObservation) -> MetricResult:
        passed = observation.cost_usd <= self.budget_usd
        return MetricResult(
            name=self.name,
            score=1.0 if passed else 0.0,
            passed=passed,
            details=f"${observation.cost_usd:.6f} vs budget ${self.budget_usd:.6f}",
        )


class MemoryDriftMetric:
    """Case-insensitive substring check for a fact in the session snapshot."""

    name = "memory_drift"

    def __init__(self, fact: str, fact_field: FactField = "any") -> None:
        if not fact:
            raise ValueError("fact must be a non-empty string")
        self.fact = fact
        self.needle = fact.lower()
        self.fact_field = fact_field

    def evaluate(self, snapshot: dict[str, Any]) -> MetricResult:
        haystack = self._haystack(snapshot)
        found = self.needle in haystack.lower()
        return MetricResult(
            name=self.name,
            score=1.0 if found else 0.0,
            passed=found,
            details=(
                f"fact={self.fact!r} field={self.fact_field} "
                f"{'present' if found else 'missing'}"
            ),
        )

    def _haystack(self, snapshot: dict[str, Any]) -> str:
        metadata = snapshot.get("project_metadata") or snapshot.get("metadata") or {}
        if self.fact_field == "project_name":
            return str(metadata.get("project_name") or "")
        if self.fact_field == "technologies":
            return " ".join(metadata.get("mentioned_technologies") or [])
        if self.fact_field == "scope":
            return str(metadata.get("agreed_scope") or "")
        if self.fact_field == "summary":
            return str(snapshot.get("rolling_summary") or snapshot.get("summary") or "")
        return json.dumps(snapshot, default=str)


class AttachmentRecallMetric:
    """1.0 if the PDF marker appears in the assistant text or session snapshot."""

    name = "attachment_recall"

    def __init__(self, marker: str = STRESS_MARKER) -> None:
        self.needle = marker.lower()

    def evaluate(self, *, response_text: str, snapshot: dict[str, Any]) -> MetricResult:
        anchors = snapshot.get("anchors") or []
        anchor_text = " ".join(str(item.get("text", "")) for item in anchors)
        haystack = " ".join(
            [
                response_text,
                str(snapshot.get("rolling_summary") or ""),
                anchor_text,
                str(snapshot.get("project_metadata") or snapshot.get("metadata") or ""),
            ]
        ).lower()
        found = self.needle in haystack
        return MetricResult(
            name=self.name,
            score=1.0 if found else 0.0,
            passed=found,
            details=f"marker={STRESS_MARKER!r} {'present' if found else 'missing'}",
        )
