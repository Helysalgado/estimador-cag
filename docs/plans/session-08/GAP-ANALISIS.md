# Gap analysis — Sesión 08 vs `sesion8.md`

Contraste entre el material de clase (`sesion8.md`) y el estado del repo en la rama **`pre-session-07`**.

Complementa [`PLAN-IMPLEMENTACION.md`](./PLAN-IMPLEMENTACION.md) y el [`README`](../../../README.md) del proyecto.

**Última actualización:** implementación en rama **`pre-session-08`** (código listo; `output_examples.txt` requiere Docker + API key en ejecución).

---

## Resumen ejecutivo

| Área | Veredicto |
|------|-----------|
| Postgres + pgvector en compose | **Cumple** |
| Alembic + schema `documents` / `chunks` | **Cumple** |
| Ingest persistido (transacción única) | **Cumple** |
| `POST /search` con `cosine_distance` | **Cumple** |
| `scripts/query_examples.py` | **Cumple** |
| `scripts/ingest_sample_corpus.py` | **Cumple** (auxiliar) |
| `output_examples.txt` | **Cumple** — generado contra corpus de 15 presupuestos |
| README justificaciones schema | **Cumple** — Modo 4 |
| Pipeline S7 (chunker, embedder, sample) | **Cumple** — reutilizado |
| Servicio Docker `ai_service` | **Cumple** |
| Tests automatizados ingest + search | **Cumple** — 113 tests verdes |

**Conclusión:** S7 es el punto de partida correcto. S8 añade capa de persistencia y retrieval; no requiere reescribir chunker ni embedder.

---

## Matriz de cumplimiento (material S8)

| Requisito (material) | Estado en `pre-session-07` | Tras S8 |
|----------------------|----------------------------|---------|
| **Paso 1** — Postgres `pgvector/pgvector:pg16` | No | `docker-compose.yml` |
| **Paso 1** — deps sqlalchemy, asyncpg, pgvector, alembic | No | `pyproject.toml` |
| **Paso 1** — `DATABASE_URL` en servicio IA | No | `ai_service` + `app/config.py` |
| **Paso 2** — Alembic init `-t async` | No | `alembic/` |
| **Paso 2** — registro tipo `vector` en `env.py` | No | `alembic/env.py` |
| **Paso 3** — extensión `vector` + tablas + índices no-vectoriales | No | `0001_initial_schema.py` |
| **Paso 3** — `vector(1536)`, embedding nullable | No | migración |
| **Paso 4** — ingest un documento por request | No | contrato nuevo |
| **Paso 4** — 409 si `source_path` duplicado | No | UNIQUE + handler |
| **Paso 4** — transacción única document + chunks | No | async session |
| **Paso 5** — `POST /search` top-k coseno | No | nuevo router |
| **Paso 6** — `query_examples.py` (5 queries) | No | `scripts/query_examples.py` |
| **Entregable** — `output_examples.txt` | No | raíz del repo |
| **Entregable** — README justificaciones (a–d) | No | Modo 4 |
| **No entra** — índice vectorial | Cumple | mantener sin índice |
| **No entra** — filtros metadata / hybrid / tuning | Cumple | no implementar |

---

## Lo que ya existe (reutilizable de S7)

| Componente | Archivo | Notas |
|------------|---------|-------|
| Chunker estructural | `app/embedding_pipeline/chunker.py` | 1 componente = 1 chunk |
| Embedder OpenAI | `app/embedding_pipeline/embedder.py` | `text-embedding-3-small`, batch 100 |
| Schemas Budget/Chunk | `app/embedding_pipeline/schemas.py` | `content` del ingest = `Budget` |
| Sample corpus | `data/budgets_sample.json` | 15 presupuestos |
| Similitud coseno | `app/embedding_pipeline/similarity.py` | útil para tests; search usa SQL |
| Tests chunker/embedder | `tests/test_*.py` | sin cambios esperados |

---

## Brechas a cerrar en `pre-session-08`

### Infraestructura

- Añadir servicio `postgres` y renombrar `api` → `ai_service`.
- Añadir `DATABASE_URL` a settings y compose.
- Copiar `alembic/` en `Dockerfile`.

### Capa de datos

- `app/db/base.py`, `models.py`, `session.py`.
- Migración Alembic con UNIQUE en `documents.source_path`.

### API (breaking change ingest)

| S7 (actual) | S8 (objetivo) |
|-------------|---------------|
| `POST …/ingest` con `{ budgets: [...] }` | `{ source_path, document_type, content }` |
| Response: `chunks[]` + `stats` | Response: `document_id`, `chunks_created`, … |
| Sin persistencia | Postgres en transacción única |

### Scripts y entregables

- `scripts/ingest_sample_corpus.py` — poblar DB desde `budgets_sample.json`.
- `scripts/query_examples.py` — 5 queries representativas.
- `output_examples.txt` — salida capturada del script.

---

## Mapeo S7 → columnas DB (decisión acordada)

| Origen S7 | Columna DB |
|-----------|------------|
| `Chunk.text` | `chunks.content` |
| constante | `chunks.chunk_type` = `"budget_component"` |
| `ChunkMetadata` (Pydantic) | `chunks.metadata` (JSONB) |
| `Budget.budget_id`, sector, year, … | `documents.metadata` (JSONB) |
| embedding 1536 dims | `chunks.embedding` `vector(1536)` |

---

## Fuera de alcance (correctamente omitido en S8)

Índices HNSW/IVFFlat, `WHERE chunk_type = …`, `metadata->>'sector'`, full-text + vector, tuning Postgres. Se cubren en sesión en vivo.

---

## Checklist para el revisor (objetivo S8)

- [x] `docker-compose.yml` con `postgres` + `ai_service`
- [x] Migración Alembic (extensión + tablas + índices no-vectoriales)
- [x] `POST /embeddings/ingest` y `/api/v1/embeddings/ingest` persistiendo
- [x] `POST /search` y `/api/v1/search` funcional
- [x] `scripts/query_examples.py`
- [x] `output_examples.txt`
- [x] README Modo 4 (justificaciones schema)
- [x] Rama **`pre-session-08`**

---

## Referencias

- Material: `sesion8.md`
- Plan S7: [`../session-07/PLAN-IMPLEMENTACION.md`](../session-07/PLAN-IMPLEMENTACION.md)
- Pipeline actual: [`app/embedding_pipeline/`](../../../app/embedding_pipeline/)
