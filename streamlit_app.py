"""Streamlit form for the estimador-cag service.

Streamlit acts as an HTTP client of the FastAPI service: it submits a typed
``EstimationRequest`` to ``POST /api/v1/estimate`` and renders the response text.
The endpoint URL is read from ``ESTIMATOR_API_BASE_URL`` (loaded from ``.env``).
"""

from __future__ import annotations

import json
import os

import httpx
import streamlit as st
from dotenv import load_dotenv

from app.schemas.estimation import DetailLevel, OutputFormat, ProjectType

load_dotenv()

API_BASE_URL = os.getenv("ESTIMATOR_API_BASE_URL", "http://localhost:8000")
ESTIMATE_PATH = f"{API_BASE_URL.rstrip('/')}/api/v1/estimate"

st.set_page_config(page_title="Estimador de software", page_icon="📊")
st.title("Estimador de software")
st.caption(
    "Completa el formulario para estimar un proyecto de software. "
    "El servicio devuelve texto libre según el formato elegido."
)

with st.form("estimation_form", clear_on_submit=False):
    description = st.text_area(
        "Descripción del proyecto",
        height=200,
        placeholder="Objetivos, funcionalidades clave, restricciones, plazos…",
        help="Entre 20 y 80.000 caracteres.",
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
    prompt_version = st.selectbox(
        "Versión del prompt (plantilla Jinja)",
        options=["v1", "v2"],
        index=0,
        help="v2 usa un tono más directo y ejemplos de calibración distintos.",
    )
    with st.expander("Proyectos de referencia (opcional)", expanded=False):
        reference_json = st.text_area(
            "JSON: lista de objetos con name, description y opcional estimated_weeks",
            value="[]",
            height=120,
            placeholder='[{"name": "Similar app", "description": "...", "estimated_weeks": 12}]',
            label_visibility="visible",
        )
    submitted = st.form_submit_button("Generar estimación", type="primary")

if submitted:
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
                    response = httpx.post(
                        ESTIMATE_PATH,
                        params={"prompt_version": prompt_version},
                        json=payload,
                        timeout=httpx.Timeout(120.0, connect=10.0),
                    )
                    response.raise_for_status()
                    body = response.json()
                except httpx.HTTPStatusError as exc:
                    detail = exc.response.text
                    try:
                        parsed = exc.response.json()
                        if isinstance(parsed, dict):
                            detail = json.dumps(parsed, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                    st.error(
                        f"El servicio respondió {exc.response.status_code}:\n\n```\n{detail}\n```"
                    )
                except httpx.HTTPError as exc:
                    st.error(
                        f"No se pudo conectar con el estimador en `{ESTIMATE_PATH}`: {exc}"
                    )
                else:
                    st.markdown(f"**Versión del prompt:** `{body.get('prompt_version', '?')}`")
                    st.markdown(body.get("text", ""))

with st.sidebar:
    st.header("Servicio")
    st.code(ESTIMATE_PATH, language="text")
    st.markdown(f"**Proveedor (API):** `{os.getenv('LLM_PROVIDER', 'openai')}`")
    st.markdown(f"**Modelo (API):** `{os.getenv('LLM_MODEL', 'gpt-4o-mini')}`")
    st.markdown(f"**TTL cache:** `{os.getenv('CACHE_TTL_SECONDS', '86400')}s`")
