import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="Smart Traffic AI System",
    layout="wide"
)

st.title("🚦 Smart Traffic Event Management System")
st.write("Dynamic API Dashboard (Priority 4 Implementation)")

# =====================================
# API SETTINGS
# =====================================
BASE_URL = "http://127.0.0.1:8000/api/v1"

# =====================================
# FETCH EVENT HISTORY
# =====================================
def fetch_event_history():
    try:
        response = requests.get(f"{BASE_URL}/events/history", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to connect to the backend server at {BASE_URL}. Ensure FastAPI is running! Error: {e}")
        return []

# =====================================
# SIDEBAR: EVENT SIMULATION FORM
# =====================================
st.sidebar.title("🚨 Event Simulation Form")
st.sidebar.write("Inject a new traffic event into the AI pipeline.")

with st.sidebar.form("event_simulation_form"):
    event_type = st.text_input("Event Type", value="Political Rally")
    zone = st.text_input("Zone / Location", value="Downtown")
    expected_attendance = st.number_input("Expected Attendance", min_value=0, value=5000)
    latitude = st.number_input("Latitude", value=12.9716, format="%.4f")
    longitude = st.number_input("Longitude", value=77.5946, format="%.4f")
    start_datetime = st.text_input("Start Datetime (ISO format)", value=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
    
    submit_button = st.form_submit_button("Submit Event to AI Backend")
    
    if submit_button:
        payload = {
            "event_type": event_type,
            "latitude": latitude,
            "longitude": longitude,
            "start_datetime": start_datetime,
            "zone": zone,
            "expected_attendance": expected_attendance
        }
        
        with st.spinner("Processing event and running AI models..."):
            try:
                post_response = requests.post(f"{BASE_URL}/events", json=payload, timeout=10)
                post_response.raise_for_status()
                result = post_response.json()
                
                prediction = result.get("prediction", {})
                recommendation = result.get("recommendation", {})
                
                st.sidebar.success(f"**Predicted Severity:** {prediction.get('severity', 'Unknown')}")
                st.sidebar.info(f"**Closure Probability:** {prediction.get('road_closure_probability', 0.0):.2%}")
                st.sidebar.warning(f"**Officers Needed:** {recommendation.get('officers_needed', 'N/A')}")
                
                # Rerun to instantly refresh the history table on the right
                st.rerun()
                
            except Exception as e:
                st.sidebar.error(f"Failed to submit event: {e}")

# =====================================
# MAIN DASHBOARD: EVENT HISTORY
# =====================================
st.subheader("📋 Recent Event History (Live Database)")

history_data = fetch_event_history()

if history_data:
    df_history = pd.DataFrame(history_data)
    
    # Clean up column order for better presentation
    cols = [
        "id", "timestamp", "event_type", "location", "expected_attendance", 
        "predicted_severity", "road_closure_probability", "alert_triggered"
    ]
    display_cols = [c for c in cols if c in df_history.columns] + [c for c in df_history.columns if c not in cols]
    
    df_history = df_history[display_cols]
    
    st.dataframe(df_history, use_container_width=True)
else:
    st.info("No events found in the database. Use the sidebar to simulate one!")

# =====================================
# FOOTER
# =====================================
st.markdown("---")
st.write("Flipkart Grid 2.0 Hackathon - Fully integrated with SQLite + SQLAlchemy + FastAPI")