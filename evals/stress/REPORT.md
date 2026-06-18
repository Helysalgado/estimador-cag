# Stress Evaluation Report

Dataset source: `evals/stress/results.csv`  
Rows in file: 20 (after dedupe: 6 successful turns, 0 errors)  

## Data quality notes

- CSV **sin fila de cabecera** detectada; columnas inferidas por el generador.
- Corrida **incompleta**: turno máximo observado = **6** (objetivo del ejercicio: 20 por sesión).
- Escenarios ausentes en los datos: **contradiction, growing**.
- Se deduplicaron filas repetidas del mismo `(scenario, kb, repeat, turn_index)`.

## Summary Table

| Metric | Value |
|---|---:|
| P50 latency (ms) | 3122 |
| P95 latency (ms) | 3760 |
| Cumulative cost (USD) | 0.0023 |
| Cache hit rate (`exact` + `semantic`) | 0.00 |
| Mean fact-tracker recall (drift, turns > 1) | 0.00 |
| Error rows | 0 |

### By scenario × attachment size (KB)

| scenario | kb | n | P50 ms | P95 ms | total $ | drift % |
|---|---:|---:|---:|---:|---:|---:|
| pivot | 0 | 6 | 3122 | 3760 | 0.0023 | 0.0 |

## Curve 1 — `latency_ms` vs `tokens_in`

| tokens_in (bucket) | avg_latency_ms | n |
|---:|---:|---:|
| 0 | 3321.7 | 6 |

## Curve 2 — cumulative `cost_usd` vs `turn_index`

| turn_index | mean_cumulative_cost_usd | n_sessions |
|---:|---:|---:|
| 1 | 0.000262 | 1 |
| 2 | 0.000567 | 1 |
| 3 | 0.000901 | 1 |
| 4 | 0.001264 | 1 |
| 5 | 0.001656 | 1 |
| 6 | 0.002269 | 1 |

## Curve 3 — `MemoryDriftMetric` vs turn index

| turn_index | mean_memory_drift | n |
|---:|---:|---:|
| 2 | 0.00 | 1 |
| 3 | 0.00 | 1 |
| 4 | 0.00 | 1 |
| 5 | 0.00 | 1 |
| 6 | 0.00 | 1 |

## Quantitative findings

Con **6** turnos medidos (deduplicados), la latencia P50 global fue **3122 ms** y P95 **3760 ms**. El coste acumulado registrado en el CSV suma **$0.0023**. Los `tokens_in` medios pasan de **1090** en el turno 1 a **3419** en el turno 6, coherente con el crecimiento del contexto en ventana deslizante.

Comparando turno 1 vs turno 6, la latencia media sube **0.7×** (3760 ms → 2504 ms) y el coste por turno **2.3×** ($0.0003 → $0.0006). El recall del fact-tracker (`memory_drift_passed` en turnos > 1) promedia **0.0%**; en sesiones conversacionales el cache permanece en `none` (tasa de hit **0.0%**), como esperado para el baseline CAG sin cache semántica en sesiones.

## Follow-up

Para un entregable completo del pre-ejercicio S6, re-ejecutar:

```bash
uv run python -m evals.stress.run \
  --http http://127.0.0.1:8000 \
  --scenarios growing,pivot,contradiction \
  --attachment-sizes 0,5,20,50,100 \
  --repeats 3 \
  --output evals/stress/results.csv

uv run python -m evals.stress.build_report
```

