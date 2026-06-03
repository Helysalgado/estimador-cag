# Plan de implementación — Sesión 7 en vivo

Rama objetivo: **`session-07-live`** (desde **`pre-session-07`**).

Material: `IAENG/material/mat-sesion7.md` — artículos teóricos 2–4 y bloques hands-on del directo.

El **pre-ejercicio** cubre solo el pipeline mínimo (JSON estructural + embed + sanity check). Este plan cubre lo que el material reserva para **sesión en vivo**.

---

## Resumen ejecutivo

| Área | `pre-session-07` | `session-07-live` |
|------|------------------|-------------------|
| `JSONStructuralChunker` | Hecho | Refactor → interfaz `Chunker` |
| `TopicSegmentationChunker` | No | **Implementar** |
| Ingest solo `budgets[]` | Hecho | **Extender** con `document_type` + transcripciones |
| Matryoshka (`dimensions`) | No en embedder | **Añadir** parámetro opcional |
| Comparativa modelos/dims | `embedding_benchmark.py` parcial | Ampliar + script tipo `simple_embed` |
| Métricas dot / euclidean | Solo coseno en `compare.py` | **Ampliar** CLI o script dedicado |
| Contextual Retrieval (LLM) | Headers estáticos en chunk | **Opcional** en vivo |
| Persistencia / búsqueda | No | S8 |

**Esfuerzo orientativo:** 2–4 sesiones de pair-programming + APIs OpenAI/local según experimentos.

---

## Mapa material → código

| Tema (material) | Entregable en repo |
|-----------------|-------------------|
| Interfaz `Chunker(ABC)` | `app/embedding_pipeline/chunker_base.py` o `chunkers/base.py` |
| `JSONStructuralChunker` | Ya en `chunker.py`; adaptar firma `chunk(document)` |
| `TopicSegmentationChunker` | `app/embedding_pipeline/topic_chunker.py` |
| `IngestRouter` + `document_type` | `router.py` + schemas ampliados |
| Matryoshka 256/1536 | `embedder.py` + benchmark |
| MiniLM para segmentación interna | Reutilizar extra `benchmark` / modelo local |
| Calibrar `similarity_threshold≈0.55` | Config + tests con transcripción sample |
| Contextual Retrieval LLM | Opcional: `contextualizer.py` |
| Comparativa chunking | `docs/` o `CHUNKING-LIVE.md` con tablas |

---

## Estado actual (`pre-session-07`) — baseline

| Componente | Ubicación | Notas |
|------------|-----------|--------|
| Chunker JSON | `app/embedding_pipeline/chunker.py` | Sin ABC; `chunk(budgets: list[Budget])` |
| Embedder | `app/embedding_pipeline/embedder.py` | Solo 1536 dims fijas |
| Router | `app/embedding_pipeline/router.py` | Solo `IngestRequest.budgets` |
| Compare | `scripts/compare.py` | Solo coseno, 2 textos |
| Benchmark | `app/embedding_pipeline/embedding_benchmark.py` | OpenAI 1536/256 + MiniLM |
| Transcripciones sample | `docs/transcripcion-reunion.md` | Texto plano reutilizable |
| Presupuestos sample | `data/budgets_sample.json` | 15 items |

---

## Alcance por fases

### Fase 0 — Rama y checklist (30 min)

- [ ] `git checkout -b session-07-live` desde `pre-session-07`
- [ ] `uv run pytest -q` verde
- [ ] Smoke: `POST /api/v1/embeddings/ingest` con 1 presupuesto
- [ ] Documentar en este plan cualquier desviación del directo

**Commit:** (rama creada)

---

### Fase 1 — Interfaz común `Chunker` (2–3 h)

**Material:** artículo 4, esqueleto `Chunker(ABC)`.

| Tarea | Detalle |
|-------|---------|
| Crear `Chunker` abstracto | `chunk(self, document: dict \| str) -> list[Chunk]` |
| Refactor `JSONStructuralChunker` | Implementar ABC; mantener tests existentes |
| Unificar tipos | `Chunk` Pydantic ya existente; no duplicar dataclass |

Estructura sugerida:

```
app/embedding_pipeline/
├── chunkers/
│   ├── __init__.py
│   ├── base.py              # Chunker ABC
│   ├── structural.py        # JSONStructuralChunker (move from chunker.py)
│   └── topic.py             # TopicSegmentationChunker (Fase 2)
├── chunker.py               # re-export o deprecate → structural
```

**Tests:** `tests/test_chunker.py` sigue verde; añadir test de que JSON implementa ABC.

