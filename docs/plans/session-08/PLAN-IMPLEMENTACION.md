# Plan de implementación — Sesión 8 (pgvector + búsqueda semántica)

Contraste entre:

- **Material:** `sesion8.md` (Migración a pgvector + endpoint de búsqueda)
- **Repo:** `estimador-cag`, rama **`pre-session-08`** (desde `pre-session-07`)
- **Estado previo:** S7 completo — chunker, embedder, ingest en memoria, `data/budgets_sample.json`

---

## Resumen ejecutivo

| Capa | Estado en `pre-session-07` | Tras S8 |
|------|----------------------------|---------|
| PostgreSQL + pgvector | No | Servicio `postgres` en compose |
| Alembic + schema | No | `documents` + `chunks` |
| `POST …/embeddings/ingest` | Devuelve vectores JSON | Persiste en DB; response con IDs |
| `POST /search` | No | Top-k por `cosine_distance` |
| `scripts/compare.py` | S7 CLI par-a-par | Se mantiene; S8 añade `query_examples.py` |
| `output_examples.txt` | No | Salida de 5 queries de búsqueda |

**Esfuerzo orientativo:** 1–2 días + ~15–20 min API OpenAI (ingestar 15 presupuestos + ejecutar queries).

---

## Decisiones de adaptación (cerradas)

| Tema | Decisión |
|------|----------|
| Rama | `pre-session-08` desde `pre-session-07` |
| Servicio Docker | Renombrar `api` → **`ai_service`** |
| Rutas HTTP | Canónicas `/api/v1/...`; alias `/embeddings/ingest`, `/search` |
| `query_examples.py` | `scripts/query_examples.py` |
| Esquema | Columnas exactas del material (opción A) |
| `source_path` | UNIQUE en DB + check en handler (409) |
| Índice vectorial | No (deliberado) |

---

## Relación con Sesión 7

S8 **no reescribe** el chunker ni el embedder. Refactoriza el router de ingest y añade:

- Capa `app/db/` (SQLAlchemy async + pgvector)
- Endpoint de búsqueda
- Scripts de corpus y ejemplos

S7 `compare.py` y `SANITY_CHECK.md` permanecen válidos como referencia de similitud fuera de DB.

---

## Alcance (material)

### Entra

| Ítem | Detalle |
|------|---------|
| Postgres + pgvector | Imagen `pgvector/pgvector:pg16` |
| Deps | `sqlalchemy`, `asyncpg`, `pgvector`, `alembic` |
| Alembic async | `alembic init -t async`; tipo `vector` en `env.py` |
| Schema | `documents`, `chunks`, extensión `vector`, índices no-vectoriales |
| Ingest | Un presupuesto por request; transacción única; 409 duplicado |
| Search | `cosine_distance`, mismo modelo que ingesta |
| CLI | `scripts/query_examples.py` — 5 queries |
| Entregable | `output_examples.txt` |
| README | Modo 4, máx. 1 página con justificaciones (a–d) |

### No entra (S8 — sesión en vivo)

| Ítem | Motivo |
|------|--------|
| Índices HNSW / IVFFlat | Baseline sequential scan |
| Filtros `WHERE chunk_type` / `metadata->>` | Se exploran en directo |
| Búsqueda híbrida full-text + vector | Sesión en vivo |
| Tuning Postgres | Defaults en el ejercicio |

---

## Convenciones de rutas

| Material | Repo (canónico) | Alias material |
|----------|-----------------|----------------|
| `POST /embeddings/ingest` | `POST /api/v1/embeddings/ingest` | `POST /embeddings/ingest` |
| `POST /search` | `POST /api/v1/search` | `POST /search` |

Comandos Docker usan servicio **`ai_service`** (renombrado desde `api`).

---

## Esquema de base de datos

### Tabla `documents`

| Columna | Tipo | Notas |
|---------|------|-------|
| `id` | BigInteger PK | |
| `source_path` | Text NOT NULL **UNIQUE** | 409 si duplicado |
| `document_type` | String(50) | p. ej. `historical_budget` |
| `ingested_at` | DateTime(tz) | `server_default=now()` |
| `metadata` | JSONB | `budget_id`, `sector`, `year`, … |

