"""Regression tests for ATLAS v1.4 synthetic incident comparison."""
import unittest

from incident_comparison import compare_incidents


class TestIncidentComparison(unittest.TestCase):

    def test_metric_differences(self):
        result = compare_incidents("provider_outage", "retry_storm")
        diff = result["differences_b_minus_a"]

        self.assertEqual(diff["success_rate_percentage_points"], 33.5)
        self.assertEqual(diff["latency_ms"], -2400)
        self.assertEqual(diff["failed_transactions"], 1116)

    def test_read_only_safety(self):
        result = compare_incidents("provider_outage", "healthy")
        self.assertTrue(result["requires_human_approval"])
        self.assertFalse(result["action_executed"])
        self.assertFalse(result["data_persisted"])

    def test_invalid_scenario(self):
        with self.assertRaises(ValueError):
            compare_incidents("invalid_scenario", "healthy")

    def test_severity_classification(self):
        result = compare_incidents("provider_outage", "healthy")
        self.assertEqual(result["incident_a"]["severity"], "CRITICAL")
        self.assertEqual(result["incident_b"]["severity"], "HEALTHY")

    def test_root_cause_included(self):
        result = compare_incidents("provider_outage", "retry_storm")
        self.assertIn("primary_hypothesis", result["root_cause_a"])
        self.assertIn("primary_hypothesis", result["root_cause_b"])


if __name__ == "__main__":
    unittest.main()
