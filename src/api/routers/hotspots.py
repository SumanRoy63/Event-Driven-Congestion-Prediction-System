from fastapi import APIRouter, Query
from typing import Dict, Any, Optional
from datetime import datetime
from src.api.services.hotspot_service import determine_hotspot_rank
from src.api.services.model_manager import get_models_for_date

router = APIRouter()

@router.get("/hotspots/rank")
def get_hotspot_rank(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location"),
    target_date: Optional[str] = Query(None, description="Date (YYYY-MM-DD) to query the correct versioned hotspots. Defaults to today.")
) -> Dict[str, Any]:
    """
    Get the hotspot rank and distance to the nearest known traffic cluster
    based on latitude and longitude coordinates and the versioned model date.
    """
    if not target_date:
        target_datetime = datetime.utcnow()
    else:
        try:
            target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            target_datetime = datetime.utcnow()
            
    # Fetch appropriate models (and hotspots CSV) based on date
    models = get_models_for_date(target_datetime)
    
    return determine_hotspot_rank(lat, lon, models.get("hotspots_df"))
