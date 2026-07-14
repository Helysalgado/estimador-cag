"""Session 10 retrieval: hybrid search, RRF fusion, and cross-encoder reranking."""

from app.embedding_pipeline.retrieval.pipeline import retrieve
from app.embedding_pipeline.retrieval.reranker import CrossEncoderReranker

__all__ = ["CrossEncoderReranker", "retrieve"]
