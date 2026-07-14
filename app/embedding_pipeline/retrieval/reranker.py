"""Cross-encoder reranker wrapper (Session 10).

Adapted from LIDR ``session_10`` ``app/generation/rag/retrieval/reranker.py``.
Loads lazily so imports stay cheap until something actually reranks.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

import structlog

from app.config import settings

log = structlog.get_logger(__name__)


class CrossEncoderReranker:
    """Lazily-loaded cross-encoder that rescores ``(query, document)`` pairs."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None
        self._load_lock = threading.Lock()

    @classmethod
    def from_settings(cls) -> CrossEncoderReranker:
        return cls(settings.RERANKER_MODEL_NAME)

    @property
    def model_name(self) -> str:
        return self._model_name

    def load(self) -> None:
        """Force-load the model (verify script / warmup)."""
        self._ensure_loaded()

    def _ensure_loaded(self):
        if self._model is not None:
            return self._model
        with self._load_lock:
            if self._model is not None:
                return self._model
            from sentence_transformers import CrossEncoder

            started = time.perf_counter()
            self._model = CrossEncoder(self._model_name)
            log.info(
                "reranker_loaded",
                model=self._model_name,
                load_ms=int((time.perf_counter() - started) * 1000),
            )
            return self._model

    def score(self, query: str, documents: list[str]) -> list[float]:
        """Relevance score for ``query`` against each document (higher = better)."""
        if not documents:
            return []
        model = self._ensure_loaded()
        pairs = [(query, document) for document in documents]
        started = time.perf_counter()
        scores = model.predict(pairs)
        log.info(
            "reranker_scored",
            model=self._model_name,
            pairs=len(pairs),
            score_ms=int((time.perf_counter() - started) * 1000),
        )
        return [float(score) for score in scores]

    def rerank(
        self,
        query: str,
        candidates: list[Any],
        *,
        top_n: int,
        text_of: Callable[[Any], str] = lambda candidate: candidate.content,
    ) -> list[Any]:
        """Reorder ``candidates`` by cross-encoder score; keep top ``top_n``."""
        if not candidates:
            return []
        scores = self.score(query, [text_of(candidate) for candidate in candidates])
        ranked = sorted(
            zip(candidates, scores, strict=True),
            key=lambda pair: pair[1],
            reverse=True,
        )
        log.info(
            "rerank_completed",
            candidates_in=len(candidates),
            candidates_out=min(top_n, len(ranked)),
        )
        return [candidate for candidate, _score in ranked[:top_n]]


_reranker_singleton: CrossEncoderReranker | None = None
_singleton_lock = threading.Lock()


def get_reranker() -> CrossEncoderReranker:
    """Process-wide lazy singleton for the configured reranker model."""
    global _reranker_singleton
    if _reranker_singleton is not None:
        return _reranker_singleton
    with _singleton_lock:
        if _reranker_singleton is None:
            _reranker_singleton = CrossEncoderReranker.from_settings()
        return _reranker_singleton
