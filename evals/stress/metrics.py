"""Stress metrics for latency, cost, and memory drift."""

from __future__ import annotations

from evals.metrics import MetricResult


class LatencyBudgetMetric:
    """1.0 if latency_ms <= budget_ms, else 0.0."""

    def __init__(self, budget_ms: int) -> None:
        self.budget_ms = budget_ms

    def evaluate(self, observation: dict[str, object]) -> MetricResult:
        latency_ms = int(observation.get("latency_ms") or 0)
        passed = latency_ms <= self.budget_ms
        return MetricResult(
            name="LatencyBudgetMetric",
            score=1.0 if passed else 0.0,
            passed=passed,
            details={"latency_ms": latency_ms, "budget_ms": self.budget_ms},
        )


class CostBudgetMetric:
    """1.0 if cost_usd <= budget_usd, else 0.0."""

    def __init__(self, budget_usd: float) -> None:
        self.budget_usd = budget_usd

    def evaluate(self, observation: dict[str, object]) -> MetricResult:
        cost_usd = float(observation.get("cost_usd") or 0.0)
        passed = cost_usd <= self.budget_usd
        return MetricResult(
            name="CostBudgetMetric",
            score=1.0 if passed else 0.0,
            passed=passed,
            details={"cost_usd": cost_usd, "budget_usd": self.budget_usd},
        )


class MemoryDriftMetric:
    """1.0 if fact appears in summary, anchors, or metadata (case-insensitive)."""

    def __init__(self, fact: str, where: list[str] | None = None) -> None:
        self.fact = fact.lower()
        self.where = where or ["summary", "anchors", "metadata"]

    def evaluate(self, session_snapshot: dict[str, object]) -> MetricResult:
        locations: list[str] = []
        if "summary" in self.where:
            summary = str(session_snapshot.get("rolling_summary") or "").lower()
            if self.fact in summary:
                locations.append("summary")
        if "anchors" in self.where:
            anchors = session_snapshot.get("anchors") or []
            anchor_text = " ".join(str(item.get("text", "")) for item in anchors).lower()
            if self.fact in anchor_text:
                locations.append("anchors")
        if "metadata" in self.where:
            metadata = session_snapshot.get("project_metadata") or {}
            metadata_blob = str(metadata).lower()
            if self.fact in metadata_blob:
                locations.append("metadata")
        passed = bool(locations)
        return MetricResult(
            name="MemoryDriftMetric",
            score=1.0 if passed else 0.0,
            passed=passed,
            details={"fact": self.fact, "locations": locations},
        )
