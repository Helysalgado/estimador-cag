# Estimador CAG

Servicio IA en FastAPI que estima proyectos de software a partir de un **formulario tipado**. El cliente (Streamlit u otro backend) envía `description` y tres enums; el servicio renderiza prompts versionados con **Jinja2** y devuelve texto libre más la versión del template usado.

Parte del programa **Master en AI Engineering** (Sesión 04). Referencia: [LIDR session_4/estimator](https://github.com/LIDR-academy/ai-engineering/tree/session_4/estimator).

## Tools / Stack

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?logo=openai&logoColor=white)
![Jinja2](https://img.shields.io/badge/Jinja2-3.1-B41717?logo=jinja&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?logo=redis&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![uv](https://img.shields.io/badge/uv-package_manager-DE5FE9)

## Requisitos

- Python 3.11+ ([`.python-version`](.python-version))
- [uv](https://docs.astral.sh/uv/)
- API key de OpenAI y/o Anthropic en `.env`
- Redis (opcional pero recomendado para cache exact-match)

## Configuración

```bash
cp .env.example .env
# Define OPENAI_API_KEY y/o ANTHROPIC_API_KEY
# REDIS_URL=redis://localhost:6379/0
# CACHE_TTL_SECONDS=86400
# ESTIMATOR_API_BASE_URL=http://localhost:8000  # cliente Streamlit
```

## Cómo levantar

### API (FastAPI)

```bash
uv sync --extra dev
docker compose up -d redis   # opcional
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger: `http://localhost:8000/docs`
- Health: `GET http://localhost:8000/health`

### Cliente Streamlit (formulario)

Corre en proceso aparte y consume la API por HTTP:

```bash
uv run streamlit run streamlit_app.py
# http://localhost:8501
```

## Probar el endpoint

```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A small B2B SaaS to manage employee equipment loans across teams. Role-based access, audit trail, weekly digest.",
    "project_type": "web_saas",
    "detail_level": "medium",
    "output_format": "phases_table"
  }'
```

Respuesta:

```json
{
  "text": "| phase | duration_weeks | cost_eur | confidence_pct | …",
  "prompt_version": "v1"
}
```

### Streaming SSE (opcional)

`POST /api/v1/estimate/stream` usa el mismo body y emite eventos `status`, `token`, `complete` o `error`.

```bash
curl -N -X POST http://localhost:8000/api/v1/estimate/stream \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "description": "Internal tool to centralise marketing assets with search, tagging and approval workflow.",
  "project_type": "internal_tool",
  "detail_level": "medium",
  "output_format": "phases_table"
}
EOF
```

## Cómo testar

```bash
uv sync --extra dev
uv run pytest
```

La suite corre en milisegundos sin APIs externas:

| Archivo | Qué cubre |
|---------|-----------|
| `tests/test_schemas.py` | Validación de `EstimationRequest` |
| `tests/test_prompts.py` | Render Jinja2 (condicionales, `<project_description>`, ejemplos) |
| `tests/test_estimate_endpoint.py` | Contrato HTTP 200/422, system/user separados |
| `tests/test_estimate_stream_endpoint.py` | SSE con payload tipado |
| `tests/test_estimate_service_cache.py` | Cache Redis en `estimate_from_request` |
| `tests/test_cache.py` | Claves y TTL |
| `tests/test_llm_wrapper.py` | Wrapper LiteLLM |
| `tests/test_health.py` | Health check |

```bash
uv run python scripts/validate_structure.py
```

## Estructura del proyecto

```
estimador-cag/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   └── estimations.py       # POST /api/v1/estimate (+ /stream)
│   ├── schemas/
│   │   └── estimation.py        # Enums + request/response
│   ├── prompts/
│   │   ├── loader.py            # render_estimation_prompt()
│   │   └── estimation/v1/
│   │       ├── system.j2
│   │       ├── user.j2
│   │       └── examples.j2
│   └── services/
│       ├── llm_wrapper.py       # LiteLLM + fallback
│       ├── llm_service.py       # Orquestación + cache
│       └── cache.py             # Redis exact-match
├── tests/
├── streamlit_app.py             # Formulario → POST /api/v1/estimate
├── docs/
│   ├── plans/session-04/        # Plan de implementación paso a paso
│   └── transcripcion-reunion.md # Texto de ejemplo (campo description)
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

### Versionado de prompts

Los templates viven en `app/prompts/estimation/<version>/`. Para iterar:

1. Copia `v1/` → `v2/` y edita los `.j2`.
2. Llama `render_estimation_prompt(request, version="v2")` desde el servicio/router.
3. Devuelve `prompt_version="v2"` en la respuesta.

El contrato Pydantic y el router no deberían cambiar solo por una nueva versión de prompt.

## Variables de entorno

| Variable | Default | Notas |
|----------|---------|--------|
| `OPENAI_API_KEY` | — | Al menos una key LLM |
| `ANTHROPIC_API_KEY` | — | Al menos una key LLM |
| `LLM_PROVIDER` | `openai` | Proveedor principal |
| `LLM_MODEL` | `gpt-4o-mini` | Modelo principal |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache exact-match |
| `CACHE_TTL_SECONDS` | `86400` | TTL en segundos (24 h) |
| `ESTIMATOR_API_BASE_URL` | `http://localhost:8000` | URL que usa Streamlit |
| `APP_ENV` | `development` | Entorno |

## Docker

```bash
docker compose build
docker compose up
```

Levanta la API y Redis. Streamlit se ejecuta fuera de Compose contra `ESTIMATOR_API_BASE_URL`.

## CI

En cada push/PR a `main`/`master`, GitHub Actions ejecuta validación de estructura y `pytest`.

## Documentación adicional

- Plan Sesión 04: [`docs/plans/session-04/`](docs/plans/session-04/README.md)
- Texto de ejemplo para el campo `description`: [`docs/transcripcion-reunion.md`](docs/transcripcion-reunion.md)
