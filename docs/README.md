# Documentación del proyecto

## Planes de implementación

- Sesión 4 (formulario tipado + prompts Jinja2):
  - **[`plans/session-04/`](./plans/session-04/README.md)**

- Sesión 5 (memoria conversacional + adjuntos):
  - **[`plans/session-05/`](./plans/session-05/README.md)**

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
