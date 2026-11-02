"""A02-only extension of the frozen 21-test E1-guarded offline whitelist."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


original = Path(__file__).with_name("d7_e4g_offline_checks.py")
if hashlib.sha256(original.read_bytes()).hexdigest() != "c0d1d0b1f47e4ee0a9112d578e1de03798310c4a59c626d52837988f91934fa5":
    raise RuntimeError("E4G_ORIGINAL_TEST_DRIFT")
# Installs E1 issuer/SQLite/native guards BEFORE importing any new wiring.
old = load("e4g_frozen_offline", original)
a02 = load("e4g_a02", Path(__file__).with_name("d7_e4g_a02.py"))
old.wire = a02.wire
a02.preflight()  # Actual frozen source/import and absent A02 paths; no host/GUI/Owner.
offline_root = Path(tempfile.mkdtemp(prefix="GDCAE-E4G-A02-OFFLINE-", dir=old.ENV.parent.parent))
real_mkdtemp = tempfile.mkdtemp


class Checks(old.Checks):
    def test_real_journal_exclusive_claim_and_partial_reservation(self):
        with patch.object(old.tempfile, "mkdtemp", side_effect=lambda **_: real_mkdtemp(prefix="journal-", dir=offline_root)):
            super().test_real_journal_exclusive_claim_and_partial_reservation()

    def test_exact_a02_binding_no_a01_mutation(self):
        self.assertEqual(a02.wire.TASK.name, "GDCAE-D7-E4G-20261102-A02")
        self.assertEqual(a02.wire.PROJECT, a02.wire.TASK / "af-test-only")
        self.assertEqual(a02.PREFERENCES.name, "GDCAE-D7-E4G-20261102-A02.ui.json")
        self.assertEqual(hashlib.sha256(a02.source.read_bytes()).hexdigest(), a02.A01_SHA)

    def test_preflight_existing_root_or_preferences_denied(self):
        for exists in ([True], [False, True]):
            with patch.object(a02.wire, "verify_runtime"), patch.object(a02.wire, "no_links"), \
                    patch.object(Path, "exists", side_effect=exists):
                with self.assertRaises(RuntimeError):
                    a02.preflight()

    def test_preflight_failure_fixed_output_no_execution(self):
        with patch.object(sys, "argv", ["a02", "--preflight-only"]), \
                patch.object(a02, "preflight", side_effect=OSError("PRIVATE_CANARY")), \
                patch.object(a02.wire, "main") as execute, patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(a02.main(), 2)
            execute.assert_not_called()
            self.assertNotIn("PRIVATE_CANARY", output.getvalue())
            self.assertFalse(json.loads(output.getvalue())["owner_started"])

    def test_wrong_preferences_denied_and_exact_binding_forwarded(self):
        with patch.object(sys, "argv", ["a02", "--execute-approved-single-attempt"]), \
                patch.object(a02.wire, "main", return_value=2) as execute, \
                patch("sys.stdout", new_callable=io.StringIO):
            with patch.dict(os.environ, {"ABQJOBPILOT_UI_PREFS": "wrong"}):
                self.assertEqual(a02.main(), 2)
                execute.assert_not_called()
            with patch.dict(os.environ, {"ABQJOBPILOT_UI_PREFS": str(a02.PREFERENCES)}):
                self.assertEqual(a02.main(), 2)
                execute.assert_called_once_with()

    def test_input_eof_empty_and_exact_confirmation_no_real_calls(self):
        # Calls original main with all side-effect boundaries mocked, E1 guards remain active.
        for response in ("", EOFError("PRIVATE_CANARY"), KeyboardInterrupt()):
            with patch.object(sys, "argv", ["a02", "--execute-approved-single-attempt"]), \
                    patch.object(a02.wire, "verify_runtime"), patch.object(a02.wire, "Journal") as journal, \
                    patch("builtins.input", **({"side_effect": response} if isinstance(response, BaseException) else {"return_value": response})), \
                    patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(a02.wire.main(), 2)
                journal.assert_not_called()
                self.assertEqual(json.loads(output.getvalue())["failure_stage"], "PREFLIGHT_OR_RESERVATION")
        result = {"status": "E4G_UNKNOWN_OR_BLOCKED", "retry": False}
        with patch.object(sys, "argv", ["a02", "--execute-approved-single-attempt"]), \
                patch.object(a02.wire, "verify_runtime"), patch.object(a02.wire, "Journal") as journal, \
                patch.object(a02.wire, "AFPort", return_value=Mock()), \
                patch.object(a02.wire, "run_once", return_value=result) as run, \
                patch("builtins.input", return_value="E4G SINGLE TEST_ONLY"), patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(a02.wire.main(), 2)
            journal.assert_called_once_with(a02.wire.TASK)
            run.assert_called_once()


if __name__ == "__main__":
    result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    print(json.dumps({"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                      "failed_tests": [test.id().split(".")[-1] for test, _ in result.failures + result.errors],
                      "owner_starts": 0, "grant_increment": 0, "run_increment": 0, "database_connections_created": 0,
                      "native": "MOCKED", "e1_guard_reused": True, "offline_directory": offline_root.name,
                      "retry": False}, sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
