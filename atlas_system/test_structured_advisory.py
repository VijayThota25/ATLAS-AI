import unittest
from structured_advisory import validate_report, evaluate_report

INCIDENT = {'metrics':{'payment_success_rate':42.5,'average_latency_ms':4200,'failed_transactions':1284}}
REPORT = {'hypothesis':'A provider outage is plausible, not confirmed.',
          'evidence_to_check':['Inspect upstream provider status and errors'],
          'recommended_next_steps':['Verify the provider status before choosing mitigation'],
          'limitations':['Metrics alone cannot establish root cause']}
class StructuredAdvisoryTests(unittest.TestCase):
    def test_valid_report(self):
        result = validate_report(REPORT, INCIDENT)
        self.assertTrue(evaluate_report(result, INCIDENT)['passed'])
        self.assertTrue(result['requires_human_approval'])
    def test_invalid_report(self):
        with self.assertRaises(ValueError): validate_report({'hypothesis':'unverified'}, INCIDENT)
    def test_source_metrics_are_not_model_generated(self):
        result = validate_report(REPORT, INCIDENT)
        self.assertEqual(result['observed_metrics'], INCIDENT['metrics'])
    def test_evaluation_detects_metric_tampering(self):
        result = validate_report(REPORT, INCIDENT)
        result['observed_metrics']['failed_transactions'] = 0
        self.assertFalse(evaluate_report(result, INCIDENT)['passed'])
