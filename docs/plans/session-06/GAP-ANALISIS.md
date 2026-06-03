# Gap analysis — Sesión 06 vs `mat-sesion6.md`

Documento de contraste entre el material de clase (`material/mat-sesion6.md`) y el estado del repo en la rama `pre-session-06`. Complementa `README.md` (bitácora de lo ya implementado en código).

## Resumen ejecutivo

| Área | Veredicto |
|------|-----------|
| Punto de partida Sesión 5 (CAG, adjuntos, evals golden, ACB, observabilidad) | **Cumple** |
| Ejercicio pre-sesión (bloques 1–5, código) | **Cumple en gran parte** |
| Entregable final (`REPORT.md` + `results.csv` con datos reales) | **Parcial** — reporte actual con fallback 100% |
| Contenido teórico post-ejercicio (RAG, catálogo, ingest) | **Fuera de alcance** del pre-ejercicio |

---

## Matriz de cumplimiento (ejercicio pre-sesión)

| Requisito (material) | Estado | Evidencia / observación |
|----------------------|--------|-------------------------|
| Punto de partida Sesión 5 | **Cumple** | `app/services/sessions.py`, `evals/golden_dataset.json`, `evals/run.py`, `GET /api/v1/sessions/{id}` |
| Bloque 1: `turn_observed` (13 campos) | **Cumple** | `app/services/session_estimation.py` — log structlog + `session.last_turn_observed` |
| Bloque 2: 3 perfiles + fact-tracker | **Parcial** | `evals/stress/scenarios.py` — solo 6 turnos; material pide N ∈ {1, 3, 6, 10, **20**} |
| Bloque 3: PDFs 5/20/50/100 KB + tamaño 0 | **Cumple (script)** / **Parcial (corrida)** | `evals/stress/fixtures/build_pdfs.py`; CSV commiteado con menos tamaños/repeticiones |
| Bloque 4: métricas stress + tests | **Cumple** | `evals/stress/metrics.py`, `tests/test_stress_metrics.py` |
| Bloque 5: runner CLI + CSV + REPORT | **Parcial** | `evals/stress/run.py` OK; `REPORT.md` con métricas en cero |
| Criterio: ≥ 50 filas CSV | **Cumple mínimo** | 54 filas en `evals/stress/results.csv` |
| Criterio: afirmaciones cuantitativas en reporte | **No cumple** | `runner_fallback=1.00`; sin claims tipo “turno N=12 recall < 60%” |
| `cache_hit_kind` exact/semantic en reporte | **Parcial** | Campo existe; sesiones siempre `"none"`; no hay cache semántica conversacional |
| `MemoryDriftMetric` en turnos posteriores (N > k) | **Parcial** | Evalúa snapshot del mismo turno, no persistencia en turnos siguientes |
| Recall de contenido de adjunto en respuesta/summary | **No implementado** | Bloque 3 del material |
| Modo in-process (`TestClient`) en stress runner | **Opcional / no hecho** | Solo httpx hoy |
| RAG, catálogo YAML, pipeline ingest | **Fuera de alcance** | Material: “Lo que NO entra” / contenido del directo |

---

## Por qué el reporte actual sale casi todo en 0

El CSV se generó con **`runner_fallback=1.00`**: el runner no obtuvo respuestas LLM reales (API caída, timeout corto o sin API keys). En ese modo no hay `turn_observed` del servicio ni memoria real, por eso latencia, tokens, costo y recall quedan en 0.

**Acción bloqueante:** re-ejecutar stress con API levantada y credenciales válidas antes de reentregar.

---

## Plan de implementación (brechas pendientes)

### Fase A — Corrida real (bloqueante)

**Objetivo:** CSV y reporte con datos operativos, no fallback.

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

uv run python -m evals.stress.run \
  --http http://127.0.0.1:8000 \
  --scenarios growing,pivot,contradiction \
  --attachment-sizes 0,5,20,50,100 \
  --repeats 3 \
  --request-timeout-s 120 \
  --output evals/stress/results.csv
