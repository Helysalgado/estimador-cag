"""Generate REPORT.md from evals/stress/results.csv."""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

from evals.stress.schema import CSV_COLUMNS

EXPECTED_TURNS = 20


def _percentile(sorted_values: list[int], pct: float) -> float:
    if not sorted_values:
        return 0.0
    idx = max(0, int(len(sorted_values) * pct) - 1)
    return float(sorted_values[idx])


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        first_line = handle.readline()
        handle.seek(0)
        if first_line.startswith("scenario,"):
            return list(csv.DictReader(handle))
        return list(csv.DictReader(handle, fieldnames=CSV_COLUMNS))


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep the last successful row per (scenario, kb, repeat, turn_index)."""
    buckets: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        if (row.get("error") or "").strip():
            continue
        turn = (row.get("turn_index") or "").strip()
        if not turn:
            continue
        key = (
            row["scenario"],
            row["attachment_size_kb"],
            row["repeat"],
            turn,
        )
        buckets[key] = row
    return list(buckets.values())


def _bool_cell(value: str) -> bool | None:
    if value == "":
        return None
    return value.strip().lower() in {"true", "1", "yes"}


def _float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def _int(value: str) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def build_report(rows: list[dict[str, str]]) -> str:
    errors = [r for r in rows if (r.get("error") or "").strip()]
    ok = dedupe_rows(rows)
    latencies = sorted(_int(r["latency_ms"]) for r in ok)
    costs = [_float(r["cost_usd"]) for r in ok]
    tokens = [_int(r["tokens_in"]) for r in ok]

    cache_hits = sum(
        1 for r in ok if r.get("cache_hit_kind") in {"exact", "semantic"}
    )
    cache_rate = cache_hits / len(ok) if ok else 0.0

    drift_rows = [r for r in ok if _bool_cell(r.get("memory_drift_passed", "")) is not None]
    drift_pass = sum(1 for r in drift_rows if _bool_cell(r["memory_drift_passed"]))
    drift_rate = drift_pass / len(drift_rows) if drift_rows else 0.0

    max_turn = max((_int(r["turn_index"]) for r in ok), default=0)
    scenarios = sorted({r["scenario"] for r in ok})
    sizes = sorted({r["attachment_size_kb"] for r in ok}, key=int)

    # Summary per scenario × attachment size
    summary_lines = [
        "| scenario | kb | n | P50 ms | P95 ms | total $ | drift % |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario in scenarios:
        for size_kb in sizes:
            group = [
                r
                for r in ok
                if r["scenario"] == scenario and r["attachment_size_kb"] == size_kb
            ]
            if not group:
                continue
            lats = sorted(_int(r["latency_ms"]) for r in group)
            group_cost = sum(_float(r["cost_usd"]) for r in group)
            drifts = [
                r
                for r in group
                if _bool_cell(r.get("memory_drift_passed", "")) is not None
            ]
            drift_pct = (
                100.0
                * sum(1 for r in drifts if _bool_cell(r["memory_drift_passed"]))
                / len(drifts)
                if drifts
                else 0.0
            )
            summary_lines.append(
                f"| {scenario} | {size_kb} | {len(group)} | "
                f"{_percentile(lats, 0.5):.0f} | {_percentile(lats, 0.95):.0f} | "
                f"{group_cost:.4f} | {drift_pct:.1f} |"
            )

    # Curve 1 — latency vs tokens_in (mean per 5k token bucket)
    token_buckets: dict[int, list[int]] = defaultdict(list)
    for row in ok:
        bucket = (_int(row["tokens_in"]) // 5000) * 5000
        token_buckets[bucket].append(_int(row["latency_ms"]))
    curve1_lines = ["| tokens_in (bucket) | avg_latency_ms | n |", "|---:|---:|---:|"]
    for bucket in sorted(token_buckets):
        values = token_buckets[bucket]
        curve1_lines.append(
            f"| {bucket} | {statistics.mean(values):.1f} | {len(values)} |"
        )

    # Curve 2 — mean cumulative cost vs turn_index (per session, then averaged)
    session_costs: dict[tuple[str, str, str, str], list[tuple[int, float]]] = defaultdict(list)
    for row in ok:
        key = (
            row["scenario"],
            row["attachment_size_kb"],
            row["repeat"],
            row["session_id"],
        )
        session_costs[key].append((_int(row["turn_index"]), _float(row["cost_usd"])))

    turn_cumulative: dict[int, list[float]] = defaultdict(list)
    for entries in session_costs.values():
        entries.sort(key=lambda item: item[0])
        running = 0.0
        for turn_index, cost in entries:
            running += cost
            turn_cumulative[turn_index].append(running)

    curve2_lines = ["| turn_index | mean_cumulative_cost_usd | n_sessions |", "|---:|---:|---:|"]
    for turn_index in sorted(turn_cumulative):
        values = turn_cumulative[turn_index]
        curve2_lines.append(
            f"| {turn_index} | {statistics.mean(values):.6f} | {len(values)} |"
        )

    # Curve 3 — memory drift rate vs turn_index
    drift_by_turn: dict[int, list[bool]] = defaultdict(list)
    for row in drift_rows:
        verdict = _bool_cell(row["memory_drift_passed"])
        if verdict is None:
            continue
        drift_by_turn[_int(row["turn_index"])].append(verdict)

    curve3_lines = ["| turn_index | mean_memory_drift | n |", "|---:|---:|---:|"]
    for turn_index in sorted(drift_by_turn):
        values = drift_by_turn[turn_index]
        curve3_lines.append(
            f"| {turn_index} | {statistics.mean(values):.2f} | {len(values)} |"
        )

    turn1 = [r for r in ok if _int(r["turn_index"]) == 1]
    turn_max = [r for r in ok if _int(r["turn_index"]) == max_turn and max_turn > 0]
    lat1 = statistics.mean(_int(r["latency_ms"]) for r in turn1) if turn1 else 0.0
    lat_max = statistics.mean(_int(r["latency_ms"]) for r in turn_max) if turn_max else 0.0
    lat_ratio = lat_max / lat1 if lat1 > 0 else 0.0

    cost1 = statistics.mean(_float(r["cost_usd"]) for r in turn1) if turn1 else 0.0
    cost_max = statistics.mean(_float(r["cost_usd"]) for r in turn_max) if turn_max else 0.0
    cost_ratio = cost_max / cost1 if cost1 > 0 else 0.0

    tok1 = statistics.mean(_int(r["tokens_in"]) for r in turn1) if turn1 else 0.0
    tok_max = statistics.mean(_int(r["tokens_in"]) for r in turn_max) if turn_max else 0.0

    incomplete = max_turn < EXPECTED_TURNS
    missing_scenarios = sorted(
        {"growing", "pivot", "contradiction"} - set(scenarios)
    )

    lines = [
        "# Stress Evaluation Report",
        "",
        f"Dataset source: `evals/stress/results.csv`  ",
        f"Rows in file: {len(rows)} (after dedupe: {len(ok)} successful turns, {len(errors)} errors)  ",
        "",
        "## Data quality notes",
        "",
    ]
    if rows and rows[0].get("scenario") in {"growing", "pivot", "contradiction"}:
        lines.append(
            "- CSV **sin fila de cabecera** detectada; columnas inferidas por el generador."
        )
    if incomplete:
        lines.append(
            f"- Corrida **incompleta**: turno máximo observado = **{max_turn}** "
            f"(objetivo del ejercicio: {EXPECTED_TURNS} por sesión)."
        )
    if missing_scenarios:
        lines.append(
            f"- Escenarios ausentes en los datos: **{', '.join(missing_scenarios)}**."
        )
    if len(rows) != len(ok) + len(errors):
        lines.append(
            f"- Se deduplicaron filas repetidas del mismo "
            f"`(scenario, kb, repeat, turn_index)`."
        )
    lines.extend(
        [
            "",
            "## Summary Table",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| P50 latency (ms) | {_percentile(latencies, 0.5):.0f} |",
            f"| P95 latency (ms) | {_percentile(latencies, 0.95):.0f} |",
            f"| Cumulative cost (USD) | {sum(costs):.4f} |",
            f"| Cache hit rate (`exact` + `semantic`) | {cache_rate:.2f} |",
            f"| Mean fact-tracker recall (drift, turns > 1) | {drift_rate:.2f} |",
            f"| Error rows | {len(errors)} |",
            "",
            "### By scenario × attachment size (KB)",
            "",
            *summary_lines,
            "",
            "## Curve 1 — `latency_ms` vs `tokens_in`",
            "",
            *curve1_lines,
            "",
            "## Curve 2 — cumulative `cost_usd` vs `turn_index`",
            "",
            *curve2_lines,
            "",
            "## Curve 3 — `MemoryDriftMetric` vs turn index",
            "",
            *curve3_lines,
            "",
            "## Quantitative findings",
            "",
            (
                f"Con **{len(ok)}** turnos medidos (deduplicados), la latencia P50 global fue "
                f"**{_percentile(latencies, 0.5):.0f} ms** y P95 **{_percentile(latencies, 0.95):.0f} ms**. "
                f"El coste acumulado registrado en el CSV suma **${sum(costs):.4f}**. "
                f"Los `tokens_in` medios pasan de **{tok1:.0f}** en el turno 1 a **{tok_max:.0f}** "
                f"en el turno {max_turn}, coherente con el crecimiento del contexto en ventana deslizante."
            ),
            "",
            (
                f"Comparando turno 1 vs turno {max_turn}, la latencia media sube "
                f"**{lat_ratio:.1f}×** ({lat1:.0f} ms → {lat_max:.0f} ms) y el coste por turno "
                f"**{cost_ratio:.1f}×** (${cost1:.4f} → ${cost_max:.4f}). "
                f"El recall del fact-tracker (`memory_drift_passed` en turnos > 1) promedia "
                f"**{drift_rate * 100:.1f}%**; en sesiones conversacionales el cache "
                f"permanece en `none` (tasa de hit **{cache_rate * 100:.1f}%**), como esperado "
                f"para el baseline CAG sin cache semántica en sesiones."
            ),
            "",
        ]
    )

    if incomplete or errors:
        lines.extend(
            [
                "## Follow-up",
                "",
                "Para un entregable completo del pre-ejercicio S6, re-ejecutar:",
                "",
                "```bash",
                "uv run python -m evals.stress.run \\",
                "  --http http://127.0.0.1:8000 \\",
                "  --scenarios growing,pivot,contradiction \\",
                "  --attachment-sizes 0,5,20,50,100 \\",
                "  --repeats 3 \\",
                "  --output evals/stress/results.csv",
                "",
                "uv run python -m evals.stress.build_report",
                "```",
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("evals/stress/results.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evals/stress/REPORT.md"),
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}")

    rows = load_rows(args.input)
    report = build_report(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote {args.output} ({len(report)} chars) from {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
