"""ATLAS v1.4: read-only comparison of fixed synthetic incidents."""
from datetime import datetime, timezone

from engine import SCENARIOS, classify
from root_cause import analyze as root_cause_analyze


def compare_incidents(scenario_a, scenario_b):
    if scenario_a not in SCENARIOS or scenario_b not in SCENARIOS:
        raise ValueError("Unknown synthetic scenario")

    metrics_a = SCENARIOS[scenario_a].copy()
    metrics_b = SCENARIOS[scenario_b].copy()

    severity_a, _ = classify(metrics_a)
    severity_b, _ = classify(metrics_b)

    differences = {
        "success_rate_percentage_points": round(
            metrics_b["payment_success_rate"] -
            metrics_a["payment_success_rate"], 2
        ),
        "latency_ms": metrics_b["average_latency_ms"] -
                      metrics_a["average_latency_ms"],
        "failed_transactions": metrics_b["failed_transactions"] -
                               metrics_a["failed_transactions"],
    }

    return {
        "version": "1.4",
        "report_type": "SYNTHETIC_INCIDENT_COMPARISON",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "incident_a": {
            "scenario": scenario_a,
            "severity": severity_a,
            "metrics": metrics_a,
        },
        "incident_b": {
            "scenario": scenario_b,
            "severity": severity_b,
            "metrics": metrics_b,
        },
        "differences_b_minus_a": differences,
        "root_cause_a": root_cause_analyze(scenario_a),
        "root_cause_b": root_cause_analyze(scenario_b),
        "requires_human_approval": True,
        "action_executed": False,
        "data_persisted": False,
        "limitations": (
            "Fixed synthetic scenario comparison only. "
            "Not real payment telemetry, causal proof, or "
            "authorization to execute recovery actions."
        ),
    }
