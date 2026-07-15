# Plan de implementación — Sesión 11 (generación grounded + RAGAS)

Pre-ejercicio: **citación verificable por línea** + evaluación **RAGAS**, reutilizando el retrieval S10. Sin content augmentation ni el pipeline LIDR completo de expansión/routing.

| Documento | Contenido |
|-----------|-----------|
| **[PLAN-IMPLEMENTACION.md](./PLAN-IMPLEMENTACION.md)** | Plan detallado por fases (material `mat-sesion11.md`) |
| **[GAP-ANALISIS.md](./GAP-ANALISIS.md)** | Estado actual vs material y brechas pendientes |
| Material de curso | `mat-sesion11.md` (ejercicio; artículos = lectura) |
| Punto de partida | Rama **`session-10/pre-work`** (híbrida + rerank + golden set) |

## Rama de trabajo

```bash
git checkout session-10/pre-work
git checkout -b session-11/pre-work
```

Convención del material de entrega: **`session-11/pre-work`** (PR + mail a lia@lidr.co).

## Objetivo en una frase

Query → retrieve S10 → ensamblar contexto con `chunk_id` → estimación estructurada con citas por línea → `verify_citations` → eval RAGAS (4 métricas × 5 queries) + nota breve.

## Decisiones de adaptación (acordadas)

| Tema | Decisión |
|------|----------|
| Rama base | `session-11/pre-work` desde `session-10/pre-work` |
| Paquete | `app/embedding_pipeline/generation/` |
| API | Nuevo `POST /api/v1/rag/estimate` (no romper `/api/v1/estimate`) |
| Structured output | Responses API + Pydantic (`SourceReference`, `EstimateLineItem`, `Estimate`) |
| Retrieval default | Híbrida, sin rerank (config B S10), `k=5` |
| Eval | Extender golden set + `scripts/eval_ragas.py` → `evals/retrieval/RAGAS_REPORT.md` |

## Prerrequisitos antes de implementar

```bash
docker compose up -d postgres ai_service
docker compose exec ai_service uv run alembic upgrade head
docker compose exec ai_service uv run python scripts/ingest_sample_corpus.py
curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Stripe checkout ecommerce", "k": 5, "search_mode": "hybrid", "rerank": false}' | jq
```

Tras implementar el generador RAG:

```bash
curl -s -X POST http://localhost:8000/api/v1/rag/estimate \
  -H "Content-Type: application/json" \
  -d '{"query": "Pasarela Stripe ecommerce — estimación frontend y backend"}' | jq

uv run python scripts/eval_ragas.py
```

## Fuera de alcance S11 (pre-work)

Content augmentation, detector de alucinaciones ACB completo, query expansion / routing / filtros metadata, cambios a Streamlit o al estimate texto libre S4. (Artículos de clase: lectura / sesión en vivo.)

## Checklist de entrega

- [x] Schema + prompt + `verify_citations` en la rama
- [x] Endpoint `POST /api/v1/rag/estimate`
- [x] Test de citación colgante
- [x] Golden set con `ground_truth` (5 queries)
- [x] Tabla RAGAS + promedio + nota en `evals/retrieval/RAGAS_REPORT.md`
- [ ] PR `session-11/pre-work` accesible
- [ ] Mail a lia@lidr.co con enlace al PR + tabla
