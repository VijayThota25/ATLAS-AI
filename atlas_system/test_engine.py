import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import engine

class TestEngine(unittest.TestCase):
    def test_all_scenarios(self):
        expected = {'healthy':'HEALTHY','provider_outage':'CRITICAL','latency_spike':'CRITICAL','retry_storm':'HIGH'}
        for name, severity in expected.items():
            with self.subTest(name=name):
                result = engine.investigate(name)
                self.assertEqual(result['severity'], severity)
                self.assertEqual(result['environment'], 'SIMULATION')
    def test_storage(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'incidents.jsonl'
            with patch.object(engine, 'HISTORY', path):
                result = engine.create_incident('healthy')
                self.assertEqual(engine.read_records(path)[0]['incident_id'], result['incident_id'])
    def test_approval_gate(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'actions.jsonl'
            with patch.object(engine, 'ACTIONS', path):
                incident = engine.investigate('retry_storm')
                proposal = engine.propose_action(incident, 'bounded_retries')
                self.assertEqual(proposal['status'], 'PENDING_HUMAN_APPROVAL')
                completed = engine.approve_action(proposal['action_id'])
                self.assertEqual(completed['status'], 'SIMULATED_EXECUTION_COMPLETE')
    def test_invalid_strategy(self):
        with self.assertRaises(ValueError):
            engine.simulate_recovery(engine.investigate('healthy'), 'unknown')

if __name__ == '__main__': unittest.main()
