import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import joblib
import os

def feature_pipeline(df, datetime_col="start_datetime"):
    """
    The Single Source of Truth for feature schemas. 
    Applies to BOTH training data and API payload inference.
    """
    # 1. Time Features
    if datetime_col in df.columns:
        df[datetime_col] = pd.to_datetime(df[datetime_col], errors='coerce')
        df['hour'] = df[datetime_col].dt.hour.fillna(12).astype(int)
        df['day_of_week'] = df[datetime_col].dt.dayofweek.fillna(0).astype(int)
    else:
        df['hour'] = 12
        df['day_of_week'] = 0
    
    # 2. Impact Distance Proxy (Geospatial logic)
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df['endlatitude'] = df.get('endlatitude', df['latitude']).fillna(df['latitude'])
        df['endlongitude'] = df.get('endlongitude', df['longitude']).fillna(df['longitude'])
        df['impact_distance'] = np.sqrt((df['endlatitude'] - df['latitude'])**2 + (df['endlongitude'] - df['longitude'])**2)
    else:
        df['impact_distance'] = 0.0
    
    # 3. Categorical Handling
    df['event_cause'] = df.get('event_cause', 'Unknown').fillna('Unknown').astype(str)
    df['event_type'] = df.get('event_type', 'unplanned').fillna('unplanned').astype(str)
    
    # 4. Strict Label Encoding (Saved for API inference)
    encoders = {}
    for col in ['event_cause', 'event_type']:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le
    
    os.makedirs("models", exist_ok=True)
    joblib.dump(encoders, "models/encoders.pkl")
    
    # 5. Clean targets for training
    if 'requires_road_closure' in df.columns:
        df['requires_road_closure'] = df['requires_road_closure'].astype(str).str.upper().map({'TRUE': 1, 'FALSE': 0, '1': 1, '0': 0}).fillna(0).astype(int)
    if 'priority' in df.columns:
        df['priority'] = df['priority'].fillna('Medium').astype(str)
        
    # 6. COLUMN LOCK: Strip out all database IDs and garbage columns
    expected_cols = ['latitude', 'longitude', 'hour', 'day_of_week', 'impact_distance', 'event_cause', 'event_type', 'requires_road_closure', 'priority']
    final_cols = [c for c in expected_cols if c in df.columns]
    
    return df[final_cols]