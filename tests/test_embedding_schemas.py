import json
from pathlib import Path

from app.embedding_pipeline.schemas import Budget, IngestRequest


def test_budgets_sample_validates_against_schemas() -> None:
    raw = json.loads(Path("data/budgets_sample.json").read_text(encoding="utf-8"))
    request = IngestRequest(budgets=[Budget.model_validate(b) for b in raw])
    assert len(request.budgets) == 15
    assert sum(len(b.components) for b in request.budgets) == 45
