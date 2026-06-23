import os
import joblib
import pandas as pd
import threading
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# In-memory Thread-Safe Cache
_model_cache: Dict[str, Any] = {}
_cache_lock = threading.Lock()

def get_latest_model() -> Dict[str, Any]:
    """
    Bypasses the date-bounding registry entirely.
    Strictly loads the freshly trained models from disk.
    """
    with _cache_lock:
        if "latest" in _model_cache:
            return _model_cache["latest"]
        
    logger.info("[CACHE MISS] Loading trained models from disk...")
    try:
        models = {
            "road_model": joblib.load(os.path.join(MODELS_DIR, "road_closure_xgb.pkl")),
            "severity_model": joblib.load(os.path.join(MODELS_DIR, "severity_xgb.pkl")),
            "categorical_encoders": joblib.load(os.path.join(MODELS_DIR, "encoders.pkl")),
            "priority_encoder": joblib.load(os.path.join(MODELS_DIR, "priority_encoder.pkl")),
            "hotspots_df": None # Disabled for now to prevent distance errors
        }
        
        with _cache_lock:
            _model_cache["latest"] = models
            
        return models
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"CRASH: Failed to load models. Did you run train.py? Error: {e}"}
        )

# Dummy functions to prevent admin.py from crashing if it calls them
def evict_from_cache(version_name: str) -> bool:
    return True

def clear_cache() -> int:
    with _cache_lock:
        _model_cache.clear()
    return 1