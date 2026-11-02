"""Exact E4-G offline unittest entry; no pytest collection, GUI, IPC or Owner.

Reuse frozen E1 audit and in-place issuer denial BEFORE importing the wiring.
Additionally deny ALL SQLite connections/native/network and real lifecycle calls.
"""
import copy
import ctypes
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

ENV = Path(r"C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-R2F-E2-20261101-A01\env02")


def need(condition):
    if not condition:
        raise RuntimeError("OFFLINE_SCOPE")


need(Path(sys.executable).resolve() == ENV / "Scripts/python.exe")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e1_path = Path(r"D:\Projects\abqjobpilot_dev\tests\no_real_grants.py")
need(hashlib.sha256(e1_path.read_bytes()).hexdigest() ==
     "fcf27ba9efd7c4902e2fd801291ed33091b278944824c556c02876e04182d747")
e1 = load("e4g_e1_boundary", e1_path)
sys.addaudithook(e1._connect_audit)
DENIED = []


def offline_audit(event, args):
    if event.startswith(("sqlite3.", "subprocess.", "socket.", "ctypes.dl")) or event in {
        "os.system", "os.exec", "os.spawn", "os.startfile", "os.startfile/2",
    }:
        DENIED.append(event)
        raise RuntimeError("E4G_OFFLINE_SIDE_EFFECT_DENIED")


sys.addaudithook(offline_audit)
from abqjobpilot.execution import standard_contract, standard_sequence, product_standard  # noqa: E402
from abqjobpilot.service_lifecycle import ServiceLifecycleManager  # noqa: E402
from abqjobpilot import product_project  # noqa: E402

# E1 original-function-object replacement also blocks previously captured aliases.
FUNCTIONS = (standard_contract._issue, standard_contract.issue_execution,
             standard_sequence.issue_pair, product_standard.ProductStandardControl.invoke,
             ServiceLifecycleManager.start, ServiceLifecycleManager.stop, product_project.create_project)
for function in FUNCTIONS:
    need(not function.__closure__)
    function.__code__ = e1._deny_production.__code__
    function.__defaults__ = ()
    function.__kwdefaults__ = None

wire = load("e4g_wire", Path(__file__).with_name("d7_e4g_lifecycle.py"))
wire.verify_runtime()  # No host observation; exact installed module/source pins only.

CTX = SimpleNamespace(project_id="synthetic-project", project_instance_id="synthetic-instance",
                      context_digest="synthetic-context", execution_store="synthetic-store")
PROCESS = {"pid": 42, "parent_pid": 41, "creation_time_100ns": 1234,
           "image_path": str(wire.BASE_PYTHON), "executable": str(wire.ENV / "Scripts/python.exe")}
STARTED = {"state": "CONNECTED", "created": True, "start_id": "synthetic-start", "owner_id": "synthetic-owner"}
ENDPOINT = {**vars(CTX), "owner_id": STARTED["owner_id"], "process": PROCESS}
HEALTH = {"process": PROCESS, "lifecycle_start_id": STARTED["start_id"], "execution_scope": "TEST_ONLY",
          "simulation": True, "backend": "fake-v1", "backends": [{"backend_id": "fake-v1", "version": 1}],
          "process_fixture_enabled": False, "operations": ["lifecycle_stop"]}


class MemoryJournal:
    def __init__(self):
        self.claimed = False
        self.rows = []
        self.fail_stage = None

    def claim(self):
        wire.need(not self.claimed)
        self.claimed = True

    def write(self, stage, evidence=None):
        if stage == self.fail_stage:
            raise OSError("SYNTHETIC_PRIVATE_PATH")
        self.rows.append((stage, copy.deepcopy(evidence)))


