import streamlit as st
import pandas as pd
import requests
import json
import os

import plotly.express as px

# =====================================
# CONSTANTS
# =====================================

API_BASE = "http://127.0.0.1:8000/api/v1"
REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "model_registry.json",
)

REQUIRED_COLUMNS = [
    "hour", "month", "latitude", "longitude",
    "zone", "event_type",
]

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="Smart Traffic AI System",
    layout="wide"
)

# =====================================
# GLOBAL DATA FETCH (API-backed)
# =====================================

@st.cache_data(ttl=30)
def fetch_event_history():
    """
    Fetch event history from the FastAPI backend.
    Falls back to an empty DataFrame with required columns
    if the backend is unreachable so that the charts don't crash.
    """
    try:
        resp = requests.get(f"{API_BASE}/events/history", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data:
            return pd.DataFrame(data)
    except Exception:
        pass

    return pd.DataFrame(columns=REQUIRED_COLUMNS)


df = fetch_event_history()

# =====================================
# HELPER: Load Model Registry
# =====================================

def load_model_registry():
    """Read model_registry.json for the System Management panel."""
    try:
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"versions": {}}


# =====================================
# SIDEBAR
# =====================================

st.sidebar.title(
    "Traffic AI Dashboard"
)

page = st.sidebar.radio(

    "Select Module",

    [
        "Overview",
        "Analytics",
        "Prediction",
        "Hotspots",
        "Recommendations",
        "System Management",
    ]
)

# =====================================
# OVERVIEW
# =====================================

if page == "Overview":

    st.title(
        "🚦 Smart Traffic Event Management System"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Events",
        len(df)
    )

    c2.metric(
        "Columns",
        df.shape[1]
    )

    c3.metric(
        "Unique Zones",
        df["zone"].nunique()
        if "zone" in df.columns else "-"
    )

    c4.metric(
        "Event Types",
        df["event_type"].nunique()
        if "event_type" in df.columns else "-"
    )

    st.dataframe(
        df.head()
    )

# =====================================
# ANALYTICS
# =====================================

