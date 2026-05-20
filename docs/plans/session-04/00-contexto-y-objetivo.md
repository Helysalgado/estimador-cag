# Paso 0 — Contexto y objetivo

> **Tipo:** lectura y decisiones (sin cambios de código obligatorios en este paso).

## Objetivo de la sesión

Al terminar la implementación, el estimador debe cumplir:

1. **Cliente (Streamlit):** formulario con `st.form` que produce un JSON tipado (`EstimationRequest`).
2. **Servicio IA (FastAPI):** recibe ese JSON, renderiza prompts con **Jinja2** desde `app/prompts/estimation/v1/`, llama al LLM con mensajes `system` y `user` separados, devuelve `{ "text", "prompt_version" }`.
3. **Infra ya existente:** wrapper LiteLLM, fallback, Redis exact-match, Docker, pytest en CI.

## Estado actual (resumen)

| Componente | Hoy |
|------------|-----|
| `app/schemas/estimation.py` | `transcription` → respuesta con `estimation`, `model`, `provider`, `timestamp` |
| Prompts | En Python: `build_system_prompt()` + `app/context/examples.py` |
| `streamlit_app.py` | Chat + streaming directo a OpenAI/Anthropic |
| `POST /api/v1/estimate` | Usa transcripción |
| `POST /api/v1/estimate/stream` | SSE con transcripción |
| Tests | Orientados a `transcription` |

## Estado objetivo (referencia LIDR session_4)

Ver [estimator README session_4](https://github.com/LIDR-academy/ai-engineering/tree/session_4/estimator).

## Fuera de alcance (por ahora)

- Structured outputs / Instructor
- Guardrails AI
- Semantic cache / embeddings
- Evaluaciones automatizadas del prompt

## Decisiones cerradas (Paso 0)

| # | Decisión | Valor acordado |
|---|----------|----------------|
| D1 | `description.max_length` | **80000** |
| D2 | Endpoint stream | **Sí** — como [LIDR session_4](https://github.com/LIDR-academy/ai-engineering/blob/session_4/estimator/app/routers/estimations.py): mantener `POST /api/v1/estimate/stream`, migrado al nuevo `EstimationRequest` + `render_estimation_prompt` (eventos SSE: `status`, `token`, `complete`, `error`) |
| D3 | Idioma templates | **Inglés** |
| D4 | `app/context/examples.py` | **Eliminar del flujo** — few-shots solo en `app/prompts/estimation/v1/examples.j2` (LIDR no tiene carpeta `context/`) |
| D5 | Rama | **`pre-session-04`** |

### Nota D2 — qué hace LIDR exactamente

En session_4 el router expone **dos** endpoints:

1. `POST /api/v1/estimate` — respuesta bloqueante `{ text, prompt_version }`.
2. `POST /api/v1/estimate/stream` — SSE con el **mismo** body tipado; usa `wrapper.complete_stream()` y emite `status` → `token` → `complete` (o `error`).

El README público del repo enfatiza el formulario y el endpoint bloqueante; el stream sigue en código para quien quiera consumirlo por HTTP.

### Nota D4 — qué hace LIDR exactamente

- No existe `app/context/` ni `examples.py` en Python.
- Los few-shots viven en [`examples.j2`](https://github.com/LIDR-academy/ai-engineering/blob/session_4/estimator/app/prompts/estimation/v1/examples.j2) e se incluyen desde `system.j2` con `{% include %}`.

En `estimador-cag` podemos borrar `app/context/examples.py` en el Paso 6 (o antes si ya no hay imports).

## Criterio de “listo” para el Paso 0

- [x] Objetivo entendido
- [x] Decisiones D1–D5 cerradas

## Antes de continuar

Confirma: **“Podemos continuar con el Paso 1 (schemas)”** cuando hayas leído este documento y cerrado las decisiones que te importen.