### Tabla `chunks`

| Columna | Tipo | Notas |
|---------|------|-------|
| `id` | BigInteger PK | |
| `document_id` | BigInteger FK CASCADE | |
| `chunk_type` | String(50) | `"budget_component"` |
| `content` | Text | texto del chunk (S7 `Chunk.text`) |
| `embedding` | `vector(1536)` nullable | `text-embedding-3-small` |
| `metadata` | JSONB | `ChunkMetadata` serializado |
| `created_at` | DateTime(tz) | `server_default=now()` |

### Índices (no vectoriales)

- `ix_documents_source_path` en `source_path`
- `ix_chunks_document_id`, `ix_chunks_chunk_type`
- `ix_chunks_metadata_gin` (GIN sobre `chunks.metadata`)

**Sin índice en `embedding`** — baseline para medir impacto en vivo.

### Justificaciones (para README)

1. **Dos tablas:** integridad referencial; `ON DELETE CASCADE` elimina chunks al borrar documento.
2. **JSONB metadata:** campos estables en columnas tipadas; metadata variable/enriquecible sin migraciones.
3. **`vector(1536)`:** dimensión fija de `text-embedding-3-small`; re-embed implica re-ingestar todo.
4. **`embedding` nullable:** puerta a ingesta asíncrona (sesiones posteriores).
5. **`cosine_distance`:** embeddings OpenAI normalizados; alinea con HNSW `vector_cosine_ops` en vivo.
6. **Sin índice vectorial:** sequential scan como baseline.

---

## Contratos API

### Ingest (S8 — reemplaza contrato S7)

**Request:**

```json
{
  "source_path": "data/budgets/BUD-2024-014.json",
  "document_type": "historical_budget",
  "content": { }
}
```

`content` = un objeto `Budget` (mismo schema Pydantic S7).

**Response 200:**

```json
{
  "document_id": 42,
  "chunks_created": 3,
  "embedding_dimension": 1536,
  "ingestion_time_ms": 1240
}
```

**Response 409:**

```json
{
  "detail": "Document already ingested",
  "document_id": 42
}
```

### Search

**Request:**

```json
{
  "query": "REST API with OAuth authentication for fintech sector",
  "k": 5
}
```

**Response:**

```json
{
  "query": "...",
  "k": 5,
  "search_time_ms": 87,
  "results": [
    {
      "chunk_id": 156,
      "document_id": 12,
      "chunk_type": "budget_component",
      "content": "...",
      "distance": 0.231,
      "metadata": { }
    }
  ]
}
```

---

## Fases de implementación

Cada fase incluye un **checkpoint** — no avanzar si falla la verificación.

---

### Fase 0 — Rama (15 min)

```bash
git checkout pre-session-07
git checkout -b pre-session-08
uv run pytest -q   # baseline verde
```

**Checkpoint:** tests S7 pasan en la nueva rama.

**Commit sugerido:** (rama creada; sin commit vacío)

---

### Fase 1 — Postgres, deps y renombrar servicio (1–2 h)

| Tarea | Archivo |
|-------|---------|
| Añadir `sqlalchemy`, `asyncpg`, `pgvector`, `alembic` | `pyproject.toml` + `uv lock` |
| Servicio `postgres` + volumen `postgres_data` | `docker-compose.yml` |
| Renombrar `api` → `ai_service` | `docker-compose.yml` |
| `depends_on: postgres` (healthy) + `DATABASE_URL` | `docker-compose.yml` |
| Campo `DATABASE_URL` | `app/config.py` |
| Actualizar comandos `compose … ai_service` | `README.md`, docs S7 si aplica |

**Verificación bloqueante (material):**

```bash
docker compose up postgres
docker compose exec postgres psql -U estimator -d estimator -c "SELECT version();"
```

**Checkpoint:** Postgres responde. Si falla, no continuar.

**Commit sugerido:** `chore(session-08): add postgres pgvector and rename api to ai_service`

---

### Fase 2 — Alembic async (1 h)

```bash
docker compose run --rm ai_service alembic init -t async alembic
```

