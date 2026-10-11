"""ATLAS v0.6 offline regression suite tests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import evaluation_suite

class EvaluationSuiteTests(unittest.TestCase):
    def test_all_fixed_cases(self):
        result=evaluation_suite.run_checks()
        self.assertEqual(result['total'],14)
        self.assertEqual(result['failed'],0)
        self.assertEqual(result['passed'],14)
    def test_persistence_and_history(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(evaluation_suite,'DB',Path(d)/'test.db'):
                first=evaluation_suite.run_and_record()
                second=evaluation_suite.run_and_record()
                self.assertEqual([r['run_id'] for r in evaluation_suite.history()],
                                 [second['run_id'],first['run_id']])
                self.assertEqual(first['failed'],0)
    def test_malformed_report_is_rejected(self):
        from structured_advisory import validate_report
        from engine import investigate
        with self.assertRaises(ValueError):
            validate_report({'hypothesis':'not enough fields'},investigate('healthy'))
