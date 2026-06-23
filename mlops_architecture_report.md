# MLOps Architecture Report
### Event-Driven Congestion Prediction System
*Generated: 2026-06-21 | Branch: sr-ml*

---

## 1. Data Ingestion & Model Generation

### 1.1 Exact Function Call Sequence (Triggered via `POST /api/v1/ingest`)

When a CSV file is uploaded, the endpoint in `src/api/routers/ingest.py` does the following synchronously, then immediately returns an HTTP response while the rest executes in a background thread:

```
POST /api/v1/ingest
  └─► [SYNC]  shutil.copyfileobj()         — saves the uploaded CSV to data/raw/uploaded_<filename>.csv
  └─► [ASYNC] BackgroundTasks.add_task()   — fires process_and_train(file_path, date_range)
                └─► load_dataset(file_path)                    [src/data/load_data.py]
                └─► clean_data(df)                             [src/data/preprocess.py]
                └─► feature_pipeline(df, "start_datetime")     [src/data/feature_engineering.py]
                    ├─► create_time_features(df, "start_datetime")
                    └─► encode_categories(df)                  → saves encoders.pkl
                └─► road_closure_model.prepare_data(df)        [src/data/models/road_closure_model.py]
                └─► road_closure_model.split_data(X, y)
                └─► road_closure_model.train_xgboost(X_train, y_train)
                └─► road_closure_model.save_model(model, "road_closure_xgb.pkl")
                └─► severity_model.prepare_data(df)            [src/data/models/severity_model.py]
                └─► severity_model.split_data(X, y)
                └─► severity_model.train_xgboost(X_train, y_train)
                └─► severity_model.save_model(model, "severity_xgb.pkl")
                └─► [VERSION] create models/v_YYYYMMDD_HHMMSS/ directory
                └─► [MOVE]    move .pkl artifacts into the versioned folder
                └─► [WRITE]   update models/model_registry.json with new version entry
```

---

### 1.2 Data Cleaning & Feature Engineering Steps (Pre-`.fit()`)

**Step 1 — `clean_data(df)` in `preprocess.py`:**
1. `df.drop_duplicates()` — removes duplicate rows
2. `pd.to_datetime(df['start_datetime'], errors='coerce')` — parses timestamps
3. Extracts `hour` and `day_of_week` from `start_datetime`
4. Coerces `latitude` and `longitude` to numeric
5. Drops any column where >70% of values are null
6. Fills remaining object/categorical nulls with `"Unknown"`
7. Fills remaining numeric nulls with column median

**Step 2 — `create_time_features(df, "start_datetime")` in `feature_engineering.py`:**
Derives the following new columns from `start_datetime`:
- `hour` (int)
- `day` (int)
- `day_of_week` (string, e.g. `"Monday"`)
- `month` (int)
- `weekend` (int, 0 or 1)

**Step 3 — `encode_categories(df)` in `feature_engineering.py`:**
- Selects all remaining `object`-dtype columns
- Fits a separate `LabelEncoder` on each
- Transforms each column in-place (replaces string with integer codes)
- Saves the full encoder dict to `models/encoders.pkl` via `joblib.dump()`

---

### 1.3 ⚠️ CRITICAL: Feature Schema Divergence Between Training Paths

There are **two completely separate `prepare_data()` functions** with **different feature schemas**. This is the root cause of any schema/prediction flow issues.

#### Road Closure Model (`road_closure_model.py → prepare_data(df, target_col)`)
- **Target column:** `requires_road_closure` (bool → mapped to int 1/0)
- **Explicit hardcoded feature list:**
  ```python
  features = ['event_type', 'hour', 'day_of_week', 'latitude', 'longitude', 'zone']
  ```
- **Pre-processing inside `train_xgboost()`:** Wraps these into a `sklearn.Pipeline` with:
  - `StandardScaler` on `['hour', 'day_of_week', 'latitude', 'longitude']`
  - `OneHotEncoder(handle_unknown='ignore')` on `['event_type', 'zone']`
  - `XGBClassifier` (binary, `objective` defaults to `binary:logistic`)
- **Saved artifact:** `models/road_closure_xgb.pkl` — this is a full `sklearn.Pipeline` object

