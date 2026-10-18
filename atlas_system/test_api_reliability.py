
import json
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

BASE_URL = "http://127.0.0.1:8765"


def get_json(path):
    try:
        with urlopen(BASE_URL + path, timeout=5) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


class TestAPIReadReliability(unittest.TestCase):

    def test_health(self):
        status, body = get_json("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["mode"], "local_simulation")

    def test_archive_history(self):
        status, body = get_json("/api/investigations/history")
        self.assertEqual(status, 200)
        self.assertIsInstance(body, list)

    def test_unknown_investigation(self):
        status, body = get_json(
            "/api/investigations/00000000-0000-4000-8000-000000000000"
        )
        self.assertEqual(status, 404)
        self.assertIn("error", body)

    def test_unknown_endpoint(self):
        status, body = get_json("/api/nonexistent-v18-test")
        self.assertEqual(status, 404)
        self.assertIn("error", body)


    def test_invalid_json_returns_400(self):
        from urllib.request import Request

        request = Request(
            BASE_URL + "/api/investigations/save",
            data=b"{invalid-json",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as result:
            urlopen(request, timeout=5)
        self.assertEqual(result.exception.code, 400)

    def test_invalid_archive_save_returns_400(self):
        from urllib.request import Request

        request = Request(
            BASE_URL + "/api/investigations/save",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as result:
            urlopen(request, timeout=5)
        self.assertEqual(result.exception.code, 400)

    def test_oversized_request_returns_413(self):
        from urllib.request import Request

        request = Request(
            BASE_URL + "/api/investigations/save",
            data=b"x" * 10001,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as result:
            urlopen(request, timeout=5)
        self.assertEqual(result.exception.code, 413)

if __name__ == "__main__":
    unittest.main()
