#!/usr/bin/env python3
"""Run RAGAS metrics on the Session 11 golden set (grounded RAG estimate).

Prerequisites: Postgres with ingested corpus + OPENAI_API_KEY.

Usage::

    uv run python scripts/eval_ragas.py
    uv run python scripts/eval_ragas.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from statistics import mean

import httpx
from dotenv import load_dotenv
from httpx import HTTPStatusError

_REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_REPO_ROOT / ".env")

GOLDEN_SET_PATH = _REPO_ROOT / "evals" / "retrieval" / "golden_set.json"
REPORT_PATH = _REPO_ROOT / "evals" / "retrieval" / "RAGAS_REPORT.md"
LAST_RUN_PATH = _REPO_ROOT / "evals" / "retrieval" / "ragas_last_run.json"
DEFAULT_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
RAG_PATH = "/api/v1/rag/estimate"


def _estimate_to_response_text(estimate: dict) -> str:
    lines = []
    if estimate.get("summary"):
        lines.append(str(estimate["summary"]))
    for item in estimate.get("line_items") or []:
        hours = item.get("hours")
        grounded = item.get("grounded")
        desc = item.get("description", "")
        assumption = item.get("assumption") or ""
        lines.append(
            f"- {desc} | hours={hours} | grounded={grounded}"
            + (f" | assumption={assumption}" if assumption else "")
        )
    if estimate.get("total_hours") is not None:
        lines.append(f"total_hours={estimate['total_hours']}")
    return "\n".join(lines)


def collect_rows(client: httpx.Client) -> list[dict]:
    golden = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for entry in golden["queries"]:
        payload = {
            "query": entry["query"],
            "k": 5,
            "search_mode": "hybrid",
            "rerank": False,
            "candidate_pool_size": 50,
        }
        print(f"Generating for {entry['id']}...")
        last_error: Exception | None = None
        body = None
        for attempt in range(1, 4):
            resp = client.post(RAG_PATH, json=payload, timeout=180.0)
            if resp.status_code < 500:
                resp.raise_for_status()
                body = resp.json()
                break
            last_error = HTTPStatusError(
                f"{resp.status_code} on attempt {attempt}",
                request=resp.request,
                response=resp,
            )
            print(f"  retry {attempt}/3 after {resp.status_code}")
        if body is None:
            assert last_error is not None
            raise last_error
        contexts = body.get("retrieval", {}).get("contexts") or []
        rows.append(
            {
                "id": entry["id"],
                "question": entry["query"],
                "answer": _estimate_to_response_text(body["estimate"]),
                "contexts": contexts,
                "ground_truth": entry["ground_truth"],
                "citation_ok": body["citation_report"]["ok"],
                "request_id": body.get("request_id"),
            }
        )
    return rows


def run_ragas(rows: list[dict], *, judge_model: str, embedding_model: str):
    from datasets import Dataset
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    dataset = Dataset.from_dict(
        {
            "question": [r["question"] for r in rows],
            "answer": [r["answer"] for r in rows],
            "contexts": [r["contexts"] for r in rows],
            "ground_truth": [r["ground_truth"] for r in rows],
        }
    )
    llm = LangchainLLMWrapper(ChatOpenAI(model=judge_model, temperature=0))
    embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(model=embedding_model)
    )
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=embeddings,
    )
    return result


def _row_scores(result) -> list[dict]:
    """Extract per-row metric scores from a ragas EvaluationResult."""
    try:
        df = result.to_pandas()
    except Exception:  # noqa: BLE001
        return []
    scores: list[dict] = []
    for _, row in df.iterrows():
        scores.append(
            {
                "faithfulness": float(row.get("faithfulness", float("nan"))),
                "answer_relevancy": float(row.get("answer_relevancy", float("nan"))),
                "context_precision": float(row.get("context_precision", float("nan"))),
                "context_recall": float(row.get("context_recall", float("nan"))),
            }
        )
    return scores


def write_report(
    rows: list[dict],
    per_row: list[dict],
    *,
    judge_model: str,
    embedding_model: str,
    generation_model: str,
) -> None:
    metrics = [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    ]

    def fmt(value: float) -> str:
        if value != value:  # NaN
            return "—"
        return f"{value:.3f}"

    lines = [
        "# RAGAS report — Session 11",
        "",
        "Evaluation of grounded RAG estimates (`POST /api/v1/rag/estimate`) "
        "against `evals/retrieval/golden_set.json` (`ground_truth`).",
        "",
        f"- Generation model: `{generation_model}`",
        f"- Judge model: `{judge_model}`",
        f"- Embeddings (RAGAS): `{embedding_model}`",
        "- Retrieval: `search_mode=hybrid`, `rerank=false`, `k=5`",
        "",
        "| Query | Faithfulness | Answer relevancy | Context precision | Context recall | Citation OK |",
        "|-------|-------------:|-----------------:|------------------:|---------------:|:-----------:|",
    ]
    aggregates = {m: [] for m in metrics}
    for entry, scores in zip(rows, per_row, strict=True):
        for m in metrics:
            aggregates[m].append(scores[m])
        lines.append(
            "| {id} | {f} | {a} | {cp} | {cr} | {ok} |".format(
                id=entry["id"],
                f=fmt(scores["faithfulness"]),
                a=fmt(scores["answer_relevancy"]),
                cp=fmt(scores["context_precision"]),
                cr=fmt(scores["context_recall"]),
                ok="yes" if entry["citation_ok"] else "no",
            )
        )

    def avg(values: list[float]) -> float:
        clean = [v for v in values if v == v]
        return mean(clean) if clean else float("nan")

    lines.append(
        "| **Average** | {f} | {a} | {cp} | {cr} | — |".format(
            f=fmt(avg(aggregates["faithfulness"])),
            a=fmt(avg(aggregates["answer_relevancy"])),
            cp=fmt(avg(aggregates["context_precision"])),
            cr=fmt(avg(aggregates["context_recall"])),
        )
    )
    lines.extend(
        [
            "",
            "## Note",
            "",
            "Faithfulness should track how well line-level citations stay inside "
            "retrieved chunks; ungrounded lines (e.g. loyalty club in q05) are "
            "expected and may lower answer completeness without failing "
            "`verify_citations`. Context precision/recall reflect hybrid retrieval "
            "quality on the sample corpus more than the generator itself.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--judge-model",
        default=os.environ.get("RAGAS_JUDGE_MODEL", "gpt-4o-mini"),
    )
    parser.add_argument(
        "--embedding-model",
        default=os.environ.get("RAGAS_EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    parser.add_argument(
        "--generation-model",
        default=os.environ.get("RAG_GENERATION_MODEL", "gpt-4o-mini"),
    )
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is required", file=sys.stderr)
        return 1

    with httpx.Client(base_url=args.base_url) as client:
        health = client.get("/health", timeout=10.0)
        health.raise_for_status()
        rows = collect_rows(client)

    LAST_RUN_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Running RAGAS evaluate...")
    result = run_ragas(
        rows,
        judge_model=args.judge_model,
        embedding_model=args.embedding_model,
    )
    per_row = _row_scores(result)
    if len(per_row) != len(rows):
        # Fallback: use overall scores repeated if per-row unavailable
        overall = dict(result)
        per_row = [
            {
                "faithfulness": float(overall.get("faithfulness", float("nan"))),
                "answer_relevancy": float(overall.get("answer_relevancy", float("nan"))),
                "context_precision": float(overall.get("context_precision", float("nan"))),
                "context_recall": float(overall.get("context_recall", float("nan"))),
            }
            for _ in rows
        ]
        print("Warning: per-row scores unavailable; using overall averages in each row.")

    write_report(
        rows,
        per_row,
        judge_model=args.judge_model,
        embedding_model=args.embedding_model,
        generation_model=args.generation_model,
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
