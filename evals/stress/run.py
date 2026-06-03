"""Stress runner for conversational estimator memory/cost/latency."""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import httpx

from app.schemas.sessions import TurnObservation
from evals.stress.fixtures.build_pdfs import build_fixtures
from evals.stress.metrics import (
    AttachmentRecallMetric,
    CostBudgetMetric,
    LatencyBudgetMetric,
    MemoryDriftMetric,
)
from evals.stress.schema import CSV_COLUMNS
from evals.stress.scenarios import Scenario, ScenarioTurn, get_scenario

_API_PREFIX = "/api/v1"
_FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


@contextmanager
def _csv_output(path: Path) -> Iterator[Any]:
    """Write CSV to a local temp file, then copy once (avoids GDrive flush timeouts)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkstemp(prefix="stress_", suffix=".csv")[1])
    try:
        with tmp.open("w", newline="", encoding="utf-8") as handle:
            yield handle
        shutil.copyfile(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


@contextmanager
def _open_client(http_base_url: str | None) -> Iterator[httpx.Client | Any]:
    if http_base_url:
        with httpx.Client(base_url=http_base_url, timeout=300.0) as client:
            yield client
        return

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        yield client


def _attachment_files(size_kb: int, fixtures_dir: Path) -> list[tuple[str, tuple[str, bytes, str]]] | None:
    if size_kb == 0:
        return None
    path = fixtures_dir / f"attach_{size_kb}kb.pdf"
    if not path.exists():
        raise FileNotFoundError(
            f"Fixture {path} missing — run "
            "`uv run python -m evals.stress.fixtures.build_pdfs` first."
        )
    return [("attachments", (path.name, path.read_bytes(), "application/pdf"))]


def _form_body(scenario: Scenario, turn: ScenarioTurn) -> dict[str, str]:
    return {
        "transcript": turn.transcript,
        "project_type": scenario.project_type.value,
        "detail_level": scenario.detail_level.value,
        "output_format": scenario.output_format.value,
    }


def _estimate_path(mode: str, session_id: str) -> str:
    endpoint = "estimate-acb" if mode == "acb" else "estimate"
    return f"{_API_PREFIX}/sessions/{session_id}/{endpoint}"


def _fallback_observation(
    session_id: str,
    turn_index: int,
    transcript: str,
    attachments_total_chars: int,
) -> TurnObservation:
    return TurnObservation(
        turn_index=turn_index,
        session_id=session_id,
        enriched_transcript_chars=len(transcript),
        attachments_total_chars=attachments_total_chars,
        messages_in_window=0,
        anchors_count=0,
        summary_chars=0,
        tokens_in=0,
        tokens_out=0,
        cost_usd=0.0,
        latency_ms=0,
        cache_hit_kind="none",
        last_resolved_tier="default",
    )


def _execute_turn(
    client: httpx.Client | Any,
    session_id: str,
    scenario: Scenario,
    turn: ScenarioTurn,
    files: list | None,
    *,
    mode: str,
    allow_fallback: bool,
    turn_index: int,
    attachments_total_chars: int,
) -> tuple[TurnObservation, dict[str, Any], int, str]:
    t0 = time.perf_counter()
    try:
        response = client.post(
            _estimate_path(mode, session_id),
            data=_form_body(scenario, turn),
            files=files,
        )
        wall_ms = int((time.perf_counter() - t0) * 1000)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        if not allow_fallback:
            raise
        wall_ms = int((time.perf_counter() - t0) * 1000)
        observation = _fallback_observation(
            session_id, turn_index, turn.transcript, attachments_total_chars
        )
        return observation, {}, wall_ms, ""

    observation_dict = payload.get("observation")
    if observation_dict is None:
        if not allow_fallback:
            raise RuntimeError(
                "response.observation is missing — rebuild the API with TurnObservation support."
            )
        observation = _fallback_observation(
            session_id, turn_index, turn.transcript, attachments_total_chars
        )
    else:
        observation = TurnObservation(**observation_dict)

    snapshot_response = client.get(f"{_API_PREFIX}/sessions/{session_id}")
    snapshot_response.raise_for_status()
    response_text = str(payload.get("text") or "")
    return observation, snapshot_response.json(), wall_ms, response_text


def _run_one_session(
    client: httpx.Client | Any,
    scenario: Scenario,
    size_kb: int,
    repeat: int,
    latency_metric: LatencyBudgetMetric,
    cost_metric: CostBudgetMetric,
    fixtures_dir: Path,
    writer: csv.DictWriter,
    *,
    mode: str,
    allow_fallback: bool,
) -> tuple[int, int]:
    """Returns (rows_written, error_rows)."""
    files = _attachment_files(size_kb, fixtures_dir)
    attachment_chars = len(files[0][1][1]) if files else 0
    recall_metric = AttachmentRecallMetric() if size_kb > 0 else None

    create_resp = client.post(f"{_API_PREFIX}/sessions")
    create_resp.raise_for_status()
    session_id = create_resp.json()["session_id"]

    tracked_fact = scenario.turns[0].fact_introduced
    tracked_field = scenario.turns[0].fact_field
    drift_metric = (
        MemoryDriftMetric(fact=tracked_fact, fact_field=tracked_field)
        if tracked_fact
        else None
    )

    rows_written = 0
    error_rows = 0
    for turn_index, turn in enumerate(scenario.turns, start=1):
        row: dict[str, Any] = {
            "scenario": scenario.name,
            "attachment_size_kb": size_kb,
            "repeat": repeat,
            "tracked_fact": tracked_fact or "",
        }
        try:
            observation, snapshot, wall_ms, response_text = _execute_turn(
                client,
                session_id,
                scenario,
                turn,
                files,
                mode=mode,
                allow_fallback=allow_fallback,
                turn_index=turn_index,
                attachments_total_chars=attachment_chars,
            )
        except Exception as exc:  # noqa: BLE001
            row.update({"turn_index": "", "error": f"{type(exc).__name__}: {str(exc)[:200]}"})
            writer.writerow(row)
            return rows_written + 1, error_rows + 1

        latency_pass = latency_metric.evaluate(observation).passed
        cost_pass = cost_metric.evaluate(observation).passed
        if drift_metric is None or observation.turn_index == 1:
            drift_pass = ""
        else:
            drift_pass = bool(drift_metric.evaluate(snapshot).passed)

        if recall_metric is None:
            recall_pass = ""
        else:
            recall_pass = bool(
                recall_metric.evaluate(response_text=response_text, snapshot=snapshot).passed
            )

        row.update(
            {
                **observation.model_dump(),
                "wall_clock_ms": wall_ms,
                "latency_budget_passed": latency_pass,
                "cost_budget_passed": cost_pass,
                "memory_drift_passed": drift_pass,
                "attachment_recall_passed": recall_pass,
                "error": "",
            }
        )
        writer.writerow(row)
        rows_written += 1

    return rows_written, error_rows


def _count_errors(csv_path: Path) -> tuple[int, int, float]:
    with csv_path.open(encoding="utf-8") as handle:
        first = handle.readline()
        handle.seek(0)
        if first.startswith("scenario,"):
            rows = list(csv.DictReader(handle))
        else:
            rows = list(csv.DictReader(handle, fieldnames=CSV_COLUMNS))
    total = len(rows)
    errors = sum(1 for row in rows if (row.get("error") or "").strip())
    rate = errors / total if total else 0.0
    return total, errors, rate


def _print_summary(csv_path: Path) -> None:
    with csv_path.open(encoding="utf-8") as handle:
        first = handle.readline()
        handle.seek(0)
        if first.startswith("scenario,"):
            reader = csv.DictReader(handle)
        else:
            reader = csv.DictReader(handle, fieldnames=CSV_COLUMNS)
        rows = [row for row in reader if not (row.get("error") or "").strip()]

    by_group: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (row["scenario"], row["attachment_size_kb"])
        by_group.setdefault(key, []).append(row)

    print("\nSummary (per scenario × attachment size)")
    header = f"{'scenario':<14} {'kb':>4} {'n':>4} {'P50 ms':>8} {'P95 ms':>8} {'tot $':>10} {'drift%':>7}"
    print(header)
    print("-" * len(header))
    for (scenario, size_kb), group in sorted(by_group.items()):
        latencies = sorted(int(r["latency_ms"]) for r in group)
        costs = [float(r["cost_usd"]) for r in group]
        drifts = [r["memory_drift_passed"] for r in group if r["memory_drift_passed"] != ""]
        p50 = latencies[len(latencies) // 2] if latencies else 0
        p95_idx = max(0, int(len(latencies) * 0.95) - 1)
        p95 = latencies[p95_idx] if latencies else 0
        total_cost = sum(costs)
        drift_pct = (
            100.0 * sum(1 for d in drifts if str(d) in {"True", "true", "1"}) / len(drifts)
            if drifts
            else 0.0
        )
        print(
            f"{scenario:<14} {size_kb:>4} {len(group):>4} "
            f"{p50:>8} {p95:>8} {total_cost:>10.4f} {drift_pct:>6.1f}%"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--http",
        default=None,
        help="Base URL (e.g. http://localhost:8000). Omit for in-process TestClient smoke.",
    )
    parser.add_argument("--scenarios", default="growing,pivot,contradiction")
    parser.add_argument("--attachment-sizes", default="0,5,20,50,100")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--mode", choices=["actor", "acb"], default="actor")
    parser.add_argument("--latency-budget-ms", type=int, default=8000)
    parser.add_argument("--cost-budget-usd", type=float, default=0.25)
    parser.add_argument("--output", type=Path, default=Path("evals/stress/results.csv"))
    parser.add_argument(
        "--allow-fallback",
        action="store_true",
        help="On HTTP/observation failure, record zeroed telemetry instead of aborting.",
    )
    parser.add_argument(
        "--max-error-rate",
        type=float,
        default=0.2,
        help="Exit 1 if error rows / total rows exceed this ratio (default 0.2).",
    )
    args = parser.parse_args()

    scenarios = [get_scenario(name) for name in _parse_csv_list(args.scenarios)]
    sizes = _parse_int_list(args.attachment_sizes)
    fixtures_dir = _FIXTURES_DIR
    build_fixtures(fixtures_dir)
    for kb in sizes:
        if kb != 0:
            _attachment_files(kb, fixtures_dir)

    latency_metric = LatencyBudgetMetric(budget_ms=args.latency_budget_ms)
    cost_metric = CostBudgetMetric(budget_usd=args.cost_budget_usd)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    print(
        f"Stress run: {len(scenarios)} scenarios × {len(sizes)} sizes × "
        f"{args.repeats} repeats × up to 20 turns each (mode={args.mode})"
    )
    total_rows = 0
    total_errors = 0
    t_start = time.perf_counter()
    with _csv_output(args.output) as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        with _open_client(args.http) as client:
            for scenario in scenarios:
                for size_kb in sizes:
                    for repeat in range(1, args.repeats + 1):
                        print(
                            f"  → {scenario.name:<14} kb={size_kb:>3} "
                            f"repeat={repeat}/{args.repeats}"
                        )
                        written, errors = _run_one_session(
                            client,
                            scenario,
                            size_kb,
                            repeat,
                            latency_metric,
                            cost_metric,
                            fixtures_dir,
                            writer,
                            mode=args.mode,
                            allow_fallback=args.allow_fallback,
                        )
                        total_rows += written
                        total_errors += errors

    elapsed_s = int(time.perf_counter() - t_start)
    print(f"\nWrote {total_rows} rows to {args.output} in {elapsed_s}s ({total_errors} error rows)")
    _print_summary(args.output)

    _, errors, rate = _count_errors(args.output)
    if errors and rate > args.max_error_rate:
        print(
            f"Error rate {rate:.1%} exceeds --max-error-rate {args.max_error_rate:.1%}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
