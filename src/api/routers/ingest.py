import os
import json
import shutil
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, UploadFile, File
from typing import Dict

from src.data.load_data import load_dataset
from src.data.preprocess import clean_data
from src.data.feature_engineering import feature_pipeline
from src.data.models import road_closure_model, severity_model

router = APIRouter()

def process_and_train(file_path: str, date_range: str):
    """
    Background task that orchestrates the entire training pipeline.
    It processes the CSV, trains new XGBoost models, and updates model_registry.json.
    """
    print(f"Background Worker: Processing {file_path} for {date_range}...")
    try:
        # 1. Load Data
        df = load_dataset(file_path)
        if df is None:
            print("Background Worker: Failed to load dataset.")
            return
            
        # 2. Preprocess
        df = clean_data(df)
        
        # 3. Feature Engineering
        df = feature_pipeline(df, "start_datetime")
        
        # Extract dynamic dates from the dataset
        if "start_datetime" in df.columns:
            min_date = df["start_datetime"].min().strftime("%Y-%m-%d")
            max_date = df["start_datetime"].max().strftime("%Y-%m-%d")
        else:
            min_date = "2024-01-01"
            max_date = "2024-12-31"
            
        print(f"Background Worker: Found data covering {min_date} to {max_date}")

        # 4. Train Road Closure Model
        print("Background Worker: Training Road Closure Model...")
        X_rc, y_rc = road_closure_model.prepare_data(df)
        X_train_rc, X_test_rc, y_train_rc, y_test_rc = road_closure_model.split_data(X_rc, y_rc)
        xgb_rc = road_closure_model.train_xgboost(X_train_rc, y_train_rc)
        road_closure_model.save_model(xgb_rc, "road_closure_xgb.pkl")
        
        # 5. Train Severity Model
        print("Background Worker: Training Severity Model...")
        X_sev, y_sev = severity_model.prepare_data(df)
        X_train_sev, X_test_sev, y_train_sev, y_test_sev = severity_model.split_data(X_sev, y_sev)
        xgb_sev = severity_model.train_xgboost(X_train_sev, y_train_sev)
        severity_model.save_model(xgb_sev, "severity_xgb.pkl")
        
        # 6. Version and Move Models
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_name = f"v_{timestamp}"
        version_dir = os.path.join("models", version_name)
        os.makedirs(version_dir, exist_ok=True)
        
        files_to_move = [
            "road_closure_xgb.pkl",
            "severity_xgb.pkl",
            "encoders.pkl",
            "priority_encoder.pkl"
        ]
        
        for f_name in files_to_move:
            src = os.path.join("models", f_name)
            dst = os.path.join(version_dir, f_name)
            if os.path.exists(src):
                shutil.move(src, dst)
                
        # 7. Update Model Registry
        registry_path = os.path.join("models", "model_registry.json")
        if os.path.exists(registry_path):
            with open(registry_path, "r") as f:
                registry = json.load(f)
        else:
            registry = {"versions": {}}
            
        registry["versions"][version_name] = {
            "start_date": min_date,
            "end_date": max_date,
            "path": version_name,
            "hotspots_path": "models/hotspots.csv"  # Fallback for now
        }
        
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=4)
            
        print(f"Background Worker: Retraining pipeline complete! New version '{version_name}' saved.")
        
    except Exception as e:
        print(f"Background Worker Error: {str(e)}")


@router.post("/ingest")
async def ingest_new_data(background_tasks: BackgroundTasks, date_range: str, file: UploadFile = File(...)):
    """
    Upload a new raw CSV file of events. 
    The server will immediately return a success response while handing off 
    the heavy data processing and model retraining to a background worker.
    """
    os.makedirs(os.path.join("data", "raw"), exist_ok=True)
    file_path = os.path.join("data", "raw", f"uploaded_{file.filename}")
    
    # Actually save the uploaded file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Add the training job to the background tasks queue
    background_tasks.add_task(process_and_train, file_path, date_range)
    
    return {
        "status": "success",
        "message": f"Dataset uploaded successfully. The retraining pipeline has started in the background. Please wait a few seconds/minutes for the models to update."
    }
