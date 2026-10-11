import unittest
from engine import investigate
from agent_pipeline import investigate_agents
from digital_twin import experiment

class AdvancedTests(unittest.TestCase):
    def test_agent_investigation(self):
        result = investigate_agents(investigate('provider_outage'))
        self.assertEqual(result['severity'], 'CRITICAL')
        self.assertTrue(result['requires_human_approval'])
        self.assertEqual(result['recommended_strategy'], 'backup_provider')
    def test_simulation_reproducible(self):
        incident = investigate('provider_outage')
        a = experiment(incident, 'backup_provider', trials=1000, seed=7)
        b = experiment(incident, 'backup_provider', trials=1000, seed=7)
        self.assertEqual(a, b)
        self.assertGreater(a['estimated_improvement_pp'], 0)
    def test_reject_bad_strategy(self):
        with self.assertRaises(ValueError):
            experiment(investigate('healthy'), 'unsafe_strategy')
    def test_invalid_trials(self):
        with self.assertRaises(ValueError):
            experiment(investigate('healthy'), 'backup_provider', trials=0)

if __name__ == '__main__': unittest.main()
