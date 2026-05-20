# Paso 3 — Refactor endpoint y servicio

> **Depende de:** Pasos 1 y 2.  
> **Siguiente:** Paso 4 (Streamlit).

## Objetivo

Conectar `POST /api/v1/estimate` (y opcionalmente `/estimate/stream`) al nuevo contrato y a `render_estimation_prompt`, manteniendo wrapper + Redis.

## Archivos a modificar

| Archivo | Acción |
|---------|--------|
| `app/services/llm_service.py` | Nueva función `estimate_from_request`; dejar de usar `build_system_prompt` + transcripción en flujo principal |
| `app/routers/estimations.py` | Usar `estimate_from_request` y `EstimationResponse` |
| `app/config.py` / `.env.example` | Opcional: `PRIMARY_MODEL`, `FALLBACK_MODEL` alineados a session_4 |
| `app/services/llm_wrapper.py` | Solo si hace falta ajustar modelos por defecto (`claude-haiku-4-5-20251001`) |

## Implementación detallada

### 3.1 `estimate_from_request(request) -> EstimationResponse`

Flujo:

1. `system, user = render_estimation_prompt(request, version="v1")`
2. `config = get_default_wrapper_config()`
3. `cache_key = make_key(system_prompt=system, user_message=user, model=..., ...)`
4. Si hit en Redis → mapear caché a `EstimationResponse(text=..., prompt_version="v1")`
5. Si miss → `generate_sync(system_prompt=system, user_message=user, config=config)`
6. El wrapper devuelve `estimation` en el dict interno → mapear a `text` en respuesta API
7. Guardar en cache el payload que necesites (puede ser dict interno o solo `text` + metadatos)

### 3.2 Router `POST /api/v1/estimate`

```python
@router.post("/estimate", response_model=EstimationResponse)
def estimate(request: EstimationRequest):
    return estimate_from_request(request)
```

### 3.3 Endpoint stream (si D2 = Sí)

- Mismo `EstimationRequest`
- `system, user = render_estimation_prompt(request)`
- Pasar a `stream_events(system_prompt=system, user_message=user, ...)`
- Eliminar referencias a `transcription` y `build_system_prompt()` en el router

### 3.4 Funciones legacy

- `estimate_project(transcription: str)` → eliminar o marcar deprecated si nada la usa
- `build_system_prompt()` → sin uso tras migración; eliminar en Paso 6 o aquí si no rompe nada

## Tareas

- [x] Implementar `estimate_from_request`
- [x] Actualizar router `/estimate`
- [x] Actualizar router `/estimate/stream` (formato SSE LIDR: status, token, complete, error)
- [x] Cache guarda `{ text, prompt_version }`; compatible con entradas antiguas vía `estimation`

## Verificación

Con API keys y Redis (opcional):

```bash
uv run uvicorn app.main:app --reload --port 8000
```

```bash
curl -s -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A small B2B SaaS to manage employee equipment loans across teams.",
    "project_type": "web_saas",
    "detail_level": "medium",
    "output_format": "phases_table"
  }' | jq .
```

Esperado: `"prompt_version": "v1"` y `"text"` con contenido no vacío.

Sin API key (mock rápido en consola o esperar Paso 5 con tests).

## Riesgos

- Payload cacheado con forma antigua (`estimation`, `model`, …): primer request tras deploy = miss; aceptable.
- `generate_sync` sigue devolviendo `estimation`; el mapeo a `text` debe ser explícito en un solo sitio.

## Antes de continuar

Confirma: **“Podemos continuar con el Paso 4 (Streamlit)”** cuando `/api/v1/estimate` responda el nuevo JSON (con curl o test mockeado).
