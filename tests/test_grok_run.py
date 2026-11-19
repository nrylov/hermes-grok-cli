import importlib.util
import json
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location(
    "grok_run", os.path.join(HERE, "..", "skills", "grok-cli", "scripts", "grok_run.py"))
grok_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(grok_run)

SAMPLE = {
    "text": "Changed a-b to a+b.", "stopReason": "end_turn", "sessionId": "abc",
    "num_turns": 3, "total_cost_usd": 0.07,
    "usage": {"input_tokens": 100, "output_tokens": 20},
}


class BuildCommand(unittest.TestCase):
    def test_flags(self):
        cmd = grok_run.build_command("do it", "bypassPermissions", 5)
        self.assertEqual(cmd[:3], ["grok", "-p", "do it"])
        self.assertIn("--output-format", cmd)
        self.assertEqual(cmd[cmd.index("--max-turns") + 1], "5")
        self.assertIn("--no-subagents", cmd)
        self.assertNotIn("-m", cmd)

    def test_model_and_no_turn_limit(self):
        cmd = grok_run.build_command("x", "plan", 0, model="grok-4.7-build")
        self.assertNotIn("--max-turns", cmd)
        self.assertEqual(cmd[cmd.index("-m") + 1], "grok-4.7-build")


class Summarize(unittest.TestCase):
    def test_fields(self):
        s = grok_run.summarize(json.dumps(SAMPLE))
        self.assertEqual(s["stop_reason"], "end_turn")
        self.assertEqual(s["num_turns"], 3)
        self.assertEqual(s["output_tokens"], 20)
        self.assertEqual(s["session_id"], "abc")

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            grok_run.summarize("not json")


class Run(unittest.TestCase):
    def test_cancelled_is_not_ok(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, ".git"))
            cancelled = dict(SAMPLE, stopReason="cancelled")
            orig = grok_run.subprocess.run
            class P: returncode = 0; stdout = json.dumps(cancelled); stderr = ""
            grok_run.subprocess.run = lambda *a, **k: P() if "grok" in a[0][0] else orig(*a, **k)
            try:
                res = grok_run.run("x", d)
            finally:
                grok_run.subprocess.run = orig
            self.assertFalse(res["ok"])
            self.assertEqual(res["stop_reason"], "cancelled")

    def test_rejects_non_repo(self):
        with tempfile.TemporaryDirectory() as d:
            res = grok_run.run("x", d)
            self.assertFalse(res["ok"])
            self.assertIn("not a git repo", res["error"])


if __name__ == "__main__":
    unittest.main()
