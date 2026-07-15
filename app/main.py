from contextlib import asynccontextmanager
import logging

import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.agents import router as agent_router
from app.config import settings
from app.db.session import dispose_engine
from app.embedding_pipeline import router as embeddings_router
from app.embedding_pipeline.errors import DuplicateDocumentError
from app.embedding_pipeline.generation import router as rag_router
from app.graph import router as graph_router
from app.graph.build import build_graph
from app.graph.checkpointer import checkpoint_postgres_uri
from app.graph.observability import configure_logfire
from app.routers import estimations, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure logging, Logfire, and the LangGraph checkpointer."""
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

    configure_logfire()
    try:
        import logfire

        logfire.instrument_fastapi(app)
        logfire.instrument_httpx()
    except Exception:  # noqa: BLE001 — observability must not block startup
        structlog.get_logger(__name__).warning("logfire_instrumentation_skipped")

    pool = AsyncConnectionPool(
        conninfo=checkpoint_postgres_uri(),
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False,
    )
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    app.state.checkpoint_pool = pool
    app.state.estimation_graph = build_graph(checkpointer)

    yield

    await pool.close()
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
app.include_router(rag_router.router)
app.include_router(agent_router.router)
app.include_router(graph_router.router)


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
