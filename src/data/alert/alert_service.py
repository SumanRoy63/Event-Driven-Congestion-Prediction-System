def check_alert(
    road_prob,
    severity
):

    alerts = []

    if road_prob >= 0.80:

        alerts.append(
            "HIGH_CONGESTION"
        )

    if str(severity).lower() in [
        "high",
        "critical"
    ]:

        alerts.append(
            "HIGH_SEVERITY"
        )

    return alerts

