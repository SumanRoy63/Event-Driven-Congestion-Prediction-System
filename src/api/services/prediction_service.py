import pandas as pd
import numpy as np
from typing import Dict, Any

def preprocess_event(payload_dict: Dict[str, Any], categorical_encoders: Dict[str, Any] = None) -> pd.DataFrame:
    df = pd.DataFrame([payload_dict])
    
    # 1. Match the exact feature engineering from training
    if "start_datetime" in df.columns:
        df["start_datetime"] = pd.to_datetime(df["start_datetime"], errors="coerce")
        df["hour"] = df["start_datetime"].dt.hour.fillna(12).astype(int)
        df["day_of_week"] = df["start_datetime"].dt.dayofweek.fillna(0).astype(int)
    else:
        df["hour"] = 12
        df["day_of_week"] = 0
        
    lat = float(df.get("latitude", 0.0).iloc[0])
    lon = float(df.get("longitude", 0.0).iloc[0])
    end_lat = float(df.get("endlatitude", lat).iloc[0])
    end_lon = float(df.get("endlongitude", lon).iloc[0])
    df["impact_distance"] = np.sqrt((end_lat - lat)**2 + (end_lon - lon)**2)
    
    df["event_cause"] = df.get("event_cause", "Unknown")
    df["event_type"] = df.get("event_type", "unplanned")
    
    if categorical_encoders is not None:
        for col in ["event_cause", "event_type"]:
            if col in categorical_encoders:
                le = categorical_encoders[col]
                df[col] = df[col].apply(lambda x: x if x in le.classes_ else le.classes_[0])
                df[col] = le.transform(df[col].astype(str))

    # 2. Strict Column Lock (Guarantees Shape Match)
    expected_features = ['latitude', 'longitude', 'hour', 'day_of_week', 'impact_distance', 'event_cause', 'event_type']
    for f in expected_features:
        if f not in df.columns:
            df[f] = 0.0
            
    final_df = df[expected_features].copy()
    return final_df.apply(pd.to_numeric, errors='coerce').fillna(0)


def predict_event(features_df: pd.DataFrame, models: Dict[str, Any]) -> Dict[str, Any]:
    road_model = models.get("road_model")
    severity_model = models.get("severity_model")
    priority_encoder = models.get("priority_encoder")

    try:
        # 1. Predict Road Closure
        road_prob = float(road_model.predict_proba(features_df)[0][1])
        
        # 2. Chained Inference (Match the severity_model training)
        severity_input = features_df.copy()
        severity_input["requires_road_closure"] = 1 if road_prob > 0.5 else 0
        
        # Ensure severity model gets exactly what it expects
        if hasattr(severity_model, 'feature_names_in_'):
            severity_input = severity_input[severity_model.feature_names_in_]
            
        # 3. Predict Severity
        severity_idx = int(severity_model.predict(severity_input)[0])
        severity = str(priority_encoder.inverse_transform([severity_idx])[0])
        
    except Exception as e:
        print(f"CRITICAL PREDICTION ERROR: {e}")
        return {"road_closure_probability": 0.0, "severity": "Medium", "error": str(e)}

    return {
        "road_closure_probability": round(road_prob, 4),
        "severity": severity
    }