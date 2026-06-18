# Paso 5 — Tests

> **Depende de:** Pasos 1–4 implementados.  
> **Siguiente:** Paso 6 (README y entregable).

## Objetivo

Suite en milisegundos, sin APIs externas: schemas, templates Jinja2, endpoint con mocks, cache/stream ajustados.

## Archivos a crear o modificar

| Archivo | Acción |
|---------|--------|
| `tests/test_schemas.py` | **Nuevo** — validación `EstimationRequest` |
| `tests/test_prompts.py` | **Nuevo** — render Jinja2 (≥3 tests de sesión) |
| `tests/test_estimate_endpoint.py` | Actualizar JSON y asserts (`text`, `prompt_version`) |
| `tests/test_estimate_service_cache.py` | Usar `EstimationRequest` + `estimate_from_request` |
| `tests/test_estimate_stream_endpoint.py` | Nuevo body tipado |
| `tests/conftest.py` | Revisar fixtures si hace falta payload válido compartido |

## Tests obligatorios (sesión)

### Schemas (`test_schemas.py`)

- [x] Request válido con enums tipados
- [x] `description` &lt; 20 → `ValidationError`
- [x] Enum inválido → `ValidationError`
- [x] `description` &gt; max_length

### Prompts (`test_prompts.py`)

- [x] `description` aparece dentro de `<project_description>` en `user`
- [x] `output_format=phases_table` → `system` contiene marcador del formato; con `narrative` no
- [x] `detail_level=detailed` → instrucción de asunciones por fase en `system`; con `summary` no

### Endpoint (`test_estimate_endpoint.py`)

- [x] `POST /api/v1/estimate` con JSON nuevo → 200
- [x] Respuesta incluye `text` y `prompt_version == "v1"`
- [x] Mock verifica system y user separados

### Regresión

- [x] `tests/test_cache.py` — sin cambios
- [x] `tests/test_llm_wrapper.py` — sin cambios
- [x] `tests/test_health.py` — intacto

## Verificación

```bash
uv run pytest -q
```

- [x] Todos los tests pasan (28 tests, ~0.4s)
- [x] Tiempo total razonable

## Antes de continuar

Confirma: **“Podemos continuar con el Paso 6 (README y entregable)”** cuando `pytest` esté en verde.
