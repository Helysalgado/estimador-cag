# Estimador CAG

Servicio API para generar estimaciones de proyectos de software a partir de una **transcripción de reunión**, usando Context-Augmented Generation (CAG) con un modelo de lenguaje (OpenAI).

## Tools / Stack

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?logo=openai&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-Server-2C3E50)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI-2088FF?logo=githubactions&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-1D63ED?logo=docker&logoColor=white)
![uv](https://img.shields.io/badge/uv-package_manager-DE5FE9)

## Requisitos

- Python 3.11+ ([`.python-version`](.python-version))
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip

## Configuración

```bash
cp .env.example .env
# Edita .env y define OPENAI_API_KEY para llamadas reales al modelo.
```

## Ejecución local

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Documentación interactiva: `http://localhost:8000/docs`
- Salud del servicio: `GET http://localhost:8000/health`
- Estimación: `POST http://localhost:8000/api/v1/estimate` con cuerpo JSON `{ "transcription": "..." }`

### Transcripción para el ejercicio

El texto de entrada del ejercicio vive en [`docs/transcripcion-reunion.md`](docs/transcripcion-reunion.md). Puedes copiar su contenido al campo `transcription` del endpoint o sustituir el archivo por la transcripción que indique el taller.

## Docker

```bash
docker compose build
docker compose up
```

Exporta `OPENAI_API_KEY` en el entorno si vas a llamar a OpenAI desde el contenedor.

## Validación automática (CI)

En cada push o pull request hacia `main`/`master`, GitHub Actions:

1. Instala dependencias con `uv sync --frozen --extra dev`
2. Ejecuta [`scripts/validate_structure.py`](scripts/validate_structure.py) (estructura mínima del repo)
3. Ejecuta `pytest`

### Ejecutar las mismas comprobaciones en local

```bash
uv sync --extra dev
uv run python scripts/validate_structure.py
uv run pytest
```

## Estructura esperada del repositorio

Se valida la presencia de `app/`, `tests/`, archivos Docker, configuración de Python y el script de validación. Detalle en `scripts/validate_structure.py`.

## Documentación adicional

- Convenciones para transcripciones: [`docs/README.md`](docs/README.md)
