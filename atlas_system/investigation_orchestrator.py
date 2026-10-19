
"""ATLAS v2.0: read-only synthetic investigation orchestration."""

from datetime import datetime, timezone
from time import perf_counter

from incident_comparison import compare_incidents
from report_evaluator import evaluate_report


def run_investigation(scenario_a="provider_outage", scenario_b="healthy"):
    """Compare and evaluate synthetic incidents without side effects."""

    stages = []
    started_at = datetime.now(timezone.utc).isoformat()

    def run_stage(name, operation):
        start = perf_counter()

        try:
            result = operation()
        except Exception as exc:
            stages.append({
                "stage": name,
                "status": "FAILED",
                "duration_ms": round(
                    (perf_counter() - start) * 1000, 3
                ),
                "error": str(exc),
            })
            raise

        stages.append({
            "stage": name,
            "status": "COMPLETED",
            "duration_ms": round(
                (perf_counter() - start) * 1000, 3
            ),
        })

        return result

    report = run_stage(
        "SYNTHETIC_COMPARISON",
        lambda: compare_incidents(scenario_a, scenario_b),
    )

    evaluation = run_stage(
        "REPORT_EVALUATION",
        lambda: evaluate_report(report),
    )

    if evaluation["status"] != "PASS":
        status = "NEEDS_REVIEW"
    else:
        status = "READY_FOR_HUMAN_REVIEW"

    return {
        "version": "2.0-dev",
        "workflow_type": "SYNTHETIC_INVESTIGATION",
        "status": status,
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "stages": stages,
        "report": report,
        "evaluation": evaluation,
        "requires_human_approval": True,
        "action_executed": False,
        "data_persisted": False,
        "limitations": (
            "Deterministic synthetic investigation only. "
            "No live payment processing, autonomous recovery, "
            "or verified causal conclusions."
        ),
    }