```

**Validación previa al reporte:**

- `runner_fallback` mayoritariamente `false`
- `latency_ms`, `tokens_in`, `cost_usd` > 0 en la mayoría de filas

**Esfuerzo estimado:** 0.5–1 día (config + una corrida completa).

---

### Fase B — Escenarios largos (N = 10 / 20)

**Objetivo:** Medir ruptura de memoria y coste en turno 20 (material).

| Tarea | Detalle |
|-------|---------|
| Extender `evals/stress/scenarios.py` | Variantes `growing_10`, `growing_20` o flag `--turn-counts 6,10,20` |
| Fact-tracker en `growing_20` | Repetir chequeo de `project name: Nimbus` en turnos 1, 10, 15, 20 |
| Runner | Selección de perfil por longitud |

**Viabilidad:** Sí — extensión directa.

---

### Fase C — Métricas alineadas al material

| Tarea | Descripción | Viabilidad |
|-------|-------------|------------|
| MemoryDrift diferida | Evaluar fact del turno `k` en turnos `k+1..N` | Sí |
| Recall de adjunto | Marcador fijo en PDF (`STRESS_MARKER_*`); buscar en `text` o `rolling_summary` | Sí |
| Columnas CSV | `memory_drift_lag`, `attachment_recall_score` | Sí |
| Semantic cache en sesiones | Implementar cache semántica en `/sessions/.../estimate` | **No recomendado** — altera baseline; documentar N/A en reporte |

---

### Fase D — Reporte automático desde CSV

**Objetivo:** `evals/stress/build_report.py` (o `run.py --write-report`) que genere `REPORT.md` con:

1. Tabla resumen por `scenario × attachment_size_kb`: P50/P95 latency, costo total, recall medio fact-tracker, cache hit rates (exact; semantic = N/A documentado).
2. Tres curvas en tabla: latency vs tokens_in; costo acumulado vs turn_index; MemoryDrift vs N.
3. Dos párrafos con ≥ 2 afirmaciones cuantitativas (ej. “a partir del turno N=12…”).

**Viabilidad:** Sí.

---

### Fase E — Endurecer runner

| Tarea | Detalle |
|-------|---------|
| `--allow-fallback` | Default `false`; fallback solo explícito |
| Fallar corrida | `exit != 0` si `runner_fallback_rate > 0.2` |
| (Opcional) `--in-process` | `TestClient` para CI sin red |

**Viabilidad:** Sí.

---

### Fase F — Documentación

- Mantener este archivo actualizado tras cada fase.
- `README.md` raíz: sección “Reproducir stress real” con prerequisitos (`.env`, Redis opcional para stateless).

---

## Qué NO implementar (justificación)

| Ítem | Decisión | Por qué |
|------|----------|---------|
| RAG completo | No | Material: ejercicio mide CAG, RAG es el directo |
| `data_catalog.yaml` + ingest multi-formato | No | Contenido teórico sesión 6 en vivo, no entregable pre |
| Optimizar CAG (bajar `MAX_CONVERSATION_TURNS`, etc.) | No | Invalida comparación del baseline |
| Comparación multi-proveedor | No | Fuera de scope |
| UI de visualización | No | Deliverable = CSV + Markdown |
| Semantic cache en sesiones (ahora) | No | No existe hoy; cambiaría mediciones sin baseline previo |

---

## Checklist de “hecho” (material)

- [x] Código `turn_observed` (13 campos)
- [x] Escenarios base + PDF builder + métricas + runner + tests unitarios
- [ ] Corrida end-to-end **real** (sin fallback masivo)
- [ ] Escenarios hasta N=20
- [ ] MemoryDrift en turnos posteriores (N > k)
- [ ] Recall de adjunto medido
- [ ] `REPORT.md` con tablas por escenario×tamaño y párrafos cuantitativos reales
- [ ] CSV con matriz recomendada: 3 escenarios × 5 tamaños × ≥ 3 repeticiones × N turnos

---

## Referencias

- Material: `../material/mat-sesion6.md` (ruta relativa al monorepo IAENG)
- Bitácora implementación: [`README.md`](./README.md)
- Artefactos: `evals/stress/results.csv`, `evals/stress/REPORT.md`
