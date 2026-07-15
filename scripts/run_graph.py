#!/usr/bin/env python3
"""Run the Session 13 LangGraph estimator and write GRAPH_TRACE.md.

Usage::

    uv run python scripts/run_graph.py \\
      --transcript examples/agent/sample_transcript_complex.txt
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

_REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_REPO_ROOT / ".env")
sys.path.insert(0, str(_REPO_ROOT))

from app.db.session import async_session_factory, dispose_engine  # noqa: E402
from app.graph.build import build_graph  # noqa: E402
from app.graph.checkpointer import checkpoint_postgres_uri  # noqa: E402
from app.graph.observability import configure_logfire  # noqa: E402
from app.graph.runner import run_estimation_graph  # noqa: E402


async def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=_REPO_ROOT / "evals" / "agent" / "GRAPH_TRACE.md",
    )
    parser.add_argument("--estimation-id", default=None)
    args = parser.parse_args()

    configure_logfire()
    transcript = args.transcript.read_text(encoding="utf-8")

    pool = AsyncConnectionPool(
        conninfo=checkpoint_postgres_uri(),
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False,
    )
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    graph = build_graph(checkpointer)

    async with async_session_factory() as session:
        result = await run_estimation_graph(
            graph=graph,
            session=session,
            transcript=transcript,
            estimation_id=args.estimation_id,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        [
            "# Graph trace — Session 13",
            "",
            f"- transcript: `{args.transcript}`",
            f"- thread_id: `{result.thread_id}`",
            f"- status: `{result.status}`",
            f"- node_spans: `{result.node_spans}`",
            f"- errors: `{result.errors}`",
            "",
            "## Node spans (Logfire / local recorder)",
            "",
        ]
        + ([f"- `node: {name}`" for name in result.node_spans] or ["- (none recorded)"])
        + [
            "",
            "## Requirements",
            "",
        ]
        + ([f"- {r}" for r in result.requirements] or ["- (none)"])
        + [
            "",
            "## Components",
            "",
            "```json",
            json.dumps(result.components, indent=2, ensure_ascii=False),
            "```",
            "",
            "## Estimate",
            "",
            "```json",
            json.dumps(result.estimate, indent=2, ensure_ascii=False),
            "```",
            "",
            "## Notes",
            "",
            "- Level 1: sequential StateGraph of five nodes.",
            "- Level 2: AsyncPostgresSaver checkpointer + Logfire spans per node.",
            f"- Level 3: conditional edge after validation → END with status `{result.status}`.",
            "- Set `LOGFIRE_TOKEN` to send spans to the Logfire cloud UI.",
            "",
        ]
    )
    args.out.write_text(body, encoding="utf-8")
    print(f"status={result.status} spans={result.node_spans}")
    print(f"Wrote {args.out}")

    await pool.close()
    await dispose_engine()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
