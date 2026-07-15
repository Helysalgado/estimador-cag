# Estimador CAG

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?logo=openai&logoColor=white)
![Jinja2](https://img.shields.io/badge/Jinja2-3.1-B41717?logo=jinja&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?logo=redis&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![uv](https://img.shields.io/badge/uv-package_manager-DE5FE9)

Servicio de estimación de proyectos de software con **FastAPI**, **LiteLLM** y plantillas **Jinja2** versionadas.

| Modo | Para qué sirve | Endpoint principal |
|------|----------------|-------------------|
| **Formulario (Sesión 4)** | Una petición, una estimación completa con enums tipados | `POST /api/v1/estimate` |
| **Conversación (Sesión 5)** | Varios turnos en la misma sesión, con memoria y adjuntos | `POST /api/v1/sessions/{id}/estimate` |
| **Embeddings (Sesión 7)** | Similitud par-a-par y sanity check (`compare.py`) | `scripts/compare.py` |
| **pgvector (Sesión 8)** | Ingesta persistida + búsqueda semántica top-k | `POST /api/v1/embeddings/ingest`, `POST /api/v1/search` |
| **Híbrida + rerank (Sesión 10)** | Full-text + RRF + cross-encoder (configs A–D) | `POST /api/v1/search` con `search_mode` / `rerank` |
| **RAG grounded (Sesión 11)** | Estimación estructurada con citas por línea + RAGAS | `POST /api/v1/rag/estimate` |
| **Agente (Sesión 12)** | Bucle tools: `search_budgets` + `calculate_estimate` + traza | `POST /api/v1/agent/estimate` |
| **Grafo LangGraph (Sesión 13)** | Orquestación de 5 nodos + checkpointer + status | `POST /api/v1/graph/estimate` |

El cliente **Streamlit** cubre formulario y conversación en pestañas; el pipeline de embeddings se consume por HTTP (curl, Swagger u otro backend).

Parte del programa **Master en AI Engineering**. Referencia LIDR: [session_4/estimator](https://github.com/LIDR-academy/ai-engineering/tree/session_4/estimator). Planes locales: [`session-04`](docs/plans/session-04/README.md) · [`session-05`](docs/plans/session-05/README.md) · [`session-06`](docs/plans/session-06/README.md) · [`session-07`](docs/plans/session-07/README.md) · [`session-08`](docs/plans/session-08/README.md) · [`session-10`](docs/plans/session-10/README.md) · [`session-11`](docs/plans/session-11/README.md) · [`session-12`](docs/plans/session-12/README.md) · [`session-13`](docs/plans/session-13/README.md).

## Requisitos

- Python 3.11+ ([`.python-version`](.python-version))
- [uv](https://docs.astral.sh/uv/)
- API key de OpenAI y/o Anthropic en `.env`
- Redis (opcional; cache solo en el modo formulario)
- PostgreSQL + pgvector (Sesiones 8–11; vía `docker compose up -d postgres`)
- Para reranking (Sesión 10): `sentence-transformers` ya viene en deps; la primera carga del modelo descarga pesos de Hugging Face
- Para RAGAS (Sesión 11): `ragas` + `datasets` + `langchain-openai` (vía `uv sync`)

## Configuración rápida

```bash
cp .env.example .env
# Rellena OPENAI_API_KEY y/o ANTHROPIC_API_KEY
uv sync --extra dev
docker compose up -d redis   # opcional
```

Variables relevantes para la **Sesión 5** (además de las del LLM):

| Variable | Default | Uso |
|----------|---------|-----|
| `SESSION_MAX_TURNS` | `6` | Pares user/assistant que se conservan en memoria (ventana deslizante) |
| `MAX_ATTACHMENT_BYTES` | `5000000` | Tamaño máximo por archivo adjunto |
| `MAX_ATTACHMENTS_PER_REQUEST` | `5` | Archivos por turno |
| `ESTIMATOR_API_BASE_URL` | `http://localhost:8000` | URL que usa Streamlit |

Variables relevantes para la **Sesión 10** (retrieval híbrido + rerank):

| Variable | Default | Uso |
|----------|---------|-----|
| `DATABASE_URL` | `postgresql+asyncpg://estimator:estimator@localhost:5432/estimator` | Postgres + pgvector |
| `RERANKING_ENABLED` | `false` | Default de `/search` si el body no envía `rerank` |
| `RERANKER_MODEL_NAME` | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | Cross-encoder multilingüe local |
| `RETRIEVAL_CANDIDATE_POOL_SIZE` | `50` | Recall amplio antes del rerank |
| `RETRIEVAL_TOP_K` | `5` | Top-k por defecto al consumidor |
| `RRF_SMOOTHING_K` | `60` | Constante de Reciprocal Rank Fusion |

Variables relevantes para la **Sesión 11** (generación grounded + RAGAS):

| Variable | Default | Uso |
|----------|---------|-----|
| `RAG_GENERATION_MODEL` | `gpt-4o-mini` | Structured output del estimate RAG |
| `RAGAS_JUDGE_MODEL` | `gpt-4o-mini` | LLM juez de métricas RAGAS |
| `RAGAS_EMBEDDING_MODEL` | `text-embedding-3-small` | Embeddings del eval RAGAS |

Variables relevantes para la **Sesión 12** (agente):

| Variable | Default | Uso |
|----------|---------|-----|
| `AGENT_MODEL` | `gpt-5` | Modelo del bucle (entrega) |
| `AGENT_DEBUG_MODEL` | `gpt-5-mini` | Smoke del bucle (`--debug`) |
| `AGENT_REASONING_EFFORT` | `medium` | `reasoning.effort` Responses API |
| `AGENT_MAX_ITERATIONS` | `12` | Tope de salvaguarda del bucle |

Variables relevantes para la **Sesión 13** (LangGraph):

| Variable | Default | Uso |
|----------|---------|-----|
| `GRAPH_LLM_MODEL` | `gpt-4o-mini` | Extract / classify nodes |
| `LOGFIRE_TOKEN` | (vacío) | Si vacío: Logfire local (`send_to_logfire=False`) |

## Cómo levantar

### API (FastAPI)

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Documentación interactiva: `http://localhost:8000/docs`
- Health: `GET http://localhost:8000/health`

### Cliente Streamlit

Proceso aparte; habla con la API por HTTP:

```bash
uv run streamlit run streamlit_app.py
# http://localhost:8501
```

- Pestaña **Conversación (Sesión 5)**: crea sesión automáticamente, chat multi-turno, adjuntos PDF/DOCX, metadata en la barra lateral.
- Pestaña **Formulario clásico (Sesión 4)**: mismo flujo que antes (`POST /api/v1/estimate`).

---

## Modo 1 — Formulario (Sesión 4)

Un JSON con `description` y tres enums. Respuesta: texto libre + `prompt_version`.

```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A small B2B SaaS to manage employee equipment loans across teams.",
    "project_type": "web_saas",
    "detail_level": "medium",
    "output_format": "phases_table"
  }'
```

```json
{
  "text": "| phase | duration_weeks | cost_eur | …",
  "prompt_version": "v1"
}
```

**Variantes útiles**

- Plantilla **v2**: `?prompt_version=v2` (mismo body).
- **Streaming** (SSE): `POST /api/v1/estimate/stream` con eventos `status`, `token`, `complete`, `error`.
- **Proyectos de referencia** (opcional): campo `reference_projects` en el JSON (bloque `<reference_projects>` en el system prompt).
- **Cache Redis**: mismas entradas system+user+modelo → misma respuesta durante `CACHE_TTL_SECONDS`.

---

## Modo 2 — Conversación con sesión (Sesión 5)

### Flujo en tres pasos

```text
1. POST /api/v1/sessions              →  { "session_id": "<uuid>" }
2. POST /api/v1/sessions/{id}/estimate (multipart, un turno)
3. GET  /api/v1/sessions/{id}          (debug de memoria/tier)
4. (Opcional) POST /api/v1/sessions/{id}/estimate-acb
```

La sesión guarda en memoria:

- **Historial** (`ConversationHistory`): últimos `SESSION_MAX_TURNS` pares user/assistant (ventana deslizante).
- **Metadata** (`ProjectMetadata`): hechos estables del proyecto (nombre, tecnologías, alcance…), separados del historial e inyectados en el system prompt.

```mermaid
sequenceDiagram
    participant C as Cliente
    participant API as FastAPI
    participant M as Memoria (proceso)
    participant LLM as LiteLLM

    C->>API: POST /sessions
    API->>M: crear session_id
    API-->>C: session_id

    C->>API: POST /sessions/{id}/estimate (transcript + adjuntos)
    API->>M: leer historial + metadata
    API->>LLM: messages[] con system + historial + turno actual
    LLM-->>API: estimación
    API->>M: guardar turno y actualizar metadata
    API-->>C: text, prompt_version, project_metadata, turn_count
```

### Crear sesión

```bash
curl -s -X POST http://localhost:8000/api/v1/sessions
# {"session_id":"550e8400-e29b-41d4-a716-446655440000"}
```

### Enviar un turno (multipart)

Campos del formulario:

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `transcript` | form field | Sí | Mensaje del usuario en este turno |
| `attachments` | file(s) | No | PDF o DOCX (hasta `MAX_ATTACHMENTS_PER_REQUEST`) |
| `prompt_version` | query | No | `v1` (default) o `v2` |
| `tier` | query | No | Override opcional: `default`, `executive`, `pm`, `developer` |

**Solo texto:**

```bash
SESSION_ID="<uuid-de-paso-anterior>"

curl -s -X POST "http://localhost:8000/api/v1/sessions/${SESSION_ID}/estimate" \
  -F 'transcript=Project called InventoryHub with React. Team of 4 developers.'
```

**Con adjunto:**

```bash
curl -s -X POST "http://localhost:8000/api/v1/sessions/${SESSION_ID}/estimate" \
  -F 'transcript=Please review the attached scope document.' \
  -F 'attachments=@./docs/scope-ejemplo.docx'
```

Respuesta de un turno:

```json
{
  "text": "…estimación del LLM…",
  "prompt_version": "v1",
  "turn_count": 2,
  "tier": "pm",
  "tier_rule": "small_team_pm",
  "project_metadata": {
    "project_name": "InventoryHub",
    "assumed_team_size": 4,
    "mentioned_technologies": ["React"],
    "agreed_scope": "…",
    "explicit_constraints": [],
    "rejected_options": []
  }
}
```

Debug de sesión:

```bash
curl -s "http://localhost:8000/api/v1/sessions/${SESSION_ID}"
```

Respuesta (campos principales):

```json
{
  "message_count": 6,
  "anchors_count": 3,
  "summary_chars": 840,
  "last_resolved_tier": "pm",
  "last_tier_rule": "small_team_pm"
}
```

Modo ACB opcional:

```bash
curl -s -X POST "http://localhost:8000/api/v1/sessions/${SESSION_ID}/estimate-acb" \
  -F 'transcript=Refine estimate with stronger risk mitigation'
```

El endpoint **stateless** `POST /api/v1/estimate` sigue disponible y no comparte memoria con las sesiones.

---

## Modo 3 — Similitud de embeddings (Sesión 7)

Chunking estructural y embeddings OpenAI `text-embedding-3-small` (ver Modo 4 para persistencia). Datos de ejemplo: [`data/budgets_sample.json`](data/budgets_sample.json). Sanity check: [`app/embedding_pipeline/SANITY_CHECK.md`](app/embedding_pipeline/SANITY_CHECK.md).

### Comparar dos textos (CLI)

Fuera del contenedor (carga `.env` automáticamente):

```bash
uv run python scripts/compare.py \
  --text-a "OAuth 2.0 authentication backend for fintech" \
  --text-b "JWT-based authorization service for banking app"
```

Dentro de Docker Compose (servicio `ai_service`):

```bash
docker compose exec ai_service python scripts/compare.py \
  --text-a "OAuth 2.0 authentication backend for fintech" \
  --text-b "JWT-based authorization service for banking app"
```

Requiere `OPENAI_API_KEY`. Plan S7: [`docs/plans/session-07/`](docs/plans/session-07/README.md).

---

## Modo 4 — pgvector + búsqueda semántica (Sesión 8)

Presupuestos JSON → chunk + embed → **PostgreSQL + pgvector** (`documents` + `chunks`) → búsqueda top-k por distancia coseno.

### Levantar stack y migrar

```bash
docker compose up -d postgres ai_service
docker compose exec ai_service uv run alembic upgrade head
```

### Ingest (un presupuesto por request)

```bash
jq '{
  source_path: ("data/budgets/" + .[0].budget_id + ".json"),
  document_type: "historical_budget",
  content: .[0]
}' data/budgets_sample.json \
  | curl -s -X POST http://localhost:8000/api/v1/embeddings/ingest \
      -H "Content-Type: application/json" -d @-
```

Respuesta: `document_id`, `chunks_created`, `embedding_dimension`, `ingestion_time_ms`. Duplicado por `source_path` → **409**.

### Poblar corpus de ejemplo (15 presupuestos)

```bash
docker compose exec ai_service uv run python scripts/ingest_sample_corpus.py
```

### Búsqueda semántica

```bash
curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "REST API with OAuth authentication for fintech sector", "k": 5}' | jq
```

Alias del material: `POST /embeddings/ingest`, `POST /search`.

### Queries de ejemplo

```bash
docker compose exec ai_service uv run python scripts/query_examples.py | tee output_examples.txt
```

### Decisiones de schema (resumen)

- **Dos tablas (`documents` + `chunks`):** un presupuesto genera N chunks; la FK con `ON DELETE CASCADE` mantiene integridad sin duplicar metadata del documento en cada fila.
- **`metadata` JSONB:** campos estables en columnas tipadas; tags, scope y enriquecimiento del chunker van en JSONB sin migrar el schema cada vez (índice GIN preparado para filtros futuros).
- **`cosine_distance`:** embeddings OpenAI normalizados; alinea con el índice HNSW `vector_cosine_ops` que se añade en la sesión en vivo.
- **Sin índice vectorial (por ahora):** sequential scan como baseline para medir el impacto del índice en directo.

Plan S8: [`docs/plans/session-08/`](docs/plans/session-08/README.md). Rama: **`pre-session-08`**.

---

## Modo 5 — Búsqueda híbrida + reranking (Sesión 10)

Extiende `POST /api/v1/search` (y el alias `POST /search`) con:

| Campo | Default | Significado |
|-------|---------|-------------|
| `search_mode` | `vector` | `vector` = solo coseno (S8); `hybrid` = vector ∥ full-text español + RRF |
| `rerank` | `null` → settings | `true`/`false` en el body; si se omite, usa `RERANKING_ENABLED` |
| `candidate_pool_size` | `50` | Tamaño del recall antes del cross-encoder |
| `k` | `5` | Resultados finales |

La columna `chunks.content_tsv` (Alembic `0002`, config `'spanish'`) alimenta la rama léxica. El reranker es `CrossEncoder` local (recall → top-k); la inferencia corre en `asyncio.to_thread`.

### Configuraciones del ejercicio (A–D)

| Config | `search_mode` | `rerank` |
|--------|---------------|----------|
| A | `vector` | `false` |
| B | `hybrid` | `false` |
| C | `vector` | `true` |
| D | `hybrid` | `true` |

Resultados medidos en este repo: [`evals/retrieval/REPORT.md`](evals/retrieval/REPORT.md) (p. ej. A/B ≈ **0.72** P@5; C/D ≈ **0.64** con ~+100 ms).

### Flujo recomendado (API local + Postgres Docker)

La imagen `ai_service` con `torch`/`sentence-transformers` es muy pesada. Para desarrollo y la medición:

```bash
docker compose up -d postgres
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
# otra terminal:
uv run python scripts/ingest_sample_corpus.py
uv run python -m app.embedding_pipeline.retrieval.verify_reranker

# Config D: hybrid + rerank
curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Integración de pagos con Stripe incluyendo webhooks",
    "k": 5,
    "search_mode": "hybrid",
    "rerank": true,
    "candidate_pool_size": 50
  }' | jq

# Medición A–D (precision@5 + latencia mediana)
uv run python scripts/measure_retrieval.py --config all
```

Golden set: [`evals/retrieval/golden_set.json`](evals/retrieval/golden_set.json).  
Plan: [`docs/plans/session-10/`](docs/plans/session-10/README.md). Rama: **`session-10/pre-work`**.

---

## Modo 6 — Estimación RAG grounded + RAGAS (Sesión 11)

Camino **aparte** del formulario S4 (`POST /api/v1/estimate` texto libre). Flujo:

`query` → retrieval S10 (híbrida por defecto) → prompt con `chunk_id` → `Estimate` estructurado (Responses API) → `verify_citations` → respuesta con `citation_report`.

| Campo request | Default | Significado |
|---------------|---------|-------------|
| `query` | — | Consulta de estimación |
| `search_mode` | `hybrid` | Mismo contrato que `/search` |
| `rerank` | `false` | Config B de S10 por defecto |
| `k` | `5` | Chunks en contexto |
| `candidate_pool_size` | `50` | Pool si `rerank=true` |

La respuesta incluye `estimate` (líneas con `grounded` / `sources`), `citation_report` (`ok`, dangling ids), `retrieval` (`chunk_ids` + `contexts`) y `request_id`. `/api/v1/estimate` legacy no cambia.

### Flujo recomendado

```bash
# API + corpus ya levantados (ver Modo 5)
curl -s -X POST http://localhost:8000/api/v1/rag/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Integración de pagos con Stripe incluyendo webhooks de facturación",
    "k": 5,
    "search_mode": "hybrid",
    "rerank": false
  }' | jq

# Eval RAGAS (5 queries + ground_truth) → evals/retrieval/RAGAS_REPORT.md
uv run python scripts/eval_ragas.py
```

### Resultados medidos (RAGAS)

Promedios en este repo ([`evals/retrieval/RAGAS_REPORT.md`](evals/retrieval/RAGAS_REPORT.md)):

| Faithfulness | Answer relevancy | Context precision | Context recall |
|-------------:|-----------------:|------------------:|---------------:|
| 0.72 | 0.42 | 0.90 | 0.58 |

`verify_citations` OK en las 5 queries del golden set. Context precision fuerte; answer relevancy más baja porque la respuesta es estructurada (líneas + huecos `grounded=false`) frente a un `ground_truth` en prosa.

| Pieza | Ubicación |
|-------|-----------|
| Schemas / verify / generate | `app/embedding_pipeline/generation/` |
| Endpoint | `POST /api/v1/rag/estimate` |
| Golden + `ground_truth` | `evals/retrieval/golden_set.json` |
| Informe RAGAS | [`evals/retrieval/RAGAS_REPORT.md`](evals/retrieval/RAGAS_REPORT.md) |
| Plan | [`docs/plans/session-11/`](docs/plans/session-11/README.md) |

Rama: **`session-11/pre-work`**.

---

## Modo 7 — Agente de estimación (Sesión 12)

Capa de **decisión** encima del retrieval S10: el modelo elige cuántas búsquedas hacer y cuándo calcular. Bucle **manual** (sin LangChain / agents SDK): `function_call` → ejecutas tú → `function_call_output` + `previous_response_id`. No modifica `/api/v1/estimate` ni `/api/v1/rag/estimate`.

Tools:

| Tool | Rol |
|------|-----|
| `search_budgets` | Envuelve hybrid retrieve (una query enfocada por componente) |
| `calculate_estimate` | Mediana determinista de `reference_amounts` → total (sin LLM) |

| Campo request | Default | Significado |
|---------------|---------|-------------|
| `transcript` | — | Transcripción de reunión (≥20 chars) |
| `model` | `AGENT_MODEL` (`gpt-5`) | Override opcional; smoke con `gpt-5-mini` |
| `max_iterations` | `12` | Tope del bucle |
| `search_mode` / `rerank` / `k` | hybrid / false / 5 | Flags del retrieval S10 |

Respuesta: `estimate_text`, `trace` / `trace_text` (STEP reasoning → action → observation), `tool_calls`, `iterations`, `request_id`.

### Flujo recomendado

```bash
# API + corpus (Modo 5)
curl -s -X POST http://localhost:8000/api/v1/agent/estimate \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile t examples/agent/sample_transcript_complex.txt '{transcript:$t}')" | jq

# CLI + traza (recomendado para la entrega)
uv run python scripts/run_agent.py \
  --transcript examples/agent/sample_transcript_complex.txt \
  --out evals/agent/TRACE_complex.md

# Smoke barato del bucle
uv run python scripts/run_agent.py \
  --transcript examples/agent/sample_transcript_simple.txt \
  --debug \
  --out evals/agent/TRACE_simple.md
```

### Resultado medido (transcript complex)

Corrida en este repo ([`evals/agent/TRACE_complex.md`](evals/agent/TRACE_complex.md)): modelo `gpt-5`, **6×** `search_budgets` (ecommerce, Stripe/Connect, scheduling, messaging, FHIR, HIPAA layer) + **1×** `calculate_estimate`; termina solo (`stopped_reason=completed`). Cumple el criterio de >1 componente y >1 búsqueda.

| Pieza | Ubicación |
|-------|-----------|
| Agente | `app/agents/` |
| Endpoint | `POST /api/v1/agent/estimate` |
| Transcripts | `examples/agent/sample_transcript_{simple,complex}.txt` |
| Traza complex | [`evals/agent/TRACE_complex.md`](evals/agent/TRACE_complex.md) |
| Plan | [`docs/plans/session-12/`](docs/plans/session-12/README.md) |

Rama: **`session-12/pre-work`**.

---

## Modo 8 — Grafo LangGraph (Sesión 13)

Orquestación **explícita** del flujo de estimación (Niveles 1–3 del material):

```text
START → extract_requirements → classify_components → search_budgets
      → generate_estimate → validate_and_consolidate → END
         (condicional: validated | needs_review)
```

Reutiliza retrieval S10 / tools S12 dentro de los nodos. Checkpointer `AsyncPostgresSaver` en el mismo Postgres. Spans Logfire por nodo.

```bash
# CLI + traza de entrega
uv run python scripts/run_graph.py \
  --transcript examples/agent/sample_transcript_complex.txt \
  --out evals/agent/GRAPH_TRACE.md

# HTTP
curl -s -X POST http://localhost:8000/api/v1/graph/estimate \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile t examples/agent/sample_transcript_complex.txt \
      '{transcript:$t, estimation_id:"demo-thread-1"}')" | jq
```

| Pieza | Ubicación |
|-------|-----------|
| Grafo | `app/graph/` |
| Endpoint | `POST /api/v1/graph/estimate` |
| Traza | [`evals/agent/GRAPH_TRACE.md`](evals/agent/GRAPH_TRACE.md) |
| Plan | [`docs/plans/session-13/`](docs/plans/session-13/README.md) |

Rama: **`session-13/pre-work`**.

---

## Adjuntos: Camino B (extracción local)

No usamos visión del modelo ni RAG en esta fase. Los archivos se procesan **en el servidor** antes de llamar al LLM:

| Formato | Librería | Qué hace |
|---------|----------|----------|
| PDF | `pypdf` | Extrae texto de cada página |
| DOCX | `python-docx` | Extrae párrafos |

**Por qué Camino B**

- Menor coste y latencia que enviar binarios al LLM.
- Comportamiento predecible en tests (texto fijo en el prompt).
- Adecuado para documentos con texto seleccionable; no sustituye OCR de escaneos.

El texto extraído se añade al turno del usuario con delimitadores:

```text
--- attachment: scope.pdf ---
<texto extraído>
```

Ese bloque viaja en el mensaje `user` del historial. Tipos no permitidos (p. ej. `.exe`) devuelven **400** con `error: unsupported_file_type`.

---

## Cómo se actualiza `project_metadata`

Tras cada turno completado, una **heurística simple** (sin LLM extra) enriquece la metadata a partir del transcript y de la respuesta del asistente:

| Señal en el texto | Campo actualizado |
|-------------------|-------------------|
| `project called X`, `app named X` | `project_name` |
| `team of N`, `N developers` | `assumed_team_size` |
| Palabras clave (React, PostgreSQL, FastAPI, …) | `mentioned_technologies` |
| Último transcript (recortado) | `agreed_scope` |
| Frases con *must* / *cannot* | `explicit_constraints` |
| *don't want*, *reject*, *instead of* | `rejected_options` |

La metadata se inyecta en el **system prompt** dentro de `<project_metadata>` (solo si hay contenido). El historial de chat no se mezcla con estos hechos: así el modelo trata la metadata como contexto estable y el historial como diálogo reciente.

---

## Limitaciones actuales (Sesión 5)

| Tema | Comportamiento |
|------|----------------|
| **Persistencia** | Las sesiones viven en un `dict` en memoria del proceso. Al reiniciar uvicorn se pierden. |
| **Varios workers** | Cada worker tiene su propio almacén; no compartir `session_id` entre procesos. |
| **TTL / archivado** | No hay expiración automática de sesiones inactivas. |
| **Cache Redis** | Solo aplica al modo formulario (`/estimate`), no a turnos de sesión. |
| **Adjuntos** | PDF/DOCX con texto extraíble; escaneos imagen necesitarían OCR (fuera de alcance). |
| **Metadata** | Heurística básica; puede omitir o sobrescribir datos si el lenguaje es ambiguo. |
| **ACB** | Implementación inicial opcional; la iteración avanzada Actor-Critic-Boss sigue siendo simplificada. |

Para producción haría falta Redis/PostgreSQL para sesiones, política de TTL y, si aplica, extracción más robusta de documentos.

---

## Probar streaming (modo formulario)

```bash
curl -N -X POST http://localhost:8000/api/v1/estimate/stream \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Internal tool for marketing assets with search and approvals.",
    "project_type": "internal_tool",
    "detail_level": "medium",
    "output_format": "phases_table"
  }'
```

## Tests

```bash
uv run pytest
```

La suite no llama a APIs externas (LLM y Redis mockeados donde hace falta):

| Archivo | Qué cubre |
|---------|-----------|
| `tests/test_schemas.py` | Validación `EstimationRequest` |
| `tests/test_prompts.py` | Jinja2, `v1`/`v2`, referencias, `<project_metadata>` |
| `tests/test_sessions.py` | Ventana deslizante, `SessionStore` |
| `tests/test_sessions_endpoint.py` | HTTP sesiones y multipart |
| `tests/test_session_estimation.py` | Orquestación de turno y heurísticas |
| `tests/test_session_integration.py` | Memoria multi-turno, adjuntos en prompt, ventana |
| `tests/test_attachments.py` | Extracción PDF/DOCX |
| `tests/test_estimate_*.py` | Estimate stateless y cache |
| `tests/test_llm_wrapper.py` | LiteLLM, mensajes multi-turno |
| `tests/test_health.py` | Health check |
| `tests/test_embedding_schemas.py` | Schemas de presupuestos/chunks |
| `tests/test_chunker.py` | Chunker estructural JSON |
| `tests/test_embedder.py` | Batching y reintentos del embedder (mock) |
| `tests/test_embeddings_router.py` | `POST /api/v1/embeddings/ingest` (persist) |
| `tests/test_search_router.py` | `POST /api/v1/search` (vector / hybrid flags) |
| `tests/test_rrf_fusion.py` | Reciprocal Rank Fusion |
| `tests/test_verify_citations.py` | Integridad de schema + citación colgante (S11) |
| `tests/test_agent_tools.py` | `calculate_estimate` + schemas/tools/traza (S12, sin OpenAI) |
| `tests/test_graph_routing.py` | Routing N3 + compile grafo (S13, sin OpenAI) |
| `tests/test_similarity.py` | Similitud coseno (stdlib) |
| `tests/test_embedding_benchmark.py` | Harness de benchmark (mock, sin red) |

Los tests de embeddings **no** llaman a OpenAI; el sanity check manual sí (ver `SANITY_CHECK.md`). El cross-encoder **no** se carga en pytest (lazy); `verify_reranker` y `measure_retrieval.py` sí lo usan. `eval_ragas.py` sí llama a OpenAI (generación + juez).

### Evals (Session 06 parity)

Dataset golden y runner CLI:

```bash
uv run python evals/run.py --mode actor
uv run python evals/run.py --mode acb
```

Incluye 16 casos en `evals/golden_dataset.json` y 3 métricas binarias:
- `SchemaAdherenceMetric`
- `CostBoundsMetric`
- `ContentRecallMetric`

Stress runner (escenarios multi-turno + adjuntos + CSV):

```bash
# API en marcha (uvicorn en :8000) y claves LLM en .env
uv run python -m evals.stress.run \
  --http http://127.0.0.1:8000 \
  --scenarios growing,pivot,contradiction \
  --attachment-sizes 0,5,20,50,100 \
  --repeats 3 \
  --mode actor \
  --latency-budget-ms 8000 \
  --cost-budget-usd 0.25 \
  --max-error-rate 0.2 \
  --output evals/stress/results.csv

# Smoke in-process (sin LLM real, útil en CI):
# uv run python -m evals.stress.run --scenarios growing --attachment-sizes 0 --repeats 1

# Reporte cuantitativo desde el CSV (Fase 5)
uv run python -m evals.stress.build_report
```

Artefactos generados:
- `evals/stress/results.csv`
- `evals/stress/REPORT.md` (regenerable con `build_report`)

Coste orientativo de la corrida completa: ~900 llamadas LLM (3 escenarios × 5 tamaños × 3 repeticiones × 20 turnos). Para validar el pipeline antes, usa un solo escenario y `--repeats 1`.

Si el repo está en Google Drive y ves `TimeoutError` al escribir el CSV, el runner guarda primero en `/tmp` y copia al final; también puedes usar `--output /tmp/results.csv`.

```bash
uv run python scripts/validate_structure.py
```

## Estructura del proyecto

```
estimador-cag/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db/                     # Sesión 8: SQLAlchemy + pgvector
│   ├── routers/
│   │   ├── estimations.py      # POST /api/v1/estimate (+ /stream)
│   │   └── sessions.py         # POST /api/v1/sessions, .../estimate
│   ├── embedding_pipeline/     # Sesiones 7–11: ingest, search, hybrid, RAG
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   ├── router.py             # ingest + /search
│   │   ├── schemas.py
│   │   ├── similarity.py
│   │   ├── retrieval/            # Sesión 10: vector, fulltext, RRF, rerank
│   │   ├── generation/           # Sesión 11: estimate estructurado + citas
│   │   ├── embedding_benchmark.py
│   │   └── SANITY_CHECK.md
│   ├── agents/                 # Sesión 12: bucle tools + traza
│   ├── graph/                  # Sesión 13: LangGraph StateGraph
│   ├── schemas/
│   │   ├── estimation.py
│   │   └── sessions.py
│   ├── prompts/
│   │   ├── loader.py
│   │   └── estimation/
│   │       ├── project_metadata.j2
│   │       ├── v1/  (system, user, examples)
│   │       └── v2/
│   └── services/
│       ├── sessions.py
│       ├── session_estimation.py
│       ├── attachments.py
│       ├── llm_wrapper.py
│       ├── llm_service.py
│       └── cache.py
├── alembic/versions/           # 0001 schema; 0002 content_tsv + GIN
├── tests/
├── streamlit_app.py
├── data/
│   └── budgets_sample.json
├── scripts/
│   ├── compare.py
│   ├── ingest_sample_corpus.py
│   ├── query_examples.py
│   ├── measure_retrieval.py    # Sesión 10: configs A–D
│   ├── eval_ragas.py           # Sesión 11: métricas RAGAS
│   ├── run_agent.py            # Sesión 12: agente + traza
│   ├── run_graph.py            # Sesión 13: grafo + GRAPH_TRACE
│   └── validate_structure.py
├── examples/
│   ├── transcripts/            # Sesión 9
│   └── agent/                  # Sesión 12: sample_transcript_*.txt
├── evals/
│   ├── retrieval/              # S10 REPORT + S11 RAGAS_REPORT + golden_set
│   ├── agent/                  # S12 TRACE + S13 GRAPH_TRACE
│   ├── golden_dataset.json
│   └── stress/
├── docs/plans/session-04/ … session-13/
├── arquitectura-actual.md      # Sesión 9: diagnóstico
└── pyproject.toml
```

### Versionado de prompts

Plantillas en `app/prompts/estimation/<version>/`. Para una nueva versión: copiar `v1/` → `vN/`, editar `.j2` y pasar `prompt_version=vN` en query (formulario o sesión).

## Variables de entorno

| Variable | Default | Notas |
|----------|---------|--------|
| `OPENAI_API_KEY` | — | Al menos una key LLM |
| `ANTHROPIC_API_KEY` | — | Al menos una key LLM |
| `LLM_PROVIDER` | `openai` | Proveedor principal |
| `LLM_MODEL` | `gpt-4o-mini` | Modelo principal |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache modo formulario |
| `CACHE_TTL_SECONDS` | `86400` | TTL cache (24 h) |
| `SESSION_MAX_TURNS` | `6` | Ventana de historial en sesiones |
| `MAX_CONVERSATION_TURNS` | `6` | Alias compatible Session 06 para ventana |
| `MAX_SUMMARY_CHARS` | `4000` | Tamaño máximo del summary acumulativo |
| `MAX_ANCHORS` | `20` | Máximo anchors heurísticos persistidos |
| `METADATA_EXTRACTOR_MODEL` | `gpt-4o-mini` | Modelo barato de extractor metadata |
| `ENABLE_ACB` | `true` | Habilita endpoint `/estimate-acb` |
| `ACB_MAX_ITERATIONS` | `2` | Iteraciones máximas de lazo ACB |
| `MAX_ATTACHMENT_BYTES` | `5000000` | Límite por adjunto |
| `MAX_ATTACHMENTS_PER_REQUEST` | `5` | Adjuntos por turno |
| `ESTIMATOR_API_BASE_URL` | `http://localhost:8000` | Cliente Streamlit |
| `APP_ENV` | `development` | En dev, 502 incluye detalle JSON |
| `DATABASE_URL` | ver `.env.example` | Postgres async (pgvector) |
| `RERANKING_ENABLED` | `false` | Default rerank en `/search` |
| `RERANKER_MODEL_NAME` | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | Modelo local S10 |
| `RETRIEVAL_CANDIDATE_POOL_SIZE` | `50` | Recall amplio |
| `RETRIEVAL_TOP_K` | `5` | Top-k default |
| `RRF_SMOOTHING_K` | `60` | Suavizado RRF |
| `RAG_GENERATION_MODEL` | `gpt-4o-mini` | Structured RAG estimate (S11) |
| `RAGAS_JUDGE_MODEL` | `gpt-4o-mini` | Juez RAGAS (S11) |
| `RAGAS_EMBEDDING_MODEL` | `text-embedding-3-small` | Embeddings RAGAS (S11) |
| `AGENT_MODEL` | `gpt-5` | Modelo agente S12 |
| `AGENT_DEBUG_MODEL` | `gpt-5-mini` | Smoke agente S12 |
| `AGENT_REASONING_EFFORT` | `medium` | Effort Responses API |
| `AGENT_MAX_ITERATIONS` | `12` | Tope bucle agente |
| `GRAPH_LLM_MODEL` | `gpt-4o-mini` | Nodos extract/classify (S13) |
| `LOGFIRE_TOKEN` | — | Observabilidad Logfire (S13) |

### Si aparece 502 (`Upstream LLM call failed`)

1. Claves en `.env` en la carpeta desde la que arrancas **uvicorn**; reinicia tras editar.
2. `LLM_PROVIDER` / `LLM_MODEL` alineados con la key disponible.
3. `ESTIMATOR_API_BASE_URL` apunta al puerto real del API (Streamlit).
4. Con `APP_ENV=development`, el JSON del 502 incluye `error_type`, `error` y `hint`; en terminal verás `estimation_llm_failed` o `session_estimation_llm_failed`.

## Docker

```bash
docker compose up -d postgres redis
# API local (recomendado en S10 por el tamaño de torch en la imagen):
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

También puedes `docker compose build && docker compose up` para `ai_service`, pero el build con `sentence-transformers` tarda mucho (deps CUDA/torch). Streamlit fuera de Compose contra `ESTIMATOR_API_BASE_URL`.

## CI

En push/PR a `main`/`master`: validación de estructura y `pytest`.

## Documentación adicional

- Plan Sesión 04: [`docs/plans/session-04/`](docs/plans/session-04/README.md)
- Plan Sesión 05: [`docs/plans/session-05/`](docs/plans/session-05/README.md)
- Plan Sesión 06 (stress CAG): [`docs/plans/session-06/`](docs/plans/session-06/README.md)
- Plan Sesión 07 (embeddings): [`docs/plans/session-07/`](docs/plans/session-07/README.md)
- Plan Sesión 08 (pgvector): [`docs/plans/session-08/`](docs/plans/session-08/README.md)
- Plan Sesión 10 (híbrida + rerank): [`docs/plans/session-10/`](docs/plans/session-10/README.md)
- Plan Sesión 11 (RAG grounded + RAGAS): [`docs/plans/session-11/`](docs/plans/session-11/README.md)
- Plan Sesión 12 (agente + tools): [`docs/plans/session-12/`](docs/plans/session-12/README.md)
- Plan Sesión 13 (LangGraph): [`docs/plans/session-13/`](docs/plans/session-13/README.md)
- Diagnóstico S9: [`arquitectura-actual.md`](arquitectura-actual.md)
- Medición retrieval S10: [`evals/retrieval/REPORT.md`](evals/retrieval/REPORT.md)
- Informe RAGAS S11: [`evals/retrieval/RAGAS_REPORT.md`](evals/retrieval/RAGAS_REPORT.md)
- Traza agente S12: [`evals/agent/TRACE_complex.md`](evals/agent/TRACE_complex.md)
- Traza grafo S13: [`evals/agent/GRAPH_TRACE.md`](evals/agent/GRAPH_TRACE.md)
- Índice de documentación: [`docs/README.md`](docs/README.md)
- Texto de ejemplo para `description`: [`docs/transcripcion-reunion.md`](docs/transcripcion-reunion.md)

## Ramas de desarrollo

| Rama | Contenido principal |
|------|---------------------|
| `pre-session-06` | Stress evals, `turn_observed`, reportes |
| `pre-session-07` | Pipeline `embedding_pipeline` + ingest + `compare.py` |
| `pre-session-08` | Postgres + pgvector + `POST /search` |
| `session-09/pre-work` | Diagnóstico arquitectónico RAG |
| `session-10/pre-work` | Híbrida (RRF) + reranker + medición A–D |
| `session-11/pre-work` | Estimate RAG structured + `verify_citations` + RAGAS |
| `session-12/pre-work` | Agente manual (`search_budgets` + `calculate_estimate`) + traza |
| `session-13/pre-work` | LangGraph (N1–N3) + checkpointer + Logfire |
| `main` | Línea base estable |
