from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
import json
import math
import os
import requests
from google import genai

# --- 1. Load the Exported Artifacts ---
print("Loading AI Models...")
try:
    model = joblib.load("models/lightgbm_impact_model.pkl")
    kmeans = joblib.load("models/kmeans_spatial_clusterer.pkl")
    features = joblib.load("models/model_features.pkl")
    with open("models/category_schemas.json", "r") as f:
        category_schemas = json.load(f)
except Exception as e:
    print(
        f"Error loading models. Make sure all 4 files are in the directory. Error: {e}"
    )

# --- 2. Initialize LLM (The Hackathon Killshot) ---
from dotenv import load_dotenv
load_dotenv()
# Get a free key from https://aistudio.google.com/
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 3. Initialize FastAPI App ---
app = FastAPI(title="Traffic Command Center API", version="5.0 - Ultimate Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# --- 4. Define Incoming Request Data Models ---
class EventRequest(BaseModel):
    latitude: float
    longitude: float
    event_cause: str
    priority: str
    requires_road_closure: bool
    corridor: str
    zone: str
    police_station: str
    event_time: str
    event_type: str = "unplanned"


class FeedbackRequest(EventRequest):
    actual_impact: str
    actual_barricades_used: int


# --- 5. The Heuristics Engine ---
BASELINE_RESOURCES = {
    "High": {
        "manpower": 8,
        "barricades": 20,
        "diversion_level": "Arterial Rerouting",
        "vms_alert": True,
    },
    "Medium": {
        "manpower": 4,
        "barricades": 10,
        "diversion_level": "Local Lane Management",
        "vms_alert": True,
    },
    "Low": {
        "manpower": 1,
        "barricades": 0,
        "diversion_level": "None",
        "vms_alert": False,
    },
}

CAUSE_MODIFIERS = {
    "water_logging": {"add_manpower": 2, "special_equip": "Pumping Truck Request"},
    "vehicle_breakdown": {
        "add_manpower": 0,
        "special_equip": "Heavy Tow Truck Dispatch",
    },
    "vip_movement": {"add_manpower": 4, "special_equip": "Pilot Clearance Vehicle"},
    "accident": {"add_manpower": 2, "special_equip": "Ambulance & Recovery Vehicle"},
    "public_event": {"add_manpower": 6, "special_equip": "Crowd Control Barriers"},
}


# --- 6. Helper: Feature Engineering Pipeline ---
def preprocess_event(request: EventRequest):
    # Parse event_time to Asia/Kolkata
    try:
        dt = pd.to_datetime(request.event_time)
        if dt.tz is None:
            dt_ist = dt.tz_localize('UTC').tz_convert('Asia/Kolkata')
        else:
            dt_ist = dt.tz_convert('Asia/Kolkata')
    except Exception:
        dt_ist = pd.Timestamp.now(tz='Asia/Kolkata')

    hour = dt_ist.hour
    dow = dt_ist.dayofweek
    is_weekend = 1 if dow >= 5 else 0
    month = dt_ist.month
    is_peak = 1 if hour in [8, 9, 10, 11, 17, 18, 19, 20] else 0
    hour_sin = math.sin(2 * math.pi * hour / 24)
    hour_cos = math.cos(2 * math.pi * hour / 24)

    is_major_corridor = 0 if request.corridor == "Non-corridor" else 1
    cause_corridor = f"{request.event_cause}_{request.corridor}"

    # Assign geo_cluster and check distance to nearest event for confidence
    geo_cluster = 0
    confidence = "Low"
    try:
        url = f"{SUPABASE_URL}/rest/v1/rpc/get_geo_context"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"lat_in": request.latitude, "lng_in": request.longitude}
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            geo_data = response.json()
            geo_cluster = int(geo_data.get("cluster_id", 0))
            confidence = geo_data.get("confidence", "Low")
    except Exception:
        geo_cluster = kmeans.predict(
            pd.DataFrame(
                [[request.latitude, request.longitude]], columns=["latitude", "longitude"]
            )
        )[0]

    # Query counts based on Mode (Past/Now vs Future)
    now_ist = pd.Timestamp.now(tz='Asia/Kolkata')
    corridor_events_24h = 0.0
    corridor_events_72h = 0.0

    if dt_ist <= now_ist:
        # Past/Now Mode: Query historical events count
        try:
            url = f"{SUPABASE_URL}/rest/v1/rpc/get_corridor_counts"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            payload = {"corridor_in": request.corridor, "event_time_in": dt_ist.isoformat()}
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                counts = response.json()
                corridor_events_24h = float(counts.get("count_24h", 0))
                corridor_events_72h = float(counts.get("count_72h", 0))
            else:
                corridor_events_24h = 4.0 if is_major_corridor else 1.0
                corridor_events_72h = corridor_events_24h * 2.5
        except Exception:
            corridor_events_24h = 4.0 if is_major_corridor else 1.0
            corridor_events_72h = corridor_events_24h * 2.5
    else:
        # Future Mode: Query corridor_hour_baseline
        try:
            url = f"{SUPABASE_URL}/rest/v1/corridor_hour_baseline"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            }
            params = {
                "corridor": f"eq.{request.corridor}",
                "zone": f"eq.{request.zone}",
                "day_of_week": f"eq.{dow}",
                "hour": f"eq.{hour}",
                "select": "avg_events_24h"
            }
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                res_data = response.json()
                if res_data and len(res_data) > 0:
                    corridor_events_24h = float(res_data[0].get("avg_events_24h", 0.0))
                else:
                    # fallback to general corridor matching
                    params_fb = {
                        "corridor": f"eq.{request.corridor}",
                        "hour": f"eq.{hour}",
                        "select": "avg_events_24h"
                    }
                    response_fb = requests.get(url, params=params_fb, headers=headers)
                    if response_fb.status_code == 200:
                        res_data_fb = response_fb.json()
                        if res_data_fb and len(res_data_fb) > 0:
                            corridor_events_24h = float(np.mean([float(r.get("avg_events_24h", 0.0)) for r in res_data_fb]))
                        else:
                            corridor_events_24h = 3.0 if is_major_corridor else 0.5
                    else:
                        corridor_events_24h = 3.0 if is_major_corridor else 0.5
            else:
                corridor_events_24h = 3.0 if is_major_corridor else 0.5
            corridor_events_72h = corridor_events_24h * 2.5
        except Exception:
            corridor_events_24h = 3.0 if is_major_corridor else 0.5
            corridor_events_72h = corridor_events_24h * 2.5

    event_dict = {
        "hour": hour,
        "dow": dow,
        "is_weekend": is_weekend,
        "month": month,
        "is_peak": is_peak,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "geo_cluster": geo_cluster,
        "cluster_density": 400,
        "event_cause": request.event_cause,
        "corridor": request.corridor,
        "is_major_corridor": is_major_corridor,
        "cause_corridor": cause_corridor,
        "police_station": request.police_station,
        "veh_type": "Unknown",
        "event_type": request.event_type,
        "corridor_events_24h": float(corridor_events_24h),
        "corridor_events_72h": float(corridor_events_72h),
    }

    input_df = pd.DataFrame([event_dict])
    for col in features:
        if col not in input_df.columns:
            input_df[col] = 0
    input_df = input_df[features]

    for col, categories in category_schemas.items():
        if col in input_df.columns:
            val = input_df[col].iloc[0]
            if val not in categories:
                input_df[col] = "Unknown"
            input_df[col] = pd.Categorical(input_df[col], categories=categories)

    return input_df, geo_cluster, corridor_events_24h, confidence


