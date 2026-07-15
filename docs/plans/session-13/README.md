# Plan de implementación — Sesión 13 (orquestación LangGraph)

Pre-ejercicio: reexpresar la estimación como **grafo LangGraph** secuencial (5 nodos), con estado tipado, checkpointer en Postgres, Logfire y arista condicional post-validación (Niveles 1–3).

| Documento | Contenido |
|-----------|-----------|
| **[EXPLICACION-ENTREGA.md](./EXPLICACION-ENTREGA.md)** | Qué se implementó (para explicar al profesor) |
| **[PLAN-IMPLEMENTACION.md](./PLAN-IMPLEMENTACION.md)** | Plan detallado N1–N3 (`mat-sesion13.md`) |
| **[GAP-ANALISIS.md](./GAP-ANALISIS.md)** | Estado actual vs material |
| Material | `mat-sesion13.md` (ejercicio; artículos = lectura) |
| Punto de partida | Rama **`session-12/pre-work`** (agente + tools) |

## Rama de trabajo

```bash
git checkout session-12/pre-work
git checkout -b session-13/pre-work
```

Entrega: **`session-13/pre-work`** + mail a lia@lidr.co.

## Objetivo en una frase

Transcripción → grafo (extract → classify → search → generate → validate) → estimate + `status` (`validated` \| `needs_review`), con checkpoints y traza por nodo.

## Decisiones acordadas

| Tema | Decisión |
|------|----------|
| Paquete | `app/graph/` |
| API | `POST /api/v1/graph/estimate` (no romper `/agent/estimate`) |
| Checkpointer | `AsyncPostgresSaver` en el Postgres del proyecto |
| Observabilidad | Logfire, span por nodo |
| N3 | Arista condicional tras `validate_and_consolidate` |
| Fuera (directo) | Parallel Send, HITL, retries/fallback |

## Prerrequisitos

```bash
docker compose up -d postgres
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
uv run python scripts/ingest_sample_corpus.py

uv run python scripts/run_graph.py \
  --transcript examples/agent/sample_transcript_complex.txt
```

## Checklist de entrega

- [x] Nivel 1: grafo secuencial + estado tipado + reducer
- [x] Nivel 2: checkpointer + Logfire + traza complex (regenerar con `scripts/run_graph.py`)
- [x] Nivel 3: arista condicional `validated` / `needs_review`
- [ ] PR `session-13/pre-work` accesible
- [ ] Mail a lia@lidr.co con enlace + traza
