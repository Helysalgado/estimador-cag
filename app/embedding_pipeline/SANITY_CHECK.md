# Sanity check — embeddings (Sesión 7)

Ejecutado con:

```bash
uv run python scripts/compare.py --text-a "..." --text-b "..."
```

Modelo: `text-embedding-3-small`. Fecha de la corrida: 2026-06-03.

## Resultados

| Pareja | Texto A (resumen) | Texto B (resumen) | Similitud coseno | Expectativa orientativa |
|--------|-------------------|-------------------|------------------|-------------------------|
| **A** (cercanos) | OAuth 2.0 + JWT fintech | Authorization + JWT banking | **0.5957** | Alta (> 0.6) |
| **B** (lejanos) | OAuth 2.0 + JWT fintech | Migración MySQL → PostgreSQL | **0.1920** | Baja (< 0.4) |
| **C** (ambiguos) | Backend services | API development | **0.5406** | Sin expectativa fija |

### Pareja A

- Texto 1: `OAuth 2.0 authentication backend with JWT tokens for fintech mobile app`
- Texto 2: `Authorization service using JSON Web Tokens for a banking application`
- **Cosine similarity: 0.5957**

### Pareja B

- Texto 1: (igual que A)
- Texto 2: `Database migration from MySQL to PostgreSQL with zero downtime`
- **Cosine similarity: 0.1920**

### Pareja C

- Texto 1: `Backend services`
- Texto 2: `API development`
- **Cosine similarity: 0.5406**

## Comentario

La pareja **B** separa bien dominios distintos (autenticación vs migración de base de datos), muy por debajo del umbral orientativo de 0.4. La pareja **A** queda en la frontera alta (~0.60): comparten OAuth/JWT y contexto fintech/banca, pero la redacción difiere; un umbral estricto de 0.6 fallaría por poco, lo cual es razonable para un sanity check manual.

La pareja **C** sorprende un poco: con textos tan genéricos la similitud (~0.54) es casi tan alta como la pareja A. Eso sugiere que frases cortas y vagas colapsan en una región densa del espacio semántico (“desarrollo backend/API”) y no discriminan tan bien como descripciones ricas. Será buen tema en vivo para chunking con más contexto (cabeceras del presupuesto) y para no confiar en embeddings de una sola línea sin metadata.
