import json
from pathlib import Path

import pytest

from app.embedding_pipeline.chunker import JSONStructuralChunker, build_chunk_text, count_tokens
from app.embedding_pipeline.schemas import Budget


@pytest.fixture
def sample_budgets() -> list[Budget]:
    raw = json.loads(Path("data/budgets_sample.json").read_text(encoding="utf-8"))
    return [Budget.model_validate(b) for b in raw]


def test_chunk_sample_produces_one_chunk_per_component(
    sample_budgets: list[Budget],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.embedding_pipeline.chunker.count_tokens",
        lambda text: max(1, len(text) // 4),
    )
    chunks = JSONStructuralChunker().chunk(sample_budgets)
    assert len(chunks) == 45
    assert chunks[0].chunk_id == "BUD-2024-014::AUTH-001"
    assert "[Project: Mobile banking API" in chunks[0].text
    assert chunks[0].metadata.client_sector == "finance"
    assert chunks[0].metadata.component_id == "AUTH-001"


def test_build_chunk_text_includes_parent_context() -> None:
    raw = json.loads(Path("data/budgets_sample.json").read_text(encoding="utf-8"))
    budget = Budget.model_validate(raw[0])
    component = budget.components[0]
    text = build_chunk_text(budget, component)
    assert "OAuth 2.0 authentication backend" in text
    assert "ruby_on_rails, postgresql, redis" in text
    assert "Complexity: high" in text


def test_count_tokens_positive_for_non_empty_text() -> None:
    try:
        assert count_tokens("hello world") >= 1
    except OSError:
        pytest.skip("tiktoken encoding download unavailable in this environment")
