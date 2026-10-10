
def detect_incident(metrics):
    """
    Evaluate payment metrics and determine incident severity.
    All data is synthetic.
    """

    success_rate = metrics["payment_success_rate"]
    latency = metrics["average_latency_ms"]
    failed_transactions = metrics["failed_transactions"]

    reasons = []

    if success_rate < 60:
        reasons.append("Critical drop in payment success rate")
    elif success_rate < 90:
        reasons.append("Payment success rate below normal")

    if latency > 3000:
        reasons.append("Severe payment processing latency")
    elif latency > 1000:
        reasons.append("Elevated payment processing latency")

    if failed_transactions > 1000:
        reasons.append("High number of failed transactions")

    if success_rate < 60 or latency > 3000:
        severity = "CRITICAL"
    elif success_rate < 90 or latency > 1000 or failed_transactions > 1000:
        severity = "HIGH"
    else:
        severity = "HEALTHY"

    return {
        "severity": severity,
        "incident_detected": severity != "HEALTHY",
        "reasons": reasons
    }


if __name__ == "__main__":
    sample_metrics = {
        "payment_success_rate": 99.2,
        "average_latency_ms": 150,
        "failed_transactions": 5
    }

    result = detect_incident(sample_metrics)

    print("\nATLAS AI - INCIDENT DETECTION ENGINE")
    print("------------------------------------")
    print("Severity:", result["severity"])
    print("Incident Detected:", result["incident_detected"])

    for reason in result["reasons"]:
        print("-", reason)
