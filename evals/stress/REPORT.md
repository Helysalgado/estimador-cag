# Stress Evaluation Report

Dataset source: `evals/stress/results.csv`  
Rows analyzed: 54 (3 scenarios x 3 attachment sizes x 1 repeat x 6 turns)

## Summary Table

| Metric | Value |
|---|---:|
| P50 latency (ms) | 0.0 |
| P95 latency (ms) | 0.0 |
| Cumulative cost (USD) | 0.0000 |
| Cache hit rate (`exact` + `semantic`) | 0.00 |
| Mean fact-tracker recall | 0.00 |
| Runner fallback rate | 1.00 |

## Curve 1 — `latency_ms` vs `tokens_in`

| tokens_in | avg_latency_ms |
|---:|---:|
| 0 | 0.0 |

## Curve 2 — `cost_usd acumulado` vs `turn_index`

| turn_index | cumulative_cost_usd |
|---:|---:|
| 1 | 0.0000 |
| 2 | 0.0000 |
| 3 | 0.0000 |
| 4 | 0.0000 |
| 5 | 0.0000 |
| 6 | 0.0000 |

## Curve 3 — `MemoryDriftMetric` vs `N`

| N (turn_index) | mean_memory_drift |
|---:|---:|
| 1 | 0.00 |
| 2 | 0.00 |
| 3 | 0.00 |
| 4 | 0.00 |
| 5 | 0.00 |
| 6 | 0.00 |

The stress run completed successfully and generated the required CSV artifacts. Quantitatively, all observed latency/cost/tokens measurements remained at zero and memory recall stayed at 0.00 because every row was recorded using runner fallback mode (`runner_fallback=1.00`), which indicates the API did not return normal LLM-backed turn observations during this capture window.

Given the 100% fallback rate, the resulting curves behave as flat baselines instead of production-like growth curves. The pipeline itself (scenario loop, attachment-size sweep, metric computation, and CSV generation) is reproducible and operational; to obtain meaningful operational numbers, rerun `python -m evals.stress.run` with a reachable API plus valid model credentials so `turn_observed` fields are emitted by the service path.
