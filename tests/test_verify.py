"""Exercise the verifier CLI through its public command and report files."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNNER = Path(__file__).resolve().parents[1] / "skills/task-worker/scripts/verify.py"


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.project = Path(self.scratch.name)
        (self.project / "app.py").write_text("print('hello')\n")
        (self.project / "check.py").write_text(
            "import subprocess, sys\n"
            "result = subprocess.run([sys.executable, 'app.py'], capture_output=True, text=True)\n"
            "assert result.returncode == 0\n"
            "assert result.stdout == 'hello\\n', repr(result.stdout)\n")
        self.task = {"id": "greeting", "sources": ["app.py", "check.py"],
                     "acceptance": [{"id": "A1", "outcome": "CLI prints hello",
                                     "verifiers": ["greeting"]}]}
        self.registry = {"verifiers": [{"id": "greeting", "scope": "project",
                                       "claim": "CLI prints hello",
                                       "command": [sys.executable, "check.py"], "timeout_seconds": 5}]}

    def run_task(self):
        (self.project / "task.json").write_text(json.dumps(self.task))
        (self.project / "registry.json").write_text(json.dumps(self.registry))
        result = subprocess.run([sys.executable, str(RUNNER), "--project", str(self.project),
                                 "--task", str(self.project / "task.json"), "--registry",
                                 str(self.project / "registry.json"), "--output",
                                 str(self.project / "evidence")], capture_output=True, text=True)
        report = None
        if result.stdout:
            report = json.loads(Path(json.loads(result.stdout)["report"]).read_text())
        return result, report

    def test_good_behavior_passes_with_persistent_evidence(self):
        result, report = self.run_task()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(Path(report["results"][0]["log"]).exists())
        self.assertEqual(report["sources_before"], report["sources_after"])
        self.assertEqual(json.loads((self.project / "task.json").read_text()), self.task)

    def test_broken_user_behavior_fails(self):
        (self.project / "app.py").write_text("print('wrong')\n")
        result, report = self.run_task()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["status"], "fail")
        self.assertIn("AssertionError", Path(report["results"][0]["log"]).read_text())

    def test_missing_required_check_blocks_even_when_other_check_passes(self):
        self.task["acceptance"][0]["verifiers"].append("missing")
        result, report = self.run_task()
        self.assertEqual(result.returncode, 2)
        self.assertEqual([r["status"] for r in report["results"]], ["pass", "blocked"])

    def test_missing_executable_blocks(self):
        self.registry["verifiers"][0]["command"] = [str(self.project / "no-such-command")]
        result, report = self.run_task()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "blocked")

    def test_timeout_blocks(self):
        self.registry["verifiers"][0].update(
            command=[sys.executable, "-c", "import time; time.sleep(30)"], timeout_seconds=0.1)
        result, report = self.run_task()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["results"][0]["reason"], "Verifier timed out")

    def test_source_changed_during_check_blocks(self):
        (self.project / "check.py").write_text("from pathlib import Path\nPath('app.py').write_text('changed')\n")
        result, report = self.run_task()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["results"][0]["status"], "pass")
        self.assertFalse(report["inputs_unchanged"])

    def test_acceptance_cannot_have_no_checks(self):
        self.task["acceptance"][0]["verifiers"] = []
        result, report = self.run_task()
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)
        self.assertIn("needs verifier ids", result.stderr)

    def test_duplicate_registration_is_rejected_before_execution(self):
        self.registry["verifiers"].append(dict(self.registry["verifiers"][0]))
        result, _ = self.run_task()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Duplicate verifier id", result.stderr)

    def test_previous_success_is_not_reused(self):
        first, _ = self.run_task()
        self.assertEqual(first.returncode, 0)
        (self.project / "app.py").write_text("raise RuntimeError('broken')\n")
        second, report = self.run_task()
        self.assertEqual(second.returncode, 1)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(len(list((self.project / "evidence").glob("*/report.json"))), 2)


if __name__ == "__main__":
    unittest.main()