# --- 7. Helper: LLM SITREP Generator ---
def generate_sitrep(
    request: EventRequest, impact: str, plan: dict, cascading_events: int
):
    try:
        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
            return "LLM API Key not configured. Please add key for automated SITREP."

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
        Act as an expert Traffic Police Dispatcher. 
        Write a 3-sentence urgent radio broadcast for field officers based on this new event:
        - Incident: {request.event_cause} at {request.corridor}
        - AI Predicted Severity: {impact.upper()}
        - Prior Events on this road today: {cascading_events} (Risk of cascading gridlock)
        - Orders: Deploy {plan['manpower']} personnel and {plan['barricades']} barricades. {plan['special_equipment']} requested.
        
        Keep it professional, urgent, and formatted for a radio readout. Do not use hashtags.
        """

        # FIX: Switched to the stable models.generate_content attribute
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"Failed to generate radio dispatch script: {str(e)}"



# --- 8. Endpoints ---
@app.get("/api/model-stats")
async def get_model_stats():
    """Return real model metadata for the Model Learning tab."""
    try:
        stats = {
            "model_loaded": model is not None,
            "model_version": "—",
            "total_events_learned": 0,
            "last_calibration": "Never",
        }
        
        # Model version from file timestamp
        import glob, os
        from datetime import datetime
        model_files = glob.glob("models/*.pkl") + glob.glob("models/*.joblib")
        primary_model = "models/lightgbm_impact_model.pkl"
        if os.path.exists(primary_model):
            mtime = os.path.getmtime(primary_model)
            dt = datetime.fromtimestamp(mtime)
            stats["model_version"] = os.path.basename(primary_model)
            stats["last_calibration"] = dt.strftime("%Y-%m-%d %H:%M")
        elif model_files:
            latest = max(model_files, key=os.path.getmtime)
            mtime = os.path.getmtime(latest)
            dt = datetime.fromtimestamp(mtime)
            stats["model_version"] = os.path.basename(latest)
            stats["last_calibration"] = dt.strftime("%Y-%m-%d %H:%M")

        # Training set size from Supabase
        url = f"{SUPABASE_URL}/rest/v1/historical_events"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Prefer": "count=exact",
        }
        res = requests.head(url, headers=headers, params={"select": "id"})
        count_header = res.headers.get("content-range", "")
        if "/" in count_header:
            stats["total_events_learned"] = int(count_header.split("/")[1])

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/geo-context")
async def get_geo_context_endpoint(lat: float, lng: float):
    try:
        url = f"{SUPABASE_URL}/rest/v1/rpc/get_geo_context"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"lat_in": lat, "lng_in": lng}
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scenarios")
async def get_scenarios():
    """Return 3 diverse real events from distinct corridors — no hardcoded names."""
    try:
        # Use Supabase RPC/SQL via PostgREST to get one sample per distinct corridor
        rpc_url = f"{SUPABASE_URL}/rest/v1/rpc/get_diverse_scenarios"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        }
        rpc_res = requests.post(rpc_url, json={}, headers=headers)

        if rpc_res.status_code == 200 and rpc_res.json():
            return rpc_res.json()

        # Fallback: plain REST query for 3 events with different impact classes
        rest_url = f"{SUPABASE_URL}/rest/v1/historical_events"
        rest_headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
        scenarios = []
        for impact in ["HIGH", "MEDIUM", "LOW"]:
            params = {
                "impact_class": f"eq.{impact}",
                "corridor": "neq.Non-corridor",
                "limit": 1,
                "select": "lat,lng,corridor,zone,police_station,event_cause,impact_class",
            }
            res = requests.get(rest_url, params=params, headers=rest_headers)
            if res.status_code == 200:
                data = res.json()
                if data:
                    scenarios.append(data[0])

        # Last-resort: just grab 3 rows
        if len(scenarios) < 3:
            params = {
                "corridor": "neq.Non-corridor",
                "limit": 3,
                "select": "lat,lng,corridor,zone,police_station,event_cause,impact_class",
            }
            res = requests.get(rest_url, params=params, headers=rest_headers)
            if res.status_code == 200:
                scenarios = res.json()

        return scenarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/centroids")
async def get_centroids():
    """Return all cluster centroids from the Supabase cluster_centroids table."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/cluster_centroids"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
        params = {
            "select": "cluster_id,centroid_lat,centroid_lng",
            "order": "cluster_id.asc",
        }
        res = requests.get(url, params=params, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.text)
        return res.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict")