#### Severity Model (`severity_model.py → prepare_data(df)`)
- **Target column:** `priority` (string, label-encoded by `LabelEncoder`)
- **Feature selection:** Takes the **entire DataFrame** minus the target, minus any column containing `"date"` or `"time"` in the name, minus any remaining `object`-dtype columns
- **⚠️ This means the severity model trains on EVERY numeric column that survived preprocessing**, which is a dynamic, non-deterministic set. It includes columns like `requires_road_closure`, `hour`, `day`, `day_of_week` (numeric), `weekend`, `month`, `latitude`, `longitude`, `client_id`, `status`, `authenticated`, etc.
- **Pre-processing inside `train_xgboost()`:** The severity model's `train_xgboost()` function does **NOT** use a `sklearn.Pipeline`. It calls `xgb.fit(X_train, y_train)` directly on the pre-encoded numeric DataFrame.
- **Saved artifacts:**
  - `models/severity_xgb.pkl` — a raw `XGBClassifier` object (not a Pipeline)
  - `models/priority_encoder.pkl` — a `LabelEncoder` for the target classes

#### Encoder Artifact from `feature_pipeline()`
- `models/encoders.pkl` — dict of `{column_name: LabelEncoder}` for all categoricals

---

### 1.4 Generated Artifacts & Save Locations

| Artifact | Location after versioning | Type |
|---|---|---|
| `road_closure_xgb.pkl` | `models/v_YYYYMMDD_HHMMSS/road_closure_xgb.pkl` | `sklearn.Pipeline` |
| `severity_xgb.pkl` | `models/v_YYYYMMDD_HHMMSS/severity_xgb.pkl` | Raw `XGBClassifier` |
| `priority_encoder.pkl` | `models/v_YYYYMMDD_HHMMSS/priority_encoder.pkl` | `LabelEncoder` |
| `encoders.pkl` | `models/v_YYYYMMDD_HHMMSS/encoders.pkl` | `dict[str, LabelEncoder]` |

The root `models/` directory also contains residual unversioned artifacts: `road_closure_pipeline.pkl`, `severity_xgb.pkl`, `priority_encoder.pkl`.

---

## 2. Model Management & Loading (`model_manager.py`)

### 2.1 Model Selection Strategy

The system uses a **"latest version" paradigm**. When `get_latest_model()` is called:

```python
selected_version = max(versions.keys())
```

`max()` is applied lexicographically to the version keys (e.g., `"v_20260620_150328"`). Since version names are timestamp-based strings in `v_YYYYMMDD_HHMMSS` format, lexicographic sort is equivalent to chronological sort, so this correctly selects the most recent version.

The version metadata from `model_registry.json` provides:
- `path` — the subdirectory name (e.g., `v_20260620_150328`)
- `hotspots_path` — path to the optional hotspots CSV

If the registry has zero versions, a `404 HTTPException` is raised with:
```json
{"status": "error", "message": "No models found in the registry. Please ingest training data first."}
```

### 2.2 Caching Mechanism

A **Thread-Safe LRU Cache** is implemented using a plain Python dict with an insertion-order guarantee (Python 3.7+) and a `threading.Lock()`.

- **Max size:** `MAX_CACHE_SIZE = 3`
- **Cache key:** version name string (e.g., `"v_20260620_150328"`)
- **Cache hit:** The version is popped and re-inserted at the end of the dict (LRU promotion). Returns immediately.
- **Cache miss:** All 4 `.pkl` files are loaded from disk via `joblib.load()`. If cache is at max capacity, the oldest entry (first key in the dict) is evicted before writing.
- **Cache eviction:**  `evict_from_cache(version_name)` — manual single-version eviction used by admin delete endpoint. `clear_cache()` — full purge used by admin reset endpoint.

---

## 3. The API Contract

### 3.1 `EventRequest` Pydantic Schema (`src/api/schemas/event.py`)

