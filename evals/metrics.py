"""Eval metrics and helpers."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol


@dataclass
class MetricResult:
    name: str
    score: float
    passed: bool
    details: dict[str, object]


class Metric(Protocol):
    def evaluate(self, observation: dict[str, object]) -> MetricResult: ...


class SchemaAdherenceMetric:
    """1.0 when response roughly follows estimator structure."""

    def evaluate(self, observation: dict[str, object]) -> MetricResult:
        text = str(observation.get("text", ""))
        needed = ["phase", "cost", "confidence", "total"]
        lowered = text.lower()
        score = float(all(token in lowered for token in needed))
        return MetricResult(
            name="SchemaAdherenceMetric",
            score=score,
            passed=bool(score),
            details={"needed": needed},
        )


class CostBoundsMetric:
    """1.0 when at least one detected cost is within expected bounds."""

    def __init__(self, *, min_cost: int, max_cost: int) -> None:
        self.min_cost = min_cost
        self.max_cost = max_cost

    def evaluate(self, observation: dict[str, object]) -> MetricResult:
        text = str(observation.get("text", ""))
        matches = re.findall(r"(\d{1,3}(?:,\d{3})+|\d+)", text.replace(".", ""))
        values = [int(value.replace(",", "")) for value in matches]
        score = float(any(self.min_cost <= value <= self.max_cost for value in values))
        return MetricResult(
            name="CostBoundsMetric",
            score=score,
            passed=bool(score),
            details={"min_cost": self.min_cost, "max_cost": self.max_cost},
        )


class ContentRecallMetric:
    """1.0 when all expected content markers are present."""

    def __init__(self, *, must_include: list[str]) -> None:
        self.must_include = must_include

    def evaluate(self, observation: dict[str, object]) -> MetricResult:
        text = str(observation.get("text", ""))
        lowered = text.lower()
        score = float(all(fragment.lower() in lowered for fragment in self.must_include))
        return MetricResult(
            name="ContentRecallMetric",
            score=score,
            passed=bool(score),
            details={"must_include": self.must_include},
        )


def run_all_metrics(observation: dict[str, object], metrics: list[Metric]) -> list[MetricResult]:
    return [metric.evaluate(observation) for metric in metrics]


def schema_adherence_metric(text: str) -> int:
    return int(SchemaAdherenceMetric().evaluate({"text": text}).score)


def cost_bounds_metric(text: str, *, min_cost: int, max_cost: int) -> int:
    return int(CostBoundsMetric(min_cost=min_cost, max_cost=max_cost).evaluate({"text": text}).score)


def content_recall_metric(text: str, *, must_include: list[str]) -> int:
    return int(ContentRecallMetric(must_include=must_include).evaluate({"text": text}).score)
