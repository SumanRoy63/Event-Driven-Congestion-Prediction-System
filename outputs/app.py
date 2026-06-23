import os
import streamlit as st
import pandas as pd
import requests
import json
import os
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
# =====================================
# CONFIG
# =====================================

st.set_page_config(
    page_title="Smart Traffic AI System",
    layout="wide"
)

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

# =====================================
# SIDEBAR
# =====================================

st.sidebar.title("Traffic AI Dashboard")
page = st.sidebar.radio(
    "Select Module",
    ["Overview", "Analytics", "Prediction", "Hotspots", "Recommendations"],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Built for traffic event analytics, prediction, and recommendation."
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

# =====================================
# ANALYTICS MODULE
# =====================================

elif page == "Analytics":
    st.title("📊 Event Analytics")
    st.markdown("Analyze event timing, type distribution, and location-based trends.")

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
# =====================================

elif page == "Prediction":

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
