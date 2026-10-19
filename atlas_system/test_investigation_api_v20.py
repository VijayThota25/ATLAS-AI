
"""HTTP regression tests for ATLAS v2.0 investigations."""

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import Handler


class InvestigationAPITests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.thread.start()
        cls.url = (
            f"http://127.0.0.1:{cls.server.server_port}"
            "/api/investigations/run"
        )

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def post(self, payload):
        request = Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_valid_investigation(self):
        status, result = self.post({
            "scenario_a": "provider_outage",
            "scenario_b": "healthy",
        })

        self.assertEqual(status, 200)
        self.assertEqual(
            result["status"], "READY_FOR_HUMAN_REVIEW"
        )
        self.assertEqual(result["evaluation"]["passed_checks"], 7)
        self.assertEqual(result["evaluation"]["total_checks"], 7)

    def test_invalid_scenario_returns_400(self):
        status, result = self.post({
            "scenario_a": "invalid_scenario",
            "scenario_b": "healthy",
        })

        self.assertEqual(status, 400)
        self.assertIn("error", result)

    def test_read_only_safety_flags(self):
        status, result = self.post({
            "scenario_a": "provider_outage",
            "scenario_b": "healthy",
        })

        self.assertEqual(status, 200)
        self.assertTrue(result["requires_human_approval"])
        self.assertFalse(result["action_executed"])
        self.assertFalse(result["data_persisted"])

    def test_execution_stages(self):
        status, result = self.post({
            "scenario_a": "provider_outage",
            "scenario_b": "healthy",
        })

        self.assertEqual(status, 200)
        self.assertEqual(
            [stage["status"] for stage in result["stages"]],
            ["COMPLETED", "COMPLETED"],
        )


if __name__ == "__main__":
    unittest.main()
