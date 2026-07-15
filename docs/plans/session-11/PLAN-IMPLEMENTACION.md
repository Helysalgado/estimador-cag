# Plan de implementación — Sesión 11 (generación grounded + RAGAS)

Plan para el pre-ejercicio de **RAG avanzado: generación y calidad** según `mat-sesion11.md`, adaptado al estado real de `estimador-cag` (retrieval S10 listo; generador RAG estructurado LIDR S9 **no** presente).

Complementa [`GAP-ANALISIS.md`](./GAP-ANALISIS.md).

---

## 1. Objetivo

Dada una consulta de estimación:

1. Recuperar contexto con el pipeline S10 (híbrida ± rerank).
2. Generar una **estimación estructurada** donde cada línea cite `chunk_id` del contexto recuperado (o declare `grounded=false`).
3. **Verificar** que no haya citaciones colgantes (`verify_citations`).
4. Evaluar calidad con **RAGAS** sobre 5 queries con `ground_truth`.

```text
query → retrieve (hybrid, opt. rerank) → context_assembler → structured_generate
      → verify_citations → Estimate + CitationReport
      → (offline) RAGAS eval script
```

---

## 2. Decisiones cerradas

| Tema | Decisión |
|------|----------|
| Rama | `session-11/pre-work` desde `session-10/pre-work` |
| Paquete | `app/embedding_pipeline/generation/` (schemas, prompts, generate, verify, assembler) |
| API | Nuevo `POST /api/v1/rag/estimate` — **no** modificar contrato de `/api/v1/estimate` texto libre |
| Structured output | OpenAI Responses API `responses.parse` (o equivalente estable del SDK) con modelos Pydantic v2 |
| Modelos HTTP | Request: `query` + flags retrieval (`search_mode`, `rerank`, `k`, `candidate_pool_size`). Response: estimate + `citation_report` + metadata retrieval |
| IDs | `chunk_id` / `document_id` como **string** en el contrato (cast desde int DB) |
| Integridad Pydantic | `grounded=True` ⇒ `sources` no vacío; `grounded=False` ⇒ sin inventar horas (p. ej. `hours` nullable o `0` + `assumption` obligatoria) |
| Retrieval default | `search_mode=hybrid`, `rerank=false` (config B S10), `k=5`, pool 50 si rerank on |
| Golden | Extender `evals/retrieval/golden_set.json` con `ground_truth` (texto o JSON corto de estimación esperada) |
| RAGAS | Dep `ragas`; script `scripts/eval_ragas.py` → `evals/retrieval/RAGAS_REPORT.md` |
| Judge / embeddings eval | OpenAI: embeddings `text-embedding-3-small`; juez chat configurable (default `gpt-4o-mini`) |
| Tests | Unitarios de `verify_citations` (OK + citación colgante forzada) |
| No tocar | Streamlit, `/estimate` /sessions, expansión/routing/filtros, content augmentation |

---

## 3. Schemas (contrato mínimo)

Alineados al material; campos concretos a fijar en código:

```text
SourceReference
  chunk_id: str
  document_id: str | None
  evidence: str          # fragmento verbatim del chunk

EstimateLineItem
  description: str
  hours: float | None
  role: str | None
  grounded: bool
  sources: list[SourceReference]
  assumption: str | None

Estimate
  summary: str | None
  line_items: list[EstimateLineItem]
  total_hours: float | None
  notes: str | None

CitationReport
  ok: bool
  dangling_chunk_ids: list[str]
  grounded_lines: int
  ungrounded_lines: int
  details: list[str] | None
```

Validadores: `model_validator` en `EstimateLineItem` para la regla grounded/sources.

---

## 4. Fases de implementación

### Fase 0 — Rama y deps

- [x] Rama `session-11/pre-work` (docs de plan)
- [ ] Añadir `ragas` (+ deps transitivas que exija la versión pinneada) en `pyproject.toml` / `uv.lock`
- [ ] Settings opcionales: `RAG_GENERATION_MODEL`, `RAGAS_JUDGE_MODEL`

### Fase 1 — Schemas + assembler

| Paso | Entrega |
|------|---------|
| 1.1 | `app/embedding_pipeline/generation/schemas.py` |
| 1.2 | `context_assembler.py`: lista de hits → bloque de texto con ids para el prompt |
| 1.3 | Export en `__init__.py` |

### Fase 2 — Generación estructurada

| Paso | Entrega |
|------|---------|
| 2.1 | Prompt system/user: solo usar chunks listados; cada línea grounded cita `chunk_id` + `evidence` verbatim; si no hay evidencia → `grounded=false` |
| 2.2 | `generate.py`: retrieve → assemble → `responses.parse` → `Estimate` |
| 2.3 | Manejo de errores API / parse fallido (mensaje claro + log) |

