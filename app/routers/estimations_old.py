from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.services.llm_service import estimate_project
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["estimations"])


# -------------------------
# Schemas
# -------------------------

class EstimationRequest(BaseModel):
    transcription: str


class EstimationResponse(BaseModel):
    estimation: str
    model: str
    provider: str
    timestamp: str


# -------------------------
# Endpoint
# -------------------------

@router.post("/estimate", response_model=EstimationResponse)
def generate_estimation(request: EstimationRequest):
    try:
        estimation = estimate_project(request.transcription)

        return EstimationResponse(
            estimation=estimation,
            model=settings.LLM_MODEL,
            provider=settings.LLM_PROVIDER,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