class FakePort:
    """No AF data, capability, grant, Run, native handle or network is created."""
    def __init__(self):
        self.context = CTX
        self.client = Mock(endpoint=copy.deepcopy(ENDPOINT))
        self.client.health.return_value = copy.deepcopy(HEALTH)
        self.ref = Mock(handle=900)
        self.ref.api.CloseHandle.return_value = 1
        self.ref.api.IsProcessInJob.side_effect = self.job
        self.ref.exit_evidence.side_effect = self.exit_evidence
        self.started = copy.deepcopy(STARTED)
        self.receipt = {"state": "STOP_COMMITTED", "action": "lifecycle_stop_idle_v1",
                        "owner_id": STARTED["owner_id"], "start_id": STARTED["start_id"],
                        "operation_key": "e4g_stop_" + STARTED["start_id"],
                        "project_instance_id": CTX.project_instance_id}
        self.calls = []
        self.stopped = False
        self.in_job = True

    def job(self, handle, job, value):
        value._obj.value = int(self.in_job)
        return 1

    def exit_evidence(self):
        if self.stopped:
            return {**PROCESS, "exit_code": 0, "exit_source": "retained_windows_handle"}
        return None

    def prepare(self):
        self.calls.append("prepare")

    def counts(self, receipts):
        return {"plans": 0, "grants": 0, "runs": 0, "gate": "PAUSED", "management_receipts": receipts}

    def start(self):
        self.calls.append("start")
        return self.started

    def connect(self):
        return self.client, self.context, self.client.health()

    def records(self, started, identity):
        return {"process": identity, "owner_id": started["owner_id"]}

    def bind(self, identity):
        wire.need(identity == PROCESS)
        self.calls.append("bind")
        return self.ref

    def stop(self, started, key):
        wire.need(self.ref.handle == 900 and key == self.receipt["operation_key"])
        self.calls.append("stop")
        self.stopped = True
        return {"replayed": False, "receipt": self.receipt}

    def durable_stop(self):
        return {"receipt": copy.deepcopy(self.receipt), "start_id": STARTED["start_id"],
                "context_digest": CTX.context_digest}


