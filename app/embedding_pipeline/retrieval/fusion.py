"""Reciprocal Rank Fusion for combining ranked retrieval lists."""

from __future__ import annotations

from collections import defaultdict

DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(
    rankings: list[list[int]],
    k: int = DEFAULT_RRF_K,
) -> list[tuple[int, float]]:
    """Fuse multiple ranked lists of chunk ids into a single ranking.

    Scores depend only on rank positions (1-based), never on raw similarity
    scores, so cosine distance and ``ts_rank`` can be combined safely.

    Returns ``(chunk_id, rrf_score)`` pairs, best first.
    """
    scores: dict[int, float] = defaultdict(float)

    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] += 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
