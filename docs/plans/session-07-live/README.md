# Plan — Sesión 7 en vivo (`session-07-live`)

Desarrollo sobre el pre-ejercicio completado en **`pre-session-07`**. Rama de trabajo propuesta: **`session-07-live`**.

| Documento | Contenido |
|-----------|-----------|
| **[PLAN-LIVE.md](./PLAN-LIVE.md)** | Fases, alcance y checklist vs material |
| Pre-ejercicio (hecho) | [`PLAN-IMPLEMENTACION.md`](./PLAN-IMPLEMENTACION.md), [`GAP-ANALISIS.md`](./GAP-ANALISIS.md) |
| Material | `IAENG/material/mat-sesion7.md` (artículos 2–4 + hands-on) |

## Punto de partida

```bash
git checkout pre-session-07
git pull
git checkout -b session-07-live
```

**Ya implementado en `pre-session-07`** (no repetir):

- `JSONStructuralChunker`, `OpenAIEmbedder`, ingest, `compare.py`, `SANITY_CHECK.md`
- Alias `POST /embeddings/ingest`
- `embedding_benchmark.py` (OpenAI vs MiniLM, extra `benchmark`)

## Objetivo de la rama live

Dos chunkers bajo interfaz común, ingest multi-tipo, experimentos de embeddings/chunking del directo — **sin** pgvector ni retrieval (S8+).

## Fuera de alcance (live tampoco, salvo que el profesor diga lo contrario)

- PostgreSQL + pgvector (S8)
- Hybrid search / recall@k formal (S10–S11)
- Catálogo completo LangChain (recursive, semantic, agentic…) como producción
- Cambios Streamlit / backend de negocio
