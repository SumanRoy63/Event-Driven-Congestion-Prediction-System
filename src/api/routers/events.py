from fastapi import APIRouter
from src.api.schemas.event import EventRequest
from src.api.schemas.response import EventResponse
from src.api.services.prediction_service import preprocess_event, predict_event
from src.api.services.model_manager import get_models_for_date
from src.api.services.hotspot_service import determine_hotspot_rank
from src.api.services.recommendation_service import generate_recommendation

router = APIRouter()

@router.post("/events", response_model=EventResponse)
def create_event(payload: EventRequest):
    # 1. Evaluate Hotspot Rank internally
    hotspot_info = determine_hotspot_rank(payload.latitude, payload.longitude)
    
    # 2. Fetch appropriate models based on event date
    models = get_models_for_date(payload.start_datetime)
    
    # 3. Build Features
    features_df = preprocess_event(payload.dict(), models["categorical_encoders"])
    
    # 4. Predict Severity and Road Closure Probability
    prediction = predict_event(features_df, models)
    
    # 5. Generate Recommendation
    recommendation = generate_recommendation(
        severity=prediction["severity"],
        closure_prob=prediction["road_closure_probability"],
        hotspot_rank=hotspot_info["rank"]
    )
    
    return {
        "prediction": prediction,
        "recommendation": recommendation,
        "hotspot_info": hotspot_info
    }