```python
class EventRequest(BaseModel):
    # Required
    event_type:          str      # e.g. "Protest", "Accident"
    latitude:            float    # Starting latitude
    longitude:           float    # Starting longitude
    start_datetime:      datetime # ISO 8601; defaults to datetime.utcnow()

    # Optional (all have defaults)
    endlatitude:         float    = 0.0
    endlongitude:        float    = 0.0
    address:             str      = "Unknown"
    event_cause:         str      = "Unknown"
    status:              int      = 1
    authenticated:       int      = 1
    description:         str      = ""
    veh_type:            str      = "Unknown"
    veh_no:              str      = "Unknown"
    corridor:            str      = "Unknown"
    client_id:           int      = 1
    created_by_id:       int      = 1
    last_modified_by_id: int      = 1
    police_station:      str      = "Unknown"
    kgid:                str      = "Unknown"
    closed_by_id:        int      = 0
    gba_identifier:      str      = "Unknown"
    zone:                str      = "Unknown"
    junction:            str      = "Unknown"

    class Config:
        extra = "allow"   # Additional fields are accepted without error
```

### 3.2 `EventResponse` Schema (`src/api/schemas/response.py`)

```python
class PredictionResponse(BaseModel):
    road_closure_probability: float
    severity:                 str

class RecommendationResponse(BaseModel):
    alert_level:      str
    traffic_officers: int
    barricades:       str
    risk_score:       float

class EventResponse(BaseModel):
    prediction:      PredictionResponse
    recommendation:  RecommendationResponse
    hotspot_info:    Dict[str, Any]
```

---

## 4. The Inference Preprocessing Bridge (`prediction_service.py`)

### 4.1 Payload-to-Feature-Matrix Mapping

`preprocess_event(payload_dict, categorical_encoders)` receives the raw Pydantic payload as a dict and executes the following in order:

1. `pd.DataFrame([payload_dict])` — wraps the dict into a single-row DataFrame
2. If `start_datetime` column exists:
   - Parses with `pd.to_datetime(..., errors='coerce')`
   - Extracts: `hour`, `day`, `day_of_week`, `month`, `weekend`
3. Drops all columns with `datetime64` dtype (removes the raw `start_datetime`)
4. Applies `categorical_encoders` (the `encoders.pkl` dict): for each known categorical column, transforms the incoming string value using the fitted `LabelEncoder`. If the value is unseen/unknown, it is replaced with `str(encoder.classes_[0])` (i.e., the first known class alphabetically) before transforming.
5. `df.select_dtypes(include=np.number)` — drops all remaining non-numeric columns

### 4.2 Hardcoded Drops, Missing Value Injections & Schema Hacks

| Behaviour | Location | Detail |
|---|---|---|
| Unseen category fallback | `prediction_service.py` L33 | Replaces unknown categories with `encoder.classes_[0]` before encoding |
| Datetime column auto-drop | `prediction_service.py` L24-26 | Any `datetime64`-typed column is dropped silently |
| Non-numeric column purge | `prediction_service.py` L37 | Any column that is still `object`-typed after encoding is silently dropped |
| Feature reindexing | `prediction_service.py` (implicit) | The resulting DataFrame is passed directly; **no explicit column reindexing to match training schema**. This is a critical gap. |

### 4.3 Categorical Encoding During Inference

- Uses the `categorical_encoders` dict loaded from `encoders.pkl` (artifact from `feature_pipeline()`).
- This encoder was fitted on **all** object columns of the processed training data.
- **⚠️ Schema mismatch risk:** The road closure model was trained via a `sklearn.Pipeline` containing its own `OneHotEncoder` for `['event_type', 'zone']`. However, at inference time, `preprocess_event()` applies `LabelEncoder` from `encoders.pkl` to these same columns — producing integer-encoded features. The `sklearn.Pipeline` inside the road closure model will then attempt to apply `OneHotEncoder` again on top of those integer values, not on the original string values. This is a critical schema conflict between training and inference.

---

## 5. The Chained Prediction Logic

### 5.1 `predict_event(features_df, models)` Execution Trace

```python
# Step 1: Unpack both model objects from the loaded dict
road_pipeline    = models.get("road_model")     # sklearn.Pipeline object
severity_pipeline = models.get("severity_model") # raw XGBClassifier object

# Step 2: Road closure probability
road_prob = float(road_pipeline.predict_proba(features_df)[0][1])
# → takes index [1] of the class probability array (P(road_closure=1))

# Step 3: Construct severity input with road closure as a feature
severity_input = features_df.copy()
severity_input["requires_road_closure"] = 1 if road_prob > 0.5 else 0
# → binarizes the road probability into 0/1 and injects it as a new column

# Step 4: Severity prediction
severity_idx = int(severity_pipeline.predict(severity_input)[0])
# → returns an integer class index

# Step 5: Decode severity label
priority_encoder = models.get("priority_encoder")  # LabelEncoder
severity = str(priority_encoder.inverse_transform([severity_idx])[0])
# → converts integer back to human-readable class (e.g., "High", "Medium", "Low")
```

