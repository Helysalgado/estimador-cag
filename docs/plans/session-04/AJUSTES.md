# Plan de ajustes — Sesión 4 (cumplimiento vs referencia LIDR)

Contraste entre:

- Material del curso: `IAENG/material/mat-sesion4.md`
- Repositorio de referencia: [LIDR-academy/ai-engineering — session_4/estimator](https://github.com/LIDR-academy/ai-engineering/tree/session_4/estimator)
- Proyecto actual: `estimador-cag` (rama `pre-session-06`, con evolución S5/S6 encima de S4)

## Veredicto global

**Sesión 4 está cumplida en lo esencial y superada en el bonus.** No hace falta rehacer la migración; los ajustes propuestos son de **alineación menor**, **limpieza** y **documentación**, no de funcionalidad core.

| Bloque (mat-sesion4 + LIDR S4) | Estado en `estimador-cag` |
|--------------------------------|---------------------------|
| Contrato `EstimationRequest` / `EstimationResponse` + enums | **Cumple** (`app/schemas/estimation.py`) |
| `description` con límite amplio (LIDR: 80k; material ejercicio: 2k — se siguió LIDR) | **Cumple** (80000) |
| Prompts Jinja2 `v1` (system, user, examples) + `StrictUndefined` | **Cumple** |
| `render_estimation_prompt` → `(system, user)` | **Cumple** (`app/prompts/loader.py`) |
| `POST /api/v1/estimate` tipado + cache exact-match | **Cumple** (`llm_service` + Redis) |
| `POST /api/v1/estimate/stream` (SSE) | **Cumple** |
| Streamlit con `st.form` → JSON al API (no chat como flujo principal) | **Cumple** (pestaña “Classic Form”) |
| Tests: schemas, prompts, endpoint, wrapper, cache | **Cumple** (+ muchos tests S5/S6) |
| Bonus: `v2`, `reference_projects`, structlog en render | **Cumple** (Paso 7 del plan local) |
| Entregable: rama `pre-session-04`, README, tests verdes | **Cumple** (histórico en git) |

**Fuera de alcance S4 (correctamente no implementado en el pre-ejercicio):** Instructor/JSON estructurado, Guardrails, cache semántico — reservados al directo según `mat-sesion4.md`.

**Evolución posterior (S5/S6):** sesiones conversacionales, adjuntos, `turn_observed`, stress evals — **no contradice** S4; añade routers y módulos aparte sin eliminar el contrato del formulario.

---

## Diferencias aceptables (no requieren cambio)

| Tema | LIDR `session_4` | `estimador-cag` | Decisión |
|------|------------------|-----------------|----------|
| Inyección LLM | `app/dependencies.py` + clase `LLMWrapper` | `llm_service` + `generate_sync` / `WrapperConfig` | Mantener: equivalente funcional desde S3 |
| Variables modelo | `PRIMARY_MODEL` / `FALLBACK_MODEL` | `LLM_PROVIDER` / `LLM_MODEL` | Mantener: convención ya documentada en README |
| Health | `status: healthy`, `environment` | `status: ok`, `service`, `version` | Mantener si tests locales lo fijan; opcional alinear |
| Versión prompt en estimate | Fijo `v1` en router | Query `prompt_version=v1\|v2` | Mantener: es el bonus del material |
| `reference_projects` | No en LIDR S4 | Sí en schema + templates | Mantener: bonus explícito |
| Ubicación tests prompts | Sugerido `tests/prompts/...` | `tests/test_prompts.py` | Mantener: misma cobertura |
| Cliente UI | Solo formulario | Formulario + conversación (S5) | Mantener: S4 no prohíbe pestaña extra |

---

## Ajustes recomendados (prioridad)

### Prioridad alta — limpieza y trazabilidad (≈ 30 min)

| ID | Ajuste | Motivo | Acción |
|----|--------|--------|--------|
| A1 | Eliminar paquete vacío `app/context/` | Plan S4 D4: few-shots solo en `.j2`; quedó `__init__.py` huérfano | Borrar carpeta si no hay imports |
| A2 | Actualizar checklist en `session-04/README.md` | Ya marcado hecho; enlazar este `AJUSTES.md` | Documentación |
| A3 | Verificar pestaña “Classic Form” en README | Entregable S4 = formulario; README ya distingue modos | Una frase “modo Sesión 4” en README si falta |

### Prioridad media — paridad opcional con LIDR (≈ 1–2 h)

| ID | Ajuste | Motivo | Acción |
|----|--------|--------|--------|
| B1 | CORS en `app/main.py` | LIDR expone `CORSMiddleware` para clientes HTTP | Añadir middleware `allow_origins` acotado en dev |
| B2 | Log `estimation_request_received` en router | LIDR loguea en `estimations.py` además del loader | `structlog` en `create_estimation` / `stream_estimation` con enums y `description_chars` |
| B3 | Health alineado a LIDR (opcional) | Facilita comparar con plantilla del curso | Añadir `environment: settings.APP_ENV` sin romper tests o actualizar `test_health.py` |
| B4 | `redoc_url` / título OpenAPI | Paridad cosmética con [main.py LIDR](https://github.com/LIDR-academy/ai-engineering/blob/session_4/estimator/app/main.py) | Opcional |

### Prioridad baja — solo si buscas clon estructural de LIDR (no obligatorio)

| ID | Ajuste | Motivo | Viabilidad |
|----|--------|--------|------------|
| C1 | Introducir `app/dependencies.py` | Mismo patrón DI que LIDR | **No recomendado ahora**: refactor amplio sin beneficio claro con `llm_service` actual |
| C2 | Renombrar servicio Docker a `servicio_ia` | Nombre del material | **No recomendado**: rompe docs/scripts existentes |

---

## Qué NO hacer (evitar regresión S4)

- No volver al chat como único cliente ni al campo `transcription` en el API stateless.
- No mover prompts de vuelta a f-strings en Python.
- No implementar cache semántico / Instructor / Guardrails “para cerrar S4” — eso es directo S4+, no pre-ejercicio.
- No eliminar `POST /estimate` ni el stream al priorizar sesiones conversacionales.

---

## Checklist de verificación rápida (regresión Sesión 4)

Ejecutar antes de dar por cerrados los ajustes:

```bash
uv run pytest tests/test_schemas.py tests/test_prompts.py \
  tests/test_estimate_endpoint.py tests/test_estimate_stream_endpoint.py \
  tests/test_llm_wrapper.py tests/test_cache.py tests/test_health.py -q

uv run python scripts/validate_structure.py

# Manual: Classic Form
uv run uvicorn app.main:app --reload
uv run streamlit run streamlit_app.py
# POST formulario → /api/v1/estimate con description + 3 enums
```

Criterio: mismos tests verdes; formulario devuelve `{ "text", "prompt_version" }`.

---

## Relación con sesiones posteriores

| Sesión | Impacto en base S4 |
|--------|-------------------|
| S5 | Añade `/sessions/*`; el formulario clásico sigue siendo el camino S4 |
| S6 | Stress/evals; no sustituye el contrato tipado |
| S7 | `embedding_pipeline` nuevo; no toca `EstimationRequest` |

Los ajustes de este documento **no bloquean** S6 (stress) ni S7 (embeddings).

---

## Secuencia sugerida de commits (si aplicas ajustes)

1. `chore(session-04): remove unused app/context package`
2. `feat(session-04): add CORS and estimation request logging` (B1 + B2)
3. `doc(session-04): document S4 compliance and optional LIDR deltas` (este archivo + README)

---

## Referencias

- [session_4/estimator](https://github.com/LIDR-academy/ai-engineering/tree/session_4/estimator)
- Plan local ejecutado: [README.md](./README.md)
- Material: `IAENG/material/mat-sesion4.md`
