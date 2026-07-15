# Gap analysis — Sesión 12 vs `mat-sesion12.md`

Contraste entre el material (agente + tools + bucle manual) y el estado del repo en **`session-11/pre-work`** (base de `session-12/pre-work`).

Complementa [`PLAN-IMPLEMENTACION.md`](./PLAN-IMPLEMENTACION.md).

---

## Resumen ejecutivo

| Área | Veredicto |
|------|-----------|
| Retrieval híbrido + rerank (S10) | **Cumple** — reusable como tool |
| Estimación RAG estructurada (S11) | **Cumple** — pipeline fijo, **no** es el agente |
| Bucle function calling manual | **No** |
| Tools `search_budgets` / `calculate_estimate` | **No** |
| Traza STEP reasoning/action/observation | **No** |
| Transcripts sample_simple / sample_complex | **No** (solo `examples/transcripts/` S9) |
| Endpoint agente | **No** |

**Conclusión:** S11 aporta generación grounded en un camino lineal. S12 añade una **capa de decisión** que elige cuántas búsquedas y en qué orden. No sustituye retrieval ni el estimate legacy.

---

## Matriz de cumplimiento (ejercicio)

| Requisito material | Estado base | Objetivo S12 |
|--------------------|-------------|--------------|
| Agente recibe transcripción | No | Request `transcript` |
| Descompone en componentes | No | System prompt + modelo |
| Tool `search_budgets` | No | Wrap `retrieve` |
| Tool `calculate_estimate` | No | Función pura |
| Bucle manual (no framework) | No | `loop.py` |
| Traza por paso | No | `trace.py` + fichero |
| >1 search + calculate en complex | No | Criterio aceptación |
| Código en inglés | Parcial | Exigencia package `agents` |

---

## Asunciones del material

| Asunción | Realidad | Adaptación |
|----------|----------|------------|
| Generador S9 live + Rails | Servicio FastAPI propio | Endpoint local `/api/v1/agent/estimate` |
| Ficheros LIDR `sample_transcript_*.txt` | No en repo | `examples/agent/` propios alineados al corpus |
| `calculate_estimate_skeleton.py` LIDR | No | Implementación local mediana/total |
| `gpt-5` siempre | Depende de cuota | Settings + fallback documentado a `gpt-5-mini` para debug |

---

## Reutilizable

| Componente | Ruta |
|------------|------|
| Retrieve hybrid | `app/embedding_pipeline/retrieval/pipeline.py` |
| Embedder | `app/embedding_pipeline/embedder.py` |
| Corpus sample | `data/budgets_sample.json` |
| Structured estimate schemas (referencia) | `app/embedding_pipeline/generation/schemas.py` |
| OpenAI client / settings | `app/config.py` |

---

## Fuera de alcance

`validate_estimate`, multi-agente, UI, content augmentation, cambios a Streamlit / estimate S4 / rag S11.

---

## Checklist revisor

- [x] `search_budgets` no reimplementa retrieval
- [x] Bucle usa `function_call` / `function_call_output` / `previous_response_id`
- [x] Traza complex en repo
- [ ] Rama `session-12/pre-work` + PR
