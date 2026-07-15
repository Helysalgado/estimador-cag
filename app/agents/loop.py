"""Manual agentic loop over the OpenAI Responses API (Session 12)."""

from __future__ import annotations

import json
import uuid
from collections import Counter
from typing import Any, Literal

import structlog
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.prompts import AGENT_SYSTEM_PROMPT
from app.agents.schemas import AgentEstimateResponse
from app.agents.tools.dispatch import execute_tool, parse_tool_arguments
from app.agents.tools.schemas import AGENT_TOOLS
from app.agents.trace import format_action, format_step, summarize_observation
from app.config import settings

log = structlog.get_logger(__name__)


def _extract_reasoning(output_items: list[Any]) -> str:
    parts: list[str] = []
    for item in output_items:
        item_type = getattr(item, "type", None)
        if item_type == "reasoning":
            summary = getattr(item, "summary", None)
            if summary:
                for block in summary:
                    text = getattr(block, "text", None) or str(block)
                    if text:
                        parts.append(str(text))
            content = getattr(item, "content", None)
            if content and not parts:
                parts.append(str(content))
    return " | ".join(parts).strip()


def _extract_final_text(output_items: list[Any]) -> str:
    texts: list[str] = []
    for item in output_items:
        if getattr(item, "type", None) != "message":
            continue
        content = getattr(item, "content", None) or []
        for block in content:
            block_type = getattr(block, "type", None)
            if block_type in {"output_text", "text"}:
                text = getattr(block, "text", None)
                if text:
                    texts.append(str(text))
    return "\n".join(texts).strip()


def _function_calls(output_items: list[Any]) -> list[Any]:
    return [item for item in output_items if getattr(item, "type", None) == "function_call"]


async def run_agent(
    session: AsyncSession,
    *,
    transcript: str,
    model: str | None = None,
    max_iterations: int | None = None,
    search_mode: Literal["vector", "hybrid"] = "hybrid",
    rerank: bool = False,
    k: int = 5,
    reasoning_effort: str | None = None,
    request_id: str | None = None,
) -> AgentEstimateResponse:
    """Run the manual tool loop until the model stops calling tools or max iterations."""
    rid = request_id or str(uuid.uuid4())
    active_model = model or settings.AGENT_MODEL
    effort = reasoning_effort or settings.AGENT_REASONING_EFFORT
    max_iters = max_iterations or settings.AGENT_MAX_ITERATIONS
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    trace_steps: list[str] = []
    tool_counter: Counter[str] = Counter()
    step_number = 0
    stopped_reason = "completed"

    response = client.responses.create(
        model=active_model,
        reasoning={"effort": effort},
        tools=AGENT_TOOLS,
        input=[
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
    )

    for iteration in range(1, max_iters + 1):
        output_items = list(getattr(response, "output", None) or [])
        calls = _function_calls(output_items)
        reasoning = _extract_reasoning(output_items)

        if not calls:
            estimate_text = _extract_final_text(output_items)
            if not estimate_text:
                estimate_text = getattr(response, "output_text", None) or "(empty final response)"
            stopped_reason = "completed"
            log.info(
                "agent_completed",
                request_id=rid,
                iterations=iteration,
                tool_calls=dict(tool_counter),
            )
            return AgentEstimateResponse(
                estimate_text=estimate_text,
                trace=trace_steps,
                trace_text="\n\n".join(trace_steps),
                iterations=iteration,
                tool_calls=dict(tool_counter),
                model=active_model,
                request_id=rid,
                stopped_reason=stopped_reason,
            )

        outputs_payload: list[dict[str, Any]] = []
        for call in calls:
            name = str(getattr(call, "name", "") or "")
            call_id = str(getattr(call, "call_id", "") or "")
            args = parse_tool_arguments(getattr(call, "arguments", "{}"))
            tool_counter[name] += 1
            step_number += 1

            result = await execute_tool(
                session,
                name,
                args,
                k=k,
                search_mode=search_mode,
                rerank=rerank,
            )
            action = format_action(name, args)
            observation = summarize_observation(result)
            trace_steps.append(
                format_step(
                    step_number,
                    reasoning=reasoning or f"Model requested {name}",
                    action=action,
                    observation=observation,
                )
            )
            log.info(
                "agent_tool_executed",
                request_id=rid,
                step=step_number,
                tool=name,
                call_id=call_id,
            )
            outputs_payload.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result, ensure_ascii=False, default=str),
                }
            )

        response = client.responses.create(
            model=active_model,
            previous_response_id=response.id,
            reasoning={"effort": effort},
            tools=AGENT_TOOLS,
            input=outputs_payload,
        )
    else:
        stopped_reason = "max_iterations"
        estimate_text = (
            _extract_final_text(list(getattr(response, "output", None) or []))
            or "(stopped: max iterations reached before final answer)"
        )
        log.warning(
            "agent_max_iterations",
            request_id=rid,
            max_iterations=max_iters,
            tool_calls=dict(tool_counter),
        )
        return AgentEstimateResponse(
            estimate_text=estimate_text,
            trace=trace_steps,
            trace_text="\n\n".join(trace_steps),
            iterations=max_iters,
            tool_calls=dict(tool_counter),
            model=active_model,
            request_id=rid,
            stopped_reason=stopped_reason,
        )
