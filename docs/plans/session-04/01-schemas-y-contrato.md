# Paso 1 — Schemas y contrato API

> **Depende de:** Paso 0 (decisiones cerradas).  
> **Siguiente:** Paso 2 (prompts Jinja2).

## Objetivo

Definir el contrato entre cliente y servicio con **Pydantic v2**: enums + `EstimationRequest` + `EstimationResponse`.

## Archivos a modificar

| Archivo | Acción |
|---------|--------|
| `app/schemas/estimation.py` | Reemplazar modelos actuales |

## Implementación detallada

### 1.1 Enums

```python
class ProjectType(str, Enum):
    MOBILE_APP = "mobile_app"
    WEB_SAAS = "web_saas"
    INTERNAL_TOOL = "internal_tool"
    DATA_PIPELINE = "data_pipeline"

class DetailLevel(str, Enum):
    SUMMARY = "summary"
    MEDIUM = "medium"
    DETAILED = "detailed"

class OutputFormat(str, Enum):
    PHASES_TABLE = "phases_table"
    LINE_ITEMS = "line_items"
    NARRATIVE = "narrative"
```

### 1.2 Request

```python
class EstimationRequest(BaseModel):
    description: str = Field(min_length=20, max_length=...)  # ver D1 en paso 0
    project_type: ProjectType
    detail_level: DetailLevel
    output_format: OutputFormat
```

### 1.3 Response

```python
class EstimationResponse(BaseModel):
    text: str
    prompt_version: str
```

### 1.4 Breaking change

- Eliminar `transcription` del schema público.
- Cualquier import de `EstimationRequest` en router/tests/streamlit **fallará** hasta actualizarse en pasos posteriores; es esperado tras este paso.

## Tareas

- [x] Añadir enums y nuevos modelos en `app/schemas/estimation.py`
- [x] Docstrings breves (opcional, como referencia LIDR)
- [x] No tocar aún router ni `llm_service` (quedan rotos temporalmente — esperado)

## Verificación

```bash
uv run python -c "
from app.schemas.estimation import EstimationRequest, ProjectType, DetailLevel, OutputFormat
r = EstimationRequest(
    description='A small B2B SaaS for equipment loans across teams.',
    project_type=ProjectType.WEB_SAAS,
    detail_level=DetailLevel.MEDIUM,
    output_format=OutputFormat.PHASES_TABLE,
)
print(r.model_dump())
"
```

- [ ] Request válido se construye sin error
- [ ] `description` con menos de 20 caracteres lanza `ValidationError`

## Riesgos

- Tests y router seguirán rotos hasta Pasos 3–5; no ejecutar `pytest` completo como criterio de éxito **solo** de este paso.

## Antes de continuar

Confirma: **“Podemos continuar con el Paso 2 (prompts Jinja2)”** cuando el schema esté en el repo y la verificación manual pase.
