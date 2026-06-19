import joblib
import pandas as pd
import numpy as np
import os
from typing import Dict, Any

# =====================================
# MODEL LOADING (Run once on startup)
# =====================================
MODELS_DIR = "models"

try:
    road_model = joblib.load(os.path.join(MODELS_DIR, "road_closure_xgb.pkl"))
    severity_model = joblib.load(os.path.join(MODELS_DIR, "severity_xgb.pkl"))
    priority_encoder = joblib.load(os.path.join(MODELS_DIR, "priority_encoder.pkl"))
    categorical_encoders = joblib.load(os.path.join(MODELS_DIR, "encoders.pkl"))
    # Optionally load kmeans/dbscan for hotspots
    kmeans_model = joblib.load(os.path.join(MODELS_DIR, "kmeans_model.pkl"))
except Exception as e:
    print(f"Warning: Models could not be loaded on startup. {e}")
    road_model = severity_model = priority_encoder = categorical_encoders = kmeans_model = None


def preprocess_event(payload_dict: Dict[str, Any]) -> pd.DataFrame:
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
    # The models/encoders.pkl holds a dict of trained LabelEncoders
    if categorical_encoders is not None:
        for col, encoder in categorical_encoders.items():
            if col in df.columns:
                # Handle unseen labels gracefully by mapping them to a default or -1
                # Standard LabelEncoder throws an error on unseen labels.
                # A quick hack for unseen data is to convert unknown strings to the 0th class
                # or safely bypass.
                known_classes = set(encoder.classes_)
                df[col] = df[col].apply(lambda x: x if str(x) in known_classes else str(encoder.classes_[0]))
                df[col] = encoder.transform(df[col].astype(str))

    # Keep only numeric columns, just like app.py
    df = df.select_dtypes(include=np.number)
    
    # Align feature columns to model expectations (using a robust approach)
    # If the model expects specific columns in a specific order, it will complain if there's a mismatch.
    # We rely on XGBoost's feature names if available.
    try:
        model_features = road_model.feature_names_in_
        # Add missing columns with 0
        for f in model_features:
            if f not in df.columns:
                df[f] = 0
        # Reorder and subset exactly as model expects
        df = df[model_features]
    except AttributeError:
        # If feature_names_in_ is not available, we just pass the DataFrame as is
        # and hope the column order matches how it was trained (alphabetical or original CSV order).
        pass

    return df

def predict_event(features_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs the inference models to predict road closure probability and severity.
    """
    if road_model is None or severity_model is None:
        return {"road_closure_probability": 0.0, "severity": "Unknown (Models not loaded)"}

    try:
        road_prob = float(road_model.predict_proba(features_df)[0][1])
        severity_idx = int(severity_model.predict(features_df)[0])
        
        # Inverse transform the severity index to actual string label (e.g. "High", "Low")
        severity = str(priority_encoder.inverse_transform([severity_idx])[0])
        
    except Exception as e:
        print(f"Prediction Error: {e}")
        road_prob = 0.0
        severity = "Error"

    return {
        "road_closure_probability": road_prob,
        "severity": severity
    }
