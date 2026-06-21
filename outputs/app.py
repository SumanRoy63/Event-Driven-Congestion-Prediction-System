import os
import streamlit as st
import pandas as pd
import requests
import json
import os
import numpy as np
<<<<<<< Updated upstream

import plotly.express as px
import plotly.graph_objects as go
# =====================================
# CONSTANTS
# =====================================

API_BASE = "http://127.0.0.1:8000/api/v1"
REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "model_registry.json",
)
RAW_EVENTS_CSV_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv",
    )
)

REQUIRED_COLUMNS = [
    "hour", "month", "latitude", "longitude",
    "zone", "event_type", "address",
]

=======
import joblib
import plotly.express as px
import plotly.graph_objects as go
>>>>>>> Stashed changes
# =====================================
# CONFIG
# =====================================

st.set_page_config(
    page_title="Smart Traffic AI System",
    layout="wide"
)

<<<<<<< Updated upstream
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
            df = pd.DataFrame(data)

            # Normalize timestamp and derive hour/month when missing
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            if "hour" not in df.columns or df["hour"].isna().all():
                if "timestamp" in df.columns:
                    df["hour"] = df["timestamp"].dt.hour
                else:
                    df["hour"] = pd.NA
            if "month" not in df.columns or df["month"].isna().all():
                if "timestamp" in df.columns:
                    df["month"] = df["timestamp"].dt.month
                else:
                    df["month"] = pd.NA

            # Ensure latitude/longitude are numeric
            if "latitude" in df.columns:
                df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
            else:
                df["latitude"] = pd.NA

            if "longitude" in df.columns:
                df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
            else:
                df["longitude"] = pd.NA

            # Clean up common missing columns
            for c in REQUIRED_COLUMNS:
                if c not in df.columns:
                    df[c] = pd.NA

            return df
    except Exception:
        pass

    return pd.DataFrame(columns=REQUIRED_COLUMNS)


@st.cache_data(ttl=30)
def load_raw_event_addresses():
    """Load raw CSV event addresses for the Hotspots page."""
    try:
        raw_df = pd.read_csv(RAW_EVENTS_CSV_PATH)
        if "latitude" in raw_df.columns:
            raw_df["latitude"] = pd.to_numeric(raw_df["latitude"], errors="coerce")
        if "longitude" in raw_df.columns:
            raw_df["longitude"] = pd.to_numeric(raw_df["longitude"], errors="coerce")
        return raw_df
    except Exception:
        return pd.DataFrame(columns=["latitude", "longitude", "address"])


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

=======
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROCESSED_CSV_PATH = os.path.join(ROOT_DIR, "data", "processed", "processed_events.csv")
RAW_CSV_PATH = os.path.join(ROOT_DIR, "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv")
HOTSPOT_CSV_PATH = os.path.join(os.path.dirname(__file__), "hotspot_clusters.csv")
ROAD_MODEL_PATH = os.path.join(ROOT_DIR, "models", "road_closure_xgb.pkl")
SEVERITY_MODEL_PATH = os.path.join(ROOT_DIR, "models", "severity_xgb.pkl")
PRIORITY_ENCODER_PATH = os.path.join(ROOT_DIR, "models", "priority_encoder.pkl")

# =====================================
# DATA LOADING
# =====================================

@st.cache_data(show_spinner=False)
def load_processed_data():
    try:
        df = pd.read_csv(PROCESSED_CSV_PATH)
        if "start_datetime" in df.columns:
            df["start_datetime"] = pd.to_datetime(df["start_datetime"], errors="coerce")
            df["hour"] = df["start_datetime"].dt.hour
            df["month"] = df["start_datetime"].dt.month
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_raw_data():
    try:
        raw_df = pd.read_csv(RAW_CSV_PATH)
        if "latitude" in raw_df.columns:
            raw_df["latitude"] = pd.to_numeric(raw_df["latitude"], errors="coerce")
        if "longitude" in raw_df.columns:
            raw_df["longitude"] = pd.to_numeric(raw_df["longitude"], errors="coerce")
        return raw_df
    except Exception:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_hotspot_data():
    try:
        return pd.read_csv(HOTSPOT_CSV_PATH)
    except Exception:
        return pd.DataFrame()


@st.cache_resource(show_spinner=False)
def load_models():
    models = {
        "road": None,
        "severity": None,
        "encoder": None,
        "road_features": [],
        "severity_features": [],
    }
    try:
        models["road"] = joblib.load(ROAD_MODEL_PATH)
        models["road_features"] = getattr(models["road"], "feature_names_in_", []).tolist()
    except Exception:
        pass
    try:
        models["severity"] = joblib.load(SEVERITY_MODEL_PATH)
        models["severity_features"] = getattr(models["severity"], "feature_names_in_", []).tolist()
    except Exception:
        pass
    try:
        models["encoder"] = joblib.load(PRIORITY_ENCODER_PATH)
    except Exception:
        pass
    return models


def estimate_delay_and_radius(severity, closure_prob, hotspot_rank, expected_attendance):
    severity_weights = {
        "Low": 0.9,
        "Medium": 1.4,
        "High": 2.1,
    }
    severity_factor = severity_weights.get(severity, 1.0)
    hotspot_rank = min(max(hotspot_rank, 1), 20)
    attendance_factor = min(max(expected_attendance, 0), 2000) / 2000

    delay_minutes = int(
        round(
            5
            + closure_prob * 70
            + (21 - hotspot_rank) * 3
            + severity_factor * 12
            + attendance_factor * 20
        )
    )
    delay_minutes = min(max(delay_minutes, 5), 240)

    affected_radius_km = round(
        min(
            6.0,
            max(
                0.5,
                0.5
                + closure_prob * 2.5
                + (21 - hotspot_rank) * 0.12
                + attendance_factor * 0.8
                + (severity_factor - 1.0) * 0.9
            ),
        ),
        2,
    )

    return delay_minutes, affected_radius_km


df = load_processed_data()
raw_df = load_raw_data()
hotspot_df = load_hotspot_data()
models = load_models()
>>>>>>> Stashed changes

# =====================================
# SIDEBAR
# =====================================

st.sidebar.title("Traffic AI Dashboard")
page = st.sidebar.radio(
    "Select Module",
    ["Overview", "Analytics", "Prediction", "Hotspots", "Recommendations"],
)