| Tarea | Archivo |
|-------|---------|
| URL desde `DATABASE_URL` (env, no hardcode) | `alembic.ini`, `alembic/env.py` |
| Registrar `vector` en dialecto | `alembic/env.py` → `do_run_migrations` |
| `target_metadata` desde modelos ORM | `alembic/env.py` |
| Copiar `alembic/` al contenedor | `Dockerfile` |

Snippet obligatorio en `env.py`:

```python
import pgvector.sqlalchemy

def do_run_migrations(connection):
    connection.dialect.ischema_names["vector"] = pgvector.sqlalchemy.Vector
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
```

**Checkpoint:** `docker compose run --rm ai_service alembic check` sin drift en columnas vector.

**Commit sugerido:** `chore(session-08): init alembic async with pgvector dialect`

---

### Fase 3 — Schema + modelos ORM (2 h)

| Tarea | Archivo |
|-------|---------|
| `DeclarativeBase` | `app/db/base.py` |
| Modelos `Document`, `Chunk` | `app/db/models.py` |
| Engine async + `get_db_session` | `app/db/session.py` |
| Migración `0001_initial_schema.py` | `alembic/versions/` |

Migración según material + **UNIQUE** en `documents.source_path`.

```bash
docker compose run --rm ai_service alembic upgrade head
```

**Checkpoint:** tablas `documents` y `chunks` existen; extensión `vector` activa.

**Commit sugerido:** `feat(session-08): add documents/chunks schema and ORM models`

---

### Fase 4 — Refactor ingest (2–3 h)

| Tarea | Archivo |
|-------|---------|
| `PersistIngestRequest`, `PersistIngestResponse` | `app/embedding_pipeline/schemas.py` |
| Handler `async` con transacción única | `app/embedding_pipeline/router.py` |
| 409 por `source_path` duplicado | mismo |
| Lifespan: dispose engine (opcional) | `app/main.py` |

**Flujo:**

1. `SELECT` por `source_path` → 409
2. `INSERT` document (+ `documents.metadata` desde budget)
3. `chunker.chunk([content])`
4. `embedder.embed_many(chunks)` — batch único OpenAI
5. `session.add_all` filas `chunks` (`content`, `chunk_type`, `metadata`, `embedding`)
6. `commit` (rollback si falla embedder)

**Script auxiliar:** `scripts/ingest_sample_corpus.py`

- Lee `data/budgets_sample.json` (15 presupuestos)
- `source_path`: `data/budgets/{budget_id}.json`
- Idempotente: ignora 409 en re-ejecución

**Prueba manual:**

```bash
docker compose up -d
docker compose run --rm ai_service alembic upgrade head
# ingest 1 presupuesto vía curl o script
```

**Checkpoint:** un ingest crea 1 document + N chunks; re-ingest mismo `source_path` → 409.

**Commit sugerido:** `feat(session-08): persist ingest in postgres with duplicate guard`

---

### Fase 5 — Endpoint search (1–2 h)

| Tarea | Archivo |
|-------|---------|
| `SearchRequest`, `SearchResponse` | `schemas.py` |
| Router `POST /search` | `router.py` o `search_router.py` |
| Query `cosine_distance` + `limit(k)` | mismo |
| Registrar en `main.py` | `app/main.py` |
| Alias `/search` | material router |

```python
stmt = (
    select(
        Chunk.id,
        Chunk.document_id,
        Chunk.chunk_type,
        Chunk.content,
        Chunk.metadata,
        Chunk.embedding.cosine_distance(query_vector).label("distance"),
    )
    .order_by(Chunk.embedding.cosine_distance(query_vector))
    .limit(k)
)
```

**Sin** filtros metadata ni índice vectorial.

**Checkpoint:** tras ingestar corpus, `POST /api/v1/search` devuelve top-k con distancias.

**Commit sugerido:** `feat(session-08): add semantic search endpoint with cosine distance`

---

### Fase 6 — query_examples + output (1 h)

| Tarea | Archivo |
|-------|---------|
| 5 queries del material | `scripts/query_examples.py` |
| Formato: chunk_id, distance (4 dec.), chunk_type, ~120 chars | mismo |
| Capturar salida | `output_examples.txt` |

