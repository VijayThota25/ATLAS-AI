"""ATLAS v1.6: explicit local archive for synthetic investigations."""

import hashlib
import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone

from atlas_store import connect
from incident_comparison import compare_incidents
from report_evaluator import evaluate_report


def _payload_digest(payload):
    """Compute a deterministic SHA-256 digest for a stored report."""
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _verify_payload(payload, expected_digest):
    """Reject a stored report whose contents have changed."""
    if expected_digest is None:
        return payload  # Legacy v1.6 record without a digest.

    if _payload_digest(payload) != expected_digest:
        raise ValueError("Archived investigation integrity check failed")

    return payload



def _create_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS investigation_reports (
            id INTEGER PRIMARY KEY,
            report_id TEXT UNIQUE NOT NULL,
            scenario_a TEXT NOT NULL,
            scenario_b TEXT NOT NULL,
            evaluation_status TEXT NOT NULL,
            payload TEXT NOT NULL,
            payload_sha256 TEXT,
            created_at TEXT NOT NULL
        )
    """)
    columns = {
        row[1] for row in db.execute(
            "PRAGMA table_info(investigation_reports)"
        )
    }
    if "payload_sha256" not in columns:
        db.execute(
            "ALTER TABLE investigation_reports "
            "ADD COLUMN payload_sha256 TEXT"
        )


def save_investigation(report):
    """Explicitly archive a valid synthetic comparison and its evaluation."""
    if not isinstance(report, dict):
        raise ValueError("A comparison report object is required")

    if report.get("report_type") != "SYNTHETIC_INCIDENT_COMPARISON":
        raise ValueError("Only synthetic incident comparisons may be saved")

    if report.get("requires_human_approval") is not True:
        raise ValueError("Human-approval safeguard is required")

    if report.get("action_executed") is not False:
        raise ValueError("Reports involving executed actions cannot be archived")

    if report.get("data_persisted") is not False:
        raise ValueError("Only previously unsaved comparisons may be archived")

    incident_a = report.get("incident_a")
    incident_b = report.get("incident_b")

    if not isinstance(incident_a, dict) or not isinstance(incident_b, dict):
        raise ValueError("Both synthetic incidents are required")

    scenario_a = incident_a.get("scenario")
    scenario_b = incident_b.get("scenario")

    # Validate against the server's current synthetic scenario definitions.
    expected = compare_incidents(scenario_a, scenario_b)

    if report.get("incident_a") != expected["incident_a"]:
        raise ValueError("Incident A does not match synthetic scenario data")

    if report.get("incident_b") != expected["incident_b"]:
        raise ValueError("Incident B does not match synthetic scenario data")

    # ATLAS_V16_VERIFY_RCA
    # Recompute deterministic RCA; ignore only its absent time-dependent fields.
    for key in ("root_cause_a", "root_cause_b"):
        if report.get(key) != expected[key]:
            raise ValueError(f"{key} does not match deterministic synthetic RCA")

    evaluation = evaluate_report(report)

    if evaluation["status"] != "PASS":
        raise ValueError("Report failed deterministic quality checks")

    report_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    saved = {
        "version": "1.6",
        "record_type": "SYNTHETIC_INVESTIGATION_ARCHIVE",
        "report_id": report_id,
        "created_at": created_at,
        "scenario_a": scenario_a,
        "scenario_b": scenario_b,
        "evaluation_status": evaluation["status"],
        "comparison": report,
        "evaluation": evaluation,
        "requires_human_approval": True,
        "action_executed": False,
        "data_persisted": True,
        "limitations": (
            "Local archive of synthetic investigation data only. "
            "No real payment processing, causal verification, "
            "or recovery action execution."
        ),
    }

    with closing(connect()) as db, db:
        _create_table(db)
        db.execute(
            """
            INSERT INTO investigation_reports
            (report_id, scenario_a, scenario_b,
             evaluation_status, payload, payload_sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                scenario_a,
                scenario_b,
                evaluation["status"],
                json.dumps(saved),
                _payload_digest(saved),
                created_at,
            ),
        )

    return saved


def investigation_history(limit=20):
    """Return the latest archived investigations."""
    limit = max(1, min(int(limit), 100))

    with closing(connect()) as db:
        _create_table(db)
        rows = db.execute(
            """
            SELECT payload, payload_sha256
            FROM investigation_reports
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        _verify_payload(json.loads(row[0]), row[1])
        for row in rows
    ]


def get_investigation(report_id):
    """Retrieve one archived investigation by ID."""
    if not isinstance(report_id, str) or not report_id.strip():
        raise ValueError("A valid report ID is required")

    with closing(connect()) as db:
        _create_table(db)
        row = db.execute(
            "SELECT payload, payload_sha256 FROM investigation_reports WHERE report_id = ?",
            (report_id,),
        ).fetchone()

    return _verify_payload(json.loads(row[0]), row[1]) if row else None
