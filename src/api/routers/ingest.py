from fastapi import APIRouter, BackgroundTasks, UploadFile, File
from typing import Dict

router = APIRouter()

def process_and_train(file_path: str, date_range: str):
    """
    Dummy background task that will eventually contain the pipeline from train.py
    It will process the CSV, train new XGBoost models, and update model_registry.json
    """
    print(f"Background Worker: Processing {file_path} for {date_range}...")
    # TODO: Call src.data.preprocess, train model, save .pkl to a new folder, and update registry
    print("Background Worker: Training complete! Notification ready to be sent to WebSocket.")

@router.post("/ingest")
async def ingest_new_data(background_tasks: BackgroundTasks, date_range: str, file: UploadFile = File(...)):
    """
    Upload a new raw CSV file of events. 
    The server will immediately return a success response while handing off 
    the heavy data processing and model retraining to a background worker.
    """
    # In a real app, save the file to disk first
    file_path = f"data/raw/uploaded_{file.filename}"
    
    # Add the training job to the background tasks queue
    background_tasks.add_task(process_and_train, file_path, date_range)
    
    return {
        "status": "processing_started",
        "message": f"Successfully received {file.filename}. The AI models are now retraining in the background for range {date_range}. You will be notified when they are ready."
    }
