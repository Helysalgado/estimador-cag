from contextlib import asynccontextmanager
import logging

import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.session import dispose_engine
from app.embedding_pipeline import router as embeddings_router
from app.embedding_pipeline.errors import DuplicateDocumentError
from app.routers import estimations, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure structured logging once per process."""
    structlog.reset_defaults()
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ]
    if settings.APP_ENV == "development":
        processors.append(structlog.dev.ConsoleRenderer(colors=False))
    else:
        processors.append(structlog.processors.JSONRenderer())
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    yield
    await dispose_engine()


app = FastAPI(
    title="Estimador CAG API",
    description=(
        "API para estimar proyectos de software desde un formulario tipado. "
        "Prompts versionados en Jinja2; respuesta en texto libre."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(DuplicateDocumentError)
async def duplicate_document_handler(_request, exc: DuplicateDocumentError):
    return JSONResponse(
        status_code=409,
        content={
            "detail": "Document already ingested",
            "document_id": exc.document_id,
        },
    )


# -------------------------
# Routers
# -------------------------

app.include_router(estimations.router)
app.include_router(sessions.router)
app.include_router(embeddings_router.router)
app.include_router(embeddings_router.material_router)
app.include_router(embeddings_router.search_router)
app.include_router(embeddings_router.material_search_router)


# -------------------------
# Health check
# -------------------------


@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "service": "estimador-cag",
        "version": "0.1.0",
    }