### 5.2 Chained Inference: Is Output-as-Input Implemented?

**Yes.** The system implements chained inference:
- The road closure model's probability (`road_prob > 0.5`) is binarized into `requires_road_closure` (0 or 1)
- This value is injected into `severity_input` before the severity model runs

**⚠️ Critical Issue:** The severity model (`severity_xgb.pkl`) is a raw `XGBClassifier` trained on the full processed DataFrame. If `requires_road_closure` was a column in the processed training data (which it is, as it's the road closure target column), the model was trained with it as a feature. However, the exact column set the severity model expects at inference time is dynamic and non-deterministic — it depends on whatever numeric columns were in the processed CSV at training time.

### 5.3 Complete Prediction Flow Summary

```
POST /api/v1/events
  │
  ├── get_latest_model()
  │     └── reads model_registry.json → picks max(version_keys)
  │         → loads from LRU cache or disk (4 .pkl files)
  │
  ├── determine_hotspot_rank(lat, lon, hotspots_df)
  │     └── haversine_distance() against each row in hotspots_df
  │         → returns {rank: int, distance_km: float}
  │
  ├── preprocess_event(payload.dict(), categorical_encoders)
  │     └── DataFrame([payload]) → extract time features → drop datetimes
  │         → LabelEncode categoricals → select_dtypes(numeric)
  │         → returns features_df (shape: 1 row × N numeric columns)
  │
  ├── predict_event(features_df, models)
  │     ├── road_pipeline.predict_proba(features_df)[0][1]  → road_prob
  │     ├── severity_input = features_df.copy()
  │     │     severity_input["requires_road_closure"] = 1 if road_prob > 0.5 else 0
  │     ├── severity_pipeline.predict(severity_input)[0]    → severity_idx
  │     └── priority_encoder.inverse_transform([severity_idx]) → severity string
  │
  ├── generate_recommendation(severity, closure_prob, hotspot_rank)
  │     └── returns {alert_level, traffic_officers, barricades, risk_score}
  │
  ├── [ASYNC if High severity or prob > 0.8]
  │     ├── send_email_alert(subject, message, recipient)
  │     └── send_twilio_alert(message)
  │
  └── [DB] db.add(EventRecord(...)) → SQLite via SQLAlchemy
```

---

## 6. Known Architectural Risks & Schema Conflicts

| # | Risk | Location | Severity |
|---|---|---|---|
| 1 | **Training/inference encoding mismatch** — road closure model trained with `OneHotEncoder` inside Pipeline, but inference applies `LabelEncoder` from `encoders.pkl` before calling the Pipeline. The Pipeline's internal OHE receives already-encoded integers, not raw strings. | `road_closure_model.py` vs `prediction_service.py` | 🔴 Critical |
| 2 | **Dynamic severity feature schema** — severity model is trained on all numeric columns in the processed CSV. The column count is unpredictable and changes with every new ingestion. | `severity_model.py prepare_data()` | 🔴 Critical |
| 3 | **No schema enforcement at inference** — `preprocess_event()` does not `reindex()` to the training column schema. Any column mismatch silently produces wrong predictions or crashes. | `prediction_service.py` | 🟠 High |
| 4 | **`day_of_week` type inconsistency** — training extracts `day_of_week` as a string day name (`"Monday"`) in `feature_engineering.py`, but `preprocess.py` extracts it as an integer (0-6). Whichever runs last wins. | `feature_engineering.py` vs `preprocess.py` | 🟠 High |
| 5 | **Hotspot CSV referenced but potentially missing** — `model_registry.json` references `models/hotspots.csv`, but this file may not exist, causing a silent `None` return from `determine_hotspot_rank()` with a default rank of 5. | `model_manager.py`, `hotspot_service.py` | 🟡 Medium |
