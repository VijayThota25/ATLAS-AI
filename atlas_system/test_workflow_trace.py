"""ATLAS v1.0 read-only workflow tests."""
import unittest
from workflow_trace import trace, regression

class WorkflowTraceTests(unittest.TestCase):
    def test_regression(self):
        report = regression()
        self.assertEqual(report['failed'], 0, report)
        self.assertEqual(report['total'], 11)

    def test_safe_failure(self):
        result = trace('provider_outage', 'persistent_timeout')
        self.assertEqual(result['reliability_outcome'], 'SAFE_FAILURE')
        self.assertFalse(result['action_executed'])
        self.assertFalse(result['data_persisted'])
        self.assertEqual(result['steps'][-1]['status'], 'AWAITING_HUMAN_REVIEW')

if __name__ == '__main__':
    unittest.main()