<<<<<<< Updated upstream
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
=======
st.sidebar.markdown("---")
st.sidebar.markdown(
    "Built for traffic event analytics, prediction, and recommendation."
>>>>>>> Stashed changes
)

# =====================================
# OVERVIEW MODULE
# =====================================

if page == "Overview":
    st.title("🚦 Smart Traffic Event Management System")
    st.markdown("Quick summary of traffic event coverage, event counts, and data quality.")

    total_events = len(df)
    unique_zones = int(df["zone"].nunique()) if "zone" in df.columns else 0
    unique_event_types = int(df["event_type"].nunique()) if "event_type" in df.columns else 0
    geo_events = len(df.dropna(subset=["latitude", "longitude"])) if {"latitude", "longitude"}.issubset(df.columns) else 0

<<<<<<< Updated upstream
    st.markdown("### 📈 System Status & Key Metrics")

    # Row 1: Main Metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Events",
        len(df),
        delta="Last 50 loaded" if len(df) > 0 else "No data"
    )

    unique_zones = df["zone"].nunique() if "zone" in df.columns else 0
    col2.metric(
        "Unique Zones",
        unique_zones,
        delta=f"Active regions" if unique_zones > 0 else "N/A"
    )

    unique_event_types = df["event_type"].nunique() if "event_type" in df.columns else 0
    col3.metric(
        "Event Types",
        unique_event_types,
        delta=f"Categories" if unique_event_types > 0 else "N/A"
    )

    events_with_coords = (
        df[["latitude", "longitude"]].notna().all(axis=1).sum()
        if "latitude" in df.columns and "longitude" in df.columns
        else 0
    )
    col4.metric(
        "Geo-Located",
        events_with_coords,
        delta=f"{(events_with_coords / len(df) * 100 if len(df) > 0 else 0):.0f}%" if len(df) > 0 else "0%"
    )

    st.markdown("---")

    # Row 2: Distribution Charts
    if not df.empty:
        col_a, col_b = st.columns(2)

        # Event Type Distribution
        if "event_type" in df.columns and df["event_type"].notna().any():
            with col_a:
                st.markdown("#### 📊 Events by Type")
                event_counts = df["event_type"].value_counts().head(10)
                fig_type = px.pie(
                    values=event_counts.values,
                    names=event_counts.index,
                    title="Event Type Breakdown"
                )
                st.plotly_chart(fig_type, use_container_width=True)

        # Zone Distribution
        if "zone" in df.columns and df["zone"].nunique() > 0:
            with col_b:
                st.markdown("#### 🗺️ Events by Zone")
                zone_counts = df["zone"].value_counts().head(10)
                fig_zone = px.bar(
                    x=zone_counts.index,
                    y=zone_counts.values,
                    title="Top 10 Zones",
                    labels={"x": "Zone", "y": "Count"}
                )
                st.plotly_chart(fig_zone, use_container_width=True)

        st.markdown("---")

        # Row 3: Time-based Insights
        col_x, col_y = st.columns(2)

        if "hour" in df.columns and df["hour"].notna().any():
            with col_x:
                st.markdown("#### 🕐 Events by Hour")
                hour_data = df["hour"].dropna().astype(int).value_counts().sort_index()
                fig_hour = px.line(
                    x=hour_data.index,
                    y=hour_data.values,
                    markers=True,
                    title="Hourly Distribution",
                    labels={"x": "Hour of Day", "y": "Count"}
                )
                st.plotly_chart(fig_hour, use_container_width=True)

        if "month" in df.columns and df["month"].notna().any():
            with col_y:
                st.markdown("#### 📅 Events by Month")
                month_data = df["month"].dropna().astype(int).value_counts().sort_index()
                month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                              7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
                month_labels = [month_names.get(int(m), str(m)) for m in month_data.index]
                fig_month = px.bar(
                    x=month_labels,
                    y=month_data.values,
                    title="Monthly Distribution",
                    labels={"x": "Month", "y": "Count"}
                )
                st.plotly_chart(fig_month, use_container_width=True)

        st.markdown("---")

        # Row 4: Data Quality & Latest Events
        st.markdown("#### 📋 Data Quality & Sample")
        col_info1, col_info2 = st.columns(2)

        with col_info1:
            st.markdown("**Data Completeness**")
            completeness = {}
            for col in df.columns:
                missing_pct = (df[col].isna().sum() / len(df) * 100)
                completeness[col] = 100 - missing_pct
            completeness_df = pd.DataFrame(
                list(completeness.items()),
                columns=["Field", "Completeness (%)"]
            ).sort_values("Completeness (%)", ascending=False)
            st.dataframe(completeness_df, hide_index=True, use_container_width=True)

        with col_info2:
            st.markdown("**Recent Events**")
            display_cols_overview = [
                c for c in ["timestamp", "event_type", "zone", "address", "latitude", "longitude"]
                if c in df.columns
            ]
            st.dataframe(df[display_cols_overview].head(10), hide_index=True, use_container_width=True)

    else:
        st.info("📭 No event data available. Submit events via the Prediction tab to populate the dashboard.")
