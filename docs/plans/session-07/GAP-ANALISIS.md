# Gap analysis — Sesión 07 vs `mat-sesion7.md`

Contraste entre el material de clase (`IAENG/material/mat-sesion7.md`) y el estado del repo en la rama **`pre-session-07`** (commit de referencia: `a411007` y posteriores en la misma rama).

Complementa [`PLAN-IMPLEMENTACION.md`](./PLAN-IMPLEMENTACION.md) y el [`README`](../../../README.md) del proyecto.

---

## Resumen ejecutivo

| Área | Veredicto |
|------|-----------|
| Ejercicio pre-sesión (pasos 1–7, código) | **Cumple en gran parte** |
| Entregable checklist (módulo, CLI, endpoint, SANITY, README, deps) | **Cumple** salvo convenciones de ruta/rama |
| Sanity check numérico (umbrales orientativos) | **Parcial** — pareja A ~0.60, no > 0.6 |
| Ejecución `compare.py` / ingest con sample **dentro de Docker** | **No cumple** — imagen no incluye `scripts/` ni `data/` |
| Punto de partida “presupuestos S6 en JSON” | **Parcial** — se usa `data/budgets_sample.json` generado localmente |
| Contenido teórico post-ejercicio (RAG, pgvector, otros chunkers) | **Fuera de alcance** (material explícito) |
| Tests automatizados | **Opcional cumplido** — 17 tests nuevos sin red en pytest |

**Conclusión:** El pipeline end-to-end está listo para entrega académica vía **`uv run`** y API local. Antes de confiar en los ejemplos Docker del README, hay que **copiar `scripts/` y `data/` en la imagen** (o montar volúmenes). Para LIDR, crear/publicar la rama **`session-07/pre-exercise`** si el revisor exige el nombre literal.

---

## Matriz de cumplimiento (ejercicio pre-sesión)

