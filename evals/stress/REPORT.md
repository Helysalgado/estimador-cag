# Stress Evaluation Report

Dataset source: `evals/stress/results.csv`  
Rows in file: 454 (after dedupe: 150 successful turns, 4 errors)  

## Data quality notes

- CSV **sin fila de cabecera** detectada; columnas inferidas por el generador.
- Corrida **incompleta**: turno máximo observado = **6** (objetivo del ejercicio: 20 por sesión).
- Escenarios ausentes en los datos: **contradiction**.
- Se deduplicaron filas repetidas del mismo `(scenario, kb, repeat, turn_index)`.

## Summary Table

| Metric | Value |
|---|---:|
| P50 latency (ms) | 4706 |
| P95 latency (ms) | 12445 |
| Cumulative cost (USD) | 0.6264 |
| Cache hit rate (`exact` + `semantic`) | 0.00 |
| Mean fact-tracker recall (drift, turns > 1) | 0.40 |
| Error rows | 4 |

### By scenario × attachment size (KB)

| scenario | kb | n | P50 ms | P95 ms | total $ | drift % |
|---|---:|---:|---:|---:|---:|---:|
| growing | 5 | 18 | 5400 | 9217 | 0.0487 | 0.0 |
| growing | 20 | 18 | 5183 | 15016 | 0.0985 | 0.0 |
| growing | 50 | 18 | 5117 | 11507 | 0.0985 | 0.0 |
| growing | 100 | 18 | 5390 | 11663 | 0.0989 | 0.0 |
| pivot | 0 | 18 | 3326 | 3844 | 0.0063 | 0.0 |
| pivot | 5 | 18 | 3902 | 5667 | 0.0477 | 100.0 |
| pivot | 20 | 18 | 5360 | 13206 | 0.0977 | 100.0 |
| pivot | 50 | 18 | 4845 | 9341 | 0.0976 | 100.0 |
| pivot | 100 | 6 | 4519 | 5483 | 0.0324 | 100.0 |

## Curve 1 — `latency_ms` vs `tokens_in`

| tokens_in (bucket) | avg_latency_ms | n |
|---:|---:|---:|
| 0 | 3337.2 | 18 |
| 5000 | 4241.2 | 12 |
| 10000 | 3907.9 | 22 |
| 15000 | 4476.0 | 22 |
| 20000 | 5550.3 | 6 |
| 25000 | 5657.6 | 16 |
| 30000 | 8275.0 | 6 |
| 35000 | 6102.7 | 16 |
| 45000 | 7216.2 | 16 |
| 65000 | 11180.9 | 16 |

## Curve 2 — cumulative `cost_usd` vs `turn_index`

| turn_index | mean_cumulative_cost_usd | n_sessions |
|---:|---:|---:|
| 1 | 0.001289 | 25 |
| 2 | 0.003662 | 25 |
| 3 | 0.007107 | 25 |
| 4 | 0.011618 | 25 |
| 5 | 0.017194 | 25 |
| 6 | 0.025057 | 25 |

## Curve 3 — `MemoryDriftMetric` vs turn index

| turn_index | mean_memory_drift | n |
|---:|---:|---:|
| 2 | 0.40 | 25 |
| 3 | 0.40 | 25 |
| 4 | 0.40 | 25 |
| 5 | 0.40 | 25 |
| 6 | 0.40 | 25 |

## Quantitative findings

Con **150** turnos medidos (deduplicados), la latencia P50 global fue **4706 ms** y P95 **12445 ms**. El coste acumulado registrado en el CSV suma **$0.6264**. Los `tokens_in` medios pasan de **7961** en el turno 1 a **51557** en el turno 6, coherente con el crecimiento del contexto en ventana deslizante.

Comparando turno 1 vs turno 6, la latencia media sube **2.8×** (3455 ms → 9634 ms) y el coste por turno **6.1×** ($0.0013 → $0.0079). El recall del fact-tracker (`memory_drift_passed` en turnos > 1) promedia **40.0%**; en sesiones conversacionales el cache permanece en `none` (tasa de hit **0.0%**), como esperado para el baseline CAG sin cache semántica en sesiones.

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

