"""Compare latency and vector size: OpenAI embeddings vs local MiniLM (lab script, not S7 deliverable)."""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from openai import OpenAI

# Allow `uv run python app/embedding_pipeline/embedding_benchmark.py` from repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

load_dotenv(_REPO_ROOT / ".env")

from app.config import settings
from app.embedding_pipeline.chunker import EMBEDDING_MODEL
LOCAL_MINILM_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

DEFAULT_SAMPLE_TEXTS = [
    "OAuth 2.0 authentication backend with JWT tokens for fintech mobile app",
    "Product catalog service with full-text search and category filtering",
    "GDPR consent management module with audit log",
    "Kubernetes deployment pipeline with blue-green release strategy",
]


def _vector_norm(vec: list[float]) -> float:
    return math.sqrt(sum(x * x for x in vec))


def benchmark(name: str, embed_fn: Callable[[str], list[float]], texts: list[str]) -> dict:
    """Run an embedding function over texts and return basic timing/size metrics."""
    if not texts:
        raise ValueError("texts must not be empty")

    start = time.perf_counter()
    embeddings = [embed_fn(t) for t in texts]
    elapsed = time.perf_counter() - start

    return {
        "model": name,
        "n_texts": len(texts),
        "total_seconds": round(elapsed, 3),
        "per_text_ms": round((elapsed / len(texts)) * 1000, 1),
        "dimensions": len(embeddings[0]),
        "first_embedding_norm": round(_vector_norm(embeddings[0]), 4),
    }


def make_openai_embedder(*, dimensions: int = 1536) -> Callable[[str], list[float]]:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def embed(text: str) -> list[float]:
        kwargs: dict = {"model": EMBEDDING_MODEL, "input": text}
        if dimensions != 1536:
            kwargs["dimensions"] = dimensions
        response = client.embeddings.create(**kwargs)
        return response.data[0].embedding

    return embed


def make_local_minilm_embedder():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "Local benchmark requires sentence-transformers. "
            "Install with: uv sync --extra benchmark"
        ) from exc

    model = SentenceTransformer(LOCAL_MINILM_MODEL)

    def embed(text: str) -> list[float]:
        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    return embed


def run_default_benchmarks(texts: list[str] | None = None) -> list[dict]:
    sample = texts or DEFAULT_SAMPLE_TEXTS
    results = [
        benchmark("openai-3-small-1536d", make_openai_embedder(dimensions=1536), sample),
        benchmark("openai-3-small-256d", make_openai_embedder(dimensions=256), sample),
        benchmark("local-minilm-l6-v2", make_local_minilm_embedder(), sample),
    ]
    return results


def main() -> int:
    for row in run_default_benchmarks():
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