class Checks(unittest.TestCase):
    def setUp(self):
        self.port, self.journal = FakePort(), MemoryJournal()

    def run_wire(self, confirm=lambda: True, **kwargs):
        return wire.run_once(self.port, self.journal, confirm, sleep=lambda _: None, **kwargs)

    def blocked(self, result, stage):
        self.assertEqual(result["status"], "E4G_UNKNOWN_OR_BLOCKED")
        self.assertEqual(result["failure_stage"], stage)
        self.assertFalse(result["retry"])

    def test_positive_job_true_same_handle_and_receipt(self):
        result = self.run_wire()
        self.assertEqual(result["status"], "E4G_SESSION_PASS")
        self.assertEqual(self.port.calls, ["prepare", "start", "bind", "stop"])
        self.port.ref.api.CloseHandle.assert_called_once_with(900)
        self.assertEqual(dict(self.journal.rows)["BOUND"]["job"]["in_any_job"], True)
        self.assertEqual(result["managed_scope"], "NOT_TESTED")

    def test_job_false_also_allowed_query_failure_blocks(self):
        self.port.in_job = False
        self.assertEqual(self.run_wire()["status"], "E4G_SESSION_PASS")
        self.setUp()
        self.port.ref.api.IsProcessInJob.side_effect = None
        self.port.ref.api.IsProcessInJob.return_value = 0
        self.blocked(self.run_wire(), "BIND")
        self.assertNotIn("stop", self.port.calls)

    def test_start_unknown_or_existing_no_retry(self):
        for status in ({"state": "STARTING", "created": True}, {**STARTED, "created": False}):
            with self.subTest(status=status["state"]):
                self.setUp()
                self.port.started = status
                self.blocked(self.run_wire(), "START")
                self.assertEqual(self.port.calls, ["prepare", "start"])

    def test_start_response_loss_no_stop(self):
        self.port.start = Mock(side_effect=OSError("PRIVATE_CANARY"))
        self.blocked(self.run_wire(), "START")
        self.port.start.assert_called_once()
        self.assertNotIn("stop", self.port.calls)

    def test_endpoint_or_health_identity_change(self):
        for key in ENDPOINT:
            with self.subTest(key=key):
                self.setUp()
                self.port.client.endpoint[key] = "wrong"
                self.blocked(self.run_wire(), "AUTHENTICATE")
                self.assertNotIn("bind", self.port.calls)

    def test_health_scope_and_later_identity_changes(self):
        for key, value in (("execution_scope", "REAL_FIXED_STANDARD"), ("simulation", False),
                           ("backend", "standard"), ("process_fixture_enabled", True),
                           ("lifecycle_start_id", "wrong"), ("backends", [])):
            with self.subTest(key=key):
                self.setUp()
                self.port.client.health.return_value[key] = value
                self.blocked(self.run_wire(), "AUTHENTICATE")
        self.setUp()
        self.port.client.health.side_effect = [HEALTH, HEALTH, {**HEALTH, "process": {}}]
        self.blocked(self.run_wire(), "BEFORE_STOP")
        self.assertNotIn("stop", self.port.calls)

    def test_ipc_failure_after_binding_no_compensation(self):
        self.port.client.health.side_effect = [HEALTH, OSError("PRIVATE_CANARY")]
        self.blocked(self.run_wire(), "BIND")
        self.assertNotIn("stop", self.port.calls)
        self.port.ref.api.CloseHandle.assert_called_once_with(900)

    def test_already_exited_or_pid_binding_failure(self):
        self.port.ref.exit_evidence.side_effect = None
        self.port.ref.exit_evidence.return_value = {"exit_code": 0}
        self.blocked(self.run_wire(), "BIND")
        self.setUp()
        self.port.bind = Mock(side_effect=RuntimeError("PROCESS_IDENTITY_MISMATCH"))
        self.blocked(self.run_wire(), "BIND")

    def test_stop_response_mismatch_and_unknown_no_retry(self):
        for key in self.port.receipt:
            with self.subTest(key=key):
                self.setUp()
                original_stop = self.port.stop
                def stop(started, operation_key):
                    value = original_stop(started, operation_key)
                    value["receipt"][key] = "wrong"
                    return value
                self.port.stop = stop
                self.blocked(self.run_wire(), "STOP")
                self.assertEqual(self.port.calls.count("stop"), 1)
        self.setUp()
        self.port.stop = Mock(side_effect=OSError("RESPONSE_LOST"))
        self.blocked(self.run_wire(), "STOP")
        self.port.stop.assert_called_once()

    def test_stop_replay_is_not_a_new_pass(self):
        self.port.stop = Mock(return_value={"replayed": True, "receipt": self.port.receipt})
        self.blocked(self.run_wire(), "STOP")

    def test_exit_timeout_nonzero_and_identity(self):
        self.port.ref.exit_evidence.side_effect = lambda: None
        self.blocked(self.run_wire(monotonic=Mock(side_effect=[0, 11])), "EXIT")
        for change in ({"exit_code": 2}, {"pid": 99}, {"creation_time_100ns": 999},
                       {"image_path": "wrong"}, {"exit_source": "pid_absent"}):
            with self.subTest(change=next(iter(change))):
                self.setUp()
                original_exit = self.port.exit_evidence
                self.port.ref.exit_evidence.side_effect = lambda: (
                    {**original_exit(), **change} if self.port.stopped else None)
                self.blocked(self.run_wire(), "EXIT")

    def test_durable_receipt_mismatch_missing_or_ipc_ambiguity(self):
        for evidence in (None, {"receipt": {}, "start_id": "wrong", "context_digest": "wrong"}):
            self.setUp()
            self.port.durable_stop = Mock(return_value=evidence)
            self.blocked(self.run_wire(), "PERSISTENT_RECEIPT")

    def test_duplicate_journal_operation_is_denied(self):
        self.assertEqual(self.run_wire()["status"], "E4G_SESSION_PASS")
        calls = list(self.port.calls)
        self.blocked(self.run_wire(), "PREPARE")
        self.assertEqual(self.port.calls, calls)

    def test_persistence_faults_before_external_calls(self):
        for stage, expected, forbidden in (("PREPARE_INTENT", "PREPARE", "prepare"),
                                           ("START_INTENT", "START", "start"),
                                           ("BOUND", "BIND", "stop"),
                                           ("STOP_INTENT", "BEFORE_STOP", "stop")):
            with self.subTest(stage=stage):
                self.setUp()
                self.journal.fail_stage = stage
                self.blocked(self.run_wire(), expected)
                self.assertNotIn(forbidden, self.port.calls)

    def test_result_write_and_handle_close_failure(self):
        self.journal.fail_stage = "RESULT"
        self.blocked(self.run_wire(), "RESULT_WRITE")
        self.setUp()
        self.port.ref.api.CloseHandle.return_value = 0
        result = self.run_wire()
        self.assertEqual(result["status"], "E4G_UNKNOWN_OR_BLOCKED")
        self.assertEqual(result["cleanup_failure_stage"], "HANDLE_CLOSE")

    def test_denial_and_json_privacy(self):
        result = self.run_wire(confirm=lambda: False)
        self.assertFalse(result["start_called"])
        self.assertNotIn("start", self.port.calls)
        text = json.dumps(result)
        self.assertNotIn("synthetic-owner", text)
        self.assertNotIn("synthetic-instance", text)
        self.assertNotIn("PRIVATE", text)

    def test_original_e1_alias_denial_and_sqlite_denial(self):
        for function in FUNCTIONS:
            with self.assertRaisesRegex(AssertionError, "E1_PRODUCTION_AUTHORITY_DENIED"):
                function()
        import sqlite3
        with self.assertRaises(Exception):
            sqlite3.connect(":memory:")

    def test_af_port_start_stop_forward_only_original_api(self):
        port = wire.AFPort()
        port.manager = Mock()
        port.start()
        port.manager.start.assert_called_once_with(wait_seconds=8)
        port.stop(STARTED, "exact-key")
        port.manager.stop.assert_called_once_with(owner_id=STARTED["owner_id"], operation_key="exact-key")

    def test_real_journal_exclusive_claim_and_partial_reservation(self):
        # New test-only files are retained; no AF Project/database is prepared here.
        root = Path(tempfile.mkdtemp(prefix="GDCAE-E4G-OFFLINE-", dir=ENV.parent.parent))
        journal = wire.Journal(root / "journal")
        journal.claim()
        with self.assertRaises(FileExistsError):
            journal.claim()
        with self.assertRaises(FileExistsError):
            wire.Journal(root / "journal")
        with patch.object(wire.Journal, "write", side_effect=OSError("FAULT")):
            with self.assertRaises(OSError):
                wire.Journal(root / "partial")
        with self.assertRaises(FileExistsError):
            wire.Journal(root / "partial")

    def test_af_port_bind_uses_installed_process_reference_without_terminate(self):
        kernel = SimpleNamespace()
        kernel.OpenProcess = Mock(return_value=900)
        def times(handle, created, *rest):
            created._obj.value = PROCESS["creation_time_100ns"]
            return 1
        def image(handle, flags, buffer, size):
            buffer.value = PROCESS["image_path"]
            return 1
        kernel.GetProcessTimes = Mock(side_effect=times)
        kernel.QueryFullProcessImageNameW = Mock(side_effect=image)
        kernel.WaitForSingleObject = Mock(return_value=258)
        kernel.GetExitCodeProcess = Mock()
        kernel.CloseHandle = Mock(return_value=1)
        with patch.object(ctypes, "WinDLL", return_value=kernel):
            ref = wire.AFPort().bind(PROCESS)
            self.assertIsNone(ref.exit_evidence())
            kernel.OpenProcess.assert_called_once_with(0x101000, False, 42)
            ref.close()
            with self.assertRaises(Exception):
                wire.AFPort().bind({**PROCESS, "creation_time_100ns": 999})

    def test_af_port_durable_stop_reuses_original_validation(self):
        port = wire.AFPort()
        port.manager = Mock()
        current = {"start_id": "synthetic-start"}
        port.manager._current.return_value = current
        port.manager._stopped.return_value = {"receipt": self.port.receipt}
        self.assertEqual(port.durable_stop(), {"receipt": self.port.receipt})
        port.manager._stopped.assert_called_once_with(current)
        port.manager._stopped.return_value = None
        with self.assertRaises(RuntimeError):
            port.durable_stop()


if __name__ == "__main__":
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    print(json.dumps({"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                      "failed_tests": [test.id().split(".")[-1] for test, _ in result.failures + result.errors],
                      "owner_starts": 0, "grant_increment": 0, "run_increment": 0,
                      "database_connections_created": 0, "native": "MOCKED",
                      "e1_guard_reused": True, "retry": False}, sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
