from fastapi import FastAPI

from app.routers import estimations


app = FastAPI(
    title="Estimador CAG API",
    description=(
        "API para estimar proyectos de software desde un formulario tipado. "
        "Prompts versionados en Jinja2; respuesta en texto libre."
    ),
    version="0.1.0"
)


# -------------------------
# Routers
# -------------------------

app.include_router(estimations.router)


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


