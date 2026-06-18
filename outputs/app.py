import streamlit as st
import pandas as pd
import numpy as np
import joblib

import plotly.express as px
import plotly.graph_objects as go

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="Smart Traffic AI System",
    layout="wide"
)

# =====================================
# LOAD DATA
# =====================================

@st.cache_data
def load_data():

    return pd.read_csv(
        "data/processed/processed_events.csv"
    )

df = load_data()

# =====================================
# LOAD MODELS
# =====================================

@st.cache_resource
def load_models():

    road_model = joblib.load(
        "models/road_closure_xgb.pkl"
    )

    severity_model = joblib.load(
        "models/severity_xgb.pkl"
    )

    priority_encoder = joblib.load(
        "models/priority_encoder.pkl"
    )

    return (
        road_model,
        severity_model,
        priority_encoder
    )

road_model, severity_model, priority_encoder = (
    load_models()
)

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
        "Recommendations"
    ]
)

# =====================================
# OVERVIEW
# =====================================

if page == "Overview":

    st.title(
        "🚦 Smart Traffic Event Management System"
    )

    c1,c2,c3,c4 = st.columns(4)

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
# PREDICTION
# =====================================

elif page == "Prediction":

    st.title(
        "🤖 AI Prediction"
    )

    st.info(
        "Enter feature values and predict road closure + severity"
    )

    numeric_cols = df.select_dtypes(
        include=np.number
    ).columns.tolist()

    target_cols = [
        "requires_road_closure",
        "priority"
    ]

    feature_cols = [
        c for c in numeric_cols
        if c not in target_cols
    ]

    input_data = {}

    for col in feature_cols[:10]:

        input_data[col] = st.number_input(

            col,

            value=float(
                df[col].median()
            )
        )

    if st.button(
        "Predict"
    ):

        X = pd.DataFrame(
            [input_data]
        )

        try:

            road_prob = (
                road_model
                .predict_proba(X)[0][1]
            )

            severity_pred = (
                severity_model
                .predict(X)[0]
            )

            severity = (
                priority_encoder
                .inverse_transform(
                    [severity_pred]
                )[0]
            )

            st.success(
                f"Road Closure Probability: {road_prob:.2%}"
            )

            st.success(
                f"Predicted Severity: {severity}"
            )

        except Exception as e:

            st.error(str(e))

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

    except:

        st.warning(
            "Run hotspot_detection.py first"
        )

# =====================================
# RECOMMENDATION ENGINE
# =====================================

elif page == "Recommendations":

    st.title(
        "🚨 Traffic Recommendations"
    )

    severity = st.selectbox(

        "Severity",

        ["Low","Medium","High"]
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

        officers = 2

        if severity == "Medium":
            officers = 5

        if severity == "High":
            officers = 10

        if hotspot_rank <= 3:
            officers += 5

        if closure_prob > 0.8:

            barricade = "Required"

        elif closure_prob > 0.5:

            barricade = "Partial"

        else:

            barricade = "Not Required"

        risk = (
            hotspot_rank * 5
            +
            closure_prob * 50
        )

        st.metric(
            "Risk Score",
            round(risk,2)
        )

        st.write(
            f"👮 Officers Required: {officers}"
        )

        st.write(
            f"🚧 Barricades: {barricade}"
        )

        st.write(
            f"📢 Alert Level: {severity}"
        )

# =====================================
# FOOTER
# =====================================

st.sidebar.markdown("---")
st.sidebar.write(
    "Flipkart Grid 2.0 Hackathon"
)