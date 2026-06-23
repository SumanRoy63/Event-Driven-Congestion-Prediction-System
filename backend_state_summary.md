# Backend State Summary

## 1. Complete Directory Structure

```text
D:\Event-Driven-Congestion-Prediction-System\
├── models\
│   ├── model_registry.json
│   ├── priority_encoder.pkl
│   ├── road_closure_pipeline.pkl
│   ├── severity_xgb.pkl
│   └── v_20260620_150328\
│       ├── encoders.pkl
│       ├── priority_encoder.pkl
│       ├── road_closure_xgb.pkl
│       └── severity_xgb.pkl
└── src\
    ├── api\
    │   ├── main.py
    │   ├── db\
    │   │   ├── database.py
    │   │   └── models.py
    │   ├── routers\
    │   │   ├── admin.py
    │   │   ├── events.py
    │   │   ├── hotspots.py
    │   │   ├── ingest.py
    │   │   ├── predictions.py
    │   │   └── recommendations.py
    │   ├── schemas\
    │   │   ├── event.py
    │   │   └── response.py
    │   └── services\
    │       ├── hotspot_service.py
    │       ├── model_manager.py
    │       ├── prediction_service.py
    │       └── recommendation_service.py
    └── data\
        ├── feature_engineering.py
        ├── load_data.py
        ├── preprocess.py
        ├── alerts\
        │   ├── email_alert.py
        │   ├── test_email.py
        │   └── twilio_alert.py
        ├── models\
        │   ├── hotspot_detection.py
        │   ├── road_closure_model.py
        │   └── severity_model.py
        └── recommendation\
            └── recommendation_engine.py
```

## 2. ML Pipeline & Model State

### Current Models Directory State
- `models/model_registry.json`
- `models/priority_encoder.pkl`
- `models/road_closure_pipeline.pkl`
- `models/severity_xgb.pkl`
- `models/v_20260620_150328/encoders.pkl`
- `models/v_20260620_150328/priority_encoder.pkl`
- `models/v_20260620_150328/road_closure_xgb.pkl`
- `models/v_20260620_150328/severity_xgb.pkl`

### Feature Preparation (`src/api/services/prediction_service.py`)
Before calling `.predict()`, the `preprocess_event` function drops raw datetime objects and extracts the following engineered features from `start_datetime`:
- `hour` (int)
- `day` (int)
- `day_of_week` (int)
- `month` (int)
- `weekend` (int)
It encodes categorical variables using `categorical_encoders` (e.g., `event_type`, `zone`, `junction`) using `LabelEncoder`. All remaining numerical columns from the payload (like `latitude`, `longitude`, `expected_attendance`, etc.) are retained, leaving purely a numeric Pandas DataFrame for XGBoost ingestion.

### Training Steps (`src/api/routers/ingest.py`)
1. **Load Data:** Loads the uploaded CSV file using `load_dataset`.
2. **Preprocess:** Cleans the data via `clean_data` (removes duplicates, sets dtypes, imputes nulls, drops columns with >70% missing).
3. **Feature Engineering:** Extracts temporal features and encodes categories via `feature_pipeline`.
4. **Train Models:** Runs `train_xgboost` independently on `road_closure_model.py` and `severity_model.py` after splitting train/test sets.
5. **Serialize:** Saves models as `.pkl` files (`road_closure_xgb.pkl`, `severity_xgb.pkl`, `encoders.pkl`, `priority_encoder.pkl`).
6. **Version & Register:** Creates a new folder `models/v_[YYYYMMDD_HHMMSS]/`, moves the `.pkl` files into it, and registers the metadata (including the min/max dates found in the data) in `model_registry.json`.

## 3. API Routes & Schemas

### Events Endpoints (`src/api/routers/events.py`)
**`POST /api/v1/events`**
*   **Request (`EventRequest`)**: 
    `event_type` (str), `latitude` (float), `longitude` (float), `start_datetime` (datetime), with optional tracking/geospatial metrics (`endlatitude`, `endlongitude`, `zone`, `expected_attendance`, `police_station`, etc.).
*   **Response (`EventResponse`)**:
    Contains nested objects: `PredictionResponse` (road_closure_probability, severity), `RecommendationResponse` (alert_level, traffic_officers, barricades, risk_score), and `hotspot_info`.

**`GET /api/v1/events/history`**
*   **Response**: A JSON array of the 50 most recent events formatted from the database (`id`, `timestamp`, `hour`, `month`, `latitude`, `longitude`, `zone`, `event_type`).