**Commit:** `refactor(session-07-live): introduce Chunker ABC and structural adapter`

---

### Fase 2 — `TopicSegmentationChunker` (1 día)

**Material:** artículo 4, líneas ~1395–1492.

| Regla | Implementación |
|-------|----------------|
| Input | Transcripción `str` (6k–12k tokens) |
| Split | Oraciones o intervenciones (`Speaker A:`) |
| Detección de tema | Similitud coseno entre embeddings **consecutivos**; corte si `< threshold` |
| Modelo segmentación | **`all-MiniLM-L6-v2` local** (rápido; no 1 API call por oración con OpenAI) |
| Modelo índice final | **`text-embedding-3-small`** vía `OpenAIEmbedder` (igual que presupuestos) |
| Headers | `[Meeting: …]`, cliente, fecha, participantes, fase |
| Metadata | `meeting_id`, `block_index`, speaker dominante, posición early/mid/late |
| `chunk_id` | `{meeting_id}::{block_index}` |
| Parámetro | `similarity_threshold=0.55` (configurable; calibrar en Fase 5) |

**Datos:**

- [ ] `data/transcripts_sample.json` o reutilizar `docs/transcripcion-reunion.md` + metadata wrapper
- [ ] Schema Pydantic `MeetingTranscript` (`meeting_id`, `client_metadata`, `date`, `participants`, `text`, `phase`)

**Tests (sin red):**

- Mock embedder local → boundaries deterministas
- Transcripción corta con 2 temas claros → ≥2 chunks

**Commit:** `feat(session-07-live): add TopicSegmentationChunker for meeting transcripts`

---

### Fase 3 — Ingest multi-tipo (`IngestRouter`) (3–4 h)

**Material:** artículo 4, `IngestRouter`, payload con `document_type`.

| Cambio | Detalle |
|--------|---------|
| Schema | `IngestRequest` ampliado: `document_type: Literal["budget", "transcript"]` |
| Payload budget | `budgets: list[Budget]` (compatibilidad: default `document_type=budget` si solo viene `budgets`) |
| Payload transcript | `transcript: MeetingTranscript` o `transcripts: list[...]` |
| Router interno | `IngestRouter.chunk(document, document_type)` |
| Handler | chunk → embed_many → `IngestResponse` (sin cambio en respuesta) |
| OpenAPI | Ejemplos para ambos tipos en `/docs` |

Contrato material (adaptado al repo):

```json
{
  "document_type": "budget",
  "budgets": [ ... ]
}
```

```json
{
  "document_type": "transcript",
  "transcript": {
    "meeting_id": "MTG-2024-001",
    "client_metadata": { "name": "...", "sector": "finance", "country": "MX" },
    "date": "2024-03-03",
    "participants": ["PM", "Tech lead"],
    "phase": "discovery",
    "text": "Speaker A: ..."
  }
}
```

**Tests:** HTTP 200 budget (existente) + 200 transcript (mock embed) + 422 tipo desconocido.

**Commit:** `feat(session-07-live): route ingest by document_type budget vs transcript`

---

### Fase 4 — Matryoshka y embedder dual-use (2 h)

**Material:** artículo 2, Matryoshka; artículo 4 (modelo distinto para segmentación vs índice).

| Tarea | Archivo |
|-------|---------|
| `OpenAIEmbedder.embed_one/many(..., dimensions: int \| None)` | `embedder.py` |
| Normalizar vectores truncados si aplica | helper en `similarity.py` |
| Documentar coste por dims | constantes en embedder |
| Topic chunker usa MiniLM **solo** para detectar cortes | ya en Fase 2 |

**Commit:** `feat(session-07-live): support Matryoshka dimensions in OpenAI embedder`

---

### Fase 5 — Scripts de experimentación en vivo (2–3 h)

**Material:** foto `simple_embed.py` (Similarity + Dot + Euclidean; dims 6/256/1536); artículo 2 benchmark.

| Entregable | Descripción |
|------------|-------------|
| Ampliar `similarity.py` | `dot_product`, `euclidean_distance` (migrar de `ejerciciosprueba/embedding_pair.py`) |
| `scripts/simple_embed.py` o extender `compare.py` | 3 parejas fijas, 3 métricas, loop dimensiones `[256, 1536]` (6 solo si API lo permite) |
| `embedding_benchmark.py` | Ya existe; alinear salida con formato del curso |
| **`CHUNKING-LIVE.md`** | Resultados: structural vs topic en mismos textos; threshold 0.45/0.55/0.65 |

Comando objetivo:

