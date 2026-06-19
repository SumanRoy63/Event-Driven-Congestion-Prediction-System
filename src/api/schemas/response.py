from pydantic import BaseModel
from typing import Dict, Any

class PredictionResponse(BaseModel):
    road_closure_probability: float
    severity: str

class RecommendationResponse(BaseModel):
    alert_level: str
    traffic_officers: int
    barricades: str
    risk_score: float

class EventResponse(BaseModel):
    prediction: PredictionResponse
    recommendation: RecommendationResponse
    hotspot_info: Dict[str, Any]