**`GET /api/v1/alerts/twilio/health`**
*   **Response**: JSON Dictionary indicating Twilio environment configurations status.

### Predictions Endpoint (`src/api/routers/predictions.py`)
**`POST /api/v1/predictions`**
*   **Request (`EventRequest`)**: Same as `/events`.
*   **Response (`PredictionResponse`)**: `{"road_closure_probability": float, "severity": str}`

### Recommendations Endpoint (`src/api/routers/recommendations.py`)
**`POST /api/v1/recommendations`**
*   **Request (`RecommendationRequest`)**: `severity` (str), `road_closure_probability` (float), `hotspot_rank` (int).
*   **Response (`RecommendationResponse`)**: `alert_level` (str), `traffic_officers` (int), `barricades` (str), `risk_score` (float).

### Hotspots Endpoint (`src/api/routers/hotspots.py`)
**`GET /api/v1/hotspots/rank`**
*   **Request**: Query parameters `lat` (float), `lon` (float), `target_date` (optional str).
*   **Response**: JSON Dictionary containing `rank`, `distance`, etc.

### Ingestion Endpoint (`src/api/routers/ingest.py`)
**`POST /api/v1/ingest`**
*   **Request**: Form-data with `date_range` (str) and `file` (UploadFile/CSV).
*   **Response**: Status message dict confirming the background task started.

### Admin Endpoints (`src/api/routers/admin.py`)
**`POST /api/v1/admin/reset`**
*   **Request**: None.
*   **Response**: Status indicating database wiping, model cache purging, and disk clearing.

**`DELETE /api/v1/admin/models/{version_name}`**
*   **Request**: Path parameter `version_name`.
*   **Response**: JSON confirming deletion.

**`GET /api/v1/admin/models`**
*   **Response**: The raw content of `model_registry.json`.

## 4. The Core Data Flows

### Ingestion Flow
1. **Trigger:** User `POST`s a CSV to `/api/v1/ingest`.
2. **Disk Save:** The file is temporarily saved to `data/raw/`.
3. **Background Task Handoff:** FastAPI `BackgroundTasks` calls `process_and_train`.
4. **Data Prep:** `load_dataset` -> `clean_data` -> `feature_pipeline`.
5. **Model Fitting:** `road_closure_model.train_xgboost()` and `severity_model.train_xgboost()` are called.
6. **Artifact Persistence:** Pipelines and Encoders are saved as `.pkl` objects.
7. **Versioning:** Artifacts are dynamically relocated to `models/v_[timestamp]/` and appended to `model_registry.json`.

### Prediction Flow
1. **Trigger:** `POST /api/v1/events` receives the `EventRequest` payload.
2. **Model Retrieval:** `get_latest_model()` retrieves the newest active model set from `model_registry.json`, loading it into an in-memory Thread-Safe LRU cache (`_model_cache`).
3. **Hotspot Evaluation:** `determine_hotspot_rank()` checks geospatial proximity.
4. **Data Transformation:** `preprocess_event()` transforms the payload to feature matrices.
5. **Inference:** `predict_event()` executes probability inference for road closures, and utilizes that output via chained inference to predict `severity`.
6. **Recommendation Formulation:** `generate_recommendation()` calculates resources needed based on the ML predictions.
7. **Alert Triggering:** Evaluates a strict threshold (`severity == 'High'` or `prob > 0.8`). If triggered, and passes a thread-safe timestamp cooldown lock check, asynchronous tasks dispatch Twilio SMS and SMTP Emails.
8. **Persistence:** Saves the event features, timestamp, and results to the SQLite DB `EventRecord` table using SQLAlchemy.

## 5. Critical Configuration

### Database 
*   **Connection**: SQLite initialized via SQLAlchemy (`src/api/db/database.py`).
*   **Tables (`models.py`)**: 
    - `event_records`:
        - `id` (Integer, primary_key)
        - `timestamp` (DateTime, index)
        - `event_type` (String, index)
        - `location` (String)
        - `expected_attendance` (Integer)
        - `road_closure_probability` (Float)
        - `predicted_severity` (String)
        - `alert_triggered` (Boolean)

### `model_registry.json` Content
```json
{
    "versions": {
        "v_20260620_150328": {
            "start_date": "2023-11-09",
            "end_date": "2024-04-08",
            "path": "v_20260620_150328",
            "hotspots_path": "models/hotspots.csv"
        }
    }
}
```
