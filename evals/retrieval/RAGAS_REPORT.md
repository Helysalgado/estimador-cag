# RAGAS report — Session 11

Evaluation of grounded RAG estimates (`POST /api/v1/rag/estimate`) against `evals/retrieval/golden_set.json` (`ground_truth`).

- Generation model: `gpt-4o-mini`
- Judge model: `gpt-4o-mini`
- Embeddings (RAGAS): `text-embedding-3-small`
- Retrieval: `search_mode=hybrid`, `rerank=false`, `k=5`

| Query | Faithfulness | Answer relevancy | Context precision | Context recall | Citation OK |
|-------|-------------:|-----------------:|------------------:|---------------:|:-----------:|
| q01 | 1.000 | 0.605 | 1.000 | 0.667 | yes |
| q02 | 0.600 | 0.430 | 1.000 | 0.500 | yes |
| q03 | 0.750 | 0.527 | 0.833 | 0.750 | yes |
| q04 | 0.250 | 0.131 | 1.000 | 0.500 | yes |
| q05 | 1.000 | 0.418 | 0.679 | 0.500 | yes |
| **Average** | 0.720 | 0.422 | 0.902 | 0.583 | — |

## Note

Context precision is strong (~0.90): hybrid top-5 usually lands on the right ecommerce/healthcare budgets. Answer relevancy is weaker (~0.42) because structured line items + explicit ungrounded gaps (subscriptions, loyalty) score lower than a fluent prose answer against long `ground_truth` texts. q04 faithfulness dipped (0.25) despite citation_ok — HIPAA lines can drift from retrieved wording while still citing valid chunk ids. `verify_citations` passed on all five queries.
