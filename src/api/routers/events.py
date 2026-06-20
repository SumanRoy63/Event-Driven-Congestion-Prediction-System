import threading
from datetime import datetime, timedelta
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas.event import EventRequest
from src.api.schemas.response import EventResponse
from src.api.services.prediction_service import preprocess_event, predict_event
from src.api.services.model_manager import get_models_for_date, ModelOutOfBoundsException
from src.api.services.hotspot_service import determine_hotspot_rank
from src.api.services.recommendation_service import generate_recommendation
from src.data.alerts.email_alert import send_email_alert
from src.data.alerts.twilio_alert import send_twilio_alert, check_twilio_health
from src.api.db.database import get_db
from src.api.db.models import EventRecord

router = APIRouter()

# Thread-safe cooldown tracking to prevent spam
# Structure: {"zone_id": last_alert_datetime}
alert_cooldowns = {}
cooldown_lock = threading.Lock()
COOLDOWN_MINUTES = 10


@router.post("/events", response_model=EventResponse)
def create_event(payload: EventRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # 1. Fetch appropriate models based on event date
        models = get_models_for_date(payload.start_datetime)

        # 2. Evaluate Hotspot Rank internally using the versioned CSV
        hotspot_info = determine_hotspot_rank(payload.latitude, payload.longitude, models.get("hotspots_df"))
        
        # 3. Build Features
        features_df = preprocess_event(payload.dict(), models["categorical_encoders"])
        
        # 4. Predict Severity and Road Closure Probability
        prediction = predict_event(features_df, models)
        
        # 5. Generate Recommendation
        recommendation = generate_recommendation(
            severity=prediction["severity"],
            closure_prob=prediction["road_closure_probability"],
            hotspot_rank=hotspot_info["rank"]
        )
    except ModelOutOfBoundsException as mob:
        # Re-raise so it hits our custom 404 handler in main.py
        raise mob
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction pipeline failure: {str(e)}")
    
    should_alert = False
    
    # 6. Event-Driven Alerting with Thread-Safe Concurrency
    if prediction["severity"] == "High" or prediction["road_closure_probability"] > 0.8:
        
        # Use zone name if provided, otherwise fallback to coordinates
        zone_id = payload.zone if payload.zone and payload.zone != "Unknown" else f"{payload.latitude},{payload.longitude}"
        current_time = datetime.now()
        
        # Thread-Safe Cooldown Check: 
        # We acquire the lock to ensure no two concurrent API requests evaluate 
        # and write to the cooldown cache for the exact same zone simultaneously.
        # This guarantees atomic checks and strictly prevents duplicate email/SMS spam.
        with cooldown_lock:
            last_alert_time = alert_cooldowns.get(zone_id)
            if not last_alert_time or (current_time - last_alert_time) > timedelta(minutes=COOLDOWN_MINUTES):
                alert_cooldowns[zone_id] = current_time
                should_alert = True
                
        if should_alert:
            subject = f"URGENT: High Traffic Alert for {zone_id}"
            message = (
                f"A high severity event has been detected at {zone_id}.\n"
                f"Road Closure Probability: {prediction['road_closure_probability']:.2f}\n"
                f"Action Recommended: {recommendation['officers_needed']} officers needed."
            )
            
            # Non-blocking I/O Delivery: Email
            background_tasks.add_task(
                send_email_alert,
                subject,
                message,
                "roysuman892749@gmail.com"  # Hardcoded receiver as per existing email_alert.py
            )
            
            # Non-blocking I/O Delivery: Twilio SMS & WhatsApp
            background_tasks.add_task(
                send_twilio_alert,
                f"{subject}\n\n{message}"
            )
            
    # 7. Data Persistence
    try:
        zone_str = payload.zone if payload.zone and payload.zone != "Unknown" else f"{payload.latitude},{payload.longitude}"
        expected_att = payload.dict().get("expected_attendance", 0)
        
        db_event = EventRecord(
            timestamp=payload.start_datetime,
            event_type=payload.event_type,
            location=zone_str,
            expected_attendance=expected_att,
            road_closure_probability=float(prediction["road_closure_probability"]),
            predicted_severity=prediction["severity"],
            alert_triggered=should_alert
        )
        db.add(db_event)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
    
    return {
        "prediction": prediction,
        "recommendation": recommendation,
        "hotspot_info": hotspot_info
    }


@router.get("/events/history")
def get_event_history(db: Session = Depends(get_db)):
    """
    Retrieves the last 50 events from the SQLite database.
    """
    events = db.query(EventRecord).order_by(EventRecord.timestamp.desc()).limit(50).all()

    # Convert ORM objects to JSON-serializable dicts with geolocation
    results = []
    for e in events:
        lat = None
        lon = None
        zone = None

        # location may contain a zone name or "lat,lon"
        if e.location:
            if "," in str(e.location):
                try:
                    parts = str(e.location).split(",")
                    lat = float(parts[0])
                    lon = float(parts[1])
                except Exception:
                    lat = None
                    lon = None
            else:
                zone = e.location

        hour = e.timestamp.hour if getattr(e, "timestamp", None) else None
        month = e.timestamp.month if getattr(e, "timestamp", None) else None

        results.append({
            "id": e.id,
            "timestamp": e.timestamp.isoformat() if getattr(e, "timestamp", None) else None,
            "hour": hour,
            "month": month,
            "latitude": lat,
            "longitude": lon,
            "zone": zone,
            "event_type": e.event_type,
        })

    return results


@router.get("/alerts/twilio/health")
def twilio_health_check():
    """
    Internal health check endpoint to verify the Twilio service configuration 
    and environment variables without actually dispatching an SMS.
    """
    return check_twilio_health()


