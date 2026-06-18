# Plan de implementación — Sesión 06 (pre-session-06)

Este documento registra el plan **ejecutado en código** para llevar `estimador-cag` a paridad técnica del pre-ejercicio en la rama `pre-session-06`.

- Análisis de brechas: **[GAP-ANALISIS.md](./GAP-ANALISIS.md)**
- **Plan de lo pendiente (implementar):** **[PLAN-IMPLEMENTACION.md](./PLAN-IMPLEMENTACION.md)**

## Objetivo

Extender el flujo conversacional con observabilidad por turno, stress evals reproducibles, métricas de presupuesto/memoria y artefactos finales (`results.csv` y `REPORT.md`).

## Plan ejecutado

### Fase 0 — Rama y baseline

- Crear rama `pre-session-06`.
- Ejecutar baseline de tests antes de cambios.

### Fase 1 — Evento agregado `turn_observed`

- Emitir 1 evento estructurado por turno con 13 campos:
  - `turn_index`
  - `session_id`
  - `enriched_transcript_chars`
  - `attachments_total_chars`
  - `messages_in_window`
  - `anchors_count`
  - `summary_chars`
  - `tokens_in`
  - `tokens_out`
  - `cost_usd`
  - `latency_ms`
  - `cache_hit_kind`
  - `last_resolved_tier`
- Exponer último evento en snapshot debug de sesión.

### Fase 2 — Escenarios y fixtures PDF

- Crear `evals/stress/scenarios.py` con perfiles:
  - `growing`
  - `pivot`
  - `contradiction`
- Incluir `fact_to_remember` por turno para medir memoria.
- Crear builder determinístico `evals/stress/fixtures/build_pdfs.py` para:
  - `attach_5kb.pdf`
  - `attach_20kb.pdf`
  - `attach_50kb.pdf`
  - `attach_100kb.pdf`
- Los binarios se regeneran; no se versionan en fixtures.

### Fase 3 — Métricas nuevas + tests

- Implementar:
  - `LatencyBudgetMetric`
  - `CostBudgetMetric`
  - `MemoryDriftMetric`
- Definir/usar contrato común `MetricResult`.
- Añadir pruebas en `tests/test_stress_metrics.py` (pass/fail/límite por métrica).

### Fase 4 — Runner de stress end-to-end

- Implementar `evals/stress/run.py` con CLI:
  - `--http`
  - `--scenarios`
  - `--attachment-sizes`
  - `--repeats`
  - `--output`
- Flujo por corrida:
  - crear sesión,
  - ejecutar turnos de escenario,
  - adjuntar PDF según tamaño,
  - recolectar observación de turno + snapshot sesión,
  - evaluar métricas,
  - exportar CSV (1 fila por turno).

### Fase 5 — Reporte y cierre

- Generar `evals/stress/results.csv` (>= 50 filas).
- Redactar `evals/stress/REPORT.md` con:
  - tabla resumen,
  - curvas tabulares,
  - lectura cuantitativa de resultados.

## Criterios de done (alcanzados)

- `POST /sessions/{id}/estimate` emite `turn_observed` completo.
- `python -m evals.stress.run` genera CSV válido.
- `tests/test_stress_metrics.py` pasa.
- Artefactos de entrega presentes:
  - `evals/stress/results.csv`
  - `evals/stress/REPORT.md`

## Checklist de progreso

- [x] Paso 0 — Rama y baseline
- [x] Paso 1 — `turn_observed` agregado
- [x] Paso 2 — Escenarios + fact-tracker
- [x] Paso 3 — Builder PDF determinístico
- [x] Paso 4 — Métricas + tests
- [x] Paso 5 — Runner stress + CSV
- [x] Paso 6 — Reporte final
