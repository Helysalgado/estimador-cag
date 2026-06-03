# Plan de implementación — Sesión 7 (embeddings + chunking)

Contraste entre:

- **Material:** `IAENG/material/mat-sesion7.md` (ejercicio pre-sesión + artículos teóricos)
- **Repo:** `estimador-cag`, rama **`pre-session-07`**
- **Estado previo:** Sesiones 4–6 (FastAPI, sesiones, stress CAG) — **sin** módulo de embeddings ni `data/budgets_sample.json`

---

## Resumen ejecutivo

| Capa | Estado actual | Tras S7 |
|------|---------------|---------|
| Módulo `embedding_pipeline/` | No existe | Crear completo |
| `POST /embeddings/ingest` | No existe | Orquestar chunk → embed → response |
| `data/budgets_sample.json` | No existe | 15 presupuestos normalizados |
| `scripts/compare.py` | No existe (hay prototipo en `ejerciciosprueba/`) | CLI + similitud coseno stdlib |
| `SANITY_CHECK.md` | No existe | 3 parejas A/B/C del material |
| Persistencia vectorial | No | S8 (pgvector) |

**Esfuerzo orientativo:** 1–2 días de implementación + ~15 min de API OpenAI (ingest sample + sanity check).

---

## Relación con Sesión 6

S6 (stress CAG conversacional) y S7 (embeddings sobre presupuestos JSON) son **caminos distintos**:

- S6 no exige presupuestos normalizados en JSON para el entregable stress.
- S7 **no modifica** `app/sessions/`, `evals/stress/`, ni el contrato de estimación.
- El material S7 asume “presupuestos históricos limpios”; si no existen en tu S6, se usa el **sample del programa** (`budgets_sample.json`).

---

## Alcance (material)

### Entra

| Ítem | Detalle |
|------|---------|
| Chunker estructural | 1 `BudgetComponent` = 1 `Chunk` |
| Embedder | `text-embedding-3-small`, batches de 100, retry rate limit |
| API | `POST …/embeddings/ingest` → chunks + `stats` |
| CLI | `scripts/compare.py` con `--text-a` / `--text-b` |
| Sanity check | `embedding_pipeline/SANITY_CHECK.md` (parejas A, B, C) |
| README | Cómo ejecutar endpoint y CLI (Docker + `uv run`) |

### No entra (S7)

| Ítem | Sesión |
|------|--------|
| Recursive / semantic / hierarchical chunking | En vivo S7 |
| Varios modelos de embedding | En vivo |
| Enriquecimiento LLM del chunk | En vivo |
| pgvector / persistencia | **S8** |
| Retrieval / hybrid search | S10+ |
| recall@k, NDCG | S11 |
| Tests automatizados obligatorios | Opcional |
| Cambios UI / backend negocio | — |

---

## Convenciones de rutas en este repo

El material escribe `POST /embeddings/ingest`. En `estimador-cag` el resto de APIs usa prefijo **`/api/v1`**.

| Opción | Ruta | Recomendación |
|--------|------|----------------|
| A (consistente repo) | `POST /api/v1/embeddings/ingest` | **Preferida** |
| B (literal material) | `POST /embeddings/ingest` | Solo si el revisor exige texto exacto |

El plan asume **opción A**; documentar ambas en README si hace falta entregar.

Módulo en disco (material dice `servicio_ia/app/`):

```
app/
├── embedding_pipeline/
│   ├── __init__.py
│   ├── schemas.py
│   ├── chunker.py
│   ├── embedder.py
│   └── router.py
scripts/
└── compare.py
data/
└── budgets_sample.json
```

---

## Esquema de datos (Pydantic)

### `Budget` / `BudgetComponent`

Alineado al JSON del material (campos mínimos):

- `budget_id`, `client_metadata` (`name`, `sector`, `country`)
- `project_summary`, `main_technology`, `year`, `total_estimated_hours`
- `components[]`: `component_id`, `name`, `description`, `tech_stack`, `estimated_hours`, `complexity`, `dependencies`

Validadores útiles: `sector` como `Literal` si el sample cierra el universo (`finance`, `ecommerce`, `healthcare`, `industrial`, …).

### `Chunk`