=======
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Events", total_events)
    c2.metric("Unique Zones", unique_zones)
    c3.metric("Unique Event Types", unique_event_types)
    c4.metric("Geo-located Events", geo_events, f"{(geo_events / total_events * 100 if total_events > 0 else 0):.0f}%")

    st.markdown("---")

    if df.empty:
        st.warning("Processed dataset not found or empty.")
    else:
        metrics_col1, metrics_col2 = st.columns(2)

        with metrics_col1:
            if "event_type" in df.columns:
                type_counts = df["event_type"].value_counts().head(8)
                fig_type = px.bar(
                    x=type_counts.values,
                    y=type_counts.index,
                    orientation="h",
                    title="Top Event Types",
                    labels={"x": "Count", "y": "Event Type"},
                    color=type_counts.values,
                    color_continuous_scale="Blues",
                )
                fig_type.update_layout(showlegend=False)
                st.plotly_chart(fig_type, use_container_width=True)

        with metrics_col2:
            if "zone" in df.columns:
                zone_counts = df["zone"].value_counts().head(8)
                fig_zone = px.bar(
                    x=zone_counts.values,
                    y=zone_counts.index,
                    orientation="h",
                    title="Top Zones",
                    labels={"x": "Count", "y": "Zone"},
                    color=zone_counts.values,
                    color_continuous_scale="Greens",
                )
                fig_zone.update_layout(showlegend=False)
                st.plotly_chart(fig_zone, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📋 Data Quality")
        completeness = (100 - df.isna().mean() * 100).round(1).sort_values(ascending=False)
        quality_df = pd.DataFrame({"Field": completeness.index, "Completeness (%)": completeness.values})
        st.dataframe(quality_df, hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🔍 Sample Records")
        display_columns = [c for c in ["start_datetime", "event_type", "zone", "address", "latitude", "longitude"] if c in df.columns]
        st.dataframe(df[display_columns].head(10), use_container_width=True)
>>>>>>> Stashed changes

# =====================================
# ANALYTICS MODULE
# =====================================

elif page == "Analytics":
    st.title("📊 Event Analytics")
    st.markdown("Analyze event timing, type distribution, and location-based trends.")

<<<<<<< Updated upstream
    st.title("📊 Event Analytics Dashboard")
    
    st.markdown("Comprehensive analysis of traffic events with detailed breakdowns and trends.")

    if df.empty:
        st.warning("⚠️ No event data available. Submit events via Prediction tab first.")
    else:
        # Row 1: Time-based Analysis
        st.markdown("### ⏰ Temporal Analysis")
        col_hour, col_month = st.columns(2)

        with col_hour:
            if "hour" in df.columns and df["hour"].notna().any():
                st.markdown("#### Events by Hour of Day")
                hour_data = df["hour"].dropna().astype(int).value_counts().sort_index()
                fig_hour = px.bar(
                    x=hour_data.index,
                    y=hour_data.values,
                    labels={"x": "Hour of Day", "y": "Event Count"},
                    title="Hourly Distribution",
                    color=hour_data.values,
                    color_continuous_scale="Viridis"
                )
                fig_hour.update_layout(showlegend=False)
                st.plotly_chart(fig_hour, use_container_width=True)
                
                st.markdown("**Data Table**")
                hour_table = pd.DataFrame({
                    "Hour": hour_data.index,
                    "Count": hour_data.values,
                    "Percentage": (hour_data.values / hour_data.sum() * 100).round(2)
                })
                st.dataframe(hour_table, hide_index=True, use_container_width=True)
            else:
                st.info("Hour data not available")

        with col_month:
            if "month" in df.columns and df["month"].notna().any():
                st.markdown("#### Events by Month")
                month_data = df["month"].dropna().astype(int).value_counts().sort_index()
                month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                              7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
                month_labels = [month_names.get(int(m), str(m)) for m in month_data.index]
                
                fig_month = px.bar(
                    x=month_labels,
                    y=month_data.values,
                    labels={"x": "Month", "y": "Event Count"},
                    title="Monthly Trend",
                    color=month_data.values,
                    color_continuous_scale="Blues"
                )
                fig_month.update_layout(showlegend=False)
                st.plotly_chart(fig_month, use_container_width=True)
                
                st.markdown("**Data Table**")
                month_table = pd.DataFrame({
                    "Month": month_labels,
                    "Count": month_data.values,
                    "Percentage": (month_data.values / month_data.sum() * 100).round(2)
                })
                st.dataframe(month_table, hide_index=True, use_container_width=True)
            else:
                st.info("Month data not available")

        st.markdown("---")

        # Row 2: Event Type & Zone Analysis
        st.markdown("### 📋 Event Classification Analysis")
        col_type, col_zone = st.columns(2)

        with col_type:
            if "event_type" in df.columns and df["event_type"].notna().any():
                st.markdown("#### Events by Type")
                type_data = df["event_type"].value_counts().head(15)
                fig_type = px.bar(
                    x=type_data.values,
                    y=type_data.index,
                    orientation="h",
                    labels={"x": "Count", "y": "Event Type"},
                    title="Top 15 Event Types",
                    color=type_data.values,
                    color_continuous_scale="Reds"
                )
                fig_type.update_layout(showlegend=False)
                st.plotly_chart(fig_type, use_container_width=True)
                
                st.markdown("**Data Table**")
                type_table = pd.DataFrame({
                    "Event Type": type_data.index,
                    "Count": type_data.values,
                    "Percentage": (type_data.values / type_data.sum() * 100).round(2)
                })
                st.dataframe(type_table, hide_index=True, use_container_width=True)
            else:
                st.info("Event Type data not available")

        with col_zone:
            if "zone" in df.columns and df["zone"].notna().any() and df["zone"].nunique() > 1:
                st.markdown("#### Events by Zone")
                zone_data = df["zone"].value_counts().head(15)
                fig_zone = px.bar(
                    x=zone_data.values,
                    y=zone_data.index,
                    orientation="h",
                    labels={"x": "Count", "y": "Zone"},
                    title="Top 15 Zones",
                    color=zone_data.values,
                    color_continuous_scale="Greens"
                )
                fig_zone.update_layout(showlegend=False)
                st.plotly_chart(fig_zone, use_container_width=True)
                
                st.markdown("**Data Table**")
                zone_table = pd.DataFrame({
                    "Zone": zone_data.index,
                    "Count": zone_data.values,
                    "Percentage": (zone_data.values / zone_data.sum() * 100).round(2)
                })
                st.dataframe(zone_table, hide_index=True, use_container_width=True)
            else:
                st.info("Zone data not available or all events in single zone")

        st.markdown("---")

        # Row 3: Cross-tabulation Analysis
        st.markdown("### 🔀 Event Type × Hour Analysis")
        if "hour" in df.columns and "event_type" in df.columns:
            df_cross = df.dropna(subset=["hour", "event_type"]).copy()
            if len(df_cross) > 0:
                df_cross["hour"] = df_cross["hour"].astype(int)
                crosstab = pd.crosstab(df_cross["hour"], df_cross["event_type"])
                
                # Heatmap
                fig_heatmap = px.imshow(
                    crosstab,
                    labels={"x": "Event Type", "y": "Hour", "color": "Count"},
                    title="Event Type × Hour Heatmap",
                    color_continuous_scale="YlOrRd",
                    aspect="auto"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                st.markdown("**Cross-tabulation Data**")
                st.dataframe(crosstab, use_container_width=True)
            else:
                st.info("Insufficient data for cross-tabulation")
        else:
            st.info("Hour or Event Type data not available")

        st.markdown("---")

        # Row 4: Geographic Analysis
        st.markdown("### 📍 Geographic Distribution")
        col_geo1, col_geo2 = st.columns(2)

        with col_geo1:
            if "latitude" in df.columns and "longitude" in df.columns:
                coords_available = df[["latitude", "longitude"]].notna().all(axis=1).sum()
                total_events = len(df)
                st.metric(
                    "Geo-Located Events",
                    coords_available,
                    f"{(coords_available / total_events * 100 if total_events > 0 else 0):.1f}%"
                )

        with col_geo2:
            if "address" in df.columns:
                address_available = df["address"].notna().sum()
                total_events = len(df)
                st.metric(
                    "Events with Address",
                    address_available,
                    f"{(address_available / total_events * 100 if total_events > 0 else 0):.1f}%"
                )

        st.markdown("---")

        # Row 5: Summary Statistics
        st.markdown("### 📈 Summary Statistics")
        col_stat1, col_stat2, col_stat3 = st.columns(3)

        with col_stat1:
            st.metric("Total Events", len(df))
            if "hour" in df.columns and df["hour"].notna().any():
                avg_hour = df["hour"].dropna().mean()
                st.metric("Avg Hour of Day", f"{avg_hour:.1f}:00")

        with col_stat2:
            unique_event_types = df["event_type"].nunique() if "event_type" in df.columns else 0
            st.metric("Unique Event Types", unique_event_types)
            if "month" in df.columns and df["month"].notna().any():
                avg_month = df["month"].dropna().mean()
                st.metric("Avg Month", f"Month {avg_month:.1f}")

        with col_stat3:
            unique_zones = df["zone"].nunique() if "zone" in df.columns else 0
            st.metric("Unique Zones", unique_zones)
            events_last_10 = len(df.head(10))
            st.metric("Sample Size", len(df), f"(Latest 10: {events_last_10})")

        st.markdown("---")

        # Row 6: Raw Data Explorer
        st.markdown("### 🔍 Raw Data Explorer")
        
        tab1, tab2, tab3 = st.tabs(["Full Dataset", "Event Type Filter", "Zone Filter"])
        
        with tab1:
            st.markdown("**Complete Event Dataset** (Last 100 records)")
            display_cols = [c for c in ["timestamp", "event_type", "zone", "address", "hour", "month", "latitude", "longitude"] if c in df.columns]
            st.dataframe(df[display_cols].head(100), use_container_width=True)
        
        with tab2:
            if "event_type" in df.columns and df["event_type"].nunique() > 0:
                selected_type = st.selectbox("Select Event Type:", df["event_type"].dropna().unique())
                filtered_type = df[df["event_type"] == selected_type]
                display_cols = [c for c in ["timestamp", "event_type", "zone", "address", "hour", "month"] if c in df.columns]
                st.dataframe(filtered_type[display_cols].head(50), use_container_width=True)
                st.write(f"**Total events of type '{selected_type}': {len(filtered_type)}**")
        
        with tab3:
            if "zone" in df.columns and df["zone"].nunique() > 1:
                selected_zone = st.selectbox("Select Zone:", df["zone"].dropna().unique())
                filtered_zone = df[df["zone"] == selected_zone]
                display_cols = [c for c in ["timestamp", "event_type", "zone", "address", "hour", "month"] if c in df.columns]
                st.dataframe(filtered_zone[display_cols].head(50), use_container_width=True)
                st.write(f"**Total events in zone '{selected_zone}': {len(filtered_zone)}**")

# =====================================
# PREDICTION (API-driven)
=======
    if df.empty:
        st.warning("No processed event data available.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            if "hour" in df.columns and df["hour"].notna().any():
                hour_counts = df["hour"].dropna().astype(int).value_counts().sort_index()
                fig_hour = px.bar(
                    x=hour_counts.index,
                    y=hour_counts.values,
                    title="Events by Hour",
                    labels={"x": "Hour", "y": "Count"},
                    color=hour_counts.values,
                    color_continuous_scale="Viridis",
                )
                fig_hour.update_layout(showlegend=False)
                st.plotly_chart(fig_hour, use_container_width=True)
                st.dataframe(pd.DataFrame({"Hour": hour_counts.index, "Count": hour_counts.values}), hide_index=True, use_container_width=True)
            else:
                st.info("Hour-based event data is unavailable.")

        with col2:
            if "month" in df.columns and df["month"].notna().any():
                month_counts = df["month"].dropna().astype(int).value_counts().sort_index()
                month_labels = [pd.Timestamp(year=2024, month=int(m), day=1).strftime("%b") for m in month_counts.index]
                fig_month = px.bar(
                    x=month_labels,
                    y=month_counts.values,
                    title="Events by Month",
                    labels={"x": "Month", "y": "Count"},
                    color=month_counts.values,
                    color_continuous_scale="Blues",
                )
                fig_month.update_layout(showlegend=False)
                st.plotly_chart(fig_month, use_container_width=True)
                st.dataframe(pd.DataFrame({"Month": month_labels, "Count": month_counts.values}), hide_index=True, use_container_width=True)
            else:
                st.info("Month-based event data is unavailable.")

        st.markdown("---")
        if {"hour", "event_type"}.issubset(df.columns):
            cross_df = df.dropna(subset=["hour", "event_type"]).copy()
            if not cross_df.empty:
                cross_tab = pd.crosstab(cross_df["hour"].astype(int), cross_df["event_type"])
                fig_heatmap = px.imshow(
                    cross_tab,
                    labels={"x": "Event Type", "y": "Hour", "color": "Count"},
                    title="Event Type × Hour Heatmap",
                    color_continuous_scale="YlOrRd",
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
                st.dataframe(cross_tab, use_container_width=True)
            else:
                st.info("Not enough valid entries for Event Type × Hour analysis.")

# =====================================
# PREDICTION MODULE (FINAL VERSION)
>>>>>>> Stashed changes
# =====================================

elif page == "Prediction":

<<<<<<< Updated upstream
    st.title("🤖 AI Event Severity & Closure Prediction")
    
    st.markdown("Predict traffic impact using AI — Analyze event details to get: 📊 Severity | 🚧 Closure Prob | 📍 Hotspot Rank | 👮 Actions")

    st.markdown("### 📝 Event Details")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Location Information**")
        latitude = st.number_input("📍 Latitude", value=12.9716, format="%.6f", help="e.g., 12.9716 for Bangalore")
        longitude = st.number_input("📍 Longitude", value=77.5946, format="%.6f", help="e.g., 77.5946 for Bangalore")
        zone = st.text_input("🗺️ Zone/Area", value="Unknown", help="Traffic zone or area name")
        
        st.markdown("**Impact Scope**")
        endlatitude = st.number_input("📍 End Latitude (optional)", value=0.0, format="%.6f")
        endlongitude = st.number_input("📍 End Longitude (optional)", value=0.0, format="%.6f")

    with col2:
        st.markdown("**Event Classification**")
        event_type = st.selectbox("🎯 Event Type", ["Accident", "Road Work", "Event", "Breakdown", "Traffic Congestion", "Other"])
        if event_type == "Other":
            event_type = st.text_input("Specify event type", value="Other")
        
        st.markdown("**Timing & Crowd**")
        start_datetime = st.text_input("🕐 Start Datetime (ISO 8601)", value="2024-03-15T10:00:00", help="Format: YYYY-MM-DDTHH:MM:SS")
        expected_attendance = st.number_input("👥 Expected Attendance (if event)", value=0, step=100)

    st.markdown("---")
    predict_button = st.button("🔮 Predict Impact", use_container_width=False)

    if predict_button:
        if not event_type or event_type.strip() == "":
            st.error("❌ Event Type is required")
        elif latitude < -90 or latitude > 90:
            st.error("❌ Invalid Latitude (must be between -90 and 90)")
        elif longitude < -180 or longitude > 180:
            st.error("❌ Invalid Longitude (must be between -180 and 180)")
        else:
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

            with st.spinner("🔄 Analyzing event... Please wait..."):
                try:
                    resp = requests.post(f"{API_BASE}/events", json=payload, timeout=10)
                    resp.raise_for_status()
                    result = resp.json()

                    prediction = result.get("prediction", {})
                    recommendation = result.get("recommendation", {})
                    hotspot_info = result.get("hotspot_info", {})

                    st.markdown("---")
                    st.markdown("## 📊 Prediction Results")
                    
                    res_col1, res_col2 = st.columns(2)
                    
                    with res_col1:
                        severity = prediction.get('severity', 'Unknown')
                        severity_color = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}.get(severity, '⚪')
                        st.markdown(f"### {severity_color} Predicted Severity")
                        st.metric("Severity Level", severity, delta="Threat Level")
                    
                    with res_col2:
                        closure_prob = prediction.get('road_closure_probability', 0)
                        closure_pct = f"{closure_prob * 100:.1f}%"
                        st.markdown("### 🚧 Road Closure Risk")
                        st.metric("Closure Probability", closure_pct, delta="Impact Risk")
                        closure_status = "🔴 CRITICAL" if closure_prob > 0.8 else "🟡 HIGH" if closure_prob > 0.5 else "🟢 LOW"
                        st.caption(f"Status: {closure_status}")
                    
                    st.markdown("---")
                    st.markdown("## 📋 Recommended Actions")
                    
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        st.metric("👮 Officers Needed", recommendation.get("traffic_officers", "-"), delta="Personnel")
                    
                    with action_col2:
                        st.metric("🚧 Barricades Required", recommendation.get("barricades", "-"), delta="Equipment")
                    
                    with action_col3:
                        alert_level = recommendation.get("alert_level", "Normal")
                        alert_emoji = {"Critical": "🚨", "High": "⚠️", "Medium": "⚡", "Low": "ℹ️", "Normal": "✅"}.get(alert_level, "❓")
                        st.metric("Alert Level", alert_level, delta=f"{alert_emoji}")
                    
                    risk_score = recommendation.get("risk_score", "-")
                    st.markdown(f"**Risk Score:** `{risk_score}`")
                    
                    st.markdown("---")
                    st.markdown("## 📍 Hotspot Information")
                    
                    if hotspot_info:
                        hotspot_col1, hotspot_col2 = st.columns(2)
                        with hotspot_col1:
                            st.markdown(f"**Hotspot Rank:** {hotspot_info.get('rank', 'N/A')}")
                            st.markdown(f"**Distance to Nearest:** {hotspot_info.get('distance_to_nearest', 'N/A')} km")
                        with hotspot_col2:
                            st.markdown(f"**Event Count in Area:** {hotspot_info.get('event_count_in_radius', 'N/A')}")
                            st.markdown(f"**Cluster ID:** {hotspot_info.get('cluster_id', 'N/A')}")
                    else:
                        st.info("No hotspot data available")
                    
                    st.markdown("---")
                    with st.expander("💾 Full JSON Response"):
                        st.json(result)

                except requests.exceptions.ConnectionError:
                    st.error("🔴 **Backend is Offline** — Start: `python -m uvicorn src.api.main:app --reload`")
                except requests.exceptions.HTTPError as http_err:
                    try:
                        detail = resp.json()
                    except Exception:
                        detail = resp.text
                    st.error(f"🔴 **API Error** ({resp.status_code}): {detail}")
                except Exception as e:
                    st.error(f"🔴 **Prediction Error:** {str(e)}")


# =====================================
# HOTSPOTS
# =====================================

elif page == "Hotspots":

    st.title(
        "🔥 Traffic Hotspots"
    )

    # Load raw event addresses from the source CSV if available
    raw_events_df = load_raw_event_addresses()
    has_raw_addresses = (
        not raw_events_df.empty
        and "latitude" in raw_events_df.columns
        and "longitude" in raw_events_df.columns
        and raw_events_df["latitude"].notna().any()
        and raw_events_df["longitude"].notna().any()
        and "address" in raw_events_df.columns
    )

    if has_raw_addresses:
        coords = raw_events_df.dropna(subset=["latitude", "longitude"]).copy()
        coords["address"] = coords["address"].fillna("Unknown")
        fig_kwargs = {
            "lat": "latitude",
            "lon": "longitude",
            "zoom": 9,
            "height": 600,
            "text": "address",
            "hover_name": "address",
        }
        if "event_type" in coords.columns:
            fig_kwargs["hover_data"] = ["event_type", "start_datetime"] if "start_datetime" in coords.columns else ["event_type"]

        fig = px.scatter_map(
            coords,
            **fig_kwargs
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        display_cols = [
            c for c in ["start_datetime", "address", "event_type", "latitude", "longitude"]
            if c in coords.columns
        ]
        st.subheader("Data — Hotspot Addresses from CSV")
        st.dataframe(coords[display_cols].head(100))

    elif (
        "latitude" in df.columns
        and "longitude" in df.columns
        and df["latitude"].notna().any()
        and df["longitude"].notna().any()
    ):
        coords = df.dropna(subset=["latitude", "longitude"]).copy()

        fig_kwargs = {
            "lat": "latitude",
            "lon": "longitude",
            "zoom": 9,
            "height": 600,
        }
        if "address" in coords.columns:
            coords["address"] = coords["address"].fillna("Unknown")
            fig_kwargs.update({"text": "address", "hover_name": "address"})
        if "event_type" in coords.columns:
            fig_kwargs["hover_data"] = ["event_type", "timestamp", "zone"]

        fig = px.scatter_map(
            coords,
            **fig_kwargs
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        display_cols = [
            c for c in ["timestamp", "address", "zone", "event_type", "latitude", "longitude"]
            if c in coords.columns
        ]
        st.subheader("Data — Hotspot Coordinates")
        st.dataframe(coords[display_cols].head(100))

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

    st.title("🚨 AI-Powered Traffic Recommendations")
    
    st.markdown("Generate data-driven recommendations based on: severity | closure probability | hotspot ranking")

    st.markdown("### 🎯 Configure Scenario")
    
    config_col1, config_col2 = st.columns(2)
    
    with config_col1:
        st.markdown("**Event Parameters**")
        severity = st.selectbox("📊 Event Severity", ["Low", "Medium", "High"], index=2, help="Severity level")
        severity_desc = {"Low": "Minor incident", "Medium": "Moderate incident", "High": "Major incident"}
        st.caption(severity_desc.get(severity, ""))

    with config_col2:
        st.markdown("**Risk Metrics**")
        closure_prob = st.slider("🚧 Closure Probability", 0.0, 1.0, 0.75, step=0.05)
        closure_pct = f"{closure_prob * 100:.0f}%"
        closure_status = "🔴 CRITICAL" if closure_prob > 0.8 else "🟡 HIGH" if closure_prob > 0.5 else "🟢 LOW"
        st.caption(f"Closure Risk: {closure_pct} — {closure_status}")
    
    st.markdown("---")
    
    hotspot_col1, hotspot_col2 = st.columns(2)
    
    with hotspot_col1:
        st.markdown("**Location Context**")
        hotspot_rank = st.slider("📍 Hotspot Rank", 1, 100, 3, step=1, help="Lower = more critical")
        rank_desc = ("🔴 Critical" if hotspot_rank <= 5 else "🟡 Important" if hotspot_rank <= 20 else "🟢 Minor")
        st.caption(f"{rank_desc} hotspot")
    
    with hotspot_col2:
        st.markdown("**Quick View**")
        st.info(f"📊 Severity: **{severity}**\n\n🚧 Closure: **{closure_pct}**\n\n📍 Hotspot: **#{hotspot_rank}**")
    
    st.markdown("---")
    generate_button = st.button("📋 Generate Recommendation", use_container_width=False)

    if generate_button:
        payload = {
            "severity": severity,
            "road_closure_probability": closure_prob,
            "hotspot_rank": hotspot_rank,
        }

        with st.spinner("🔄 Generating recommendations..."):
            try:
                resp = requests.post(f"{API_BASE}/recommendations", json=payload, timeout=5)
                resp.raise_for_status()
                rec = resp.json()

                st.markdown("---")
                st.markdown("## ✅ Recommendations Generated")
                
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric("⚠️ Risk Score", rec.get("risk_score", "-"), delta="Overall")
                
                with metric_col2:
                    officers = rec.get("traffic_officers", "-")
                    st.metric("👮 Officers Needed", officers, delta="Personnel")
                
                with metric_col3:
                    barricades = rec.get("barricades", "-")
                    st.metric("🚧 Barricades", barricades, delta="Equipment")
                
                with metric_col4:
                    alert_level = rec.get("alert_level", "Normal")
                    alert_emoji = {"Critical": "🚨", "High": "⚠️", "Medium": "⚡", "Low": "ℹ️", "Normal": "✅"}.get(alert_level, "❓")
                    st.metric("Alert Level", alert_level, delta=f"{alert_emoji}")
                
                st.markdown("---")
                st.markdown("## 📋 Action Plan")
                
                action_items = []
                if severity == "High" or closure_prob > 0.7:
                    action_items.append("🚨 **Declare Traffic Alert** — Notify commuters")
                    action_items.append("📡 **Activate VMS** — Display alternate routes")
                if officers and officers != "-":
                    try:
                        if int(officers) > 0:
                            action_items.append(f"👮 **Deploy {officers} Officers** — Manage traffic")
                    except:
                        pass
                if barricades and barricades != "-" and barricades.lower() != "none":
                    action_items.append(f"🚧 **Set up {barricades}** — Control movement")
                if hotspot_rank <= 10:
                    action_items.append("📍 **Pre-position Resources** — High-frequency area")
                    action_items.append("📞 **Alert Police Stations** — Rapid response")
                if severity == "Low" and closure_prob < 0.3:
                    action_items.append("✅ **Monitor** — Standard protocols")
                if not action_items:
                    action_items.append("✅ **Standard Protocol** — Monitor situation")
                
                for idx, action in enumerate(action_items, 1):
                    st.markdown(f"{idx}. {action}")
                
                st.markdown("---")
                with st.expander("💾 Full Response"):
                    st.json(rec)

            except requests.exceptions.ConnectionError:
                st.error("🔴 **Backend Offline** — Start: `python -m uvicorn src.api.main:app --reload`")
            except Exception as e:
                st.error(f"🔴 **Error:** {str(e)}")


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
=======
    st.title("🤖 AI Traffic Prediction")
    st.markdown(
        "Predict road closure probability, severity level, and recommended actions."
    )

    if (
        models["road"] is None
        or models["severity"] is None
        or models["encoder"] is None
    ):
        st.error("Prediction models are not loaded.")
        st.stop()

    if df.empty:
        st.error("Processed dataset not found.")
        st.stop()

    # Load exact model features
    road_features = models.get("road_features", [])
    severity_features = models.get("severity_features", [])

    if len(road_features) == 0:
        st.error("Road model feature schema not found.")
        st.stop()

    # Combine all required features
    all_features = sorted(
        list(
            set(road_features) |
            set(severity_features)
        )
    )

    # Remove target column if present
    if "requires_road_closure" in all_features:
        all_features.remove(
            "requires_road_closure"
        )

    st.subheader("📥 Enter Event Details")

    col1, col2 = st.columns(2)

    input_data = {}

    for idx, feature in enumerate(all_features):

        default_value = 0.0

        if feature in df.columns:
            try:
                default_value = float(
                    df[feature].median()
                )
            except:
                default_value = 0.0

        if idx % 2 == 0:

            with col1:

                input_data[feature] = st.number_input(
                    feature,
                    value=default_value,
                    format="%.4f"
                )
>>>>>>> Stashed changes

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

<<<<<<< Updated upstream
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
=======
            with col2:

                input_data[feature] = st.number_input(
                    feature,
                    value=default_value,
                    format="%.4f"
                )

    st.markdown("---")

    if st.button("🚀 Predict"):

        try:

            X_full = pd.DataFrame(
                [input_data]
            )

            # Match exact training schema
            road_input = X_full.reindex(
                columns=road_features,
                fill_value=0
            )

            severity_input = X_full.reindex(
                columns=severity_features,
                fill_value=0
            )

            # Road Closure Prediction
            road_prob = float(
                models["road"]
                .predict_proba(
                    road_input
                )[0][1]
            )

            road_pred = int(
                models["road"]
                .predict(
                    road_input
                )[0]
            )

            # Pass road closure prediction if severity model uses it
            if (
                "requires_road_closure"
                in severity_input.columns
            ):
                severity_input[
                    "requires_road_closure"
                ] = road_pred

            # Severity Prediction
            severity_code = int(
                models["severity"]
                .predict(
                    severity_input
                )[0]
            )

            severity = (
                models["encoder"]
                .inverse_transform(
                    [severity_code]
                )[0]
            )

            # Risk Score
            risk_score = round(
                road_prob * 100,
                2
            )

            if risk_score >= 80:
                risk_level = "🔴 Critical"

            elif risk_score >= 60:
                risk_level = "🟠 High"

            elif risk_score >= 40:
                risk_level = "🟡 Medium"

            else:
                risk_level = "🟢 Low"

            st.subheader(
                "📊 Prediction Results"
            )

            m1, m2, m3 = st.columns(3)

            m1.metric(
                "Road Closure Probability",
                f"{risk_score}%"
            )

            m2.metric(
                "Closure Required",
                "YES" if road_pred else "NO"
            )

            m3.metric(
                "Severity",
                str(severity)
            )

            st.progress(
                min(max(road_prob, 0), 1)
            )

            st.markdown(
                f"### Risk Level: {risk_level}"
            )

            # Recommendations
            st.subheader(
                "🚔 Recommended Actions"
            )

            recommendations = []

            if road_pred:
                recommendations.extend([
                    "Deploy traffic officers",
                    "Install temporary barricades",
                    "Activate diversion routes"
                ])

            if str(severity).lower() in [
                "high",
                "critical"
            ]:
                recommendations.extend([
                    "Issue public advisory",
                    "Increase monitoring",
                    "Prepare emergency response"
                ])

            if not recommendations:
                recommendations.append(
                    "Normal monitoring is sufficient"
                )

            for rec in recommendations:
                st.success(rec)

            # Alert Banner
            if risk_score >= 80:

                st.error(
                    "🚨 HIGH-RISK CONGESTION EVENT DETECTED"
                )

        except Exception as e:

            st.error(
                f"Prediction Failed: {str(e)}"
            )


>>>>>>> Stashed changes

# =====================================
# HOTSPOTS MODULE
# =====================================

elif page == "Hotspots":
    st.title("🔥 Traffic Hotspots")
    st.markdown("Map event locations, hotspot clusters, risk zones, and suggested diversions.")

    source_df = raw_df if not raw_df.empty else df

    if source_df.empty:
        st.warning("No geolocation dataset available for hotspots.")
    elif {"latitude", "longitude"}.issubset(source_df.columns):
        map_df = source_df.dropna(subset=["latitude", "longitude"]).copy()
        if not map_df.empty:
            st.markdown("### 🗺️ Interactive Multi-Layer Map")

            fig = px.scatter_mapbox(
                map_df.head(1),
                lat="latitude",
                lon="longitude",
                title="Event Location, Hotspots, Risk Zones & Suggested Diversions",
                zoom=9,
                height=700,
            )

            if "address" in map_df.columns:
                map_df["address"] = map_df["address"].fillna("Unknown")

            severity_high = map_df[map_df["status"] == "closed"] if "status" in map_df.columns else map_df.head(0)
            severity_medium = map_df[map_df["status"] != "closed"] if "status" in map_df.columns else map_df.tail(len(map_df) - len(severity_high))

            fig.add_scattermapbox(
                lat=severity_high["latitude"],
                lon=severity_high["longitude"],
                mode="markers",
                marker=dict(size=8, color="red", opacity=0.7),
                name="Event Location (High Risk)",
                text=severity_high.get("address", severity_high.get("event_type", "Event")),
                hovertemplate="<b>Event Location (High Risk)</b><br>%{text}<extra></extra>",
            )

            fig.add_scattermapbox(
                lat=severity_medium["latitude"],
                lon=severity_medium["longitude"],
                mode="markers",
                marker=dict(size=6, color="orange", opacity=0.6),
                name="Event Location (Medium Risk)",
                text=severity_medium.get("address", severity_medium.get("event_type", "Event")),
                hovertemplate="<b>Event Location (Medium Risk)</b><br>%{text}<extra></extra>",
            )

            if not hotspot_df.empty and len(map_df) > 0:
                sample_size = min(5, len(hotspot_df))
                hotspot_lats = map_df["latitude"].quantile([i / (sample_size - 1) for i in range(sample_size)]).values
                hotspot_lons = map_df["longitude"].quantile([i / (sample_size - 1) for i in range(sample_size)]).values

                fig.add_scattermapbox(
                    lat=hotspot_lats,
                    lon=hotspot_lons,
                    mode="markers+text",
                    marker=dict(size=12, color="blue", symbol="diamond", opacity=0.8),
                    name="Hotspot Cluster",
                    text=[f"C{i}" for i in range(len(hotspot_lats))],
                    textposition="top center",
                    hovertemplate="<b>Hotspot Cluster</b><br>Cluster Point<extra></extra>",
                )

            event_type_counts = map_df["event_type"].value_counts() if "event_type" in map_df.columns else pd.Series()
            risk_zones = map_df[map_df["event_type"].isin(event_type_counts.head(3).index)] if "event_type" in map_df.columns else map_df
            if len(risk_zones) > 0:
                fig.add_scattermapbox(
                    lat=risk_zones["latitude"],
                    lon=risk_zones["longitude"],
                    mode="markers",
                    marker=dict(size=4, color="purple", opacity=0.4),
                    name="Risk Zone (Top Event Types)",
                    hovertemplate="<b>Risk Zone</b><extra></extra>",
                )

            if len(map_df) >= 2:
                lat_center = map_df["latitude"].mean()
                lon_center = map_df["longitude"].mean()
                lat_offset = (map_df["latitude"].max() - map_df["latitude"].min()) * 0.15
                lon_offset = (map_df["longitude"].max() - map_df["longitude"].min()) * 0.15

                diversion_lats = [lat_center + lat_offset, lat_center - lat_offset]
                diversion_lons = [lon_center + lon_offset, lon_center - lon_offset]

                fig.add_scattermapbox(
                    lat=diversion_lats,
                    lon=diversion_lons,
                    mode="markers+lines",
                    marker=dict(size=10, color="green", symbol="star", opacity=0.7),
                    name="Suggested Diversion",
                    line=dict(color="green", width=2),
                    hovertemplate="<b>Suggested Diversion Route</b><extra></extra>",
                )
            else:
                diversion_lats = []
                diversion_lons = []

            fig.update_layout(
                mapbox_style="open-street-map",
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                hovermode="closest",
                legend=dict(x=0.01, y=0.99),
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📊 Map Layers Summary")
            layer_cols = st.columns(4)
            layer_cols[0].info(f"🔴 **Event (High)**: {len(severity_high)}")
            layer_cols[1].info(f"🟠 **Event (Medium)**: {len(severity_medium)}")
            layer_cols[2].info(f"🟣 **Risk Zone**: {len(risk_zones)}")
            layer_cols[3].info(f"🟢 **Diversion**: {len(diversion_lats)} routes")
        else:
            st.warning("No valid latitude/longitude rows found.")
    else:
        st.warning("Latitude and longitude columns are missing.")

    if not hotspot_df.empty:
        st.markdown("---")
        st.subheader("📈 Hotspot Rankings")
        st.dataframe(hotspot_df.head(20), use_container_width=True)
    else:
        st.warning("Hotspot cluster data not available. Run hotspot_detection.py.")

# =====================================
# RECOMMENDATIONS MODULE
# =====================================

elif page == "Recommendations":
    st.title("🚨 Traffic Recommendations")
    st.markdown("Generate recommended resources and actions for event response.")

    severity = st.selectbox("Severity", ["Low", "Medium", "High"], index=2)
    closure_prob = st.slider("Road Closure Probability", 0.0, 1.0, 0.75, step=0.05)
    hotspot_rank = st.slider("Hotspot Rank", 1, 20, 3)
    expected_attendance = st.number_input("Expected Attendance", min_value=0, value=0, step=50)

    if st.button("Generate Recommendation"):
        officers = 2
        if severity == "Medium":
            officers = 5
        elif severity == "High":
            officers = 10
        if hotspot_rank <= 5:
            officers += 4
        if expected_attendance > 500:
            officers += 2

        if closure_prob > 0.8:
            barricades = "Full barricade deployment"
        elif closure_prob > 0.5:
            barricades = "Partial barricade deployment"
        else:
            barricades = "Standard traffic control"

        risk_score = round(hotspot_rank * 4 + closure_prob * 40 + expected_attendance * 0.01, 1)
        expected_delay, affected_radius = estimate_delay_and_radius(
            severity, closure_prob, hotspot_rank, expected_attendance
        )

        st.markdown("---")
        st.subheader("Recommendation Summary")
        cols = st.columns(4)
        cols[0].metric("Risk Score", risk_score)
        cols[1].metric("Officers Required", officers)
        cols[2].metric("Barricade Plan", barricades)
        cols[3].metric("Alert Level", severity)

        st.markdown("### Estimated Impact")
        impact_cols = st.columns(2)
        impact_cols[0].metric("Expected Delay", f"{expected_delay} min")
        impact_cols[1].metric("Affected Radius", f"{affected_radius:.2f} km")

        st.markdown("---")
        st.markdown("### Suggested Actions")

        actions = []
        if severity == "High" or closure_prob > 0.7:
            actions.append("🚨 Declare alert and notify stakeholders.")
            actions.append("📡 Activate alternate route messaging.")
        if officers > 0:
            actions.append(f"👮 Deploy {officers} officers for traffic control.")
        if barricades.startswith("Full"):
            actions.append("🚧 Set up full barricades and detours.")
        elif barricades.startswith("Partial"):
            actions.append("🚧 Deploy partial barricades on affected lanes.")
        if hotspot_rank <= 5:
            actions.append("📍 Prioritize response in the hotspot area.")
        if expected_attendance > 300:
            actions.append("📢 Send traveler alerts and delay notices.")
        if expected_delay > 90:
            actions.append("⏱ Anticipate long delays and stage resources early.")
        if affected_radius >= 3.0:
            actions.append("📍 Coordinate response across a wider impact area.")
        if not actions:
            actions.append("✅ Monitor situation and maintain standard operations.")

        for idx, action in enumerate(actions, start=1):
            st.write(f"{idx}. {action}")

        st.markdown("---")
        summary_df = pd.DataFrame(
            {
                "Parameter": [
                    "Severity",
                    "Closure Probability",
                    "Hotspot Rank",
                    "Expected Attendance",
                    "Estimated Delay (min)",
                    "Affected Radius (km)",
                ],
                "Value": [
                    severity,
                    f"{closure_prob:.0%}",
                    hotspot_rank,
                    expected_attendance,
                    expected_delay,
                    affected_radius,
                ],
            }
        )
        st.dataframe(summary_df, hide_index=True, use_container_width=True)

st.sidebar.write("\n---\nBuilt for traffic event analysis and visualization.")
