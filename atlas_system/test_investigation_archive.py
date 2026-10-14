"""Regression tests for ATLAS v1.6 investigation archive."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import atlas_store
from incident_comparison import compare_incidents
from investigation_archive import (
    get_investigation,
    investigation_history,
    save_investigation,
)


class InvestigationArchiveTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(
            atlas_store, "DB",
            Path(self.temp_dir.name) / "test_atlas.db"
        )
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_save_valid_investigation(self):
        report = compare_incidents("provider_outage", "healthy")
        saved = save_investigation(report)
        self.assertEqual(saved["version"], "1.6")
        self.assertEqual(saved["evaluation_status"], "PASS")
        self.assertTrue(saved["data_persisted"])
        self.assertFalse(saved["action_executed"])
        self.assertTrue(saved["requires_human_approval"])

    def test_retrieve_saved_investigation(self):
        report = compare_incidents("provider_outage", "retry_storm")
        saved = save_investigation(report)
        self.assertEqual(get_investigation(saved["report_id"]), saved)

    def test_history_returns_saved_reports(self):
        first = save_investigation(
            compare_incidents("healthy", "latency_spike")
        )
        second = save_investigation(
            compare_incidents("provider_outage", "healthy")
        )
        history = investigation_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["report_id"], second["report_id"])
        self.assertEqual(history[1]["report_id"], first["report_id"])

    def test_reject_executed_action(self):
        report = compare_incidents("provider_outage", "healthy")
        report["action_executed"] = True
        with self.assertRaises(ValueError):
            save_investigation(report)

    def test_reject_missing_human_approval(self):
        report = compare_incidents("provider_outage", "healthy")
        report["requires_human_approval"] = False
        with self.assertRaises(ValueError):
            save_investigation(report)

    def test_reject_modified_synthetic_metrics(self):
        report = compare_incidents("provider_outage", "healthy")
        report["incident_a"]["metrics"]["failed_transactions"] = 999999
        with self.assertRaises(ValueError):
            save_investigation(report)

    def test_reject_tampered_root_cause(self):
        report = compare_incidents("provider_outage", "healthy")
        report["root_cause_a"]["primary_hypothesis"] = (
            "Fabricated verified provider failure"
        )

        with self.assertRaises(ValueError):
            save_investigation(report)

    def test_reject_invalid_report(self):
        with self.assertRaises(ValueError):
            save_investigation({"report_type": "UNKNOWN"})

    def test_unknown_report_returns_none(self):
        self.assertIsNone(get_investigation("missing-report-id"))


if __name__ == "__main__":
    unittest.main()
