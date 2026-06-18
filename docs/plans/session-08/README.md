# Plan de implementación — Sesión 08 (pgvector + búsqueda semántica)

Pre-ejercicio: **persistir el pipeline S7 en PostgreSQL + pgvector** y exponer búsqueda semántica por distancia coseno.

| Documento | Contenido |
|-----------|-----------|
| **[PLAN-IMPLEMENTACION.md](./PLAN-IMPLEMENTACION.md)** | Plan detallado por pasos (material `sesion8.md`) |
| **[GAP-ANALISIS.md](./GAP-ANALISIS.md)** | Estado actual vs material y brechas pendientes |
| Material de curso | `sesion8.md` (Migración a pgvector + endpoint de búsqueda) |
| Punto de partida | Rama **`pre-session-07`** (pipeline embeddings en memoria) |

## Rama de trabajo

```bash
git checkout pre-session-07
git checkout -b pre-session-08
```

Convención del repo: **`pre-session-08`** (igual que S4–S7).

## Objetivo en una frase

Presupuesto JSON → chunk + embed → **persistir** en `documents` + `chunks` (transacción única) → `POST /search` por distancia coseno + `scripts/query_examples.py` + `output_examples.txt`.

## Decisiones de adaptación (acordadas)

| Tema | Decisión |
|------|----------|
| Rama base | `pre-session-08` desde `pre-session-07` |
| Servicio Docker | Renombrar `api` → **`ai_service`** (literal material) |
| Rutas HTTP | Canónicas `/api/v1/...`; alias material `/embeddings/ingest` y `/search` |
| `query_examples.py` | **`scripts/query_examples.py`** (convención repo) |
| Esquema DB | Columnas exactas del material; mapeo S7 → `content` + JSONB metadata |
| `source_path` | Índice **UNIQUE** (soporte 409 duplicados) |
| Índice vectorial | **No** (baseline para sesión en vivo) |

## Fuera de alcance S8

Índices HNSW/IVFFlat, filtros por metadata, búsqueda híbrida full-text + vector, tuning de parámetros Postgres (`shared_buffers`, `ef_search`, etc.).
