import pandas as pd
import numpy as np
from typing import Dict, Any
from datetime import datetime
from src.api.services.model_manager import get_models_for_date

def preprocess_event(payload_dict: Dict[str, Any], categorical_encoders: Dict[str, Any]) -> pd.DataFrame:
    """
    Transforms the raw EventRequest dictionary into a feature DataFrame 
    ready for the XGBoost models.
    """
    df = pd.DataFrame([payload_dict])
    
    # 1. Create Time Features
    if "start_datetime" in df.columns:
        df["start_datetime"] = pd.to_datetime(df["start_datetime"], errors="coerce")
        df["hour"] = df["start_datetime"].dt.hour
        df["day"] = df["start_datetime"].dt.day
        df["day_of_week"] = df["start_datetime"].dt.dayofweek
        df["month"] = df["start_datetime"].dt.month
        df["weekend"] = df["start_datetime"].dt.dayofweek.isin([5,6]).astype(int)
        
    # Drop datetimes as models usually don't accept raw datetime objects
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df = df.drop(columns=[col])

    # 2. Encode Categorical Variables
    if categorical_encoders is not None:
        for col, encoder in categorical_encoders.items():
            if col in df.columns:
                known_classes = set(encoder.classes_)
                df[col] = df[col].apply(lambda x: x if str(x) in known_classes else str(encoder.classes_[0]))
                df[col] = encoder.transform(df[col].astype(str))

    # Keep only numeric columns
    df = df.select_dtypes(include=np.number)
    
    return df

def predict_event(features_df: pd.DataFrame, models: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs the inference models to predict road closure probability and severity.
    """
    road_model = models.get("road_model")
    severity_model = models.get("severity_model")
    priority_encoder = models.get("priority_encoder")

    try:
        # Align features for road model
        road_features = features_df.copy()
        if hasattr(road_model, "feature_names_in_"):
            for f in road_model.feature_names_in_:
                if f not in road_features.columns:
                    road_features[f] = 0
            road_features = road_features[road_model.feature_names_in_]
            
        road_prob = float(road_model.predict_proba(road_features)[0][1])
        
        # Align features for severity model
        severity_features = features_df.copy()
        if "requires_road_closure" not in severity_features.columns:
             severity_features["requires_road_closure"] = 1 if road_prob > 0.5 else 0
             
        if hasattr(severity_model, "feature_names_in_"):
            for f in severity_model.feature_names_in_:
                if f not in severity_features.columns:
                    severity_features[f] = 0
            severity_features = severity_features[severity_model.feature_names_in_]
            
        severity_idx = int(severity_model.predict(severity_features)[0])

        # Inverse transform the severity index to actual string label
        severity = str(priority_encoder.inverse_transform([severity_idx])[0])
        
    except Exception as e:
        print(f"Prediction Error: {e}")
        road_prob = 0.0
        severity = "Error"

    return {
        "road_closure_probability": road_prob,
        "severity": severity
    }
