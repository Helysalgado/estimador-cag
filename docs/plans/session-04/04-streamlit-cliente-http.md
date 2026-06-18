# Paso 4 — Streamlit como cliente HTTP

> **Depende de:** Paso 3 (API funcionando con nuevo contrato).  
> **Siguiente:** Paso 5 (tests).

## Objetivo

Reemplazar el chat por un **formulario** que llama al backend por HTTP. Streamlit ya no invoca el LLM directamente en el flujo principal.

## Archivos a modificar

| Archivo | Acción |
|---------|--------|
| `streamlit_app.py` | Reescritura mayor |
| `pyproject.toml` | Añadir `httpx` si no está como dependencia directa |
| `.env.example` | `ESTIMATOR_API_BASE_URL=http://localhost:8000` |

## Implementación detallada

### 4.1 Comportamiento UI

- `st.set_page_config`, título “Software Estimator” (o equivalente en español si prefieres UI localizada).
- `st.form("estimation_form")` con:
  - `st.text_area` → `description`
  - `st.selectbox` → `project_type` (valores de `ProjectType`)
  - `st.radio` horizontal → `detail_level`
  - `st.selectbox` o `st.radio` → `output_format`
  - `st.form_submit_button("Generar estimación")` (o “Generate estimation”)
- Validación cliente: `len(description.strip()) >= 20` → `st.error` si no.
- Al enviar: `httpx.post(f"{base}/api/v1/estimate", json=payload, timeout=...)`
- Éxito: `st.markdown(body["text"])`, `st.caption` o markdown con `prompt_version`
- Error HTTP: `st.error` con status y cuerpo

### 4.2 Configuración

```python
API_BASE_URL = os.getenv("ESTIMATOR_API_BASE_URL", "http://localhost:8000")
ESTIMATE_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/api/v1/estimate"
```

`load_dotenv()` al inicio.

### 4.3 Sidebar (opcional pero útil)

- URL del endpoint (`st.code`)
- Modelos primary/fallback desde env (solo informativo)
- TTL de cache

### 4.4 Código a eliminar del flujo principal

- `st.chat_message`, `st.chat_input`, `st.write_stream`
- Imports directos de OpenAI/Anthropic para generación
- `session_state.messages` para conversación
- `build_system_prompt` / streaming en UI

Puedes conservar un archivo aparte `streamlit_chat_legacy.py` solo si lo necesitas para demo; **no** es parte del entregable session_4.

### 4.5 Tipado en cliente

Importar enums desde `app.schemas.estimation` para poblar opciones del formulario (como referencia LIDR).

## Tareas

- [x] Reescribir `streamlit_app.py`
- [x] Añadir `httpx` a dependencias principales
- [x] Documentar `ESTIMATOR_API_BASE_URL` en `.env.example`

## Verificación manual

Terminal 1:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Terminal 2:

```bash
uv run streamlit run streamlit_app.py
```

- [ ] Formulario visible en `http://localhost:8501`
- [ ] Submit con descripción válida muestra estimación en markdown
- [ ] Se muestra `prompt_version: v1`
- [ ] Con API apagada, mensaje de error claro

## Antes de continuar

Confirma: **“Podemos continuar con el Paso 5 (tests)”** cuando la UI funcione contra el API local.
