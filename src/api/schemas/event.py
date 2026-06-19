from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class EventRequest(BaseModel):
    event_type: str = Field(..., description="Type of event (e.g., Political Rally, Accident)")
    latitude: float = Field(..., description="Starting latitude")
    longitude: float = Field(..., description="Starting longitude")
    start_datetime: datetime = Field(default_factory=datetime.utcnow, description="When the event starts")
    
    # Optional fields with defaults to match your dataset
    endlatitude: float = 0.0
    endlongitude: float = 0.0
    address: str = "Unknown"
    event_cause: str = "Unknown"
    status: int = 1
    authenticated: int = 1
    description: str = ""
    veh_type: str = "Unknown"
    veh_no: str = "Unknown"
    corridor: str = "Unknown"
    client_id: int = 1
    created_by_id: int = 1
    last_modified_by_id: int = 1
    police_station: str = "Unknown"
    kgid: str = "Unknown"
    closed_by_id: int = 0
    gba_identifier: str = "Unknown"
    zone: str = "Unknown"
    junction: str = "Unknown"

    class Config:
        extra = "allow"

class RecommendationRequest(BaseModel):
    severity: str = Field(..., description="Predicted severity level (e.g., High, Medium, Low)")
    road_closure_probability: float = Field(..., description="Probability of road closure (0.0 to 1.0)")
    hotspot_rank: int = Field(..., description="Rank of the hotspot (1 is highest priority)")

