"""Pre-flight check: does the cross-encoder download, load and score?

Run BEFORE relying on rerank in the pipeline::

    docker compose exec ai_service uv run python -m app.embedding_pipeline.retrieval.verify_reranker
"""

from __future__ import annotations

import sys

from app.embedding_pipeline.retrieval.reranker import CrossEncoderReranker

_QUERY = "e-commerce checkout and shopping cart platform"
_DOCUMENTS = [
    "Online store checkout flow with shopping cart, payment and order management.",
    "Hospital patient appointment scheduling and telemedicine video consultations.",
]


def main() -> int:
    reranker = CrossEncoderReranker.from_settings()
    print(f"Loading reranker model: {reranker.model_name} ...")
    try:
        scores = reranker.score(_QUERY, _DOCUMENTS)
    except Exception as exc:  # noqa: BLE001 — surface any load/score failure
        print(
            f"FAILED to load or run the reranker: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    print(f"Query: {_QUERY!r}")
    print(f"Relevant doc:   score = {scores[0]:.4f}")
    print(f"Irrelevant doc: score = {scores[1]:.4f}")

    if scores[0] <= scores[1]:
        print(
            "WARNING: the relevant document did not outscore the irrelevant one. "
            "The model loaded, but its ranking looks off — check the model name.",
            file=sys.stderr,
        )
        return 2

    print("OK: reranker loaded and ranked the relevant document first.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
