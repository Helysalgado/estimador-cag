# routers/estimations.py
from fastapi import APIRouter

from app.schemas.estimation import EstimationRequest, EstimationResponse
from app.services.llm_service import estimate_project

router = APIRouter(prefix="/api/v1", tags=["estimations"])


@router.post("/estimate", response_model=EstimationResponse)
def estimate(request: EstimationRequest):
    result = estimate_project(request.transcription)
    return result

