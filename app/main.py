from fastapi import FastAPI

from app.routers import estimations


app = FastAPI(
    title="Estimador CAG API",
    description=(
        "API para generar estimaciones de proyectos de software utilizando "
        "Context-Augmented Generation (CAG) con modelos de lenguaje."
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


