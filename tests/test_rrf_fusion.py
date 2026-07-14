"""Unit tests for Reciprocal Rank Fusion."""

from app.embedding_pipeline.retrieval.fusion import reciprocal_rank_fusion


def test_rrf_prefers_consensus_over_single_list_champion() -> None:
    semantic = [10, 20, 30]
    lexical = [40, 10, 50]
    fused = reciprocal_rank_fusion([semantic, lexical], k=60)
    ids = [chunk_id for chunk_id, _score in fused]
    # chunk 10 is 1st in semantic and 2nd in lexical → should rank above 20 (only in semantic)
    assert ids[0] == 10
    assert ids.index(10) < ids.index(20)


def test_rrf_includes_ids_from_either_list() -> None:
    fused = reciprocal_rank_fusion([[1, 2], [3, 1]], k=60)
    ids = {chunk_id for chunk_id, _ in fused}
    assert ids == {1, 2, 3}


def test_rrf_empty_rankings() -> None:
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []
