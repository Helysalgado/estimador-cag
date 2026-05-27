from evals.stress.metrics import CostBudgetMetric, LatencyBudgetMetric, MemoryDriftMetric


def test_latency_budget_metric_pass_fail_limit():
    metric = LatencyBudgetMetric(4000)
    assert metric.evaluate({"latency_ms": 3999}).passed is True
    assert metric.evaluate({"latency_ms": 4001}).passed is False
    assert metric.evaluate({"latency_ms": 4000}).passed is True


def test_cost_budget_metric_pass_fail_limit():
    metric = CostBudgetMetric(0.05)
    assert metric.evaluate({"cost_usd": 0.01}).passed is True
    assert metric.evaluate({"cost_usd": 0.06}).passed is False
    assert metric.evaluate({"cost_usd": 0.05}).passed is True


def test_memory_drift_metric_pass_fail_limit():
    metric = MemoryDriftMetric("project name: nimbus")
    passing_snapshot = {
        "rolling_summary": "Project name: Nimbus and scope updated",
        "anchors": [],
        "project_metadata": {},
    }
    failing_snapshot = {
        "rolling_summary": "other summary",
        "anchors": [{"text": "budget locked: 30000 eur"}],
        "project_metadata": {"project_name": "Atlas"},
    }
    assert metric.evaluate(passing_snapshot).passed is True
    assert metric.evaluate(failing_snapshot).passed is False
    boundary = {
        "rolling_summary": "",
        "anchors": [{"text": "project name: nimbus"}],
        "project_metadata": {},
    }
    assert metric.evaluate(boundary).passed is True
