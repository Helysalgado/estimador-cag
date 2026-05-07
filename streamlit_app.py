from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Generator

import streamlit as st
from anthropic import Anthropic
from anthropic import (
    APIConnectionError as AnthropicConnectionError,
)
from anthropic import APITimeoutError as AnthropicTimeoutError
from anthropic import InternalServerError as AnthropicInternalServerError
from anthropic import RateLimitError as AnthropicRateLimitError
from openai import APIConnectionError as OpenAIConnectionError
from openai import APITimeoutError as OpenAITimeoutError
from openai import InternalServerError as OpenAIInternalServerError
from openai import OpenAI
from openai import RateLimitError as OpenAIRateLimitError

from app.config import settings
from app.context.examples import ESTIMATION_EXAMPLES
from app.schemas.estimation import EstimationRequest
from app.services.llm_service import build_system_prompt

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
}
RECOVERABLE_EXCEPTIONS = (
    OpenAIRateLimitError,
    OpenAITimeoutError,
    OpenAIConnectionError,
    OpenAIInternalServerError,
    AnthropicRateLimitError,
    AnthropicTimeoutError,
    AnthropicConnectionError,
    AnthropicInternalServerError,
    TimeoutError,
    ConnectionError,
)


@dataclass
class StreamMetrics:
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    response_time_s: float
    fallback_used: bool
    fallback_reason: str | None
    timestamp: str


def _secret_value(key: str) -> str | None:
    try:
        return st.secrets.get(key)  # type: ignore[arg-type]
    except Exception:
        return None


def _provider_api_key(provider: str) -> str | None:
    if provider == "openai":
        return _secret_value("OPENAI_API_KEY") or settings.OPENAI_API_KEY
    if provider == "anthropic":
        return _secret_value("ANTHROPIC_API_KEY") or settings.ANTHROPIC_API_KEY
    return None


def _render_chat_history() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def _build_user_prompt(message: str) -> str:
    previous_turns = st.session_state.messages[-6:]
    history_lines: list[str] = []
    for turn in previous_turns:
        role = "Usuario" if turn["role"] == "user" else "Asistente"
        history_lines.append(f"{role}: {turn['content']}")

    history_block = "\n".join(history_lines)
    return (
        "Contexto conversacional reciente:\n"
        f"{history_block}\n\n"
        "Mensaje actual del usuario:\n"
        f"{message}\n\n"
        "Genera o ajusta la estimación siguiendo el formato de los ejemplos."
    )


def _requires_minimum_transcription() -> bool:
    # Solo exigir transcripción larga en el primer mensaje de usuario.
    return not any(msg["role"] == "user" for msg in st.session_state.messages[:-1])


def _stream_openai(model: str, system_prompt: str, user_prompt: str) -> tuple[Generator[str, None, None], Callable[[], tuple[int | None, int | None]]]:
    client = OpenAI(api_key=_provider_api_key("openai"))
    stream = client.responses.stream(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_output_tokens=900,
    )

    usage_holder: dict[str, int | None] = {"input": None, "output": None}

    def token_generator() -> Generator[str, None, None]:
        with stream as response_stream:
            for event in response_stream:
                if getattr(event, "type", "") == "response.output_text.delta":
                    yield event.delta
            final_response = response_stream.get_final_response()
            if getattr(final_response, "usage", None):
                usage_holder["input"] = getattr(final_response.usage, "input_tokens", None)
                usage_holder["output"] = getattr(final_response.usage, "output_tokens", None)

    def get_usage() -> tuple[int | None, int | None]:
        return usage_holder["input"], usage_holder["output"]

    return token_generator(), get_usage


