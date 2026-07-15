# Explicación de la entrega — Sesión 13 (orquestación LangGraph)

Documento orientado al profesor: qué se hizo, por qué, y dónde verificarlo.

**Rama:** `session-13/pre-work`  
**Material de referencia:** `mat-sesion13.md` (Niveles 1–3)  
**Punto de partida:** agente de Sesión 12 (`app/agents/`)

---

## 1. Qué problema resuelve esta sesión

En Sesión 12 la estimación era un **bucle agéntico** (el LLM decidía cuándo llamar tools). En Sesión 13 se reexpresa el mismo flujo de negocio como un **grafo explícito** con LangGraph:

- Cada paso del proceso es un **nodo** con responsabilidad clara.
- El estado compartido viaja tipado entre nodos.
- La orquestación queda **cableada en código** (no depende del modelo para el orden de pasos).
- Se añade persistencia (checkpointer) y observabilidad (spans) como en un flujo de producción.

Contrato de salida hacia “backend”: estimación + `status` ∈ {`validated`, `needs_review`}.

---

## 2. Flujo implementado

```text
START
  → extract_requirements
  → classify_components
  → search_budgets
  → generate_estimate
  → validate_and_consolidate
  → [condicional] validated | needs_review
END
```

| Nodo | Rol |
|------|-----|
| `extract_requirements` | Del transcript obtiene lista de requisitos (LLM). |
| `classify_components` | Convierte requisitos en componentes tipados (`name`, `category`). |
| `search_budgets` | Por cada componente busca presupuestos de referencia (reutiliza tool S12 / retrieval S10). |
| `generate_estimate` | Consolida matches con `calculate_estimate` (mediana / cálculo determinista). |
| `validate_and_consolidate` | Heurística de calidad → asigna `status`. |

Arista condicional (Nivel 3): tras validar se enruta por `status`; ambas ramas terminan en `END` (el status queda en el estado para el cliente).

---

## 3. Cumplimiento por niveles del material

### Nivel 1 — Grafo secuencial + estado tipado

- Estado: `EstimationState` en [`app/graph/state.py`](../../../app/graph/state.py).
- Reducers con `operator.add` en `budget_matches` y `errors` (acumuladores; el nodo de búsqueda aporta parciales sin pisar lo anterior).
- Cinco nodos en [`app/graph/nodes.py`](../../../app/graph/nodes.py).
- Cableado en [`app/graph/build.py`](../../../app/graph/build.py).
- API nueva (sin romper S12): `POST /api/v1/graph/estimate`.

### Nivel 2 — Checkpointer + observabilidad

- `AsyncPostgresSaver` sobre el Postgres del proyecto (`DATABASE_URL`).
- Setup en lifespan de FastAPI; grafo compilado con checkpointer en `app.state.estimation_graph`.
- `thread_id` = `estimation_id` (reanudación / historial por estimaciones).
- Span Logfire por nodo (`node: extract_requirements`, etc.); con o sin `LOGFIRE_TOKEN` se registra también localmente para la traza de entrega.
- Evidencia: [`evals/agent/GRAPH_TRACE.md`](../../../evals/agent/GRAPH_TRACE.md) generada con el transcript complex.

### Nivel 3 — Arista condicional

- Router: [`app/graph/routing.py`](../../../app/graph/routing.py) → `validated` | `needs_review`.
- Tests unitarios: [`tests/test_graph_routing.py`](../../../tests/test_graph_routing.py).

### Fuera de alcance (explícito en el material / pre-work)

Parallel `Send`, HITL, retries/fallback — no implementados a propósito.

---

## 4. Relación con sesiones anteriores

No se reescribió el retrieval ni el agente desde cero:

| Pieza previa | Uso en S13 |
|--------------|------------|
| `search_budgets` (S12) | Nodo `search_budgets` |
| `calculate_estimate` (S12) | Nodo `generate_estimate` |
| Búsqueda híbrida (S10) | Dentro de la tool de búsqueda |
| Corpus / pgvector (S7–S8) | Misma base indexada |
| Transcript complex (S12) | Input de la traza del grafo |

El endpoint del agente (`/api/v1/agent/estimate`) **sigue disponible**. El grafo es un modo paralelo de orquestación, documentado como **Modo 8** en el README del repo.

---

## 5. Mapa de archivos clave

```text
app/graph/
  state.py           # EstimationState + reducers
  nodes.py           # 5 nodos
  build.py           # StateGraph + edges + conditional
  routing.py         # N3: route_after_validation
  checkpointer.py    # URI Postgres para AsyncPostgresSaver
  observability.py   # Logfire + recorder local de spans
  runner.py          # invoke del grafo
  router.py          # FastAPI
  schemas.py         # request/response HTTP

scripts/run_graph.py              # CLI → GRAPH_TRACE.md
evals/agent/GRAPH_TRACE.md        # evidencia de corrida complex
docs/plans/session-13/            # plan, gap e esta explicación
```

Config relevante: `GRAPH_LLM_MODEL`, `LOGFIRE_TOKEN` (opcionales) en `.env.example` / `app/config.py`.

---

## 6. Cómo reproducir la demostración

Prerrequisitos: Postgres arriba, deps (`uv sync`), migraciones, corpus ingerido, servidor si se usa HTTP.

```bash
# Traza de entrega (transcript complex)
uv run python scripts/run_graph.py \
  --transcript examples/agent/sample_transcript_complex.txt \
  --out evals/agent/GRAPH_TRACE.md

# HTTP
curl -s -X POST http://localhost:8000/api/v1/graph/estimate \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile t examples/agent/sample_transcript_complex.txt \
      '{transcript:$t, estimation_id:"demo-thread-1"}')" | jq

# Tests de routing N3
uv run pytest tests/test_graph_routing.py -q
```

En una corrida válida se espera:

- Los 5 spans de nodo en orden.
- `status` = `validated` o `needs_review`.
- Campos de requisitos, componentes, matches y estimate en la traza / respuesta JSON.

---

## 7. Resultado de la corrida documentada

En [`evals/agent/GRAPH_TRACE.md`](../../../evals/agent/GRAPH_TRACE.md) (corrida con transcript complex):

- `status`: `validated`
- `node_spans`: los cinco nodos listados arriba
- `errors`: vacío
- Contenido: requirements, components, estimate y matches usados

Eso demuestra el grafo end-to-end (N1), checkpointer + spans (N2) y la decisión de status post-validación (N3).

---

## 8. Decisiones de diseño (útiles para la revisión)

1. **Grafo nuevo, no reemplazo silencioso del agente** — conviven S12 y S13; se compara orquestación LLM vs grafo fijado.
2. **Búsqueda secuencial por componente** — evita saturar el pool / sesiones async (misma lección práctica que en hybrid retrieval).
3. **Validación heurística** — suficiente para emitir `validated` / `needs_review` y ejercitar la arista condicional sin un segundo LLM de “juiciador”.
4. **Logfire** — elegido como capa de spans del material; el markdown de traza permite entregar evidencia aunque no haya UI Logfire configurada.

---

## 9. Resumen en una frase

Se tomó el flujo de estimación de presupuestos y se orquestó con LangGraph en cinco nodos tipados, con estado acumulable, checkpoint en Postgres, spans por nodo y salida con `status` validado o en revisión — evidenciado con `GRAPH_TRACE.md` sobre el transcript complex.
