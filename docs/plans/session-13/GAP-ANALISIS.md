# Gap analysis — Sesión 13 vs `mat-sesion13.md`

Base: rama **`session-12/pre-work`**. Complementa [`PLAN-IMPLEMENTACION.md`](./PLAN-IMPLEMENTACION.md).

---

## Resumen

| Área | Estado S12 | Objetivo S13 |
|------|------------|--------------|
| Bucle agéntico manual | Sí — `app/agents/` | Sustituido *internamente* por grafo (endpoint nuevo) |
| Tools search / calculate | Sí | Reutilizadas dentro de nodos |
| LangGraph StateGraph | **No** | N1 |
| Checkpointer Postgres | **No** | N2 |
| Logfire spans por nodo | **No** | N2 |
| Arista condicional status | **No** | N3 |
| Contrato hacia “backend” con `status` | Parcial (sin status formal) | `validated` \| `needs_review` |

---

## Matriz de cumplimiento

| Nivel | Requisito | Tras S13 |
|-------|-----------|----------|
| 1 | Estado tipado + reducer `operator.add` | `EstimationState` |
| 1 | 5 nodos funciones puras / parciales | `app/graph/nodes.py` |
| 1 | Grafo cableado secuencial | `build.py` |
| 1 | Endpoint estimate + status | `POST /api/v1/graph/estimate` |
| 2 | AsyncPostgresSaver + thread_id | lifespan + invoke |
| 2 | Traza span por nodo (Logfire) | nodos + `GRAPH_TRACE.md` |
| 3 | Conditional edge post-validate | `routing.py` |
| — | Parallel Send / HITL / retries | **Fuera** (directo) |

---

## Reutilizable

| Pieza | Ruta |
|-------|------|
| `search_budgets` | `app/agents/tools/search_budgets.py` |
| `calculate_estimate` | `app/agents/tools/calculate_estimate.py` |
| Transcript complex | `examples/agent/sample_transcript_complex.txt` |
| Postgres + pgvector | `DATABASE_URL` / docker compose |
| Traza S12 (referencia) | `evals/agent/TRACE_complex.md` |

---

## Checklist revisor

- [x] Grafo cableado end-to-end (`app/graph/`)
- [x] Reducer acumulador en estado
- [x] Checkpointer + thread_id
- [x] Span por nodo + traza documentada (`evals/agent/GRAPH_TRACE.md`)
- [x] Status `validated` / `needs_review` vía arista N3
- [ ] Rama `session-13/pre-work` + PR