```bash
uv run python scripts/simple_embed.py   # o compare.py --full-metrics
uv run python app/embedding_pipeline/embedding_benchmark.py
```

**Commit:** `feat(session-07-live): add simple_embed metrics and chunking live report`

---

### Fase 6 — Calibración topic threshold (hands-on, 1–2 h)

**Material:** “calibraremos sobre transcripciones reales”.

| Paso | Acción |
|------|--------|
| 1 | Correr topic chunker con threshold 0.45, 0.55, 0.65 |
| 2 | Revisión manual: ¿cortes respetan cambios de tema (auth → hosting → auth)? |
| 3 | Fijar default en config (`TOPIC_SIMILARITY_THRESHOLD`) |
| 4 | Registrar en `CHUNKING-LIVE.md` |

No requiere código nuevo si Fase 2 expone el parámetro.

---

### Fase 7 — Contextual Retrieval con LLM (opcional, si el directo lo pide)

**Material:** artículo 3–4, variante LLM de headers (Anthropic Contextual Retrieval).

| Tarea | Alcance |
|-------|---------|
| `ContextualChunkEnricher` | Prompt corto: “sitúa este chunk en el documento padre” |
| A/B | Chunks con header estático vs enriquecidos LLM |
| Medir | Similitud query–chunk en 5 consultas de ejemplo |

**No bloqueante** para cerrar la rama si el tiempo apremia.

**Commit:** `feat(session-07-live): optional LLM contextual headers for chunks`

---

### Fase 8 — Documentación y cierre (1 h)

- [ ] Actualizar `README.md` (Modo 3: ingest transcript, scripts live)
- [ ] Actualizar `GAP-ANALISIS` o crear `GAP-LIVE.md` vs material
- [ ] `uv run pytest -q`
- [ ] Push `session-07-live`

---

## Matriz: pre-sesión vs en vivo

| Ítem | Pre (`pre-session-07`) | Live (`session-07-live`) |
|------|------------------------|---------------------------|
| JSONStructuralChunker | Sí | Refactor ABC |
| TopicSegmentationChunker | No | **Sí** |
| Ingest `budgets` only | Sí | + `document_type` |
| Matryoshka | No | Sí |
| compare.py coseno | Sí | + dot/euclidean script |
| Model compare OpenAI vs MiniLM | Parcial | Completar + documentar |
| LLM contextualizer | No | Opcional |
| pgvector | No | **S8** |

---

## Orden de commits sugerido

1. `refactor(session-07-live): introduce Chunker ABC and structural adapter`
2. `feat(session-07-live): add TopicSegmentationChunker for meeting transcripts`
3. `feat(session-07-live): route ingest by document_type budget vs transcript`
4. `feat(session-07-live): support Matryoshka dimensions in OpenAI embedder`
5. `feat(session-07-live): add simple_embed metrics and chunking live report`
6. `doc(session-07-live): CHUNKING-LIVE calibration and README updates`
7. (Opcional) `feat(session-07-live): optional LLM contextual headers`

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Coste API al embeder cada oración con OpenAI en topic split | MiniLM **solo** para boundaries; OpenAI para chunks finales |
| `sentence-transformers` pesado | Extra `benchmark`; no en Docker API |
| Transcripción sin speakers | Fallback split por oraciones (regex `. `) |
| Incompatibilidad payload material vs repo | Mantener `budgets[]` + añadir `document_type`; default backward-compatible |
| Threshold 0.55 no sirve para tu español/inglés mixto | Fase 6 calibración documentada |

---

## Checklist final rama `session-07-live`

- [ ] `Chunker` ABC + 2 implementaciones
- [ ] Ingest `document_type=budget|transcript` en `/docs`
- [ ] Sample transcripción ingestible
- [ ] Matryoshka en embedder
- [ ] Script métricas múltiples (coseno/dot/euclidean)
- [ ] `CHUNKING-LIVE.md` con calibración threshold
- [ ] Tests pytest sin red para chunkers y router
- [ ] README actualizado
- [ ] Push rama remota

---

## Referencias

- [`docs/plans/session-07/PLAN-IMPLEMENTACION.md`](../session-07/PLAN-IMPLEMENTACION.md) — pre-ejercicio
- [`docs/plans/session-07/GAP-ANALISIS.md`](../session-07/GAP-ANALISIS.md) — cumplimiento pre-sesión
- [`docs/transcripcion-reunion.md`](../../transcripcion-reunion.md) — texto para topic chunker
- [`app/embedding_pipeline/SANITY_CHECK.md`](../../../app/embedding_pipeline/SANITY_CHECK.md) — baseline embeddings
