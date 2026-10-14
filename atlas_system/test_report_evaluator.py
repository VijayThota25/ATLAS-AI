"""ATLAS v1.5 regression tests for report quality evaluation."""
import copy
import unittest

from incident_comparison import compare_incidents
from report_evaluator import evaluate_report


class TestReportEvaluator(unittest.TestCase):

    def setUp(self):
        self.report = compare_incidents(
            "provider_outage", "retry_storm"
        )

    def test_valid_report_passes(self):
        result = evaluate_report(self.report)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["passed_checks"], 7)

    def test_incorrect_metric_detected(self):
        report = copy.deepcopy(self.report)
        report["incident_a"]["metrics"]["average_latency_ms"] = 999

        result = evaluate_report(report)
        self.assertIn("incident_consistency", result["failed_checks"])

    def test_incorrect_difference_detected(self):
        report = copy.deepcopy(self.report)
        report["differences_b_minus_a"]["latency_ms"] = 0

        result = evaluate_report(report)
        self.assertIn("metric_differences", result["failed_checks"])

    def test_missing_evidence_detected(self):
        report = copy.deepcopy(self.report)
        report["root_cause_a"]["supporting_evidence"] = []

        result = evaluate_report(report)
        self.assertIn("root_cause_a_evidence", result["failed_checks"])

    def test_unsafe_action_detected(self):
        report = copy.deepcopy(self.report)
        report["action_executed"] = True

        result = evaluate_report(report)
        self.assertIn("read_only_safety", result["failed_checks"])

    def test_missing_limitations_detected(self):
        report = copy.deepcopy(self.report)
        report["limitations"] = ""

        result = evaluate_report(report)
        self.assertIn("limitations_disclosed", result["failed_checks"])

    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_report(None)


if __name__ == "__main__":
    unittest.main()
