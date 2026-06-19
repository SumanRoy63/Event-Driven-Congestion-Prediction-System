import json
import os
import joblib
import pandas as pd
import threading
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODELS_DIR = os.path.join(BASE_DIR, "models")
REGISTRY_PATH = os.path.join(MODELS_DIR, "model_registry.json")

# In-memory Thread-Safe LRU Cache
MAX_CACHE_SIZE = 3
_model_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.Lock()

class ModelOutOfBoundsException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

def load_registry() -> Dict[str, Any]:
    if not os.path.exists(REGISTRY_PATH):
        return {"versions": {}}
    with open(REGISTRY_PATH, 'r') as f:
        return json.load(f)

def get_models_for_date(target_datetime: datetime) -> Dict[str, Any]:
    """
    Scans the registry for a model version that covers the target_datetime.
    If found, loads the models (from cache if available) and returns them.
    If not found, raises ModelOutOfBoundsException.
    """
    registry = load_registry()
    target_date = target_datetime.date()
    
    selected_version = None
    selected_path = ""
    selected_hotspots = ""
    
    for version, meta in registry.get("versions", {}).items():
        try:
            start_d = datetime.strptime(meta["start_date"], "%Y-%m-%d").date()
            end_d = datetime.strptime(meta["end_date"], "%Y-%m-%d").date()
            if start_d <= target_date <= end_d:
                selected_version = version
                selected_path = meta.get("path", "")
                selected_hotspots = meta.get("hotspots_path", "")
                break
        except Exception as e:
            continue
            
    if not selected_version:
        date_str = target_date.strftime("%Y-%m-%d")
        raise ModelOutOfBoundsException(
            f"No model is trained for events on {date_str}. Please upload a CSV for this date range via the /api/v1/ingest pipeline, or wait for the server to process new data."
        )
        
    # Thread-Safe LRU Cache Hit Check
    with _cache_lock:
        if selected_version in _model_cache:
            # Move to end of dict to mark as most recently used
            models = _model_cache.pop(selected_version)
            _model_cache[selected_version] = models
            logger.info(f"[CACHE HIT] Loaded version '{selected_version}' from LRU memory.")
            return models
        
    # Cache Miss - Load into memory from disk
    logger.info(f"[CACHE MISS] Loading model version '{selected_version}' from disk...")
    try:
        base_path = os.path.join(MODELS_DIR, selected_path)
        road_model = joblib.load(os.path.join(base_path, "road_closure_xgb.pkl"))
        severity_model = joblib.load(os.path.join(base_path, "severity_xgb.pkl"))
        priority_encoder = joblib.load(os.path.join(base_path, "priority_encoder.pkl"))
        categorical_encoders = joblib.load(os.path.join(base_path, "encoders.pkl"))
        
        # Load hotspots df if path provided
        hotspots_df = None
        if selected_hotspots and os.path.exists(selected_hotspots):
            hotspots_df = pd.read_csv(selected_hotspots)
        
        models = {
            "road_model": road_model,
            "severity_model": severity_model,
            "priority_encoder": priority_encoder,
            "categorical_encoders": categorical_encoders,
            "hotspots_df": hotspots_df
        }
        
        # Thread-Safe LRU Cache Write and Eviction
        with _cache_lock:
            # Evict the oldest model if we are at capacity
            if len(_model_cache) >= MAX_CACHE_SIZE:
                # Python 3.7+ dicts preserve insertion order. The first item is the oldest.
                oldest_version = next(iter(_model_cache))
                del _model_cache[oldest_version]
                logger.info(f"[CACHE EVICT] Max capacity ({MAX_CACHE_SIZE}) reached. Evicted oldest version: '{oldest_version}'.")
            
            _model_cache[selected_version] = models
            logger.info(f"[CACHE STORE] Version '{selected_version}' cached. Current cache size: {len(_model_cache)}/{MAX_CACHE_SIZE}.")
            
        return models
    except Exception as e:
        raise ModelOutOfBoundsException(f"Found version '{selected_version}' in registry, but failed to load .pkl files. Error: {e}")
