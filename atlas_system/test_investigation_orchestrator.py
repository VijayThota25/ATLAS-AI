
"""Regression tests for the ATLAS v2.0 investigation orchestrator."""

import unittest
from unittest.mock import patch

from investigation_orchestrator import run_investigation


class InvestigationOrchestratorTests(unittest.TestCase):

    def test_successful_investigation(self):
        result = run_investigation("provider_outage", "healthy")

        self.assertEqual(
            result["status"], "READY_FOR_HUMAN_REVIEW"
        )
        self.assertEqual(result["evaluation"]["status"], "PASS")
        self.assertEqual(result["evaluation"]["passed_checks"], 7)

    def test_completed_stages(self):
        result = run_investigation()

        self.assertEqual(
            [stage["stage"] for stage in result["stages"]],
            ["SYNTHETIC_COMPARISON", "REPORT_EVALUATION"],
        )
        self.assertTrue(
            all(stage["status"] == "COMPLETED"
                for stage in result["stages"])
        )

    def test_invalid_scenario_rejected(self):
        with self.assertRaises(ValueError):
            run_investigation("invalid_scenario", "healthy")

    def test_evaluation_failure_requires_review(self):
        with patch(
            "investigation_orchestrator.evaluate_report",
            return_value={
                "status": "NEEDS_REVIEW",
                "passed_checks": 6,
                "total_checks": 7,
            },
        ):
            result = run_investigation()

        self.assertEqual(result["status"], "NEEDS_REVIEW")

    def test_read_only_safety(self):
        result = run_investigation()

        self.assertTrue(result["requires_human_approval"])
        self.assertFalse(result["action_executed"])
        self.assertFalse(result["data_persisted"])
        self.assertFalse(result["report"]["action_executed"])
        self.assertFalse(result["report"]["data_persisted"])

    def test_stage_timing_recorded(self):
        result = run_investigation()

        for stage in result["stages"]:
            self.assertGreaterEqual(stage["duration_ms"], 0)
            self.assertEqual(stage["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
