"""Streamlit form for the estimador-cag service.

Streamlit acts as an HTTP client of the FastAPI service: it submits a typed
``EstimationRequest`` to ``POST /api/v1/estimate`` and renders the response text.
The endpoint URL is read from ``ESTIMATOR_API_BASE_URL`` (loaded from ``.env``).
"""

from __future__ import annotations

import os

import httpx
import streamlit as st
from dotenv import load_dotenv

from app.schemas.estimation import DetailLevel, OutputFormat, ProjectType

load_dotenv()

API_BASE_URL = os.getenv("ESTIMATOR_API_BASE_URL", "http://localhost:8000")
ESTIMATE_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/api/v1/estimate"

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
        with st.spinner("Llamando al servicio de estimación…"):
            try:
                response = httpx.post(
                    ESTIMATE_ENDPOINT,
                    json=payload,
                    timeout=httpx.Timeout(120.0, connect=10.0),
                )
                response.raise_for_status()
                body = response.json()
            except httpx.HTTPStatusError as exc:
                st.error(
                    f"El servicio respondió {exc.response.status_code}: {exc.response.text}"
                )
            except httpx.HTTPError as exc:
                st.error(
                    f"No se pudo conectar con el estimador en `{ESTIMATE_ENDPOINT}`: {exc}"
                )
            else:
                st.markdown(f"**Versión del prompt:** `{body.get('prompt_version', '?')}`")
                st.markdown(body.get("text", ""))

with st.sidebar:
    st.header("Servicio")
    st.code(ESTIMATE_ENDPOINT, language="text")
    st.markdown(f"**Proveedor (API):** `{os.getenv('LLM_PROVIDER', 'openai')}`")
    st.markdown(f"**Modelo (API):** `{os.getenv('LLM_MODEL', 'gpt-4o-mini')}`")
    st.markdown(f"**TTL cache:** `{os.getenv('CACHE_TTL_SECONDS', '86400')}s`")
