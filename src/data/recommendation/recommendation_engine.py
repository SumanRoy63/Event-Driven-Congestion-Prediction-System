# =====================================================
# AI RECOMMENDATION ENGINE
# =====================================================

import pandas as pd
import numpy as np

import joblib
import os

# =====================================================
# LOAD MODELS
# =====================================================

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


# =====================================================
# GENERATE RECOMMENDATION
# =====================================================

def generate_recommendation(
        severity,
        closure_probability,
        hotspot_rank
):

    recommendation = {}

    # --------------------------------
    # ALERT LEVEL
    # --------------------------------

    if severity == "High":

        recommendation[
            "alert_level"
        ] = "RED"

    elif severity == "Medium":

        recommendation[
            "alert_level"
        ] = "ORANGE"

    else:

        recommendation[
            "alert_level"
        ] = "YELLOW"

    # --------------------------------
    # TRAFFIC OFFICERS
    # --------------------------------

    officers = 2

    if severity == "Medium":
        officers = 5

    if severity == "High":
        officers = 10

    if hotspot_rank <= 3:
        officers += 5

    recommendation[
        "traffic_officers"
    ] = officers

    # --------------------------------
    # BARRICADES
    # --------------------------------

    if closure_probability > 0.80:

        recommendation[
            "barricades"
        ] = "Required"

    elif closure_probability > 0.50:

        recommendation[
            "barricades"
        ] = "Partial"

    else:

        recommendation[
            "barricades"
        ] = "Not Required"

    # --------------------------------
    # DIVERSION PLAN
    # --------------------------------

    if closure_probability > 0.70:

        recommendation[
            "diversion_plan"
        ] = (
            "Activate Alternate Route"
        )

    else:

        recommendation[
            "diversion_plan"
        ] = (
            "Monitor Traffic Flow"
        )

    # --------------------------------
    # EMERGENCY TEAM
    # --------------------------------

    if severity == "High":

        recommendation[
            "emergency_team"
        ] = "Dispatch Immediately"

    else:

        recommendation[
            "emergency_team"
        ] = "Standby"

    # --------------------------------
    # PUBLIC ALERT
    # --------------------------------

    if severity == "High":

        recommendation[
            "public_notification"
        ] = (
            "Send SMS + App Alert"
        )

    elif severity == "Medium":

        recommendation[
            "public_notification"
        ] = (
            "App Notification"
        )

    else:

        recommendation[
            "public_notification"
        ] = (
            "No Public Alert"
        )

    return recommendation


# =====================================================
# RISK SCORE
# =====================================================

def calculate_risk_score(
        severity,
        closure_probability,
        hotspot_rank
):

    score = 0

    # Severity Weight

    if severity == "High":
        score += 50

    elif severity == "Medium":
        score += 30

    else:
        score += 10

    # Closure Probability

    score += (
        closure_probability * 30
    )

    # Hotspot Weight

    score += max(
        0,
        (10 - hotspot_rank)
    ) * 2

    return round(score,2)


# =====================================================
# BATCH RECOMMENDATIONS
# =====================================================

def generate_batch_recommendations(df):

    recommendations = []

    for _, row in df.iterrows():

        severity = row["severity"]

        closure_prob = row[
            "closure_probability"
        ]

        hotspot_rank = row[
            "hotspot_rank"
        ]

        rec = generate_recommendation(

            severity,

            closure_prob,

            hotspot_rank
        )

        risk_score = (
            calculate_risk_score(
                severity,
                closure_prob,
                hotspot_rank
            )
        )

        recommendations.append({

            "severity": severity,

            "closure_probability":
            closure_prob,

            "hotspot_rank":
            hotspot_rank,

            "risk_score":
            risk_score,

            **rec
        })

    return pd.DataFrame(
        recommendations
    )


# =====================================================
# DEMO DATA
# =====================================================

def create_demo_data():

    return pd.DataFrame({

        "severity":[

            "High",
            "Medium",
            "Low",
            "High"
        ],

        "closure_probability":[

            0.95,
            0.65,
            0.20,
            0.88
        ],

        "hotspot_rank":[

            1,
            4,
            8,
            2
        ]
    })


# =====================================================
# SAVE OUTPUT
# =====================================================

def save_output(df):

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    df.to_csv(

        "outputs/recommendations.csv",

        index=False
    )

    print(
        "Recommendations Saved"
    )


# =====================================================
# MAIN
# =====================================================

def main():

    print("="*50)
    print(
        "AI RECOMMENDATION ENGINE"
    )
    print("="*50)

    data = create_demo_data()

    result = (
        generate_batch_recommendations(
            data
        )
    )

    print("\n")

    print(result)

    save_output(result)

    print("\n")

    print("="*50)
    print(
        "Recommendation Engine Complete"
    )
    print("="*50)


if __name__ == "__main__":

    main()

    