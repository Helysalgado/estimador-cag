#!/usr/bin/env python3
"""Run the Session 12 estimation agent on a transcript and save the trace.

Usage::

    uv run python scripts/run_agent.py \\
      --transcript examples/agent/sample_transcript_complex.txt

    # cheaper smoke loop
    uv run python scripts/run_agent.py \\
      --transcript examples/agent/sample_transcript_simple.txt \\
      --model gpt-5-mini
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_REPO_ROOT / ".env")
sys.path.insert(0, str(_REPO_ROOT))

from app.agents.loop import run_agent  # noqa: E402
from app.config import settings  # noqa: E402
from app.db.session import async_session_factory, dispose_engine  # noqa: E402


async def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--debug", action="store_true", help="Use AGENT_DEBUG_MODEL")
    parser.add_argument("--max-iterations", type=int, default=None)
    parser.add_argument(
        "--out",
        type=Path,
        default=_REPO_ROOT / "evals" / "agent" / "TRACE_complex.md",
    )
    parser.add_argument("--search-mode", choices=("vector", "hybrid"), default="hybrid")
    parser.add_argument("--rerank", action="store_true")
    args = parser.parse_args()

    transcript = args.transcript.read_text(encoding="utf-8")
    model = args.model
    if args.debug and model is None:
        model = settings.AGENT_DEBUG_MODEL

    async with async_session_factory() as session:
        result = await run_agent(
            session,
            transcript=transcript,
            model=model,
            max_iterations=args.max_iterations,
            search_mode=args.search_mode,
            rerank=args.rerank,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        [
            "# Agent trace — Session 12",
            "",
            f"- model: `{result.model}`",
            f"- request_id: `{result.request_id}`",
            f"- iterations: {result.iterations}",
            f"- stopped_reason: {result.stopped_reason}",
            f"- tool_calls: `{result.tool_calls}`",
            f"- transcript: `{args.transcript}`",
            "",
            "## Trace",
            "",
            result.trace_text or "(empty)",
            "",
            "## Final estimate",
            "",
            result.estimate_text,
            "",
        ]
    )
    args.out.write_text(body, encoding="utf-8")
    print(result.trace_text)
    print("\n===== FINAL ESTIMATE =====\n")
    print(result.estimate_text)
    print(f"\nWrote {args.out}")
    await dispose_engine()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
