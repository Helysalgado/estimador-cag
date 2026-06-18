from evals.metrics import content_recall_metric, cost_bounds_metric, schema_adherence_metric


def test_schema_adherence_metric_binary():
    assert schema_adherence_metric("phase cost confidence total") == 1
    assert schema_adherence_metric("just text") == 0


def test_cost_bounds_metric_binary():
    assert cost_bounds_metric("Totals: 45,000 EUR", min_cost=10000, max_cost=50000) == 1
    assert cost_bounds_metric("Totals: 900 EUR", min_cost=10000, max_cost=50000) == 0


def test_content_recall_metric_binary():
    assert content_recall_metric("Discovery QA Totals", must_include=["Discovery", "Totals"]) == 1
    assert content_recall_metric("Discovery only", must_include=["Discovery", "Totals"]) == 0
