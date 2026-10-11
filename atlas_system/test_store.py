import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import atlas_store

class StoreTests(unittest.TestCase):
    def test_mirror_idempotent_and_metrics(self):
        with tempfile.TemporaryDirectory() as d, patch.object(atlas_store, 'DB', Path(d) / 'atlas.db'):
            incident = {'incident_id': 'i1', 'metrics': {'payment_success_rate': 42.5}}
            atlas_store.mirror('incident', incident)
            atlas_store.mirror('incident', incident)
            atlas_store.mirror('action', {'action_id':'a1', 'status':'PENDING_HUMAN_APPROVAL'})
            atlas_store.mirror('action', {'action_id':'a1', 'status':'SIMULATED_EXECUTION_COMPLETE'})
            atlas_store.record_operation('llm_analysis', 150, True)
            stats = atlas_store.overview()
            self.assertEqual(stats['records']['incident'], 1)
            self.assertEqual(stats['records']['action'], 2)
            self.assertEqual(stats['operations'][0]['average_duration_ms'], 150)
    def test_history_import(self):
        with tempfile.TemporaryDirectory() as d, patch.object(atlas_store, 'DB', Path(d) / 'atlas.db'):
            p = Path(d) / 'incidents.jsonl'
            p.write_text(json.dumps({'incident_id':'historical'})+'\n', encoding='utf-8')
            self.assertEqual(atlas_store.import_history(p, Path(d) / 'missing'), 1)
            self.assertEqual(atlas_store.overview()['records']['incident'], 1)
