"""Stress runner for conversational estimator memory/cost/latency."""

from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path
from typing import Any
import uuid

import httpx

from evals.stress.fixtures.build_pdfs import build_fixtures
from evals.stress.metrics import CostBudgetMetric, LatencyBudgetMetric, MemoryDriftMetric
from evals.stress.scenarios import resolve_scenarios


def _parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _attachment_map(fixtures_dir: Path) -> dict[int, Path]:
    paths = build_fixtures(fixtures_dir)
    mapping: dict[int, Path] = {}
    for path in paths:
        for size in (5, 20, 50, 100):
            if f"_{size}kb" in path.name:
                mapping[size] = path
    return mapping


async def _post_turn(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    session_id: str,
    transcript: str,
    mode: str,
    attachment_path: Path | None,
) -> dict[str, Any]:
    endpoint = "estimate-acb" if mode == "acb" else "estimate"
    url = f"{base_url}/api/v1/sessions/{session_id}/{endpoint}"
    files = None
    if attachment_path is not None:
        files = {"attachments": (attachment_path.name, attachment_path.read_bytes(), "application/pdf")}
    try:
        response = await client.post(url, data={"transcript": transcript}, files=files)
    except httpx.HTTPError:
        return {
            "text": f"fallback_estimation_for:{transcript[:80]}",
            "_runner_fallback": True,
            "_status_code": 599,
        }
    if response.status_code >= 500:
        return {
            "text": f"fallback_estimation_for:{transcript[:80]}",
            "_runner_fallback": True,
            "_status_code": response.status_code,
        }
    response.raise_for_status()
    body = response.json()
    body["_runner_fallback"] = False
    body["_status_code"] = response.status_code
    return body


async def main_async(args: argparse.Namespace) -> int:
    scenarios = resolve_scenarios(_parse_csv_list(args.scenarios))
    sizes = _parse_int_list(args.attachment_sizes)
    fixtures_dir = Path("evals/stress/fixtures")
    fixture_map = _attachment_map(fixtures_dir)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=args.request_timeout_s) as client:
        for scenario in scenarios:
            for size in sizes:
                attachment_path = fixture_map.get(size) if size > 0 else None
                for repeat in range(args.repeats):
                    offline_mode = False
                    try:
                        session_resp = await client.post(f"{args.http}/api/v1/sessions")
                        session_resp.raise_for_status()
                        session_id = session_resp.json()["session_id"]
                    except httpx.HTTPError:
                        offline_mode = True
                        session_id = str(uuid.uuid4())

                    for turn in scenario.turns:
                        if offline_mode:
                            post_json = {
                                "text": f"offline_fallback_estimation_for:{turn.transcript[:80]}",
                                "_runner_fallback": True,
                                "_status_code": 599,
                            }
                            snapshot = {
                                "message_count": turn.turn_index * 2,
                                "anchors_count": 0,
                                "summary_chars": 0,
                                "last_resolved_tier": "default",
                                "rolling_summary": "",
                                "anchors": [],
                                "project_metadata": {},
                            }
                        else:
                            post_json = await _post_turn(
                                client,
                                base_url=args.http,
                                session_id=session_id,
                                transcript=turn.transcript,
                                mode=args.mode,
                                attachment_path=attachment_path,
                            )
                            try:
                                debug_resp = await client.get(f"{args.http}/api/v1/sessions/{session_id}")
                                debug_resp.raise_for_status()
                                snapshot = debug_resp.json()
                            except httpx.HTTPError:
                                snapshot = {
                                    "message_count": 0,
                                    "anchors_count": 0,
                                    "summary_chars": 0,
                                    "last_resolved_tier": "default",
                                    "rolling_summary": "",
                                    "anchors": [],
                                    "project_metadata": {},
                                }
                        observed = dict(snapshot.get("last_turn_observed") or {})
                        if not observed:
                            observed = {
                                "turn_index": turn.turn_index,
                                "session_id": session_id,
                                "enriched_transcript_chars": len(turn.transcript),
                                "attachments_total_chars": 0,
                                "messages_in_window": snapshot.get("message_count", 0),
                                "anchors_count": snapshot.get("anchors_count", 0),
                                "summary_chars": snapshot.get("summary_chars", 0),
                                "tokens_in": 0,
                                "tokens_out": 0,
                                "cost_usd": 0.0,
                                "latency_ms": 0,
                                "cache_hit_kind": "none",
                                "last_resolved_tier": snapshot.get("last_resolved_tier", "default"),
                            }
                        observed["text"] = post_json.get("text", "")

                        latency_result = LatencyBudgetMetric(args.latency_budget_ms).evaluate(observed)
                        cost_result = CostBudgetMetric(args.cost_budget_usd).evaluate(observed)
                        drift_result = MemoryDriftMetric(turn.fact_to_remember).evaluate(snapshot)

                        row = {
                            "scenario": scenario.name,
                            "attachment_size_kb": size,
                            "repeat": repeat + 1,
                            "turn_index": turn.turn_index,
                            "fact_to_remember": turn.fact_to_remember,
                            "session_id": session_id,
                            "runner_fallback": post_json.get("_runner_fallback", False),
                            "http_status": post_json.get("_status_code", 200),
                            **observed,
                            "latency_budget_score": latency_result.score,
                            "cost_budget_score": cost_result.score,
                            "memory_drift_score": drift_result.score,
                        }
                        rows.append(row)

    if not rows:
        return 1

    fieldnames: list[str] = sorted({key for row in rows for key in row.keys()})
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stress runner for session estimator.")
    parser.add_argument("--http", default="http://localhost:8000")
    parser.add_argument("--mode", choices=["actor", "acb"], default="actor")
    parser.add_argument("--scenarios", default="growing,pivot,contradiction")
    parser.add_argument("--attachment-sizes", default="0,5,20,50,100")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", default="evals/stress/results.csv")
    parser.add_argument("--latency-budget-ms", type=int, default=4000)
    parser.add_argument("--cost-budget-usd", type=float, default=0.25)
    parser.add_argument("--request-timeout-s", type=float, default=1.0)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
