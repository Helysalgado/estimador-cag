"""CLI runner for golden eval dataset in actor/acb modes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

from evals.metrics import content_recall_metric, cost_bounds_metric, schema_adherence_metric


def _load_dataset(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_case(case: dict, *, mode: str, base_url: str) -> dict:
    with httpx.Client(timeout=120.0) as client:
        session_id = client.post(f"{base_url}/api/v1/sessions").json()["session_id"]
        endpoint = "estimate-acb" if mode == "acb" else "estimate"
        resp = client.post(
            f"{base_url}/api/v1/sessions/{session_id}/{endpoint}",
            data={"transcript": case["transcript"]},
        )
        resp.raise_for_status()
        text = resp.json().get("text", "")
    schema_ok = schema_adherence_metric(text)
    cost_ok = cost_bounds_metric(text, min_cost=case["min_cost"], max_cost=case["max_cost"])
    recall_ok = content_recall_metric(text, must_include=case["must_include"])
    return {
        "id": case["id"],
        "schema": schema_ok,
        "cost": cost_ok,
        "recall": recall_ok,
        "score": schema_ok + cost_ok + recall_ok,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run golden evals for estimator.")
    parser.add_argument("--mode", choices=["actor", "acb"], default="actor")
    parser.add_argument(
        "--dataset",
        default="evals/golden_dataset.json",
        help="Path to golden dataset JSON.",
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    dataset = _load_dataset(Path(args.dataset))
    results = [_run_case(case, mode=args.mode, base_url=args.base_url) for case in dataset]
    total = sum(item["score"] for item in results)
    max_total = len(results) * 3
    report = {"mode": args.mode, "cases": results, "total_score": total, "max_score": max_total}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
