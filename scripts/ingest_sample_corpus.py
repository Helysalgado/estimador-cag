#!/usr/bin/env python3
"""Ingest all budgets from data/budgets_sample.json into the vector store."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

SAMPLE_PATH = _REPO_ROOT / "data" / "budgets_sample.json"
DEFAULT_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
INGEST_PATH = "/api/v1/embeddings/ingest"


def main() -> int:
    budgets = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    base_url = DEFAULT_BASE_URL.rstrip("/")
    created = 0
    skipped = 0
    errors = 0

    with httpx.Client(base_url=base_url, timeout=120.0) as client:
        for budget in budgets:
            budget_id = budget["budget_id"]
            source_path = f"data/budgets/{budget_id}.json"
            payload = {
                "source_path": source_path,
                "document_type": "historical_budget",
                "content": budget,
            }
            response = client.post(INGEST_PATH, json=payload)
            if response.status_code == 200:
                body = response.json()
                print(f"OK  {source_path} -> document_id={body['document_id']} chunks={body['chunks_created']}")
                created += 1
            elif response.status_code == 409:
                body = response.json()
                print(f"SKIP {source_path} (already ingested, document_id={body['document_id']})")
                skipped += 1
            else:
                print(f"ERR {source_path} -> {response.status_code} {response.text}")
                errors += 1

    print(f"\nSummary: created={created} skipped={skipped} errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
