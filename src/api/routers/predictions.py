from fastapi import APIRouter
from src.api.schemas.event import EventRequest
from src.api.schemas.response import PredictionResponse
from src.api.services.prediction_service import preprocess_event, predict_event
from src.api.services.model_manager import get_models_for_date

router = APIRouter()

@router.post("/predictions", response_model=PredictionResponse)
def get_prediction(payload: EventRequest):
    """
    Get only the machine learning prediction (Road Closure Probability and Severity) 
    for a given event, without the recommendation or hotspot logic.
    """
    # Fetch appropriate models based on event date
    models = get_models_for_date(payload.start_datetime)
    
    # Build Features
    features_df = preprocess_event(payload.dict(), models["categorical_encoders"])
    
    # Predict
    prediction = predict_event(features_df, models)
    
    return prediction
