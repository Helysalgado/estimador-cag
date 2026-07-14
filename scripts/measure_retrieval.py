#!/usr/bin/env python3
"""Artisanal retrieval measurement against a hand-annotated golden set (Session 10).

Runs configurations A–D against ``evals/retrieval/golden_set.json`` via HTTP:

  A  vector + no rerank
  B  hybrid + no rerank
  C  vector + rerank
  D  hybrid + rerank

Usage (API + corpus already up)::

    uv run python scripts/measure_retrieval.py --config all
    uv run python scripts/measure_retrieval.py --config A
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from statistics import median

import httpx

_REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_SET_PATH = _REPO_ROOT / "evals" / "retrieval" / "golden_set.json"
DEFAULT_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
SEARCH_PATH = "/api/v1/search"
TOP_K = 5
RUNS_PER_QUERY = 3
CANDIDATE_POOL_SIZE = 50

CONFIGS: dict[str, dict] = {
    "A": {"search_mode": "vector", "rerank": False},
    "B": {"search_mode": "hybrid", "rerank": False},
    "C": {"search_mode": "vector", "rerank": True},
    "D": {"search_mode": "hybrid", "rerank": True},
}


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Fraction of the top-k retrieved budget ids that are relevant."""
    top = retrieved_ids[:k]
    if not top:
        return 0.0
    hits = sum(1 for budget_id in top if budget_id in relevant_ids)
    return hits / len(top)


def _budget_ids_from_results(results: list[dict]) -> list[str]:
    ids: list[str] = []
    for item in results:
        meta = item.get("metadata") or {}
        budget_id = meta.get("budget_id")
        ids.append(str(budget_id) if budget_id is not None else "")
    return ids


def measure_config(client: httpx.Client, config_name: str) -> dict:
    cfg = CONFIGS[config_name]
    golden = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    precisions: list[float] = []
    latencies_ms: list[float] = []

    print("=" * 72)
    print(
        f"Config {config_name}: search_mode={cfg['search_mode']} rerank={cfg['rerank']}"
    )
    print("=" * 72)

    for entry in golden["queries"]:
        relevant_ids = set(entry["relevant_budget_ids"])
        payload = {
            "query": entry["query"],
            "k": TOP_K,
            "search_mode": cfg["search_mode"],
            "rerank": cfg["rerank"],
            "candidate_pool_size": CANDIDATE_POOL_SIZE,
        }

        # Warm-up (discard cold start for this query)
        warm = client.post(SEARCH_PATH, json=payload)
        warm.raise_for_status()

        last_results: list[dict] = []
        for _ in range(RUNS_PER_QUERY):
            started = time.perf_counter()
            response = client.post(SEARCH_PATH, json=payload)
            response.raise_for_status()
            latencies_ms.append((time.perf_counter() - started) * 1000)
            last_results = response.json()["results"]

        retrieved_ids = _budget_ids_from_results(last_results)
        precision = precision_at_k(retrieved_ids, relevant_ids, TOP_K)
        precisions.append(precision)
        print(
            f"  {entry['id']}: precision@{TOP_K}={precision:.2f} "
            f"budgets={retrieved_ids}"
        )

    mean_p = sum(precisions) / len(precisions) if precisions else 0.0
    med_lat = median(latencies_ms) if latencies_ms else 0.0
    print(f"  mean precision@{TOP_K}: {mean_p:.2f}")
    print(f"  median latency: {med_lat:.0f} ms")
    return {
        "config": config_name,
        "search_mode": cfg["search_mode"],
        "rerank": cfg["rerank"],
        "mean_precision_at_5": round(mean_p, 4),
        "median_latency_ms": round(med_lat, 1),
        "per_query_precision": dict(
            zip([q["id"] for q in golden["queries"]], precisions, strict=True)
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        choices=[*CONFIGS.keys(), "all"],
        default="all",
        help="Which configuration to measure (default: all)",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})",
    )
    args = parser.parse_args(argv)

    if not GOLDEN_SET_PATH.is_file():
        print(f"ERROR: golden set not found: {GOLDEN_SET_PATH}", file=sys.stderr)
        return 1

    names = list(CONFIGS.keys()) if args.config == "all" else [args.config]
    results: list[dict] = []

    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=180.0) as client:
        health = client.get("/health")
        health.raise_for_status()
        for name in names:
            results.append(measure_config(client, name))

    print()
    print("Summary")
    print(f"{'Config':<8} {'Mode':<8} {'Rerank':<8} {'P@5':>8} {'Latency_ms':>12}")
    for row in results:
        print(
            f"{row['config']:<8} {row['search_mode']:<8} {str(row['rerank']):<8} "
            f"{row['mean_precision_at_5']:>8.2f} {row['median_latency_ms']:>12.0f}"
        )

    out_path = _REPO_ROOT / "evals" / "retrieval" / "last_run.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
