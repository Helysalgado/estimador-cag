# Documentación del proyecto

## Planes de implementación

- Sesión 4 (formulario tipado + prompts Jinja2):
  - **[`plans/session-04/`](./plans/session-04/README.md)** — plan de implementación
  - **[`plans/session-04/AJUSTES.md`](./plans/session-04/AJUSTES.md)** — cumplimiento vs LIDR y ajustes opcionales

- Sesión 5 (memoria conversacional + adjuntos):
  - **[`plans/session-05/`](./plans/session-05/README.md)** — plan de implementación
  - **[`plans/session-05/CUMPLIMIENTO.md`](./plans/session-05/CUMPLIMIENTO.md)** — cumplimiento vs material y LIDR S5

- Sesión 6 (stress CAG + observabilidad por turno):
  - **[`plans/session-06/`](./plans/session-06/README.md)** — bitácora de implementación
  - **[`plans/session-06/GAP-ANALISIS.md`](./plans/session-06/GAP-ANALISIS.md)** — cumplimiento vs material
  - **[`plans/session-06/PLAN-IMPLEMENTACION.md`](./plans/session-06/PLAN-IMPLEMENTACION.md)** — qué falta implementar (vs LIDR S6)

- Sesión 7 (embeddings + chunking estructural):
  - **[`plans/session-07/`](./plans/session-07/README.md)** — índice
  - **[`plans/session-07/PLAN-IMPLEMENTACION.md`](./plans/session-07/PLAN-IMPLEMENTACION.md)** — plan detallado (material `mat-sesion7.md`)
  - **[`plans/session-07/GAP-ANALISIS.md`](./plans/session-07/GAP-ANALISIS.md)** — cumplimiento vs material

- Sesión 8 (pgvector + búsqueda semántica):
  - **[`plans/session-08/`](./plans/session-08/README.md)** — índice pre-ejercicio
  - **[`plans/session-08/PLAN-IMPLEMENTACION.md`](./plans/session-08/PLAN-IMPLEMENTACION.md)** — plan detallado (material `sesion8.md`)
  - **[`plans/session-08/GAP-ANALISIS.md`](./plans/session-08/GAP-ANALISIS.md)** — cumplimiento vs material

- Sesión 10 (híbrida + reranking + medición):
  - **[`plans/session-10/`](./plans/session-10/README.md)** — índice pre-ejercicio
  - **[`plans/session-10/PLAN-IMPLEMENTACION.md`](./plans/session-10/PLAN-IMPLEMENTACION.md)** — plan detallado (material `mat-sesion10.md`)
  - **[`plans/session-10/GAP-ANALISIS.md`](./plans/session-10/GAP-ANALISIS.md)** — cumplimiento vs material

- Sesión 11 (generación grounded + RAGAS):
  - **[`plans/session-11/`](./plans/session-11/README.md)** — índice pre-ejercicio
  - **[`plans/session-11/PLAN-IMPLEMENTACION.md`](./plans/session-11/PLAN-IMPLEMENTACION.md)** — plan detallado (material `mat-sesion11.md`)
  - **[`plans/session-11/GAP-ANALISIS.md`](./plans/session-11/GAP-ANALISIS.md)** — cumplimiento vs material

- Sesión 12 (agente + tools):
  - **[`plans/session-12/`](./plans/session-12/README.md)** — índice pre-ejercicio
  - **[`plans/session-12/PLAN-IMPLEMENTACION.md`](./plans/session-12/PLAN-IMPLEMENTACION.md)** — plan detallado (material `mat-sesion12.md`)
  - **[`plans/session-12/GAP-ANALISIS.md`](./plans/session-12/GAP-ANALISIS.md)** — cumplimiento vs material

- Sesión 13 (orquestación LangGraph):
  - **[`plans/session-13/`](./plans/session-13/README.md)** — índice pre-ejercicio
  - **[`plans/session-13/EXPLICACION-ENTREGA.md`](./plans/session-13/EXPLICACION-ENTREGA.md)** — qué se implementó (explicación para el profesor)
  - **[`plans/session-13/PLAN-IMPLEMENTACION.md`](./plans/session-13/PLAN-IMPLEMENTACION.md)** — plan N1–N3 (material `mat-sesion13.md`)
  - **[`plans/session-13/GAP-ANALISIS.md`](./plans/session-13/GAP-ANALISIS.md)** — cumplimiento vs material

## Texto de entrada de ejemplo

- **`transcripcion-reunion.md`**: reunión ficticia con un cliente. Puedes pegar su contenido en el campo **`description`** del formulario Streamlit o del body JSON del API (mínimo 20 caracteres, máximo 80.000).

### Ejemplo de body JSON

```json
{
  "description": "Pega aquí el contenido de transcripcion-reunion.md",
  "project_type": "web_saas",
  "detail_level": "medium",
  "output_format": "phases_table"
}
```

Endpoint: `POST http://localhost:8000/api/v1/estimate`

## Formato recomendado para `description`

- Objetivo del producto, usuarios, funcionalidades clave.
- Integraciones, restricciones y plazos mencionados.
- Datos ficticios si el ejercicio lo requiere (sin PII real).
