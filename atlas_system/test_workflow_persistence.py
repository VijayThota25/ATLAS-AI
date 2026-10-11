"""v1.1 persistence checks; use temporary SQLite database."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import atlas_store
from workflow_trace import trace, regression

class PersistenceTests(unittest.TestCase):
    def test_save_and_history(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(atlas_store, 'DB', Path(tmp)/'test.db'):
            source = trace()
            saved = atlas_store.save_workflow_trace(source)
            self.assertTrue(saved['data_persisted'])
            self.assertFalse(saved['action_executed'])
            self.assertTrue(saved['requires_human_approval'])
            self.assertFalse(source['data_persisted'])
            self.assertEqual(atlas_store.workflow_history()[0]['trace_id'], saved['trace_id'])
    def test_reject_unsafe(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(atlas_store, 'DB', Path(tmp)/'test.db'):
            with self.assertRaises(ValueError):
                atlas_store.save_workflow_trace(dict(trace(), action_executed=True))
            self.assertEqual(atlas_store.workflow_history(), [])
    def test_old_regression(self):
        result=regression()
        self.assertEqual(result['failed'],0)

if __name__ == '__main__': unittest.main()