**Queries (material):**

1. Sanity — `"REST API development with JWT authentication for financial sector"`
2. Reformulación — `"secure backend service with token-based access control for banking applications"`
3. Dominio distinto — `"mobile application for restaurant reservations"`
4. Ambigua — `"integration with external system"`
5. Específica — `"migration from monolith to microservices architecture using Kubernetes"`

**Pipeline completo:**

```bash
docker compose up -d
docker compose run --rm ai_service alembic upgrade head
docker compose run --rm ai_service python scripts/ingest_sample_corpus.py
docker compose run --rm ai_service python scripts/query_examples.py | tee output_examples.txt
```

**Checkpoint:** `output_examples.txt` con resultados legibles de 5 queries × top-5.

**Commit sugerido:** `feat(session-08): add query_examples script and sample output`

---

### Fase 7 — Tests y README (1–2 h)

| Tarea | Archivo |
|-------|---------|
| Actualizar tests ingest (mock async session) | `tests/test_embeddings_router.py` |
| Tests search (mock embedder + DB) | `tests/test_search_router.py` |
| Modo 4 — pgvector | `README.md` |
| Enlace en índice docs | `docs/README.md` |

Tests chunker, embedder, similarity: **sin cambios**.

**Commit sugerido:** `test(session-08): update ingest tests and add search tests` + `doc(session-08): README modo pgvector`

---

## Criterios de aceptación (checklist entregable)

- [ ] `docker-compose.yml` con `postgres` y `ai_service`
- [ ] Migración Alembic (extensión + tablas + índices no-vectoriales)
- [ ] `POST /embeddings/ingest` persistiendo + 409 duplicado
- [ ] `POST /search` funcional
- [ ] `scripts/query_examples.py`
- [ ] `output_examples.txt`
- [ ] README con justificaciones (a) dos tablas, (b) JSONB, (c) cosine, (d) sin índice vectorial
- [ ] Rama `pre-session-08`

---

## Matriz: material vs implementación

| Requisito material | Plan repo |
|--------------------|-----------|
| Servicio `ai_service` | Renombrar desde `api` |
| `POST /embeddings/ingest` | + `/api/v1/embeddings/ingest` |
| `POST /search` | + `/api/v1/search` |
| `python query_examples.py` | `scripts/query_examples.py` |
| `compare.py` S7 | Se mantiene (no es entregable S8) |
| Corpus ejemplo | `data/budgets_sample.json` |
| Rama entrega | **`pre-session-08`** |

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Breaking change ingest S7 → S8 | Actualizar tests y README; documentar migración |
| Coste OpenAI (15 ingests) | Script idempotente; log en ingest |
| `embedder` sync en handler async | `asyncio.to_thread` o llamada sync dentro de async (aceptable S8) |
| Alembic no detecta `vector` | `ischema_names["vector"]` en `env.py` |
| Puerto 5432 ocupado en host | Documentar en README o variable de puerto |

---

## Orden de commits recomendado

1. `chore(session-08): add postgres pgvector and rename api to ai_service`
2. `chore(session-08): init alembic async with pgvector dialect`
3. `feat(session-08): add documents/chunks schema and ORM models`
4. `feat(session-08): persist ingest in postgres with duplicate guard`
5. `feat(session-08): add semantic search endpoint with cosine distance`
6. `feat(session-08): add query_examples script and sample output`
7. `test(session-08): update ingest tests and add search tests`
8. `doc(session-08): README modo pgvector and session-08 plan`

---

## Después de S8 (no implementar ahora)

| Sesión | Tema |
|--------|------|
| En vivo S8 | Índices HNSW, filtros metadata, hybrid search, tuning |
| S10+ | Retrieval avanzado |
| S11 | recall@k, NDCG |

---

## Referencias

- Material: `sesion8.md`
- Plan S7: [`../session-07/PLAN-IMPLEMENTACION.md`](../session-07/PLAN-IMPLEMENTACION.md)
- Gap S7: [`../session-07/GAP-ANALISIS.md`](../session-07/GAP-ANALISIS.md)
