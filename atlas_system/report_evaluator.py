"""ATLAS v1.5: deterministic validation of synthetic comparison reports."""

from engine import SCENARIOS, classify

METRICS = (
    "payment_success_rate",
    "average_latency_ms",
    "failed_transactions",
)


def evaluate_report(report):
    """Validate report structure, consistency, evidence, and safety."""
    if not isinstance(report, dict):
        raise ValueError("Report must be a JSON object")

    checks = {}

    checks["report_identity"] = (
        report.get("report_type") == "SYNTHETIC_INCIDENT_COMPARISON"
        and isinstance(report.get("generated_at"), str)
        and bool(report["generated_at"])
    )

    incidents_valid = True
    for side in ("a", "b"):
        incident = report.get(f"incident_{side}")
        if not isinstance(incident, dict):
            incidents_valid = False
            continue

        scenario = incident.get("scenario")
        if scenario not in SCENARIOS:
            incidents_valid = False
            continue

        metrics = incident.get("metrics")
        severity = incident.get("severity")

        if (
            not isinstance(metrics, dict)
            or metrics != SCENARIOS[scenario]
            or severity != classify(SCENARIOS[scenario])[0]
        ):
            incidents_valid = False

    checks["incident_consistency"] = incidents_valid

    differences = report.get("differences_b_minus_a")
    differences_valid = False

    if incidents_valid and isinstance(differences, dict):
        a = report["incident_a"]["metrics"]
        b = report["incident_b"]["metrics"]

        differences_valid = differences == {
            "success_rate_percentage_points": round(
                b["payment_success_rate"] - a["payment_success_rate"], 2
            ),
            "latency_ms": b["average_latency_ms"] - a["average_latency_ms"],
            "failed_transactions": (
                b["failed_transactions"] - a["failed_transactions"]
            ),
        }

    checks["metric_differences"] = differences_valid

    for side in ("a", "b"):
        rca = report.get(f"root_cause_{side}")
        checks[f"root_cause_{side}_evidence"] = (
            isinstance(rca, dict)
            and rca.get("scenario") == (
                report.get(f"incident_{side}", {}).get("scenario")
                if isinstance(report.get(f"incident_{side}"), dict)
                else None
            )
            and rca.get("confidence") == "UNVERIFIED_HYPOTHESIS"
            and isinstance(rca.get("supporting_evidence"), list)
            and len(rca["supporting_evidence"]) > 0
            and isinstance(rca.get("missing_evidence"), list)
            and isinstance(rca.get("limitations"), str)
            and bool(rca["limitations"].strip())
        )

    checks["read_only_safety"] = (
        report.get("requires_human_approval") is True
        and report.get("action_executed") is False
        and report.get("data_persisted") is False
    )

    checks["limitations_disclosed"] = (
        isinstance(report.get("limitations"), str)
        and "synthetic" in report["limitations"].lower()
        and "causal proof" in report["limitations"].lower()
    )

    passed = sum(value is True for value in checks.values())
    total = len(checks)

    return {
        "version": "1.5",
        "evaluation_type": "DETERMINISTIC_REPORT_CHECKLIST",
        "passed_checks": passed,
        "total_checks": total,
        "failed_checks": [key for key, value in checks.items() if not value],
        "checks": checks,
        "status": "PASS" if passed == total else "NEEDS_REVIEW",
        "action_executed": False,
        "data_persisted": False,
        "limitations": (
            "Rule-based validation of fixed synthetic report fields only. "
            "Not calibrated AI accuracy, causal verification, or "
            "authorization for recovery actions."
        ),
    }
