import pandas as pd
import numpy as np
import os
import math
from typing import Dict, Any

HOTSPOTS_FILE = "outputs/hotspot_clusters.csv"
hotspots_df = None

try:
    if os.path.exists(HOTSPOTS_FILE):
        hotspots_df = pd.read_csv(HOTSPOTS_FILE)
except Exception as e:
    print(f"Warning: Could not load hotspots file. {e}")

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in kilometers between two points on earth."""
    R = 6371.0 # Earth radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def determine_hotspot_rank(lat: float, lon: float) -> Dict[str, Any]:
    """
    Given a latitude and longitude, determines the hotspot rank by finding
    the nearest cluster center.
    """
    if hotspots_df is None or hotspots_df.empty or "latitude" not in hotspots_df.columns:
        # Fallback if no hotspot data available
        return {"rank": 5, "distance_km": None, "message": "No hotspot data available"}
    
    closest_distance = float('inf')
    closest_rank = 5 # Default medium rank
    
    for _, row in hotspots_df.iterrows():
        try:
            h_lat = float(row['latitude'])
            h_lon = float(row['longitude'])
            
            dist = haversine_distance(lat, lon, h_lat, h_lon)
            
            if dist < closest_distance:
                closest_distance = dist
                if 'rank' in row:
                    closest_rank = int(row['rank'])
                else:
                    # Deduce rank from proximity: lower rank (1) means higher priority/danger
                    closest_rank = 1 if dist < 1 else (3 if dist < 3 else 7)
        except Exception:
            pass

    return {
        "rank": int(closest_rank),
        "distance_km": round(closest_distance, 2) if closest_distance != float('inf') else None
    }
