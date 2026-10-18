from contextlib import closing
import json
import sqlite3
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


class TestArchiveIntegrity(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        temporary_db = Path(self.temp_dir.name) / "atlas_test.db"

        db_patch = patch.object(atlas_store, "DB", temporary_db)
        db_patch.start()
        self.addCleanup(db_patch.stop)

    def test_save_and_retrieve_investigation(self):
        comparison = compare_incidents(
            "provider_outage",
            "healthy",
        )

        saved = save_investigation(comparison)
        retrieved = get_investigation(saved["report_id"])

        self.assertEqual(retrieved, saved)
        self.assertEqual(saved["evaluation_status"], "PASS")
        self.assertTrue(saved["requires_human_approval"])
        self.assertFalse(saved["action_executed"])
        self.assertTrue(saved["data_persisted"])

        history = investigation_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["report_id"], saved["report_id"])


    def test_rejects_missing_human_approval(self):
        comparison = compare_incidents("provider_outage", "healthy")
        comparison["requires_human_approval"] = False

        with self.assertRaises(ValueError):
            save_investigation(comparison)

        self.assertEqual(investigation_history(), [])

    def test_rejects_executed_action(self):
        comparison = compare_incidents("provider_outage", "healthy")
        comparison["action_executed"] = True

        with self.assertRaises(ValueError):
            save_investigation(comparison)

        self.assertEqual(investigation_history(), [])

    def test_rejects_previously_persisted_comparison(self):
        comparison = compare_incidents("provider_outage", "healthy")
        comparison["data_persisted"] = True

        with self.assertRaises(ValueError):
            save_investigation(comparison)

        self.assertEqual(investigation_history(), [])

    def test_rejects_tampered_incident_data(self):
        comparison = compare_incidents("provider_outage", "healthy")

        # Tamper with the synthetic incident before archiving.
        comparison["incident_a"]["scenario"] = "healthy"

        with self.assertRaises(ValueError):
            save_investigation(comparison)

        # Invalid reports must never reach the archive.
        self.assertEqual(investigation_history(), [])

    def test_detects_modified_stored_report(self):
        comparison = compare_incidents("provider_outage", "healthy")
        saved = save_investigation(comparison)

        # Modify only the temporary test database.
        with closing(sqlite3.connect(atlas_store.DB)) as db, db:
            row = db.execute(
                "SELECT payload FROM investigation_reports WHERE report_id = ?",
                (saved["report_id"],),
            ).fetchone()

            tampered = json.loads(row[0])
            tampered["evaluation_status"] = "FAIL"

            db.execute(
                "UPDATE investigation_reports SET payload = ? WHERE report_id = ?",
                (json.dumps(tampered), saved["report_id"]),
            )

                # Future integrity verification must reject modified records.
        try:
            get_investigation(saved["report_id"])
        except ValueError:
            pass
        else:
            self.fail("Modified stored report was not rejected")

if __name__ == "__main__":
    unittest.main()
