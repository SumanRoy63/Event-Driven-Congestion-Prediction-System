from fastapi import APIRouter
from src.api.schemas.event import RecommendationRequest
from src.api.schemas.response import RecommendationResponse
from src.api.services.recommendation_service import generate_recommendation

router = APIRouter()

@router.post("/recommendations", response_model=RecommendationResponse)
def get_recommendation(payload: RecommendationRequest):
    """
    Generate actionable traffic and resource recommendations
    based on prediction severity, closure probability, and hotspot rank.
    """
    recommendation = generate_recommendation(
        severity=payload.severity,
        closure_prob=payload.road_closure_probability,
        hotspot_rank=payload.hotspot_rank
    )
    
    return recommendation
