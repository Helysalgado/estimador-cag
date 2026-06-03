from app.schemas.sessions import TurnObservation
from evals.stress.metrics import (
    AttachmentRecallMetric,
    CostBudgetMetric,
    LatencyBudgetMetric,
    MemoryDriftMetric,
)
from evals.stress.schema import STRESS_MARKER


def _obs(**kwargs: object) -> TurnObservation:
    defaults = {
        "turn_index": 1,
        "session_id": "s1",
        "enriched_transcript_chars": 10,
        "attachments_total_chars": 0,
        "messages_in_window": 2,
        "anchors_count": 0,
        "summary_chars": 0,
        "tokens_in": 100,
        "tokens_out": 50,
        "cost_usd": 0.01,
        "latency_ms": 1000,
    }
    defaults.update(kwargs)
    return TurnObservation(**defaults)  # type: ignore[arg-type]


def test_latency_budget_metric_pass_fail_limit():
    metric = LatencyBudgetMetric(4000)
    assert metric.evaluate(_obs(latency_ms=3999)).passed is True
    assert metric.evaluate(_obs(latency_ms=4001)).passed is False
    assert metric.evaluate(_obs(latency_ms=4000)).passed is True


def test_cost_budget_metric_pass_fail_limit():
    metric = CostBudgetMetric(0.05)
    assert metric.evaluate(_obs(cost_usd=0.01)).passed is True
    assert metric.evaluate(_obs(cost_usd=0.06)).passed is False
    assert metric.evaluate(_obs(cost_usd=0.05)).passed is True


def test_memory_drift_metric_pass_fail_limit():
    metric = MemoryDriftMetric("Nimbus", fact_field="project_name")
    passing_snapshot = {
        "rolling_summary": "other",
        "anchors": [],
        "project_metadata": {"project_name": "Nimbus"},
    }
    failing_snapshot = {
        "rolling_summary": "other summary",
        "anchors": [],
        "project_metadata": {"project_name": "Atlas"},
    }
    assert metric.evaluate(passing_snapshot).passed is True
    assert metric.evaluate(failing_snapshot).passed is False

    any_metric = MemoryDriftMetric("Flutter", fact_field="any")
    assert any_metric.evaluate(
        {"rolling_summary": "", "anchors": [{"text": "Flutter SDK"}], "project_metadata": {}}
    ).passed is True


def test_attachment_recall_metric_finds_marker_in_response():
    metric = AttachmentRecallMetric()
    assert metric.evaluate(
        response_text=f"See {STRESS_MARKER} in the attachment summary.",
        snapshot={"rolling_summary": "", "anchors": []},
    ).passed is True
    assert metric.evaluate(
        response_text="No marker here.",
        snapshot={"rolling_summary": "", "anchors": []},
    ).passed is False