| Campo | Regla |
|-------|--------|
| `chunk_id` | `{budget_id}::{component_id}` |
| `text` | Plantilla con contexto padre + componente (ver abajo) |
| `metadata` | `budget_id`, `component_id`, `client_sector`, `main_technology`, `year`, `complexity`, `estimated_hours` |
| `token_count` | `tiktoken` modelo `text-embedding-3-small` |

Plantilla sugerida para `text`:

```text
[Project: {project_summary}]
[Client sector: {sector} | Year: {year} | Main tech: {main_technology}]

Component: {name}
Description: {description}
Tech stack: {tech_stack joined}
Complexity: {complexity}
Estimated hours: {estimated_hours}
```

### `EmbeddedChunk`

`Chunk` + `embedding: list[float]` (1536 dims).

### `IngestRequest` / `IngestResponse`

- Request: `budgets: list[Budget]`
- Response: `chunks: list[EmbeddedChunk]`, `stats: dict` con:
  - `total_budgets`, `total_chunks`, `total_tokens`, `estimated_cost_usd`

Coste: constante **`$0.02 / 1M tokens`** (entrada), documentada en `embedder.py`.

---

## Fases de implementación

### Fase 0 — Rama y baseline (15 min)

- [x] Crear rama `pre-session-07` desde `pre-session-06`
- [ ] `uv run pytest -q` verde
- [ ] `OPENAI_API_KEY` en `.env`
- [ ] `docker compose build` si se usa contenedor (opcional)

**Commit sugerido:** (rama ya creada; sin commit vacío)

---

### Fase 1 — Dependencias y datos (1 h)

| Tarea | Archivo |
|-------|---------|
| Añadir `tiktoken>=0.7.0` si falta | `pyproject.toml` |
| Crear `data/budgets_sample.json` con **15** presupuestos | `data/` |
| Verificar `openai` ya presente | `pyproject.toml` |

El sample debe cubrir sectores y stacks variados (material). Puede generarse a mano o adaptarse del JSON de ejemplo del material × 15 entradas.

**No añadir:** `numpy`, `scikit-learn`.

**Commit sugerido:** `chore(session-07): add budgets sample data and tiktoken dependency`

---

### Fase 2 — Schemas Pydantic (1 h)

| Tarea | Archivo |
|-------|---------|
| Modelos `Budget`, `BudgetComponent`, `Chunk`, `EmbeddedChunk` | `app/embedding_pipeline/schemas.py` |
| `IngestRequest`, `IngestResponse`, `IngestStats` (typed dict o model) | mismo |

**Tests opcionales:** validación de JSON sample contra schema.

**Commit sugerido:** `feat(session-07): add embedding pipeline pydantic schemas`

---

### Fase 3 — Chunker estructural (1.5 h)

| Tarea | Archivo |
|-------|---------|
| Clase `JSONStructuralChunker` | `app/embedding_pipeline/chunker.py` |
| Método `chunk(budgets) -> list[Chunk]` | |
| Sin overlap, sin split por tamaño fijo | |

**Commit sugerido:** `feat(session-07): add JSONStructuralChunker for budget components`

---

### Fase 4 — Embedder OpenAI (2 h)

| Tarea | Archivo |
|-------|---------|
| `OpenAIEmbedder.embed_one(text)` | `app/embedding_pipeline/embedder.py` |
| `embed_many(chunks)` con batches de 100 | |
| Retry `RateLimitError`: 1s, 2s, 4s (3 intentos) | |
| structlog por batch: chunks, tokens, latency | |
| Acumular tokens y `estimated_cost_usd` | |

Reutilizar patrón de API key / cliente desde `app/config.py` y convención structlog de S3.

**Commit sugerido:** `feat(session-07): add OpenAI batch embedder with cost stats`

---

### Fase 5 — Router FastAPI (1 h)

| Tarea | Archivo |
|-------|---------|
| Router `POST /ingest` bajo prefix `/embeddings` | `app/embedding_pipeline/router.py` |
| Registrar en `app/main.py` con prefix `/api/v1` | `main.py` |
| 200 OK, 422 Pydantic, 500 API embedding (log + mensaje genérico) | |

Flujo: `chunker.chunk` → `embedder.embed_many` → `IngestResponse`.

**Commit sugerido:** `feat(session-07): expose POST /api/v1/embeddings/ingest endpoint`

---

### Fase 6 — Script `compare.py` (1 h)

