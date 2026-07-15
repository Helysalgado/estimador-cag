# Plan de implementación — Sesión 12 (agente + tools)

Plan para el pre-ejercicio **Introducción a agentes de IA** (`mat-sesion12.md`), sobre `session-11/pre-work`.

Complementa [`GAP-ANALISIS.md`](./GAP-ANALISIS.md).

---

## 1. Objetivo

Dada una transcripción de reunión:

1. El modelo descompone el problema en componentes.
2. Invoca `search_budgets` (una query enfocada por componente) vía retrieval S10.
3. Invoca `calculate_estimate` con referencias recuperadas.
4. Termina con una estimación estructurada y una **traza** STEP.

```text
transcript → responses.create(tools) ⟷ execute(search|calculate)
           → final estimate + ordered trace
```

---

## 2. Decisiones cerradas

| Tema | Decisión |
|------|----------|
| Rama | `session-12/pre-work` desde `session-11/pre-work` |
| Paquete | `app/agents/` |
| Idioma | Inglés en código del agente (material) |
| API | `POST /api/v1/agent/estimate` |
| Loop | Manual; max 12 iteraciones; N `function_call` por turno |
| Modelos | `AGENT_MODEL=gpt-5`, debug `AGENT_DEBUG_MODEL=gpt-5-mini`, effort `medium` |
| Traza | Consola + `evals/agent/TRACE_complex.md` |
| Fuera | `validate_estimate`, frameworks, UI |

---

## 3. Tools (contrato)

### `search_budgets`

- Params: `query` (string), `component_type` (enum: integration, migration, frontend, backend, mobile, other)
- Returns: list of `{budget_id, component_id, estimated_hours, complexity, snippet, distance}`
- Impl: embed query → `retrieve(hybrid, rerank optional)` → compact JSON (top-k, no dump completo)

### `calculate_estimate`

- Params: `components`: `[{name, reference_amounts: number[]}]`
- Returns: `{components: [{name, estimated_hours, method}], total_hours}`
- Impl: mediana de `reference_amounts` por componente; suma = total; sin LLM

Schemas Responses API: flat `{type, name, description, parameters, strict: true}`.

---

## 4. Fases

### Fase 0 — Rama y docs

- [x] Rama + este plan

### Fase 1 — Tools

| Paso | Entrega |
|------|---------|
| 1.1 | `app/agents/tools/calculate_estimate.py` — hecho |
| 1.2 | `app/agents/tools/search_budgets.py` — hecho |
| 1.3 | `app/agents/tools/schemas.py` (TOOL definitions) — hecho |
| 1.4 | Tests unitarios cálculo + dispatch — hecho |

### Fase 2 — Loop + traza

| Paso | Entrega |
|------|---------|
| 2.1 | System prompt (`prompts.py`) — hecho |
| 2.2 | `loop.py` (manual Responses loop) — hecho |
| 2.3 | `trace.py` (formato STEP) — hecho |
| 2.4 | HTTP router + CLI — hecho |

### Fase 3 — Evidencia

| Paso | Entrega |
|------|---------|
| 3.1 | `examples/agent/sample_transcript_{simple,complex}.txt` — hecho |
| 3.2 | Corrida complex → `evals/agent/TRACE_complex.md` — hecho |
| 3.3 | README Modo 7 — hecho |

---

## 5. API

### Request

```json
{
  "transcript": "...",
  "model": null,
  "max_iterations": 12,
  "search_mode": "hybrid",
  "rerank": false,
  "k": 5
}
```

### Response

```json
{
  "estimate_text": "...",
  "trace": ["STEP 1 ...", "STEP 2 ..."],
  "trace_text": "STEP 1 ...\nSTEP 2 ...",
  "iterations": 4,
  "tool_calls": {"search_budgets": 3, "calculate_estimate": 1},
  "request_id": "..."
}
```

---

## 6. Criterios de aceptación

| # | Criterio |
|---|----------|
| A1 | >1 componente y >1 `search_budgets` en complex |
| A2 | Al menos una `calculate_estimate` |
| A3 | Termina sin loop infinito (max iterations) |
| A4 | Traza con reasoning + action + observation por paso |
| A5 | `/api/v1/estimate` y `/api/v1/rag/estimate` intactos |

---

## 7. Referencias

- Material: `mat-sesion12.md`
- Retrieval: `app/embedding_pipeline/retrieval/`
- LIDR ejemplos (si disponibles): `session_12` / `calculate_estimate_skeleton.py`
