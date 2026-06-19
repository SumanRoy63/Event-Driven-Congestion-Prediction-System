from fastapi import APIRouter, Query
from typing import Dict, Any
from src.api.services.hotspot_service import determine_hotspot_rank

router = APIRouter()

@router.get("/hotspots/rank")
def get_hotspot_rank(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location")
) -> Dict[str, Any]:
    """
    Get the hotspot rank and distance to the nearest known traffic cluster
    based on latitude and longitude coordinates.
    """
    return determine_hotspot_rank(lat, lon)