| Tarea | Archivo |
|-------|---------|
| CLI `--text-a`, `--text-b` | `scripts/compare.py` |
| Reutilizar `OpenAIEmbedder.embed_one` | |
| `cosine_similarity` en stdlib (como material y `ejerciciosprueba/embedding_pair.py`) | |
| Cargar `.env` con `python-dotenv` fuera de Docker | |

Salida ejemplo: textos + `Cosine similarity: 0.xxxx`.

**Commit sugerido:** `feat(session-07): add compare.py CLI for embedding similarity`

---

### Fase 7 — Sanity check y documentación (1 h)

| Tarea | Entregable |
|-------|------------|
| Ejecutar 3 parejas del material | `embedding_pipeline/SANITY_CHECK.md` |
| Pareja A: similitud alta (> 0.6 orientativo) | |
| Pareja B: similitud baja (< 0.4 orientativo) | |
| Pareja C: comentario sin expectativa fija | |
| Probar ingest con `data/budgets_sample.json` en `/docs` | |
| Actualizar README (endpoint, docker, uv) | `README.md` |

Comando ingest de prueba (curl):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/embeddings/ingest \
  -H "Content-Type: application/json" \
  -d @<(python3 -c "import json; print(json.dumps({'budgets': json.load(open('data/budgets_sample.json'))}))") \
  | python3 -m json.tool | head -40
```

(Ajustar si el body es lista directa o wrapper `budgets` según schema.)

**Commit sugerido:** `doc(session-07): add SANITY_CHECK and README for embedding pipeline`

---

## Criterios de aceptación (checklist entregable)

- [ ] `app/embedding_pipeline/` completo (`__init__`, `schemas`, `chunker`, `embedder`, `router`)
- [ ] `scripts/compare.py` funcional (Docker y `uv run`)
- [ ] Endpoint visible en OpenAPI `/docs`
- [ ] `embedding_pipeline/SANITY_CHECK.md` con 3 similitudes + comentario 3–5 líneas
- [ ] `data/budgets_sample.json` (15 presupuestos)
- [ ] `pyproject.toml` con `tiktoken` si aplica
- [ ] README con instrucciones de ejecución

**Tests:** no obligatorios; opcional `tests/test_chunker.py`, `tests/test_compare_cosine.py` (sin red).

---

## Matriz: material vs implementación

| Requisito material | Plan repo |
|------------------|-----------|
| Módulo `embedding_pipeline/` | `app/embedding_pipeline/` |
| `POST /embeddings/ingest` | `POST /api/v1/embeddings/ingest` |
| `scripts/compare.py` | `scripts/compare.py` |
| `data/budgets_sample.json` | `data/budgets_sample.json` |
| Rama `session-07/pre-exercise` (entrega) | Desarrollo en `pre-session-07`; tag/PR según curso |
| Sin numpy para coseno | stdlib math |
| Batch 100 | Constante `EMBED_BATCH_SIZE = 100` |

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| No hay JSON de presupuestos de S6 | Crear `budgets_sample.json` del material |
| Coste API | Ingest 15 presupuestos × N componentes ≈ bajo; log `estimated_cost_usd` |
| Rate limits | Retry exponencial en embedder |
| Confusión S6 stress vs S7 | Documentar en README; rutas separadas |
| Prototipo suelto `ejerciciosprueba/` | Migrar lógica a `scripts/compare.py`; no commitear ejercicios sueltos salvo que quieras |

---

## Orden de commits recomendado

1. `chore(session-07): add budgets sample data and tiktoken dependency`
2. `feat(session-07): add embedding pipeline pydantic schemas`
3. `feat(session-07): add JSONStructuralChunker for budget components`
4. `feat(session-07): add OpenAI batch embedder with cost stats`
5. `feat(session-07): expose POST /api/v1/embeddings/ingest endpoint`
6. `feat(session-07): add compare.py CLI for embedding similarity`
7. `doc(session-07): add SANITY_CHECK and README for embedding pipeline`

---

## Después de S7 (no implementar ahora)

| Sesión | Tema |
|--------|------|
| S8 | PostgreSQL + pgvector, persistencia |
| S10 | Hybrid search |
| S11 | Métricas retrieval formales |

---

## Referencias

- `IAENG/material/mat-sesion7.md` — pasos 1–7 y entregable
- `ejerciciosprueba/embedding_pair.py` — referencia local de coseno + `embed()`
- Artículos en material (teoría embeddings, métricas) — lectura, no código