elif page == "Analytics":

    st.title(
        "📊 Event Analytics"
    )

    if "hour" in df.columns:

        fig = px.histogram(

            df,

            x="hour",

            title="Events by Hour"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    if "month" in df.columns:

        fig = px.histogram(

            df,

            x="month",

            title="Monthly Trend"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================================
# PREDICTION (API-driven)
# =====================================

elif page == "Prediction":

    st.title("🤖 AI Prediction")

    st.info(
        "Fill in the event details below and hit **Predict** "
        "to get a severity and road-closure assessment from the backend."
    )

    # ---- Input Form ----
    col1, col2 = st.columns(2)

    with col1:
        event_type = st.text_input("Event Type", value="Accident")
        latitude = st.number_input("Latitude", value=12.9716, format="%.6f")
        longitude = st.number_input("Longitude", value=77.5946, format="%.6f")
        zone = st.text_input("Zone", value="Unknown")

    with col2:
        start_datetime = st.text_input(
            "Start Datetime (ISO 8601)",
            value="2024-03-15T10:00:00"
        )
        endlatitude = st.number_input("End Latitude", value=0.0, format="%.6f")
        endlongitude = st.number_input("End Longitude", value=0.0, format="%.6f")
        expected_attendance = st.number_input(
            "Expected Attendance", value=0, step=100
        )

    # ---- Predict ----
    if st.button("Predict"):

        payload = {
            "event_type": event_type,
            "latitude": latitude,
            "longitude": longitude,
            "start_datetime": start_datetime,
            "endlatitude": endlatitude,
            "endlongitude": endlongitude,
            "zone": zone,
            "expected_attendance": expected_attendance,
        }

        try:
            resp = requests.post(
                f"{API_BASE}/events",
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            result = resp.json()

            prediction = result.get("prediction", {})
            recommendation = result.get("recommendation", {})
            hotspot_info = result.get("hotspot_info", {})

            st.success(
                f"Road Closure Probability: "
                f"{prediction.get('road_closure_probability', 0):.2%}"
            )

            st.success(
                f"Predicted Severity: "
                f"{prediction.get('severity', 'N/A')}"
            )

            st.markdown("---")
            st.subheader("📋 Recommendation")

            r1, r2, r3, r4 = st.columns(4)
            r1.metric(
                "Risk Score",
                recommendation.get("risk_score", "-")
            )
            r2.metric(
                "Officers Needed",
                recommendation.get("traffic_officers", "-")
            )
            r3.metric(
                "Barricades",
                recommendation.get("barricades", "-")
            )
            r4.metric(
                "Alert Level",
                recommendation.get("alert_level", "-")
            )

            st.markdown("---")
            st.subheader("📍 Hotspot Info")
            st.json(hotspot_info)

        except requests.exceptions.ConnectionError:
            st.error(
                "Backend is offline. Start the FastAPI server: "
                "`uvicorn src.api.main:app --reload`"
            )
        except requests.exceptions.HTTPError as http_err:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            st.error(f"API Error ({resp.status_code}): {detail}")
        except Exception as e:
            st.error(f"Prediction Error: {e}")


# =====================================
# HOTSPOTS
# =====================================

elif page == "Hotspots":

    st.title(
        "🔥 Traffic Hotspots"
    )

    if (
        "latitude" in df.columns
        and
        "longitude" in df.columns
        and
        len(df) > 0
    ):

        fig = px.scatter_map(

            df,

            lat="latitude",

            lon="longitude",

            zoom=9,

            height=600
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        st.warning(
            "No event history with coordinates available. "
            "Submit events via the Prediction tab first."
        )

    # Hotspot cluster table via API history (no local CSV dependency)
    try:
        hotspot_df = pd.read_csv(
            "outputs/hotspot_clusters.csv"
        )

        st.subheader(
            "Hotspot Ranking"
        )

        st.dataframe(
            hotspot_df.head(20)
        )

    except Exception:

        st.warning(
            "Hotspot cluster data not available. "
            "Run hotspot_detection.py or trigger a retrain via System Management."
        )

# =====================================
# RECOMMENDATIONS
# =====================================

elif page == "Recommendations":

    st.title(
        "🚨 Traffic Recommendations"
    )

    severity = st.selectbox(

        "Severity",

        ["Low", "Medium", "High"]
    )

    closure_prob = st.slider(

        "Road Closure Probability",

        0.0,
        1.0,
        0.75
    )

    hotspot_rank = st.slider(

        "Hotspot Rank",

        1,
        10,
        3
    )

    if st.button(
        "Generate Recommendation"
    ):

        payload = {
            "severity": severity,
            "road_closure_probability": closure_prob,
            "hotspot_rank": hotspot_rank,
        }

        try:
            resp = requests.post(
                f"{API_BASE}/recommendations",
                json=payload,
                timeout=5,
            )
            resp.raise_for_status()
            rec = resp.json()

            st.metric(
                "Risk Score",
                rec.get("risk_score", "-")
            )

            st.write(
                f"👮 Officers Required: {rec.get('traffic_officers', '-')}"
            )

            st.write(
                f"🚧 Barricades: {rec.get('barricades', '-')}"
            )

            st.write(
                f"📢 Alert Level: {rec.get('alert_level', '-')}"
            )

        except requests.exceptions.ConnectionError:
            st.error(
                "Backend is offline. Start the FastAPI server."
            )
        except Exception as e:
            st.error(f"Error: {e}")


# =====================================
# SYSTEM MANAGEMENT (new tab)
# =====================================

elif page == "System Management":

    st.title("⚙️ System Management")

    # ----- Section 1: Data Ingestion (Create) -----
    st.header("📥 Data Ingestion — Create New Model")
    st.caption(
        "Upload a new raw CSV file of events. The backend will preprocess "
        "the data, retrain XGBoost models, and register a new version automatically."
    )

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        key="ingest_uploader",
    )

    date_range = st.text_input(
        "Date Range Label (for registry metadata)",
        value="2024-01-01 to 2024-12-31",
        help="Descriptive label passed to the backend. "
             "Actual dates are extracted from the CSV automatically.",
    )

    if uploaded_file is not None:
        if st.button("🚀 Upload & Retrain"):
            try:
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "text/csv",
                    )
                }
                resp = requests.post(
                    f"{API_BASE}/ingest",
                    files=files,
                    params={"date_range": date_range},
                    timeout=30,
                )
                resp.raise_for_status()
                result = resp.json()
                st.success(result.get("message", "Upload complete."))
                st.cache_data.clear()

            except requests.exceptions.ConnectionError:
                st.error(
                    "Backend is offline. Start the FastAPI server."
                )
            except requests.exceptions.HTTPError:
                try:
                    detail = resp.json()
                except Exception:
                    detail = resp.text
                st.error(f"API Error ({resp.status_code}): {detail}")
            except Exception as e:
                st.error(f"Upload Error: {e}")

    st.markdown("---")

    # ----- Section 2: Model Registry — View & Delete -----
    st.header("🧠 Model Registry")
    st.caption(
        "All registered model versions. You can delete individual versions "
        "or reset the entire system."
    )

    # Fetch registry from the API (not local filesystem)
    try:
        reg_resp = requests.get(f"{API_BASE}/admin/models", timeout=5)
        reg_resp.raise_for_status()
        registry = reg_resp.json()
    except Exception:
        # Fallback to local file if API is down
        registry = load_model_registry()

    versions = registry.get("versions", {})

    if not versions:
        st.info("📭 No model versions registered. Upload a CSV above to create one.")
    else:
        for version_name, meta in versions.items():
            with st.expander(f"🏷️ {version_name}", expanded=True):
                m1, m2, m3 = st.columns(3)
                m1.metric("Start Date", meta.get("start_date", "—"))
                m2.metric("End Date", meta.get("end_date", "—"))

                desc = meta.get("description", "")
                model_path = meta.get("path", "")
                hotspots_path = meta.get("hotspots_path", "")

                if desc:
                    m3.metric("Description", desc[:30])
                else:
                    m3.metric("Model Path", model_path if model_path else "root")

                st.info(
                    f"**Artifacts:** `models/{model_path}/road_closure_xgb.pkl`, "
                    f"`models/{model_path}/severity_xgb.pkl`, "
                    f"`models/{model_path}/priority_encoder.pkl`  \n"
                    f"**Hotspots CSV:** `{hotspots_path}`"
                )

                # ---- Delete this version ----
                if st.button(
                    f"🗑️ Delete {version_name}",
                    key=f"delete_{version_name}",
                    type="primary",
                ):
                    try:
                        del_resp = requests.delete(
                            f"{API_BASE}/admin/models/{version_name}",
                            timeout=10,
                        )
                        del_resp.raise_for_status()
                        result = del_resp.json()
                        st.success(
                            f"✅ {result.get('message', 'Deleted.')} "
                            f"Artifacts removed: {result.get('deleted_artifacts', [])}"
                        )
                        st.cache_data.clear()
                        st.rerun()
                    except requests.exceptions.ConnectionError:
                        st.error("Backend is offline.")
                    except requests.exceptions.HTTPError:
                        try:
                            detail = del_resp.json()
                        except Exception:
                            detail = del_resp.text
                        st.error(f"Delete failed ({del_resp.status_code}): {detail}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.markdown("---")

    # ----- Section 3: Full System Reset -----
    st.header("🔄 Full System Reset")
    st.caption(
        "⚠️ This will wipe **all** model versions, purge the event database, "
        "and clear the in-memory model cache. This action is irreversible."
    )

    col_reset, col_spacer = st.columns([1, 3])
    with col_reset:
        if st.button("💣 Reset Entire System", type="primary"):
            try:
                reset_resp = requests.post(
                    f"{API_BASE}/admin/reset",
                    timeout=10,
                )
                reset_resp.raise_for_status()
                result = reset_resp.json()
                st.success(f"✅ {result.get('message', 'System reset complete.')}")
                st.cache_data.clear()
                st.rerun()
            except requests.exceptions.ConnectionError:
                st.error("Backend is offline. Start the FastAPI server.")
            except Exception as e:
                st.error(f"Reset failed: {e}")

    st.markdown("---")

    # ----- Section 4: Backend Health -----
    st.header("💚 Backend Health Check")

    if st.button("Ping Backend"):
        try:
            resp = requests.get("http://127.0.0.1:8000/health", timeout=3)
            resp.raise_for_status()
            health = resp.json()
            st.success(
                f"✅ **{health.get('service', 'API')}** is "
                f"**{health.get('status', 'unknown')}**"
            )
        except requests.exceptions.ConnectionError:
            st.error("❌ Backend is unreachable at http://127.0.0.1:8000")
        except Exception as e:
            st.error(f"Health check failed: {e}")

# =====================================
# FOOTER
# =====================================

st.sidebar.markdown("---")
st.sidebar.write(
    "Flipkart Grid 2.0 Hackathon"
)