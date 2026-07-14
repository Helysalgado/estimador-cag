# Plan de implementación — Sesión 10 (híbrida + reranking + medición)

Pre-ejercicio: **mejorar y medir la recuperación** con búsqueda híbrida (full-text + vector + RRF) y reranking cross-encoder, sin construir generación RAG ni técnicas de los artículos 4–6.

| Documento | Contenido |
|-----------|-----------|
| **[PLAN-IMPLEMENTACION.md](./PLAN-IMPLEMENTACION.md)** | Plan detallado por fases (material `mat-sesion10.md`) |
| **[GAP-ANALISIS.md](./GAP-ANALISIS.md)** | Estado actual vs material y brechas pendientes |
| Material de curso | `mat-sesion10.md` (ejercicio + artículos 1–3) |
| Punto de partida | Rama **`session-09/pre-work`** (S8 search + diagnóstico S9) |

## Rama de trabajo

```bash
git checkout session-09/pre-work
git checkout -b session-10/pre-work
```

Convención del material de entrega: **`session-10/pre-work`** (PR + mail a lia@lidr.co).

## Objetivo en una frase

Query → (vector **o** híbrida RRF) → pool amplio → (opcional) rerank → top-5 medible con golden set → tabla **A/B/C/D** (precision@5 + latencia) + conclusiones.

## Decisiones de adaptación (acordadas)

| Tema | Decisión |
|------|----------|
| Rama base | `session-10/pre-work` desde `session-09/pre-work` |
| Alcance | Solo **retrieval** (no orquestador estimate↔search) |
| Paquete | `app/embedding_pipeline/retrieval/` (adaptación; no `app/generation/rag/`) |
| Full-text | `to_tsvector('spanish', content)` + GIN |
| RRF | `k = 60` |
| API | Extender `SearchRequest`: `search_mode`, `rerank`, `candidate_pool_size` |
| Medición | `evals/retrieval/golden_set.json` + `scripts/measure_retrieval.py` |
| Informe | `evals/retrieval/REPORT.md` |

## Configuraciones del entregable

| Config | Búsqueda | Reranking |
|--------|----------|-----------|
| A | Vectorial | No |
| B | Híbrida | No |
| C | Vectorial | Sí |
| D | Híbrida | Sí |

## Prerrequisitos antes de implementar

```bash
docker compose up -d postgres ai_service
docker compose exec ai_service uv run alembic upgrade head
docker compose exec ai_service uv run python scripts/ingest_sample_corpus.py
curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Stripe checkout ecommerce", "k": 3}' | jq
```

Tras integrar el reranker:

```bash
docker compose exec ai_service uv run python -m app.embedding_pipeline.retrieval.verify_reranker
```

## Fuera de alcance S10 (pre-work)

Expansión / descomposición de consultas, routing multi-índice, filtrado por metadata, Elasticsearch, cambios a Streamlit o `/estimate`. (Artículos 4–6: lectura post-entrega / sesión en vivo.)

## Checklist de entrega

- [ ] Código híbrida + rerank en la rama
- [ ] Golden set 5 queries anotadas
- [ ] Tabla A–D (precision@5 + latencia mediana)
- [ ] Conclusiones en `evals/retrieval/REPORT.md`
- [ ] PR `session-10/pre-work` accesible
- [ ] Mail a lia@lidr.co con enlace al PR + tabla
