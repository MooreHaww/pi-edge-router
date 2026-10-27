"""Tests for eco_core with fake tiers only. No model servers, no cloud calls.

Run with: python -m unittest -v test_eco_core
"""
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

import eco_core
from eco_core import Tier

GOOD = "```python\ndef add(a, b):\n    return a + b\n```"
BAD = "```python\ndef add(a, b):\n    return a - b\n```"
TESTS = [[[1, 2], 3], [[5, 5], 10]]
PROMPT = "Write add(a, b) that returns the sum."


def fake(name, reply, kind="local", cost=0.0):
    """A tier that records how often it was called and returns a fixed reply."""
    calls = []

    def ask(prompt):
        calls.append(prompt)
        return reply

    return Tier(name, kind, ask, cost), calls


class SolveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self.tmp.name, "eco_log.jsonl")

    def tearDown(self):
        self.tmp.cleanup()

    def run_solve(self, tiers, **env):
        with mock.patch.dict(os.environ, env, clear=False):
            if "ALLOW_CLOUD" not in env:
                os.environ.pop("ALLOW_CLOUD", None)
            return eco_core.solve(PROMPT, TESTS, "add", tiers, task_id="t_add", log_path=self.log)

    def test_a_stops_at_first_passing_tier(self):
        first, first_calls = fake("pi", GOOD)
        second, second_calls = fake("pc", GOOD)
        result = self.run_solve([first, second])
        self.assertEqual(result["solved_by"], "pi")
        self.assertEqual(len(first_calls), 1)
        self.assertEqual(second_calls, [])
        self.assertEqual([a["tier"] for a in result["attempts"]], ["pi"])

    def test_b_escalates_when_tests_fail(self):
        first, first_calls = fake("pi", BAD)
        second, second_calls = fake("pc", GOOD)
        result = self.run_solve([first, second])
        self.assertEqual(result["solved_by"], "pc")
        self.assertEqual([(a["tier"], a["passed"]) for a in result["attempts"]],
                         [("pi", False), ("pc", True)])
        self.assertEqual((len(first_calls), len(second_calls)), (1, 1))

    def test_c_cloud_not_called_without_allow_cloud(self):
        local, _ = fake("pc", BAD)
        cloud, cloud_calls = fake("cloud", GOOD, kind="cloud", cost=0.01)
        for value in (None, "0", "yes"):
            env = {} if value is None else {"ALLOW_CLOUD": value}
            result = self.run_solve([local, cloud], **env)
            self.assertEqual(cloud_calls, [], f"cloud was called with ALLOW_CLOUD={value!r}")
            self.assertIsNone(result["solved_by"])
            self.assertEqual(result["skipped"], ["cloud"])
            self.assertEqual(result["cost_usd"], 0.0)
        result = self.run_solve([local, cloud], ALLOW_CLOUD="1")
        self.assertEqual(len(cloud_calls), 1)
        self.assertEqual(result["solved_by"], "cloud")
        self.assertEqual(result["cost_usd"], 0.01)

    def test_d_log_line_has_expected_fields(self):
        tier, _ = fake("pc", GOOD)
        result = self.run_solve([tier])
        with open(self.log, encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        for field in ("timestamp", "task_id", "solved_by", "attempts", "cost_usd", "seconds",
                      "estimated_cloud_cost_avoided_usd"):
            self.assertIn(field, entry)
        self.assertEqual(entry["task_id"], "t_add")
        self.assertEqual(entry["solved_by"], "pc")
        self.assertEqual(entry["attempts"][0]["tier"], "pc")
        self.assertEqual(entry["estimated_cloud_cost_avoided_usd"], result["estimated_cloud_cost_avoided_usd"])

    def test_e_none_when_every_tier_fails(self):
        first, _ = fake("pi", BAD)
        second, _ = fake("pc", "no code here at all")
        result = self.run_solve([first, second])
        self.assertIsNone(result["solved_by"])
        self.assertEqual(len(result["attempts"]), 2)
        self.assertFalse(any(a["passed"] for a in result["attempts"]))
        self.assertEqual(result["estimated_cloud_cost_avoided_usd"], 0.0)


class DiscoverTests(unittest.TestCase):
    def test_f_discover_reports_models_and_skips_closed_ports(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = json.dumps({"data": [{"id": "fake-model"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            open_port = server.server_address[1]
            with HTTPServer(("127.0.0.1", 0), Handler) as closed:
                closed_port = closed.server_address[1]  # bound then closed: nothing listens
            found = eco_core.discover_local({open_port: "stub", closed_port: "none"},
                                            host="127.0.0.1", timeout=1.0)
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual([(s["port"], s["models"]) for s in found], [(open_port, ["fake-model"])])


if __name__ == "__main__":
    unittest.main()
