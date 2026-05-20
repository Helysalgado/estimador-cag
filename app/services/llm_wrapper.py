from __future__ import annotations

import time
from collections.abc import AsyncGenerator, Iterator
from dataclasses import dataclass
from datetime import datetime, timezone

from litellm import acompletion, completion

from app.config import settings


RECOVERABLE_STATUS = {408, 429, 500, 502, 503, 504}
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
}


@dataclass
class WrapperConfig:
    provider: str
    model: str
    max_tokens: int = 900
    temperature: float = 0.3
    thinking_budget: int | None = None
    fallback_provider: str | None = None
    fallback_model: str | None = None


def _provider_model(provider: str, model: str) -> str:
    if "/" in model:
        return model
    return f"{provider}/{model}"


def _status_code(error: Exception) -> int | None:
    code = getattr(error, "status_code", None)
    if code is not None:
        return code
    response = getattr(error, "response", None)
    return getattr(response, "status_code", None)


def _is_recoverable(error: Exception) -> bool:
    status = _status_code(error)
    if status in RECOVERABLE_STATUS:
        return True
    text = str(error).lower()
    return "timeout" in text or "connection" in text or "rate limit" in text


def _base_messages(system_prompt: str, user_message: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


def generate_sync(
    *,
    system_prompt: str,
    user_message: str,
    config: WrapperConfig,
) -> dict:
    started = time.perf_counter()
    attempts: list[tuple[str, str]] = [(config.provider, config.model)]
    if config.fallback_provider:
        attempts.append(
            (
                config.fallback_provider,
                config.fallback_model or DEFAULT_MODELS[config.fallback_provider],
            )
        )

    fallback_used = False
    fallback_reason: str | None = None
    for index, (provider, model) in enumerate(attempts):
        try:
            response = completion(
                model=_provider_model(provider, model),
                messages=_base_messages(system_prompt, user_message),
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )
            text = response.choices[0].message.content if response.choices else ""
            usage = getattr(response, "usage", None)
            return {
                "estimation": text or "",
                "model": model,
                "provider": provider,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "meta": {
                    "input_tokens": getattr(usage, "prompt_tokens", None),
                    "output_tokens": getattr(usage, "completion_tokens", None),
                    "response_time_s": round(time.perf_counter() - started, 2),
                    "fallback_used": fallback_used,
                    "fallback_reason": fallback_reason,
                },
            }
        except Exception as error:  # noqa: BLE001
            if index == 0 and len(attempts) > 1 and _is_recoverable(error):
                fallback_used = True
                fallback_reason = f"{type(error).__name__}: {error}"
                continue
            raise
    raise RuntimeError("No se pudo generar respuesta con los proveedores configurados.")


def complete_stream(
    *,
    system_prompt: str,
    user_message: str,
    config: WrapperConfig,
) -> Iterator[str]:
    """Yield incremental text chunks from the LLM (synchronous streaming)."""
    attempts: list[tuple[str, str]] = [(config.provider, config.model)]
    if config.fallback_provider:
        attempts.append(
            (
                config.fallback_provider,
                config.fallback_model or DEFAULT_MODELS[config.fallback_provider],
            )
        )

    for index, (provider, model) in enumerate(attempts):
        try:
            stream = completion(
                model=_provider_model(provider, model),
                messages=_base_messages(system_prompt, user_message),
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                stream=True,
            )
            for chunk in stream:
                choices = getattr(chunk, "choices", []) or []
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                content = getattr(delta, "content", None) if delta else None
                if content:
                    yield content
            return
        except Exception as error:  # noqa: BLE001
            if index == 0 and len(attempts) > 1 and _is_recoverable(error):
                continue
            raise
    raise RuntimeError("No se pudo generar respuesta con los proveedores configurados.")


async def stream_events(
    *,
    system_prompt: str,
    user_message: str,
    config: WrapperConfig,
) -> AsyncGenerator[dict, None]:
    started = time.perf_counter()
    attempts: list[tuple[str, str]] = [(config.provider, config.model)]
    if config.fallback_provider:
        attempts.append(
            (
                config.fallback_provider,
                config.fallback_model or DEFAULT_MODELS[config.fallback_provider],
            )
        )

    fallback_used = False
    fallback_reason: str | None = None
    for index, (provider, model) in enumerate(attempts):
        output_parts: list[str] = []
        try:
            stream = await acompletion(
                model=_provider_model(provider, model),
                messages=_base_messages(system_prompt, user_message),
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                stream=True,
            )
            async for chunk in stream:
                choices = getattr(chunk, "choices", []) or []
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                content = getattr(delta, "content", None) if delta else None
                if content:
                    output_parts.append(content)
                    yield {"event": "token", "data": content}
            yield {
                "event": "meta",
                "data": {
                    "provider": provider,
                    "model": model,
                    "response_time_s": round(time.perf_counter() - started, 2),
                    "fallback_used": fallback_used,
                    "fallback_reason": fallback_reason,
                },
            }
            yield {"event": "done", "data": "".join(output_parts)}
            return
        except Exception as error:  # noqa: BLE001
            if index == 0 and len(attempts) > 1 and _is_recoverable(error):
                fallback_used = True
                fallback_reason = f"{type(error).__name__}: {error}"
                yield {"event": "meta", "data": {"fallback_triggered": True, "reason": fallback_reason}}
                continue
            yield {"event": "error", "data": str(error)}
            return


def get_default_wrapper_config() -> WrapperConfig:
    provider = settings.LLM_PROVIDER if settings.LLM_PROVIDER in DEFAULT_MODELS else "openai"
    fallback = "anthropic" if provider == "openai" else "openai"
    model = settings.LLM_MODEL or DEFAULT_MODELS[provider]
    return WrapperConfig(
        provider=provider,
        model=model,
        fallback_provider=fallback,
        fallback_model=DEFAULT_MODELS[fallback],
    )