### Fase 3 — Verificación + endpoint

| Paso | Entrega |
|------|---------|
| 3.1 | `verify_citations(estimate, retrieved_chunk_ids) → CitationReport` |
| 3.2 | Logs structlog: `request_id`, dangling ids, conteos |
| 3.3 | Router: `POST /api/v1/rag/estimate` (mount junto a search o sub-router generation) |
| 3.4 | Tests unitarios citación colgante |

### Fase 4 — Golden + RAGAS

| Paso | Entrega |
|------|---------|
| 4.1 | Extender `golden_set.json` con `ground_truth` por query |
| 4.2 | `scripts/eval_ragas.py`: 5 queries → retrieve + generate → métricas RAGAS |
| 4.3 | Tabla en `evals/retrieval/RAGAS_REPORT.md` + promedio + nota breve |
| 4.4 | README root / sección uso del nuevo endpoint (breve) |

### Fase 5 — Entrega

- [ ] PR `session-11/pre-work`
- [ ] Mail a lia@lidr.co con enlace + tabla RAGAS

---

## 5. API — forma del contrato

### Request (propuesta)

```json
{
  "query": "Pasarela Stripe en ecommerce — horas frontend y backend",
  "k": 5,
  "search_mode": "hybrid",
  "rerank": false,
  "candidate_pool_size": 50
}
```

### Response (propuesta)

```json
{
  "estimate": {
    "summary": "...",
    "line_items": [
      {
        "description": "Integración Stripe Checkout",
        "hours": 24,
        "role": "backend",
        "grounded": true,
        "sources": [
          {
            "chunk_id": "12",
            "document_id": "3",
            "evidence": "..."
          }
        ],
        "assumption": null
      }
    ],
    "total_hours": 24,
    "notes": null
  },
  "citation_report": {
    "ok": true,
    "dangling_chunk_ids": [],
    "grounded_lines": 1,
    "ungrounded_lines": 0
  },
  "retrieval": {
    "search_mode": "hybrid",
    "rerank": false,
    "chunk_ids": ["12", "7", "..."]
  }
}
```

---

## 6. Prompt — reglas mínimas

1. El contexto lista chunks con id explícito; **prohibido** citar ids no listados.
2. Toda afirmación cuantitativa o de alcance en una línea `grounded=true` lleva ≥1 `SourceReference` con `evidence` tomados del chunk.
3. Si el contexto no soporta la línea → `grounded=false`, `sources=[]`, explicar en `assumption`.
4. No inventar módulos, precios o plazos ausentes del contexto.

---

## 7. RAGAS — inputs por fila

| Campo RAGAS | Origen |
|-------------|--------|
| `user_input` / question | `query` del golden set |
| `retrieved_contexts` | textos de chunks recuperados |
| `response` | serialización del `Estimate` (o summary + lines) |
| `reference` / ground_truth | campo `ground_truth` del golden set |

Métricas: **faithfulness**, **answer_relevancy**, **context_precision**, **context_recall**.

Coste: una pasada offline sobre 5 queries; documentar modelo juez en el informe.

---

## 8. Criterios de aceptación

| # | Criterio |
|---|----------|
| A1 | Estimate Pydantic con líneas `grounded` + `sources` |
| A2 | Prompt + generate usan solo `chunk_id` del retrieval |
| A3 | `verify_citations` marca dangling cuando se fuerza un id inventado |
| A4 | `POST /api/v1/rag/estimate` responde estimate + citation_report |
| A5 | `/api/v1/estimate` legacy sigue igual |
| A6 | Golden set con 5 `ground_truth` |
| A7 | Tabla RAGAS 5×4 + promedio + nota en `RAGAS_REPORT.md` |

---

## 9. Orden de trabajo (checklist ejecución)

1. Schemas + validadores  
2. Context assembler  
3. Generador + prompt  
4. `verify_citations` + endpoint + tests  
5. Extender golden set  
6. Script RAGAS + informe  
7. Docs breves de uso + PR  

---

## 10. Referencias

- Material: `mat-sesion11.md`
- Gap: [`GAP-ANALISIS.md`](./GAP-ANALISIS.md)
- S10 retrieval: [`../session-10/PLAN-IMPLEMENTACION.md`](../session-10/PLAN-IMPLEMENTACION.md)
- Código retrieval: `app/embedding_pipeline/retrieval/`
- LIDR S11 (referencia): `estimator/app/generation/rag/`