| Requisito (material) | Estado | Evidencia / observación |
|----------------------|--------|-------------------------|
| **Paso 1** — Árbol `embedding_pipeline/` + `scripts/compare.py` + `data/budgets_sample.json` | **Cumple** | `app/embedding_pipeline/*`, `scripts/compare.py`, `data/budgets_sample.json` (15 presupuestos, 45 componentes) |
| **Paso 1** — `openai` + `tiktoken` en `pyproject.toml` | **Cumple** | `tiktoken>=0.7.0`; `openai>=2.33.0` ya presente |
| **Paso 1** — Sin numpy/sklearn para coseno | **Cumple** | `app/embedding_pipeline/similarity.py` (stdlib) |
| **Paso 1** — `docker compose build servicio_ia` | **Parcial** | Servicio se llama **`api`** en `docker-compose.yml`; build OK pero imagen incompleta para CLI (ver abajo) |
| **Paso 2** — Modelos Pydantic (`Budget`, `BudgetComponent`, `Chunk`, …) | **Cumple** | `app/embedding_pipeline/schemas.py` |
| **Paso 2** — `metadata` como `dict` | **Parcial** | `ChunkMetadata` tipado (equivalente funcional; serializa como objeto JSON en respuesta) |
| **Paso 2** — `sector` con `Literal` | **Cumple** | 6 sectores del sample (`finance`, `ecommerce`, …) |
| **Paso 3** — `JSONStructuralChunker`, 1 componente = 1 chunk | **Cumple** | `app/embedding_pipeline/chunker.py` |
| **Paso 3** — Plantilla `text` con contexto padre | **Cumple** | `build_chunk_text()` alineada al material |
| **Paso 3** — `chunk_id` `{budget_id}::{component_id}` | **Cumple** | Tests en `tests/test_chunker.py` |
| **Paso 3** — `token_count` con tiktoken | **Cumple** | `count_tokens()`; requiere descarga de vocabulario la primera vez |
| **Paso 3** — Sin overlap / fixed-size split | **Cumple** | No implementado (correcto por scope) |
| **Paso 4** — `OpenAIEmbedder.embed_one` / `embed_many` | **Cumple** | `app/embedding_pipeline/embedder.py` |
| **Paso 4** — Modelo `text-embedding-3-small`, 1536 dims | **Cumple** | Sin `dimensions` forzado |
| **Paso 4** — Batches de 100 | **Cumple** | `EMBED_BATCH_SIZE = 100` |
| **Paso 4** — Retry `RateLimitError` 1s, 2s, 4s | **Cumple** | 3 reintentos + intento inicial |
| **Paso 4** — structlog por batch | **Cumple** | `embedding_batch_complete` |
| **Paso 4** — Coste `$0.02 / 1M tokens` en stats | **Cumple** | `estimate_embedding_cost_usd()` en router |
| **Paso 5** — `POST /embeddings/ingest` | **Parcial** | Ruta real: **`POST /api/v1/embeddings/ingest`** (convención del repo) |
| **Paso 5** — Orquestación chunk → embed → response | **Cumple** | `app/embedding_pipeline/router.py` |
| **Paso 5** — 200 / 422 / 500 | **Cumple** | Tests `tests/test_embeddings_router.py` |
| **Paso 5** — Visible en `/docs` | **Cumple** | Tag `embeddings` en OpenAPI |
| **Paso 6** — `scripts/compare.py` `--text-a` / `--text-b` | **Cumple** | Reutiliza `OpenAIEmbedder` |
| **Paso 6** — Salida con similitud coseno | **Cumple** | Formato `Cosine similarity: 0.xxxx` |
| **Paso 6** — `uv run` + `.env` | **Cumple** | `load_dotenv` en script |
| **Paso 6** — Dentro del contenedor | **No cumple (imagen actual)** | `Dockerfile` solo `COPY app`; no hay `scripts/` ni `data/` en el contenedor |
| **Paso 6** — README ambas formas | **Cumple** | Sección “Modo 3” en `README.md` (asume imagen con scripts; ver brecha Docker) |
| **Paso 7** — Tres parejas en `SANITY_CHECK.md` | **Cumple** | `app/embedding_pipeline/SANITY_CHECK.md` |
| **Paso 7** — Valores numéricos + comentario 3–5 líneas | **Cumple** | Corrida 2026-06-03 documentada |
| **Paso 7** — Pareja A > 0.6 orientativo | **Parcial** | **0.5957** (frontera; pipeline OK, umbral estricto falla) |
| **Paso 7** — Pareja B < 0.4 | **Cumple** | **0.1920** |
| **Paso 7** — Pareja C comentada | **Cumple** | **0.5406** — texto genérico casi tan alto como A |
| **Entregable** — Rama `session-07/pre-exercise` | **Pendiente operativo** | Desarrollo en **`pre-session-07`**; falta rama/URL de entrega LIDR |
| **Entregable** — Módulo completo | **Cumple** | 5 archivos Python + `SANITY_CHECK.md` (+ `similarity.py` auxiliar) |
| **Entregable** — Tests no obligatorios | **Extra** | 6 archivos de test, 109 tests totales en suite |
| **No entra** — pgvector, retrieval, otros chunkers, UI | **Cumple** | No implementado |
| **Prerrequisito** — Presupuestos normalizados desde S6 | **Parcial** | S6 aportó stress/CAG, no un export JSON de presupuestos; sample local válido según material |

---

## Brechas detalladas

### 1. Ruta HTTP (`/embeddings` vs `/api/v1/embeddings`)

| Material | Repo |
|----------|------|
| `POST /embeddings/ingest` | `POST /api/v1/embeddings/ingest` |

**Impacto:** Ninguno para Swagger ni clientes que lean `/docs`. Clientes con URL hardcodeada del PDF del material deben ajustar el prefijo.

**Opciones:** (a) mantener consistencia con S4–S6; (b) registrar un segundo router sin prefijo solo para entrega literal.

---

### 2. Docker: `compare.py` e ingest con `budgets_sample.json`

El `Dockerfile` actual:

```dockerfile
COPY app ./app
```

No copia `scripts/` ni `data/`. Por tanto:

```bash
docker compose exec api python scripts/compare.py ...
```

**fallará** (archivo inexistente en `/app/scripts/`).

**Acción recomendada (Fase Docker, ~15 min):**

```dockerfile
COPY scripts ./scripts
COPY data ./data
```

Reconstruir: `docker compose build api`. Opcional: documentar en README que hasta entonces solo aplique el camino `uv run`.