def _stream_anthropic(model: str, system_prompt: str, user_prompt: str) -> tuple[Generator[str, None, None], Callable[[], tuple[int | None, int | None]]]:
    client = Anthropic(api_key=_provider_api_key("anthropic"))
    stream = client.messages.stream(
        model=model,
        max_tokens=900,
        temperature=0.3,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    usage_holder: dict[str, int | None] = {"input": None, "output": None}

    def token_generator() -> Generator[str, None, None]:
        with stream as message_stream:
            for text in message_stream.text_stream:
                yield text
            final_message = message_stream.get_final_message()
            if getattr(final_message, "usage", None):
                usage_holder["input"] = getattr(final_message.usage, "input_tokens", None)
                usage_holder["output"] = getattr(final_message.usage, "output_tokens", None)

    def get_usage() -> tuple[int | None, int | None]:
        return usage_holder["input"], usage_holder["output"]

    return token_generator(), get_usage


def _is_recoverable(error: Exception) -> bool:
    if isinstance(error, RECOVERABLE_EXCEPTIONS):
        return True
    status_code = getattr(error, "status_code", None)
    return status_code in (408, 429, 500, 502, 503, 504)


def _stream_with_fallback(
    primary_provider: str,
    secondary_provider: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, StreamMetrics]:
    started_at = time.perf_counter()
    fallback_used = False
    fallback_reason: str | None = None

    for idx, provider in enumerate((primary_provider, secondary_provider)):
        provider_model = model if idx == 0 else DEFAULT_MODELS[provider]
        try:
            if provider == "openai":
                stream_generator, get_usage = _stream_openai(provider_model, system_prompt, user_prompt)
            else:
                stream_generator, get_usage = _stream_anthropic(provider_model, system_prompt, user_prompt)

            output_text = st.write_stream(stream_generator)
            input_tokens, output_tokens = get_usage()
            metrics = StreamMetrics(
                provider=provider,
                model=provider_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_time_s=round(time.perf_counter() - started_at, 2),
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            return output_text, metrics
        except Exception as error:  # noqa: BLE001
            if idx == 0 and _is_recoverable(error):
                fallback_used = True
                fallback_reason = f"{type(error).__name__}: {error}"
                st.info(f"Se activó fallback a `{secondary_provider}` por error recuperable del primario.")
                continue
            raise

    raise RuntimeError("No fue posible generar la estimación con proveedores disponibles.")


def main() -> None:
    st.set_page_config(page_title="Estimador CAG Chat", page_icon="💬", layout="wide")
    st.title("Estimador CAG - Chat de estimación")
    st.caption("Pega una transcripción y recibe una estimación en streaming.")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_metrics" not in st.session_state:
        st.session_state.last_metrics = None

    system_prompt = build_system_prompt()
    provider_default = settings.LLM_PROVIDER if settings.LLM_PROVIDER in ("openai", "anthropic") else "openai"

    st.sidebar.header("Configuración")
    primary_provider = st.sidebar.selectbox(
        "Proveedor primario",
        options=["openai", "anthropic"],
        index=0 if provider_default == "openai" else 1,
    )
    secondary_provider = "anthropic" if primary_provider == "openai" else "openai"

    default_model = settings.LLM_MODEL if primary_provider == provider_default else DEFAULT_MODELS[primary_provider]
    selected_model = st.sidebar.text_input("Modelo primario", value=default_model)
    st.sidebar.caption(f"Fallback automático configurado a: `{secondary_provider}`")

    st.sidebar.subheader("System prompt activo")
    st.sidebar.code(system_prompt, language="text")

    st.sidebar.subheader("Contexto estático CAG")
    for idx, example in enumerate(ESTIMATION_EXAMPLES, start=1):
        with st.sidebar.expander(f"Ejemplo {idx}", expanded=False):
            st.markdown(f"**Resumen:** {example['meeting_summary']}")
            st.markdown(example["estimation"])

    st.sidebar.subheader("Métricas última llamada")
    metrics: StreamMetrics | None = st.session_state.last_metrics
    if metrics is None:
        st.sidebar.write("Aún no hay llamadas.")
    else:
        st.sidebar.write(f"Proveedor: `{metrics.provider}`")
        st.sidebar.write(f"Modelo: `{metrics.model}`")
        st.sidebar.write(f"Input tokens: `{metrics.input_tokens or 'N/A'}`")
        st.sidebar.write(f"Output tokens: `{metrics.output_tokens or 'N/A'}`")
        st.sidebar.write(f"Tiempo respuesta: `{metrics.response_time_s}s`")
        st.sidebar.write(f"Fallback usado: `{metrics.fallback_used}`")
        if metrics.fallback_reason:
            st.sidebar.caption(f"Motivo fallback: {metrics.fallback_reason}")

    _render_chat_history()

    user_input = st.chat_input("Pega aquí la transcripción de reunión...")
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            if _requires_minimum_transcription():
                EstimationRequest(transcription=user_input)
            elif len(user_input.strip()) < 3:
                st.warning("Escribe un poco más de contexto para ajustar la estimación.")
                return
            if not _provider_api_key(primary_provider):
                st.error(f"Falta credencial del proveedor primario `{primary_provider}`.")
                return
            if not _provider_api_key(secondary_provider):
                st.warning(f"No hay API key de fallback para `{secondary_provider}`. Solo se usará el primario.")

            user_prompt = _build_user_prompt(user_input)
            estimation_text, metrics = _stream_with_fallback(
                primary_provider=primary_provider,
                secondary_provider=secondary_provider,
                model=selected_model.strip() or DEFAULT_MODELS[primary_provider],
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            st.session_state.last_metrics = metrics
        except Exception as error:  # noqa: BLE001
            st.error(f"No se pudo generar la estimación: {error}")
            return

    st.session_state.messages.append({"role": "assistant", "content": estimation_text})


if __name__ == "__main__":
    main()