async def predict_impact(request: EventRequest):
    try:
        # 1. Feature Engineering
        input_df, geo_cluster, corridor_events_24h, confidence = preprocess_event(request)

        # 2. LightGBM Prediction
        predicted_impact = model.predict(input_df)[0]

        # 3. Rule-Based Recommendations
        plan = BASELINE_RESOURCES.get(
            predicted_impact, BASELINE_RESOURCES["Low"]
        ).copy()
        cause_mod = CAUSE_MODIFIERS.get(
            request.event_cause, {"add_manpower": 0, "special_equip": "None"}
        )

        plan["manpower"] += cause_mod["add_manpower"]
        plan["special_equipment"] = cause_mod["special_equip"]
        if request.corridor != "Non-corridor":
            plan["barricades"] = int(plan["barricades"] * 1.5)

        # 4. LLM Radio Dispatch Script
        sitrep_script = generate_sitrep(
            request, predicted_impact, plan, int(corridor_events_24h)
        )

        return {
            "status": "success",
            "prediction": {"impact_severity": predicted_impact.upper()},
            "recommendations": plan,
            "llm_dispatch_script": sitrep_script,
            "metadata": {
                "geo_cluster": int(geo_cluster),
                "cascading_events_24h": int(corridor_events_24h),
                "confidence": confidence,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    try:
        log_file = "validated_logs.json"
        logs = []
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = json.load(f)

        logs.append(request.model_dump())
        with open(log_file, "w") as f:
            json.dump(logs, f)

        return {
            "status": "success",
            "message": "Feedback logged.",
            "total_verified_logs": len(logs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retrain")
async def trigger_retraining():
    global model
    try:
        log_file = "validated_logs.json"
        if not os.path.exists(log_file):
            return {"status": "error", "message": "No logs collected yet."}

        with open(log_file, "r") as f:
            logs = json.load(f)

        if len(logs) < 5:
            return {
                "status": "waiting",
                "message": f"Need at least 5 logs to retrain. Currently have {len(logs)}.",
            }

        X_new_list = []
        y_new_list = []
        for log in logs:
            req = EventRequest(**log)
            input_df, _, _, _ = preprocess_event(req)
            X_new_list.append(input_df)
            y_new_list.append(log["actual_impact"].capitalize())

        X_new = pd.concat(X_new_list, ignore_index=True)
        y_new = pd.Series(y_new_list)

        for missing_class in ["Low", "Medium", "High"]:
            if missing_class not in y_new.values:
                y_new.loc[len(y_new)] = missing_class
                X_new.loc[len(X_new)] = X_new.iloc[0]

        print("Starting progressive retraining...")
        fine_tuned_model = lgb.LGBMClassifier(
            n_estimators=20, learning_rate=0.01, random_state=42
        )
        fine_tuned_model.fit(X_new, y_new, init_model=model)

        model = fine_tuned_model
        joblib.dump(model, "lightgbm_impact_model.pkl")
        os.remove(log_file)

        return {
            "status": "success",
            "message": "Model successfully fine-tuned with human feedback!",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
