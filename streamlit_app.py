"""Streamlit client for estimador-cag (session 5: multi-turn + attachments)."""

from __future__ import annotations

import json
import os

import httpx
import streamlit as st
from dotenv import load_dotenv

from app.schemas.estimation import DetailLevel, OutputFormat, ProjectType

load_dotenv()

API_BASE_URL = os.getenv("ESTIMATOR_API_BASE_URL", "http://localhost:8000").rstrip("/")
SESSIONS_PATH = f"{API_BASE_URL}/api/v1/sessions"
ESTIMATE_PATH = f"{API_BASE_URL}/api/v1/estimate"
HTTP_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


def _format_http_error(exc: httpx.HTTPStatusError) -> str:
    detail = exc.response.text
    try:
        parsed = exc.response.json()
        if isinstance(parsed, dict):
            detail = json.dumps(parsed, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return f"El servicio respondió {exc.response.status_code}:\n\n```\n{detail}\n```"


def _create_session(client: httpx.Client) -> str:
    response = client.post(SESSIONS_PATH, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    return response.json()["session_id"]


def _response_is_session_not_found(response: httpx.Response) -> bool:
    if response.status_code != 404:
        return False
    try:
        payload = response.json()
        detail = payload.get("detail")
        if isinstance(detail, dict):
            return detail.get("error") == "session_not_found"
    except Exception:
        pass
    return False


def _is_session_not_found(exc: httpx.HTTPStatusError) -> bool:
    return _response_is_session_not_found(exc.response)


def _refresh_session_after_api_restart() -> str:
    """Create a new server-side session when the API process was restarted."""
    with httpx.Client() as client:
        return _create_session(client)


def _ensure_session_state() -> None:
    if "session_id" not in st.session_state:
        with httpx.Client() as client:
            st.session_state.session_id = _create_session(client)
        st.session_state.messages = []
        st.session_state.project_metadata = {}


def _start_new_conversation() -> None:
    with httpx.Client() as client:
        st.session_state.session_id = _create_session(client)
    st.session_state.messages = []
    st.session_state.project_metadata = {}


def _post_session_turn(
    *,
    transcript: str,
    uploaded_files: list,
    prompt_version: str,
    allow_session_recovery: bool = True,
) -> dict:
    files: list[tuple[str, tuple[str, bytes, str]]] = []
    for uploaded in uploaded_files:
        content_type = uploaded.type or "application/octet-stream"
        files.append(
            ("attachments", (uploaded.name, uploaded.getvalue(), content_type)),
        )
    url = f"{SESSIONS_PATH}/{st.session_state.session_id}/estimate"
    with httpx.Client() as client:
        response = client.post(
            url,
            data={"transcript": transcript},
            files=files,
            params={"prompt_version": prompt_version},
            timeout=HTTP_TIMEOUT,
        )
        if allow_session_recovery and _response_is_session_not_found(response):
            st.session_state.session_id = _refresh_session_after_api_restart()
            st.session_state.turn_count = 0
            st.session_state.session_recovered = True
            return _post_session_turn(
                transcript=transcript,
                uploaded_files=uploaded_files,
                prompt_version=prompt_version,
                allow_session_recovery=False,
            )
        response.raise_for_status()
        return response.json()


st.set_page_config(page_title="Estimador de software", page_icon="📊")
st.title("Estimador de software")
st.caption(
    "Conversación multi-turno con memoria de proyecto y adjuntos PDF/DOCX. "
    "Cada turno llama a `POST /api/v1/sessions/{session_id}/estimate`."
)

_ensure_session_state()

tab_chat, tab_classic = st.tabs(["Conversación (Sesión 5)", "Formulario clásico (Sesión 4)"])

with tab_chat:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    with st.form("session_turn_form", clear_on_submit=True):
        transcript = st.text_area(
            "Tu mensaje",
            height=120,
            placeholder="Describe el proyecto, aclara alcance, pregunta por fases…",
        )
        uploaded_files = st.file_uploader(
            "Adjuntos (PDF o DOCX)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
        )
        prompt_version = st.selectbox(
            "Versión del prompt",
            options=["v1", "v2"],
            index=0,
        )
        submitted = st.form_submit_button("Enviar turno", type="primary")

    if submitted:
        clean = transcript.strip()
        if not clean:
            st.error("Escribe un mensaje antes de enviar.")
        else:
            st.session_state.messages.append({"role": "user", "content": clean})
            with st.spinner("Generando estimación del turno…"):
                try:
                    body = _post_session_turn(
                        transcript=clean,
                        uploaded_files=uploaded_files or [],
                        prompt_version=prompt_version,
                    )
                except httpx.HTTPStatusError as exc:
                    if _is_session_not_found(exc):
                        st.warning(
                            "La sesión ya no existe en el API (suele pasar si reiniciaste "
                            "uvicorn). Pulsa **Nueva conversación** o recarga tras actualizar "
                            "Streamlit para recuperación automática."
                        )
                    st.error(_format_http_error(exc))
                    st.session_state.messages.pop()
                except httpx.HTTPError as exc:
                    st.error(f"No se pudo conectar con el API en `{API_BASE_URL}`: {exc}")
                    st.session_state.messages.pop()
                else:
                    if st.session_state.pop("session_recovered", False):
                        st.info(
                            "Se creó una sesión nueva en el API (la anterior se perdió al "
                            "reiniciar el servidor)."
                        )
                    assistant_text = body.get("text", "")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": assistant_text},
                    )
                    st.session_state.project_metadata = body.get("project_metadata", {})
                    st.session_state.last_prompt_version = body.get("prompt_version")
                    st.session_state.turn_count = body.get("turn_count")
                    st.rerun()

with tab_classic:
    with st.form("estimation_form", clear_on_submit=False):
        description = st.text_area(
            "Descripción del proyecto",
            height=200,
            placeholder="Objetivos, funcionalidades clave, restricciones, plazos…",
        )
        project_type = st.selectbox(
            "Tipo de proyecto",
            options=[t.value for t in ProjectType],
            index=1,
            format_func=lambda v: v.replace("_", " ").title(),
        )
        detail_level = st.radio(
            "Nivel de detalle",
            options=[d.value for d in DetailLevel],
            index=1,
            horizontal=True,
            format_func=lambda v: v.title(),
        )
        output_format = st.selectbox(
            "Formato de salida",
            options=[f.value for f in OutputFormat],
            index=0,
            format_func=lambda v: v.replace("_", " ").title(),
        )
        classic_prompt_version = st.selectbox(
            "Versión del prompt (plantilla Jinja)",
            options=["v1", "v2"],
            index=0,
            key="classic_prompt_version",
        )
        with st.expander("Proyectos de referencia (opcional)", expanded=False):
            reference_json = st.text_area(
                "JSON: lista con name, description y opcional estimated_weeks",
                value="[]",
                height=120,
            )
        classic_submitted = st.form_submit_button("Generar estimación", type="primary")

    if classic_submitted:
        if len(description.strip()) < 20:
            st.error("La descripción debe tener al menos 20 caracteres.")
        else:
            payload = {
                "description": description.strip(),
                "project_type": project_type,
                "detail_level": detail_level,
                "output_format": output_format,
            }
            refs_ok = True
            ref_raw = reference_json.strip()
            if ref_raw and ref_raw != "[]":
                try:
                    parsed = json.loads(ref_raw)
                    if not isinstance(parsed, list):
                        raise ValueError("Debe ser una lista JSON")
                    payload["reference_projects"] = parsed
                except (json.JSONDecodeError, ValueError) as exc:
                    st.error(f"JSON de referencias inválido: {exc}")
                    refs_ok = False
            if refs_ok:
                with st.spinner("Llamando al servicio de estimación…"):
                    try:
                        with httpx.Client() as client:
                            response = client.post(
                                ESTIMATE_PATH,
                                params={"prompt_version": classic_prompt_version},
                                json=payload,
                                timeout=HTTP_TIMEOUT,
                            )
                        response.raise_for_status()
                        body = response.json()
                    except httpx.HTTPStatusError as exc:
                        st.error(_format_http_error(exc))
                    except httpx.HTTPError as exc:
                        st.error(f"No se pudo conectar con `{ESTIMATE_PATH}`: {exc}")
                    else:
                        st.markdown(f"**Versión del prompt:** `{body.get('prompt_version', '?')}`")
                        st.markdown(body.get("text", ""))

with st.sidebar:
    st.header("Sesión")
    st.markdown(f"**session_id:** `{st.session_state.session_id}`")
    if st.button("Nueva conversación", type="secondary"):
        _start_new_conversation()
        st.rerun()

    st.markdown(f"**Turnos completados:** `{st.session_state.get('turn_count', 0)}`")
    if st.session_state.get("last_prompt_version"):
        st.markdown(f"**Último prompt:** `{st.session_state.last_prompt_version}`")

    st.subheader("Metadata (debug)")
    metadata = st.session_state.get("project_metadata") or {}
    if metadata:
        st.json(metadata)
    else:
        st.caption("Aún sin metadata acumulada; envía un turno con detalles del proyecto.")

    st.divider()
    st.header("Servicio")
    st.code(f"{SESSIONS_PATH}/{{session_id}}/estimate", language="text")
    st.markdown(f"**API base:** `{API_BASE_URL}`")
    st.markdown(f"**Proveedor (API):** `{os.getenv('LLM_PROVIDER', 'openai')}`")
    st.markdown(f"**Modelo (API):** `{os.getenv('LLM_MODEL', 'gpt-4o-mini')}`")
