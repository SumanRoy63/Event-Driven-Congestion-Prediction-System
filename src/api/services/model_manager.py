import json
import os
import joblib
import pandas as pd
from datetime import datetime
from typing import Dict, Any

MODELS_DIR = "models"
REGISTRY_PATH = os.path.join(MODELS_DIR, "model_registry.json")

# In-memory cache to store loaded models (LRU style concept)
# Structure: {"v1_baseline": {"road_model": ..., "severity_model": ..., ...}}
_model_cache: Dict[str, Dict[str, Any]] = {}

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
        
    # If it's already in memory, return it
    if selected_version in _model_cache:
        return _model_cache[selected_version]
        
    # Load into memory
    print(f"Loading model version: {selected_version} into memory...")
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
        
        # Cache it
        _model_cache[selected_version] = models
        return models
    except Exception as e:
        raise ModelOutOfBoundsException(f"Found version '{selected_version}' in registry, but failed to load .pkl files. Error: {e}")
