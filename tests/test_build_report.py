from pathlib import Path

from evals.stress.build_report import build_report, dedupe_rows, load_rows
from evals.stress.schema import CSV_COLUMNS


def test_build_report_from_fixture(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    header = ",".join(CSV_COLUMNS)
    csv_path.write_text(
        f"{header}\n"
        "growing,0,1,1,s1,100,0,2,0,0,1000,50,0.01,2000,2500,none,default,True,True,,,Nimbus,\n"
        "growing,0,1,2,s1,100,0,4,0,0,2000,60,0.02,3000,3500,none,default,True,True,True,,Nimbus,\n",
        encoding="utf-8",
    )
    rows = load_rows(csv_path)
    report = build_report(rows)
    assert "Stress Evaluation Report" in report
    assert "P50 latency" in report
    assert "growing" in report
    assert "Quantitative findings" in report


def test_dedupe_keeps_last_row() -> None:
    rows = [
        {
            "scenario": "growing",
            "attachment_size_kb": "0",
            "repeat": "1",
            "turn_index": "1",
            "session_id": "s",
            "error": "",
            "latency_ms": "100",
            "tokens_in": "1",
            "cost_usd": "0.1",
            "memory_drift_passed": "",
            "cache_hit_kind": "none",
        },
        {
            "scenario": "growing",
            "attachment_size_kb": "0",
            "repeat": "1",
            "turn_index": "1",
            "session_id": "s",
            "error": "",
            "latency_ms": "200",
            "tokens_in": "2",
            "cost_usd": "0.2",
            "memory_drift_passed": "",
            "cache_hit_kind": "none",
        },
    ]
    deduped = dedupe_rows(rows)
    assert len(deduped) == 1
    assert deduped[0]["latency_ms"] == "200"
