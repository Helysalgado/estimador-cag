import pytest

from app.embedding_pipeline.embedding_benchmark import benchmark


def test_benchmark_metrics_with_mock_embedder() -> None:
    def fake_embed(_text: str) -> list[float]:
        return [1.0, 0.0, 0.0]

    result = benchmark("mock", fake_embed, ["a", "b"])

    assert result["model"] == "mock"
    assert result["n_texts"] == 2
    assert result["dimensions"] == 3
    assert result["first_embedding_norm"] == pytest.approx(1.0)
    assert result["per_text_ms"] >= 0


def test_benchmark_rejects_empty_texts() -> None:
    with pytest.raises(ValueError, match="empty"):
        benchmark("mock", lambda t: [1.0], [])
