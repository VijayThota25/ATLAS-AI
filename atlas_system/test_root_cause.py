"""ATLAS v1.3 deterministic RCA safety and regression tests."""
import unittest
from root_cause import analyze
from engine import SCENARIOS, classify

class RootCauseTests(unittest.TestCase):
    def test_all_scenarios(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                result = analyze(scenario)
                self.assertEqual(result['scenario'], scenario)
                self.assertEqual(result['severity'], classify(SCENARIOS[scenario])[0])
                self.assertEqual(result['confidence'], 'UNVERIFIED_HYPOTHESIS')
                self.assertTrue(result['alternative_explanations'])
                self.assertTrue(result['missing_evidence'])
                self.assertTrue(result['investigation_steps'])
                self.assertEqual(len(result['supporting_evidence']), 3)
    def test_safety_guards(self):
        for scenario in SCENARIOS:
            result = analyze(scenario)
            self.assertIs(result['requires_human_approval'], True)
            self.assertIs(result['action_executed'], False)
            self.assertIs(result['data_persisted'], False)
    def test_invalid_scenarios(self):
        for value in ('unknown', '', None, 42, {}, []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyze(value)
    def test_deterministic(self):
        for scenario in SCENARIOS:
            self.assertEqual(analyze(scenario), analyze(scenario))
    def test_provider_outage_evidence(self):
        result = analyze('provider_outage')
        self.assertEqual(result['severity'], 'CRITICAL')
        self.assertEqual(result['supporting_evidence'][0]['value'], 42.5)
        self.assertIn('provider', result['primary_hypothesis'].lower())

if __name__ == '__main__':
    unittest.main()
