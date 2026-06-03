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

El material sugiere la rama `session-07/pre-exercise`; **este repo mantiene `pre-session-07`** (igual que S4–S6) para entrega y revisión.

## Objetivo en una frase

JSON de presupuestos → chunks estructurados → embeddings OpenAI → `POST …/embeddings/ingest` + `scripts/compare.py` + `SANITY_CHECK.md`.

## Fuera de alcance S7

pgvector, retrieval, otros chunkers, métricas recall@k, cambios en Streamlit o backend de negocio.
