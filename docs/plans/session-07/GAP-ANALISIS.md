# Gap analysis — Sesión 07 vs `mat-sesion7.md`

Contraste entre el material de clase (`IAENG/material/mat-sesion7.md`) y el estado del repo en la rama **`pre-session-07`**.

Complementa [`PLAN-IMPLEMENTACION.md`](./PLAN-IMPLEMENTACION.md) y el [`README`](../../../README.md) del proyecto.

**Última actualización:** cierre de brechas operativas (Docker + alias `/embeddings/ingest`). Rama de entrega: se mantiene **`pre-session-07`** por decisión del alumno.

---

## Resumen ejecutivo

| Área | Veredicto |
|------|-----------|
| Ejercicio pre-sesión (pasos 1–7, código) | **Cumple** |
| Entregable checklist (módulo, CLI, endpoint, SANITY, README, deps) | **Cumple** |
| Rutas HTTP | **Cumple** — `/api/v1/embeddings/ingest` + alias material `/embeddings/ingest` |
| Sanity check numérico (umbrales orientativos) | **Parcial aceptable** — pareja A 0.5957 (~0.6); B y C OK |
| Ejecución `compare.py` / sample en Docker | **Cumple** — `Dockerfile` copia `scripts/` y `data/` |
| Punto de partida “presupuestos S6 en JSON” | **Parcial aceptable** — `data/budgets_sample.json` (válido según material) |
| Rama `session-07/pre-exercise` (nombre LIDR) | **No aplica** — se entrega **`pre-session-07`** |
| Contenido teórico post-ejercicio | **Fuera de alcance** |
| Tests automatizados | **Extra cumplido** — suite con mocks, sin red |

**Conclusión:** Pre-ejercicio S7 **listo para entrega** en `pre-session-07`. Indicar al revisor la ruta canónica `/api/v1/...` y el alias `/embeddings/ingest` del enunciado.

---

## Matriz de cumplimiento (ejercicio pre-sesión)

| Requisito (material) | Estado | Evidencia / observación |
|----------------------|--------|-------------------------|
| **Paso 1** — Árbol módulo + `compare.py` + `budgets_sample.json` | **Cumple** | 15 presupuestos, 45 componentes |
| **Paso 1** — `openai` + `tiktoken` | **Cumple** | `pyproject.toml` |
| **Paso 1** — Sin numpy/sklearn | **Cumple** | `similarity.py` |
| **Paso 1** — Docker build | **Cumple** | Servicio `api`; imagen incluye `app`, `scripts`, `data` |
| **Paso 2** — Pydantic models | **Cumple** | `schemas.py` |
| **Paso 2** — `metadata` como `dict` | **Parcial aceptable** | `ChunkMetadata` tipado (JSON equivalente) |
| **Paso 3** — Chunker estructural | **Cumple** | `JSONStructuralChunker` |
| **Paso 4** — Embedder batch/retry/log/coste | **Cumple** | `embedder.py` |
| **Paso 5** — `POST /embeddings/ingest` | **Cumple** | Alias en `material_router`; canónico `/api/v1/embeddings/ingest` |
| **Paso 5** — 200 / 422 / 500 + `/docs` | **Cumple** | Tests router |
| **Paso 6** — `compare.py` local y contenedor | **Cumple** | README + `COPY scripts` en Dockerfile |
| **Paso 7** — `SANITY_CHECK.md` | **Cumple** | Tres parejas + comentario |
| **Paso 7** — Pareja A > 0.6 | **Parcial aceptable** | 0.5957 (orientativo, no formal) |
| **Entregable** — Rama material | **Sustituido** | **`pre-session-07`** (convención del repo) |
| **No entra** — pgvector, retrieval, UI, otros chunkers | **Cumple** | No implementado |

---

## Brechas cerradas

### Docker — `scripts/` y `data/` en la imagen

`Dockerfile` actualizado:

```dockerfile
COPY scripts ./scripts
COPY data ./data
```

Permite:

```bash
docker compose build api
docker compose exec api python scripts/compare.py --text-a "..." --text-b "..."
docker compose exec api sh -c 'jq -n --slurpfile b data/budgets_sample.json "{budgets: \$b[0]}" | curl -s -X POST http://127.0.0.1:8000/api/v1/embeddings/ingest -H Content-Type:application/json -d @-"'
```

(Requiere `jq` en la imagen solo para el ejemplo curl; el sample está en `/app/data/`.)

### Alias `POST /embeddings/ingest`

`material_router` en `app/embedding_pipeline/router.py` expone la misma handler que `/api/v1/embeddings/ingest`. Test: `tests/test_embeddings_router.py`.

### Rama de entrega

Decisión documentada: **no** crear `session-07/pre-exercise`; push y enlace LIDR apuntan a **`pre-session-07`**.

---

## Brechas residuales (no bloqueantes)

| Tema | Estado | Notas |
|------|--------|-------|
| Pareja A sanity < 0.6 | Aceptable | Pipeline correcto; umbral orientativo del PDF |
| Presupuestos desde S6 | Aceptable | Sample del material sustituye export S6 |
| Nombre servicio Compose `servicio_ia` vs `api` | Cosmético | README usa `api` |
| `metadata` tipado vs `dict` | Aceptable | Misma información en respuesta JSON |

---

## Fuera de alcance (correctamente omitido)

PostgreSQL + pgvector (S8), retrieval, hybrid search, recall@k/NDCG, otros chunkers, enriquecimiento LLM de chunks, cambios Streamlit/backend negocio, artículos teóricos (solo lectura).

---

## Checklist para el revisor

- [x] `app/embedding_pipeline/` completo
- [x] `scripts/compare.py`
- [x] `POST /embeddings/ingest` y `POST /api/v1/embeddings/ingest`
- [x] `SANITY_CHECK.md`
- [x] `README.md`
- [x] `pyproject.toml` + `tiktoken`
- [x] `data/budgets_sample.json`
- [x] Docker: `scripts/` + `data/` en imagen
- [x] Rama de trabajo: **`pre-session-07`** (en lugar de `session-07/pre-exercise`)

---

## Referencias

- Material: `IAENG/material/mat-sesion7.md`
- Sanity check: [`app/embedding_pipeline/SANITY_CHECK.md`](../../../app/embedding_pipeline/SANITY_CHECK.md)
- Commits S7: `38ebad2` … `a411007` + cierre GAP/Docker
