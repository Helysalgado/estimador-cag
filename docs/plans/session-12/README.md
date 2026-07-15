# Plan de implementación — Sesión 12 (agente con tools)

Pre-ejercicio: **agente manual** (Responses API + function calling) que orquesta `search_budgets` y `calculate_estimate` sobre una transcripción, con traza razonamiento → acción → observación. Sin frameworks de orquestación.

| Documento | Contenido |
|-----------|-----------|
| **[PLAN-IMPLEMENTACION.md](./PLAN-IMPLEMENTACION.md)** | Plan detallado por fases (material `mat-sesion12.md`) |
| **[GAP-ANALISIS.md](./GAP-ANALISIS.md)** | Estado actual vs material y brechas pendientes |
| Material de curso | `mat-sesion12.md` (ejercicio; artículos = lectura) |
| Punto de partida | Rama **`session-11/pre-work`** (RAG grounded + retrieval S10) |

## Rama de trabajo

```bash
git checkout session-11/pre-work
git checkout -b session-12/pre-work
```

Convención del material de entrega: **`session-12/pre-work`** (PR + mail a lia@lidr.co).

## Objetivo en una frase

Transcripción → bucle agéntico (decide → tool → observa) → `search_budgets` (×n) + `calculate_estimate` → estimación estructurada + traza STEP.

## Decisiones de adaptación (acordadas)

| Tema | Decisión |
|------|----------|
| Rama base | `session-12/pre-work` desde `session-11/pre-work` |
| Paquete | `app/agents/` |
| API | Nuevo `POST /api/v1/agent/estimate` |
| Retrieval | Reutilizar pipeline S10 (no reimplementar) |
| Cálculo | `calculate_estimate` determinista (mediana de referencias) |
| Traza | CLI `scripts/run_agent.py` → `evals/agent/TRACE_complex.md` |

## Prerrequisitos

```bash
docker compose up -d postgres
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
uv run python scripts/ingest_sample_corpus.py

# Agente (después de implementar)
uv run python scripts/run_agent.py --transcript examples/agent/sample_transcript_complex.txt
```

## Fuera de alcance S12 (pre-work)

`validate_estimate` (extensión opcional), LangChain/agente SDK, UI, reimplementar retrieval, multi-agente.

## Checklist de entrega

- [x] Tools `search_budgets` + `calculate_estimate` (+ schemas strict)
- [x] Bucle manual Responses API con traza STEP
- [x] Endpoint y/o CLI ejecutables
- [x] Traza sobre transcript compleja (>1 search, calculate_estimate)
- [ ] PR `session-12/pre-work` accesible
- [ ] Mail a lia@lidr.co con enlace + traza