---

### 3. Sanity check — pareja A en el umbral

| Pareja | Resultado | Expectativa material |
|--------|-----------|----------------------|
| A | 0.5957 | Alta (> 0.6) |
| B | 0.1920 | Baja (< 0.4) ✓ |
| C | 0.5406 | Discusión ✓ |

No invalida el ejercicio: el material aclara que es un mínimo orientativo, no métrica formal. Útil mencionar en la sesión en vivo (redacción distinta, mismo dominio).

---

### 4. Dataset de presupuestos vs narrativa S6

El material asume “presupuestos históricos limpios” al cerrar S6. En este repo:

- **S6** entregó stress CAG, `turn_observed`, evals — no un fichero `budgets_*.json` de producción.
- **S7** usa `data/budgets_sample.json` alineado al esquema del material (válido: *“en caso contrario, se trabaja con el sample proporcionado”*).

**Gap narrativo, no bloqueante** para el pre-ejercicio.

---

### 5. Rama de entrega LIDR

| Esperado (material) | Actual |
|---------------------|--------|
| `session-07/pre-exercise` | `pre-session-07` |

```bash
git checkout pre-session-07
git branch session-07/pre-exercise
git push -u origin session-07/pre-exercise
```

Enviar URL de esa rama a lia@lidr.co según plazo del programa.

---

### 6. Nombre del servicio Compose

Material: `servicio_ia`. Repo: **`api`**. Solo afecta ejemplos copy-paste del PDF; el README del repo ya usa `api`.

---

## Fuera de alcance (correctamente omitido)

| Tema | Sesión prevista (material) |
|------|----------------------------|
| Recursive / semantic / hierarchical chunking | En vivo S7 |
| Varios modelos de embedding | En vivo S7 |
| Enriquecimiento LLM del chunk | En vivo S7 |
| PostgreSQL + pgvector | **S8** |
| Retrieval / hybrid search | S10+ |
| recall@k, NDCG | S11 |
| Cambios Streamlit / backend negocio | — |
| Artículos teóricos (embeddings, métricas, etc.) | Lectura; no código del entregable |

---

## Plan de cierre (solo brechas operativas)

### Fase A — Docker (recomendado antes de demo en contenedor)

| Tarea | Esfuerzo |
|-------|----------|
| `COPY scripts` + `COPY data` en `Dockerfile` | ~10 min |
| `docker compose build api` + probar `exec … compare.py` | ~10 min |

### Fase B — Entrega LIDR

| Tarea | Esfuerzo |
|-------|----------|
| Push rama `session-07/pre-exercise` | ~5 min |
| Email con enlace + nota de ruta `/api/v1/embeddings/ingest` | ~5 min |

### Fase C — Opcional

| Tarea | Motivo |
|-------|--------|
| Alias `POST /embeddings/ingest` | Solo si el revisor exige URL literal |
| Re-ejecutar pareja A con textos más largos | Subir similitud por encima de 0.6 (no requerido) |
| Ingest E2E manual con 15 presupuestos | Evidencia de coste `stats` en issue/PR |

---

## Checklist rápido para el revisor

- [x] `app/embedding_pipeline/` (`__init__`, `schemas`, `chunker`, `embedder`, `router`)
- [x] `scripts/compare.py`
- [x] `POST /api/v1/embeddings/ingest` (+ OpenAPI)
- [x] `app/embedding_pipeline/SANITY_CHECK.md` (3 similitudes + comentario)
- [x] `README.md` (ingest + compare local)
- [x] `pyproject.toml` + `tiktoken`
- [x] `data/budgets_sample.json` (15 items)
- [ ] `compare.py` verificado **dentro** de imagen Docker (pendiente Fase A)
- [ ] Rama publicada `session-07/pre-exercise` (pendiente Fase B)

---

## Referencias

- Material: `IAENG/material/mat-sesion7.md`
- Plan local: [`PLAN-IMPLEMENTACION.md`](./PLAN-IMPLEMENTACION.md)
- Sanity check: [`app/embedding_pipeline/SANITY_CHECK.md`](../../../app/embedding_pipeline/SANITY_CHECK.md)
- Commits S7 en `pre-session-07`: `38ebad2` … `a411007`
