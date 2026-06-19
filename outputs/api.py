from functools import lru_cache
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

app = FastAPI(
    title="Smart Traffic Prediction API",
    version="0.1.0",
    description="Predict road closure probability and event severity using saved models."
)

class TrafficEventFeatures(BaseModel):
    id: int = Field(..., description="Event identifier")
    event_type: int = Field(..., description="Encoded event type")
    latitude: float = Field(..., description="Latitude of the event")
    longitude: float = Field(..., description="Longitude of the event")
    endlatitude: float = Field(..., description="End latitude of the event")
    endlongitude: float = Field(..., description="End longitude of the event")
    address: int = Field(..., description="Encoded address feature")
    event_cause: int = Field(..., description="Encoded event cause")
    status: int = Field(..., description="Encoded status")
    authenticated: int = Field(..., description="Authenticated flag")
    modified_datetime: int = Field(..., description="Encoded modified datetime")
    description: int = Field(..., description="Encoded description")
    veh_type: int = Field(..., description="Encoded vehicle type")
    veh_no: int = Field(..., description="Encoded vehicle number")
    corridor: int = Field(..., description="Encoded corridor")
    priority: int = Field(..., description="Encoded priority label")
    created_date: int = Field(..., description="Encoded created date")
    client_id: int = Field(..., description="Client identifier")
    created_by_id: int = Field(..., description="Created by user identifier")
    last_modified_by_id: int = Field(..., description="Last modified by user identifier")
    police_station: int = Field(..., description="Encoded police station")
    kgid: int = Field(..., description="KGID feature")
    closed_by_id: int = Field(..., description="Closed by user identifier")
    closed_datetime: int = Field(..., description="Encoded closed datetime")
    gba_identifier: int = Field(..., description="Encoded GBA identifier")
    zone: int = Field(..., description="Encoded zone")
    junction: int = Field(..., description="Encoded junction")
    hour: int = Field(..., description="Event hour")
    day: int = Field(..., description="Event day")
    day_of_week: int = Field(..., description="Day of week")
    month: int = Field(..., description="Event month")
    weekend: int = Field(..., description="Weekend flag (0 or 1)")
    requires_road_closure: Optional[bool] = Field(
        None,
        description="Optional override value for road closure before severity prediction"
    )


@lru_cache(maxsize=1)
def load_models():
    try:
        road_model = joblib.load(MODELS_DIR / "road_closure_xgb.pkl")
        severity_model = joblib.load(MODELS_DIR / "severity_xgb.pkl")
        priority_encoder = joblib.load(MODELS_DIR / "priority_encoder.pkl")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Model file not found: {exc}")

    return road_model, severity_model, priority_encoder


def get_feature_names(model):
    if hasattr(model, "feature_names_in_"):
        return list(model.feature_names_in_)
    raise HTTPException(
        status_code=500,
        detail="Model does not expose feature names."
    )


@app.on_event("startup")
def startup_event():
    load_models()


@app.get("/")
def root():
    return {
        "status": "running",
        "prediction_endpoint": "/predict",
        "health_endpoint": "/health"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(event: TrafficEventFeatures):
    road_model, severity_model, priority_encoder = load_models()

    road_features = get_feature_names(road_model)
    severity_features = get_feature_names(severity_model)

    event_data = event.dict()
    road_input = np.array(
        [[event_data[name] for name in road_features]],
        dtype=float
    )

    road_prob = float(
        road_model.predict_proba(road_input)[0][1]
    )

    requires_road_closure = (
        int(event_data["requires_road_closure"])
        if event_data["requires_road_closure"] is not None
        else int(road_prob >= 0.5)
    )

    severity_input_values = {
        **event_data,
        "requires_road_closure": requires_road_closure
    }

    severity_input = np.array(
        [[severity_input_values[name] for name in severity_features]],
        dtype=float
    )

    severity_pred = int(severity_model.predict(severity_input)[0])
    severity_label = priority_encoder.inverse_transform([severity_pred])[0]

    return {
        "road_closure_probability": road_prob,
        "requires_road_closure": bool(requires_road_closure),
        "severity_prediction": severity_pred,
        "severity_label": severity_label
    }
