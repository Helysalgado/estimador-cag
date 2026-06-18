#!/usr/bin/env python3
"""Compare cosine similarity between two texts using OpenAI embeddings."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow `uv run python scripts/compare.py` from repo root.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.embedding_pipeline.embedder import OpenAIEmbedder
from app.embedding_pipeline.similarity import cosine_similarity


def main() -> int:
    load_dotenv(_REPO_ROOT / ".env")

    parser = argparse.ArgumentParser(
        description="Embed two texts and print their cosine similarity.",
    )
    parser.add_argument("--text-a", required=True, help="First text to embed")
    parser.add_argument("--text-b", required=True, help="Second text to embed")
    args = parser.parse_args()

    embedder = OpenAIEmbedder()
    vec_a = embedder.embed_one(args.text_a)
    vec_b = embedder.embed_one(args.text_b)
    similarity = cosine_similarity(vec_a, vec_b)

    print(f"Text A: {args.text_a}")
    print(f"Text B: {args.text_b}")
    print(f"Cosine similarity: {similarity:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
