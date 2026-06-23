import xgboost as xgb
from sklearn.model_selection import train_test_split
import joblib
import os
import pandas as pd

def prepare_data(df):
    features = ['latitude', 'longitude', 'hour', 'day_of_week', 'impact_distance', 'event_cause', 'event_type']
    # Force numeric to prevent XGBoost panics
    X = df[features].apply(pd.to_numeric, errors='coerce').fillna(0)
    y = df['requires_road_closure'].astype(int)
    return X, y

def split_data(X, y):
    return train_test_split(X, y, test_size=0.2, random_state=42)

def train_xgboost(X_train, y_train):
    model = xgb.XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)
    return model

def save_model(model, filename):
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, os.path.join("models", filename))