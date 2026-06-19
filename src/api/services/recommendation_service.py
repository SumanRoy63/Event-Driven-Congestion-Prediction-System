from typing import Dict, Any

def generate_recommendation(severity: str, closure_prob: float, hotspot_rank: int) -> Dict[str, Any]:
    """
    Generates actionable recommendations based on prediction outputs.
    """
    officers = 2

    # Map string severities back to logic
    severity_upper = severity.upper()
    if severity_upper in ["MEDIUM", "MODERATE"]:
        officers = 5
    elif severity_upper in ["HIGH", "SEVERE", "CRITICAL"]:
        officers = 10

    # Lower rank means higher priority (e.g. Rank 1 is very bad)
    if hotspot_rank <= 3:
        officers += 5

    if closure_prob > 0.8:
        barricade = "Required"
        alert_level = "RED"
    elif closure_prob > 0.5:
        barricade = "Partial"
        alert_level = "ORANGE"
    else:
        barricade = "Not Required"
        alert_level = severity_upper if severity_upper in ["LOW", "MEDIUM", "HIGH"] else "GREEN"

    # Risk score calculation logic (mirroring Streamlit)
    risk = (hotspot_rank * 5) + (closure_prob * 50)

    return {
        "alert_level": alert_level,
        "traffic_officers": officers,
        "barricades": barricade,
        "risk_score": round(risk, 2)
    }
