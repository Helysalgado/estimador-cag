# Retrieval measurement report — Session 10

**Fecha:** 2026-07-14  
**Corpus:** `data/budgets_sample.json` (15 presupuestos, ~45 chunks)  
**Golden set:** [`golden_set.json`](./golden_set.json)  
**Harness:** `uv run python scripts/measure_retrieval.py --config all`  
**Entorno:** API local (`uvicorn`) + Postgres Docker; modelo `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`  
**Métrica:** precision@5 a nivel `budget_id` de cada chunk del top-5 (warm-up descartado; mediana de 3 runs)

## Tabla A–D

| Config | Búsqueda | Reranking | precision@5 (media) | latencia mediana (ms) |
|--------|----------|-----------|---------------------|------------------------|
| **A** | Vectorial | No | **0.72** | 347 |
| **B** | Híbrida | No | **0.72** | 337 |
| **C** | Vectorial | Sí | 0.64 | 453 |
| **D** | Híbrida | Sí | 0.64 | 441 |

Detalle por query (`last_run.json`):

| Query | A | B | C | D |
|-------|---|---|---|---|
| q01 ecommerce catalog/cart/admin | 0.80 | 0.80 | 0.80 | 0.80 |
| q02 Stripe mobile payments | 0.40 | 0.40 | 0.40 | 0.40 |
| q03 Stripe webhooks (ES) | 0.40 | 0.40 | 0.40 | 0.40 |
| q04 HIPAA patient portal | 1.00 | 1.00 | 0.60 | 0.60 |
| q05 messy multi-topic shop | 1.00 | 1.00 | 1.00 | 1.00 |

## Conclusiones

En este corpus pequeño y ya bien diferenciado, **la configuración que usaría es B (híbrida, sin rerank)** — o A si se prioriza simplicidad operativa. A y B empatan en precision@5 media (0.72); B añade la rama léxica con RRF a coste de latencia comparable (incluso ligeramente menor en esta corrida), y deja listo el rescate de términos exactos (Stripe, HIPAA, siglas) cuando el vocabulario léxico discrimine más que en este golden set.

**El reranking no justifica aquí su latencia:** C/D bajan la media a 0.64 y añaden ~100 ms. Con k=5 y muchos hits duplicando el mismo `budget_id` relevante, el baseline vectorial ya “llena” el top-5 de budgets útiles; el cross-encoder reordena chunks y en q04 empujó wallets financieros (`BUD-2024-009`) por delante de FHIR. Frente a una estimación LLM de varios segundos, +100 ms sería aceptable si la precisión subiera, pero en estos números **no compensa**. Vale la pena re-medir con un golden set más grande o precision sobre budgets únicos cuando el histórico crezca.

## Cómo reproducir

```bash
docker compose up -d postgres
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
uv run python scripts/ingest_sample_corpus.py
uv run python -m app.embedding_pipeline.retrieval.verify_reranker
uv run python scripts/measure_retrieval.py --config all
```

Nota: la imagen Docker del `ai_service` con `sentence-transformers`/`torch` es muy pesada (pull de CUDA). Para desarrollo, API local + Postgres en Docker es el camino práctico.
