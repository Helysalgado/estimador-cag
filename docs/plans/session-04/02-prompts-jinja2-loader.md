# Paso 2 — Prompts Jinja2 y loader

> **Depende de:** Paso 1 (schemas).  
> **Siguiente:** Paso 3 (endpoint y servicio).

## Objetivo

Sacar el prompt del código Python y versionarlo en templates Jinja2 bajo `app/prompts/estimation/v1/`.

## Archivos a crear

```text
app/prompts/
├── loader.py
└── estimation/
    └── v1/
        ├── system.j2
        ├── user.j2
        └── examples.j2
```

## Archivos a modificar

| Archivo | Acción |
|---------|--------|
| `pyproject.toml` | Añadir dependencia explícita `jinja2>=3.1` |

## Implementación detallada

### 2.1 `loader.py`

- `Environment` con `FileSystemLoader` apuntando a `app/prompts/`
- `undefined=StrictUndefined`
- `trim_blocks=True`, `lstrip_blocks=True`
- Función pública:

```python
def render_estimation_prompt(
    request: EstimationRequest,
    version: str = "v1",
) -> tuple[str, str]:
    ...
    return system, user
```

- Contexto de render: `description`, `project_type`, `detail_level`, `output_format` (valores `.value` de enums).

### 2.2 `system.j2`

Debe incluir:

- Rol del modelo (estimador senior).
- Reglas generales (moneda, fases, conservadurismo — alinear con [referencia LIDR](https://github.com/LIDR-academy/ai-engineering/blob/session_4/estimator/app/prompts/estimation/v1/system.j2)).
- Bloque condicional `{% if output_format == "phases_table" %}` … `line_items` … `narrative`.
- Bloque condicional `{% if detail_level == "summary" %}` … `medium` … `detailed` (en `detailed`: asunciones por fase + riesgos).
- `{% include "estimation/v1/examples.j2" %}`

Incluir palabra clave identificable para tests, p. ej. `phases_table` o `confidence_pct` en rama `phases_table`.

### 2.3 `user.j2`

- Envolver la descripción en `<project_description>...</project_description>` (requerido por tests de sesión).
- Mencionar `project_type`.

### 2.4 `examples.j2`

- 2–3 few-shots plausibles (proyectos inventados, no copiar enunciado).
- Puedes inspirarte en `app/context/examples.py` pero reescribir en inglés y al nuevo formato.

## Tareas

- [x] Crear estructura de carpetas
- [x] Implementar `loader.py`
- [x] Escribir los tres `.j2` (alineados con LIDR session_4)
- [x] `uv add jinja2` + lock actualizado

## Verificación (sin LLM)

```bash
uv run python -c "
from app.schemas.estimation import *
from app.prompts.loader import render_estimation_prompt
req = EstimationRequest(
    description='Test project for equipment tracking.',
    project_type=ProjectType.WEB_SAAS,
    detail_level=DetailLevel.DETAILED,
    output_format=OutputFormat.PHASES_TABLE,
)
s, u = render_estimation_prompt(req)
assert 'Test project for equipment tracking.' in u
assert '<project_description>' in u
assert 'phases_table' in s or 'confidence_pct' in s
print('OK', len(s), len(u))
"
```

## Qué NO hacer en este paso

- No conectar aún el router ni `llm_service`.
- No borrar aún `app/context/examples.py` (Paso 3 o 6).

## Antes de continuar

Confirma: **“Podemos continuar con el Paso 3 (endpoint y servicio)”** cuando el render manual pase.
