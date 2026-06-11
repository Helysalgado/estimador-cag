#!/usr/bin/env python3
"""Run representative semantic search queries against POST /search."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

DEFAULT_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
SEARCH_PATH = "/api/v1/search"
CONTENT_PREVIEW_CHARS = 120

QUERIES = [
    ("1_sanity_direct_match", "REST API development with JWT authentication for financial sector"),
    (
        "2_semantic_rephrase",
        "secure backend service with token-based access control for banking applications",
    ),
    ("3_different_domain", "mobile application for restaurant reservations"),
    ("4_ambiguous", "integration with external system"),
    (
        "5_specific_technical",
        "migration from monolith to microservices architecture using Kubernetes",
    ),
]


def _preview(text: str) -> str:
    text = text.replace("\n", " ")
    if len(text) <= CONTENT_PREVIEW_CHARS:
        return text
    return text[:CONTENT_PREVIEW_CHARS] + "..."


def main() -> int:
    base_url = os.environ.get("API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    with httpx.Client(base_url=base_url, timeout=60.0) as client:
        for label, query in QUERIES:
            print("=" * 72)
            print(f"Query [{label}]: {query}")
            response = client.post(SEARCH_PATH, json={"query": query, "k": 5})
            if response.status_code != 200:
                print(f"ERROR {response.status_code}: {response.text}")
                return 1

            body = response.json()
            print(f"search_time_ms={body['search_time_ms']}")
            for rank, item in enumerate(body["results"], start=1):
                print(
                    f"  {rank}. chunk_id={item['chunk_id']} "
                    f"distance={item['distance']:.4f} "
                    f"chunk_type={item['chunk_type']}"
                )
                print(f"     {_preview(item['content'])}")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
