# Plan de implementación — Sesión 13 (LangGraph N1–N3)

Material: `mat-sesion13.md`. Complementa [`GAP-ANALISIS.md`](./GAP-ANALISIS.md).

---

## 1. Objetivo

```text
START → extract_requirements → classify_components → search_budgets
      → generate_estimate → validate_and_consolidate
           ├─(validated)──→ END
           └─(needs_review)→ END
```

---

## 2. Decisiones cerradas

| Tema | Decisión |
|------|----------|
| Rama | `session-13/pre-work` desde `session-12/pre-work` |
| Paquete | `app/graph/` (`state`, `nodes`, `build`, `routing`, `schemas`, `router`) |
| Deps | `langgraph`, `langgraph-checkpoint-postgres`, `logfire` |
| Search | Secuencial por componente (reuso tool S12 + retrieve S10) |
| Generate | `calculate_estimate` + armado de dict estimate |
| Validate | Heurística: sin matches / horas nulas / total 0 → `needs_review` |
| N3 | `add_conditional_edges` tras validate; ambos paths a `END` |
| API | `POST /api/v1/graph/estimate` |
| Checkpointer | `AsyncPostgresSaver`; URL derivada de `DATABASE_URL` |
| Observabilidad | Logfire (`LOGFIRE_TOKEN` opcional; consola local si falta) |
| Traza entrega | `evals/agent/GRAPH_TRACE.md` |
| Fuera | Send paralelo, HITL, retries |

---

## 3. Estado

```python
class Component(TypedDict):
    name: str
    category: str

class BudgetMatch(TypedDict):
    component: str
    reference_budget_id: str
    amount: float

class EstimationState(TypedDict):
    transcript: str
    requirements: list[str]
    components: list[Component]
    budget_matches: Annotated[list[BudgetMatch], operator.add]
    estimate: dict | None
    status: str | None  # validated | needs_review
    errors: Annotated[list[str], operator.add]
    estimation_id: str
```

---

## 4. Fases

### Fase 0 — Docs y rama

- [x] Rama + este plan

### Fase 1 — Nivel 1 (grafo)

| Paso | Entrega |
|------|---------|
| 1.1 | `state.py` — hecho |
| 1.2 | Nodos extract / classify / search / generate / validate — hecho |
| 1.3 | `build_graph` aristas fijas + N3 — hecho |
| 1.4 | Endpoint `POST /api/v1/graph/estimate` — hecho |

### Fase 2 — Nivel 2 (persistencia + obs)

| Paso | Entrega |
|------|---------|
| 2.1 | Checkpointer setup en lifespan — hecho |
| 2.2 | `thread_id` = `estimation_id` — hecho |
| 2.3 | `logfire.span("node: …")` en cada nodo — hecho |
| 2.4 | CLI `run_graph.py` + `GRAPH_TRACE.md` — hecho |

### Fase 3 — Nivel 3 (condicional)

| Paso | Entrega |
|------|---------|
| 3.1 | `route_after_validation` — hecho |
| 3.2 | `add_conditional_edges` → END — hecho |
| 3.3 | Tests de routing — hecho |

### Fase 4 — Docs producto

| Paso | Entrega |
|------|---------|
| 4.1 | README Modo 8 — hecho |
| 4.2 | `.env.example` Logfire — hecho |

---

## 5. API

### Request

```json
{
  "transcript": "...",
  "estimation_id": "optional-uuid",
  "k": 5,
  "search_mode": "hybrid",
  "rerank": false
}
```

### Response

```json
{
  "estimate": { "components": [], "total_hours": 0 },
  "status": "validated",
  "thread_id": "...",
  "errors": [],
  "requirements": [],
  "components": []
}
```

---

## 6. Criterios de aceptación

| # | Criterio |
|---|----------|
| A1 | Grafo end-to-end sin error |
| A2 | Reducer en `budget_matches` y/o `errors` |
| A3 | Checkpointer + thread_id |
| A4 | Traza con span por nodo documentada |
| A5 | Status vía N3 según validación |
| A6 | `/agent/estimate` y `/rag/estimate` intactos |

---

## 7. Referencias

- LangGraph: https://docs.langchain.com/oss/python/langgraph
- Persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- Logfire: https://pydantic.dev/docs/logfire/get-started/
