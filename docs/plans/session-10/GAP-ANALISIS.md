# Gap analysis — Sesión 10 vs `mat-sesion10.md`

Contraste entre el material de clase (`mat-sesion10.md`: búsqueda híbrida + reranking + medición) y el estado del repo en la rama **`session-09/pre-work`** (base de `session-10/pre-work`).

Complementa [`PLAN-IMPLEMENTACION.md`](./PLAN-IMPLEMENTACION.md) y el [`README`](../../../README.md) del proyecto.

**Última actualización:** implementación en `session-10/pre-work` (híbrida + rerank + medición A–D ejecutada).

---

## Resumen ejecutivo

| Área | Veredicto |
|------|-----------|
| Corpus + search vectorial (S8) | **Cumple** |
| Diagnóstico arquitectónico (S9 pre-work) | **Cumple** |
| Pipeline RAG end-to-end (reformulación → generación) | **No** (fuera de S10; intentional) |
| Wrapper cross-encoder | **Cumple** — `app/embedding_pipeline/retrieval/reranker.py` (patrón LIDR) |
| Columna `tsvector` + índice GIN | **Cumple** — migración `0002` |
| Búsqueda full-text + RRF | **Cumple** |
| Reranking recall-then-rerank (toggle) | **Cumple** |
| Golden set + medición A/B/C/D | **Cumple** — ver `evals/retrieval/REPORT.md` |

**Conclusión:** S10 implementado midiendo solo recuperación. Entregable numérico en [`evals/retrieval/REPORT.md`](../../../evals/retrieval/REPORT.md).

---

## Matriz de cumplimiento (material S10 — ejercicio)

| Requisito (material) | Estado en `session-09/pre-work` | Tras S10 (objetivo) |
|----------------------|--------------------------------|---------------------|
| **Paso 1** — Migración `tsvector` generado + GIN, config `spanish` | No | Alembic `0002_...` |
| **Paso 2** — Rama léxica + fusión RRF → híbrida | No | `fulltext.py` + `fusion.py` + pipeline |
| **Paso 3** — Integrar reranker recall→rerank (toggle) | No | `reranker.py` + settings |
| **Paso 4** — Golden set 5 queries + configs A–D | No | `evals/retrieval/` + `measure_retrieval.py` |
| **Paso 5** — Conclusiones (config elegida + trade-off latencia) | No | `evals/retrieval/REPORT.md` |
| **Verificación** — `verify_reranker` carga modelo | No | `python -m app.embedding_pipeline.retrieval.verify_reranker` |
| **No entra** — query expansion / multi-index / filtros metadata | Cumple (no implementado) | mantener fuera |

---

## Lo que ya existe (reutilizable)

| Componente | Archivo | Notas |
|------------|---------|-------|
| Chunker estructural | `app/embedding_pipeline/chunker.py` | Sin cambios |
| Embedder OpenAI | `app/embedding_pipeline/embedder.py` | Vector branch del híbrido |
| Search vectorial | `app/embedding_pipeline/router.py` (`_semantic_search`) | Base a refactorizar hacia pipeline |
| Schemas search | `app/embedding_pipeline/schemas.py` | Extender `SearchRequest` |
| ORM `Document` / `Chunk` | `app/db/models.py` | Añadir `content_tsv` |
| Migración inicial | `alembic/versions/0001_initial_schema.py` | Base para `0002` |
| Corpus sample | `data/budgets_sample.json` | 15 presupuestos / ~45 chunks |
| Ingest corpus | `scripts/ingest_sample_corpus.py` | Idempotente |
| `sentence-transformers` | `pyproject.toml` extra `benchmark` | Promover a runtime (reranker) |
| Transcripciones ejemplo | `examples/transcripts/` | Útil para 1 query “larga” del golden set |
| Diagnóstico S9 | `arquitectura-actual.md` | Contexto de gaps (no sustituye medición) |

---

## Asunciones del material que no aplican tal cual

| Asunción LIDR / material | Realidad en `estimador-cag` | Adaptación |
|--------------------------|----------------------------|------------|
| Pipeline RAG previo funcionando | Solo search + diagnose; estimate no usa retrieval | Medir retrieval aislado; no construir orquestador RAG en S10 |
| `app/generation/rag/retrieval/` | No existe | `app/embedding_pipeline/retrieval/` |
| `docker compose exec ai-service …` | Servicio `ai_service` | Mismos comandos con nombre local |
| Reranker “ya construido, solo integrar” | No hay wrapper | Portar patrón del material/LIDR (CrossEncoder) y verificar carga |

---

## Brechas a cerrar en `session-10/pre-work`

### Infraestructura / deps

- Dependencia runtime de `sentence-transformers` (y transitivas PyTorch) para el servicio.
- Settings: `RERANKING_ENABLED`, `RERANKER_MODEL_NAME`, `RETRIEVAL_CANDIDATE_POOL_SIZE`, `RRF_SMOOTHING_K`.
- Imagen Docker con capacidad de descargar/cargar el modelo (primera vez lenta; disco/memoria).

### Capa de datos

- Columna generada `chunks.content_tsv` con `to_tsvector('spanish', content)`.
- Índice GIN `ix_chunks_content_tsv`.
- Actualizar ORM para reflejar la columna (solo lectura desde app).

### Retrieval

- Full-text: `websearch_to_tsquery('spanish', …)` + `ts_rank` + `@@`.
- RRF puro sobre listas de `chunk_id` (`k=60`).
- Pipeline: `vector | hybrid` × `rerank on|off`.
- Reranker: recall pool (default 50) → top-k (default 5); `asyncio.to_thread` para no bloquear el event loop.

### API

- Extender `POST /search` (y alias) sin romper el contrato actual: defaults = comportamiento S8 (vectorial, sin rerank, `k=5`).

### Medición / entregable

- `evals/retrieval/golden_set.json` (criterio escrito + 5 queries).
- `scripts/measure_retrieval.py` (precision@5 a nivel `budget_id`, latencia mediana en caliente).
- `evals/retrieval/REPORT.md` con tabla A–D y párrafo de conclusiones.
- PR `session-10/pre-work` + mail con enlace y tabla.

---

## Fuera de alcance (correctamente omitido en S10 pre-work)

Expansión / descomposición de queries, routing multi-índice, filtrado por `metadata`, índices HNSW, generación de estimación grounded en chunks, cambios a Streamlit o a `/estimate`.

---

## Checklist para el revisor (objetivo S10)

- [x] Migración Alembic `content_tsv` + GIN (`spanish`)
- [x] Búsqueda híbrida (vector + full-text + RRF) invocable
- [x] Reranker integrado, toggleable, recall→rerank
- [x] `verify_reranker` OK (local; Docker image con torch es pesada)
- [x] Golden set 5 queries + harness A–D
- [x] Tabla precision@5 + latencia + conclusiones
- [ ] Rama **`session-10/pre-work`** pusheada + PR accesible (pendiente commit/push)

---

## Referencias

- Material: `mat-sesion10.md` (ejercicio + artículos 1–3; 4–6 solo lectura post-entrega)
- Plan S8: [`../session-08/PLAN-IMPLEMENTACION.md`](../session-08/PLAN-IMPLEMENTACION.md)
- Diagnóstico S9: [`../../../arquitectura-actual.md`](../../../arquitectura-actual.md)
- Pipeline actual: [`app/embedding_pipeline/`](../../../app/embedding_pipeline/)
- Repo LIDR referencia: rama `session_10` (`estimator/app/generation/rag/retrieval/`)
