# Paso 7 — Bonus (opcional)

> **Depende de:** Paso 6 completado.

## Objetivo

Extensiones alineadas al bonus de la sesión: **v2** por query param, **`reference_projects`** opcional, **structlog** en el loader.

## Implementado

### 7.1 Versionado real (`prompt_version=v2`)

- [x] Carpeta `app/prompts/estimation/v2/` (tono `BONUS_V2_PROFILE`, ejemplos `V2_CALIBRATION_SET`).
- [x] `POST /api/v1/estimate?prompt_version=v1|v2` y el mismo parámetro en `/estimate/stream`.
- [x] `EstimationResponse.prompt_version` refleja la versión usada.
- [x] Tests: v2 ≠ v1; 422 si versión no soportada.

### 7.2 Contexto de proyectos similares

- [x] `ReferenceProject` + `reference_projects` opcional (máx. 10) en `EstimationRequest`.
- [x] Bloque `<reference_projects>` en `system.j2` (v1 y v2).
- [x] Tests: nombre presente cuando hay lista; bloque ausente sin lista.
- [x] Streamlit: expander con JSON opcional.

### 7.3 Logging del prompt renderizado

- [x] Dependencia `structlog`.
- [x] Evento `prompt_rendered` con `prompt_template_version`, `app_env`, `content_sha256`, `description_chars`.
- [x] Configuración en `lifespan` de `app/main.py` según `APP_ENV` (consola en development, JSON en otro).
- [x] Test con `structlog.testing.capture_logs`.

## Verificación bonus

```bash
uv run pytest -q
```

- [x] Tests nuevos pasan junto a la suite existente.
