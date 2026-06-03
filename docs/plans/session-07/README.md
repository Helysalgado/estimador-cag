# Plan de implementación — Sesión 07 (pre-session-07)

Pre-ejercicio: **pipeline mínimo de embeddings y chunking** sobre presupuestos JSON.

| Documento | Contenido |
|-----------|-----------|
| **[PLAN-IMPLEMENTACION.md](./PLAN-IMPLEMENTACION.md)** | Plan detallado por fases (material `mat-sesion7.md`) |
| **[GAP-ANALISIS.md](./GAP-ANALISIS.md)** | Cumplimiento vs material y brechas pendientes |
| Material de curso | `IAENG/material/mat-sesion7.md` |

## Rama de trabajo

```bash
git checkout pre-session-07
```

La entrega del programa pide una rama tipo `session-07/pre-exercise`; en este repo el desarrollo sigue la convención `pre-session-07` (igual que S4–S6).

## Objetivo en una frase

JSON de presupuestos → chunks estructurados → embeddings OpenAI → `POST …/embeddings/ingest` + `scripts/compare.py` + `SANITY_CHECK.md`.

## Fuera de alcance S7

pgvector, retrieval, otros chunkers, métricas recall@k, cambios en Streamlit o backend de negocio.
