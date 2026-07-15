# Gap analysis — Sesión 11 vs `mat-sesion11.md`

Contraste entre el material de clase (`mat-sesion11.md`: citación verificable por línea + RAGAS) y el estado del repo en la rama **`session-10/pre-work`** (base de `session-11/pre-work`).

Complementa [`PLAN-IMPLEMENTACION.md`](./PLAN-IMPLEMENTACION.md).

**Última actualización:** plan pre-implementación (sin generador RAG estructurado ni RAGAS aún).

---

## Resumen ejecutivo

| Área | Veredicto |
|------|-----------|
| Retrieval híbrido + RRF + rerank (S10) | **Cumple** — `app/embedding_pipeline/retrieval/` |
| Golden set 5 queries (S10) | **Cumple** — sin campo `ground_truth` |
| `/estimate` texto libre (S4 Jinja2 + LiteLLM) | **Cumple** — **sin** retrieval ni citas |
| Generador RAG estructurado + Responses API | **No** |
| Prompt de atribución por línea | **No** |
| `verify_citations` + `CitationReport` | **No** |
| Endpoint RAG estimate | **No** |
| Extensión golden set con `ground_truth` | **No** |
| Eval RAGAS (4 métricas) | **No** |

**Conclusión:** El ejercicio S11 es viable montando un **camino RAG de estimación estructurada** sobre el retrieval S10. No hace falta el pipeline LIDR completo (expansión, routing, filtros temporales, augmentation). El formulario S4 y las sesiones S5 se dejan intactos.

---

## Matriz de cumplimiento (material S11 — ejercicio)

| Requisito (material) | Estado en `session-10/pre-work` | Tras S11 (objetivo) |
|----------------------|---------------------------------|---------------------|
| **1.1** Schema `SourceReference` / `EstimateLineItem` / `Estimate` | No (solo `EstimationResponse.text`) | Pydantic v2 + validadores |
| **1.2** Prompt atribución por línea + evidence verbatim | No | Prompt + context assembler con `chunk_id` |
| **1.3** `verify_citations` post-generación | No | Función + `CitationReport` + logs |
| **2.1** Golden set + `ground_truth` | Parcial (queries S10) | Extender JSON |
| **2.2** RAGAS 4 métricas | No | `scripts/eval_ragas.py` |
| **2.3** Tabla + promedio + nota | No | `evals/retrieval/RAGAS_REPORT.md` |
| Structured output (Responses API) | No (LiteLLM chat texto) | `responses.parse` / equivalente OpenAI |
| **No entra** — augmentation / hallucination pipeline completo | Cumple (no implementado) | mantener fuera |

---

## Asunciones del material que no aplican tal cual

| Asunción LIDR / material | Realidad en `estimador-cag` | Adaptación |
|--------------------------|----------------------------|------------|
| Generador S9 con citación gruesa ya existe | Solo estimate texto libre | Nuevo camino estructurado RAG |
| `app/generation/rag/` | No existe | `app/embedding_pipeline/generation/` |
| Reformulación + expansión + routing + filtros | Solo hybrid ± rerank | Reutilizar S10 sin añadir esas piezas |
| Backend Rails consume contrato | Streamlit / HTTP propio | Enriquecer body nuevo endpoint; no romper `/estimate` |

---

## Lo que ya existe (reutilizable)

| Componente | Archivo | Notas |
|------------|---------|-------|
| Retrieval pipeline | `app/embedding_pipeline/retrieval/pipeline.py` | Entrada al assembler |
| Search HTTP | `app/embedding_pipeline/router.py` | Flags `search_mode` / `rerank` |
| Golden set queries | `evals/retrieval/golden_set.json` | Base para `ground_truth` |
| Informe retrieval | `evals/retrieval/REPORT.md` | Baseline de recuperación (S10) |
| OpenAI client / settings | `app/config.py`, embedder | Clave + modelo juez/embeddings |
| structlog | `app/main.py` lifespan | Correlacionar `request_id` |
| Corpus sample | `data/budgets_sample.json` | Contexto recuperable |

---

## Brechas a cerrar en `session-11/pre-work`

### Generación grounded

- Schemas: `SourceReference`, `EstimateLineItem`, `Estimate`, `CitationReport`.
- Context assembler: formatear chunks con `chunk_id` / `document_id` / `content`.
- Generador estructurado + prompt de atribución.
- `verify_citations` (detectar citaciones colgantes).
- Endpoint `POST /api/v1/rag/estimate`.

### Evaluación

- Extender golden set: `ground_truth` por `q01`–`q05`.
- Dependencia `ragas` + script de evaluación.
- Informe tabular + nota de 2–3 frases.

### Tests

- Unitarios: línea grounded OK; citación colgante forzada; línea `grounded=False` sin sources.

---

## Fuera de alcance (pre-work S11)

Content augmentation extractiva/abstractiva, detector de alucinaciones ACB completo, query expansion / multi-índice / filtros metadata, cambios a Streamlit o a `/api/v1/estimate` legacy, merge de estimación RAG en el flujo conversacional S5.

---

## Checklist para el revisor (objetivo S11)

- [x] Schema por línea con `sources` / `grounded`
- [x] Prompt fuerza atribución a `chunk_id` del contexto
- [x] `verify_citations` detecta citación colgante en test/manual
- [x] Golden set con `ground_truth` (5 queries)
- [x] Tabla RAGAS 4 métricas × 5 + promedio
- [x] Nota breve sobre números llamativos
- [ ] Rama **`session-11/pre-work`** + PR accesible

---

## Referencias

- Material: `mat-sesion11.md` (ejercicio; artículos posteriores = lectura)
- Plan S10: [`../session-10/PLAN-IMPLEMENTACION.md`](../session-10/PLAN-IMPLEMENTACION.md)
- Retrieval: [`app/embedding_pipeline/retrieval/`](../../../app/embedding_pipeline/retrieval/)
- Estimate legacy: [`app/schemas/estimation.py`](../../../app/schemas/estimation.py)
- LIDR referencia: rama `session_11` (`estimator/app/generation/rag/`)
