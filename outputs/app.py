import streamlit as st
import pandas as pd
import requests
import json
import os
import numpy as np

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

# =====================================
# ANALYTICS
# =====================================

elif page == "Analytics":

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
# =====================================

elif page == "Prediction":

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