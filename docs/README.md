# Transcripciones de reunión (ejercicio)

Este directorio guarda el material de texto que sirve de **entrada** para la estimación.

## Archivo principal del ejercicio

- **`transcripcion-reunion.md`**: transcripción de ejemplo (o la que asigne el instructor). Es la referencia por defecto mencionada en el README del proyecto.

## Formato recomendado

- Markdown o texto plano.
- Incluir contexto suficiente: objetivo del producto, usuarios, integraciones, plazos mencionados y restricciones.
- No incluir datos personales reales; usa datos ficticios si el ejercicio lo requiere.

## Cómo usarla con la API

Envía el contenido completo (o un extracto representativo) como JSON:

```json
{
  "transcription": "Pega aquí el texto de transcripcion-reunion.md"
}
```

al endpoint `POST /api/v1/estimate`.
