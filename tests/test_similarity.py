import math

import pytest

from app.embedding_pipeline.similarity import cosine_similarity


def test_cosine_identical_vectors() -> None:
    vec = [1.0, 0.0, 0.0]
    assert cosine_similarity(vec, vec) == pytest.approx(1.0)


def test_cosine_orthogonal_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_dimension_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="same dimensionality"):
        cosine_similarity([1.0], [1.0, 0.0])


def test_cosine_zero_vector_raises() -> None:
    with pytest.raises(ValueError, match="zero-norm"):
        cosine_similarity([0.0, 0.0], [1.0, 0.0])


def test_cosine_known_angle() -> None:
    vec_a = [1.0, 1.0]
    vec_b = [1.0, 0.0]
    expected = 1 / math.sqrt(2)
    assert cosine_similarity(vec_a, vec_b) == pytest.approx(expected)
