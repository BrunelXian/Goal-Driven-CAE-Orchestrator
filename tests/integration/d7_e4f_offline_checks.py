"""Exact standalone E4-F unittest whitelist; no pytest collection or database.

Run only with candidate02 env02 -I -B. All Windows calls are mocked.
Import/SQL/native/network denial is installed before importing any AF module.
"""
import copy
import ctypes
import importlib.abc
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

# Retained historical identity/receipt; F2 does not reinterpret the failed run.
E4F_PROBE_SHA256 = "5d88b575db54990b804f728983c1574cfaccaa4fa67b1df062e3ea6c2506d3c8"
E4F_FAILURE_RECEIPT = {"detail": "CHECK_FAILED_OR_UNKNOWN", "owner_started": False,
                       "retry": False, "status": "BLOCKED_HOST_PROBE"}
ALLOWED_AF = {"abqjobpilot", "abqjobpilot.execution", "abqjobpilot.execution.models",
              "abqjobpilot.execution.process_handles"}
DENIED = []


class ImportBoundary(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("abqjobpilot.") and fullname not in ALLOWED_AF:
            raise RuntimeError("E4F_AF_BUSINESS_IMPORT_DENIED")


def audit(event, args):
    if event.startswith(("sqlite3.", "subprocess.", "socket.", "ctypes.dl")) or event in {
        "os.system", "os.exec", "os.spawn", "os.startfile", "os.startfile/2",
    }:
        DENIED.append(event)
        raise RuntimeError("E4F_SIDE_EFFECT_DENIED")


sys.meta_path.insert(0, ImportBoundary())
sys.addaudithook(audit)
spec = importlib.util.spec_from_file_location("e4_observation", Path(__file__).with_name("d7_e4f_observation.py"))
observation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observation)
observation.candidate_check()
from abqjobpilot.execution import process_handles  # noqa: E402

assert Path(process_handles.__file__).resolve() == (
    observation.ENV / "Lib/site-packages/abqjobpilot/execution/process_handles.py").resolve()


class Kernel:
    def __init__(self):
        self.OpenProcess = Mock(return_value=123)
        self.GetProcessTimes = Mock(side_effect=self.times)
        self.QueryFullProcessImageNameW = Mock(side_effect=self.image)
        self.WaitForSingleObject = Mock(return_value=258)
        self.GetExitCodeProcess = Mock(side_effect=self.code)
        self.CloseHandle = Mock(return_value=1)
        self.IsProcessInJob = Mock(side_effect=self.job)
        self.OpenProcessToken = Mock(side_effect=self.token)
        self.GetTokenInformation = Mock(side_effect=self.elevation)

    @staticmethod
    def times(handle, created, *unused):
        created._obj.value = 100
        return 1

    @staticmethod
    def image(handle, flags, buffer, size):
        buffer.value = r"C:\synthetic\python.exe"
        return 1

    @staticmethod
    def code(handle, code):
        code._obj.value = 0
        return 1

    @staticmethod
    def job(handle, job, result):
        result._obj.value = 0
        return 1

    @staticmethod
    def token(handle, access, token):
        token._obj.value = 900
        return 1

    @staticmethod
    def elevation(token, information, value, size, length):
        value._obj.value = 0
        length._obj.value = 4
        return 1


IDENTITY = {"pid": 42, "creation_time_100ns": 100, "image_path": r"C:\synthetic\python.exe",
            "parent_pid": 41, "executable": r"C:\synthetic\venv\python.exe"}
EXPECTED = {"owner_id": "synthetic-owner", "project_id": "synthetic-project",
            "project_instance_id": "synthetic-instance", "context_digest": "synthetic-digest",
            "execution_store": "synthetic-store", "lifecycle_start_id": "synthetic-start",
            "process": IDENTITY}
HEALTH = {"process": IDENTITY, "lifecycle_start_id": "synthetic-start",
          "execution_scope": "TEST_ONLY", "simulation": True, "backend": "fake-v1",
          "backends": [{"backend_id": "fake-v1", "version": 1}], "process_fixture_enabled": False}


class Checks(unittest.TestCase):
    def setUp(self):
        self.api = Kernel()
        self.dll = patch.object(ctypes, "WinDLL", return_value=self.api)
        self.dll.start()
        self.addCleanup(self.dll.stop)
        self.client = Mock(endpoint=copy.deepcopy(EXPECTED))
        self.client.health.return_value = copy.deepcopy(HEALTH)

    def reference(self):
        return process_handles.ProcessReference(42, IDENTITY, cleanup=False)

    def test_retained_handle_read_only_and_exit(self):
        ref = observation.bind_owner(self.client, EXPECTED)
        self.api.OpenProcess.assert_called_once_with(0x101000, False, 42)
        self.assertEqual(self.client.health.call_count, 2)
        # A stop acknowledgement cannot change the held object; only native signal can.
        self.assertIsNone(ref.exit_evidence())
        self.api.WaitForSingleObject.return_value = 0
        evidence = observation.observe_exit(ref)
        self.assertEqual(evidence["exit_source"], "retained_windows_handle")
        self.assertEqual(evidence["exit_code"], 0)
        self.assertTrue(all(c.args[0] == 123 for c in self.api.WaitForSingleObject.call_args_list))
        observation.close_checked(ref)
        self.api.CloseHandle.assert_called_once_with(123)

    def test_pid_reuse_and_image_mismatch(self):
        for field, value in (("pid", 43), ("creation_time_100ns", 101), ("image_path", r"C:\wrong.exe")):
            with self.subTest(field=field), self.assertRaises(Exception):
                process_handles.ProcessReference(42, {**IDENTITY, field: value}, cleanup=False)
        self.assertEqual(self.api.CloseHandle.call_count, 3)

    def test_open_denied(self):
        self.api.OpenProcess.return_value = 0
        with self.assertRaises(Exception):
            self.reference()
        self.api.WaitForSingleObject.assert_not_called()

    def test_native_identity_query_failures(self):
        for name in ("GetProcessTimes", "QueryFullProcessImageNameW"):
            with self.subTest(name=name), patch.object(self.api, name, Mock(return_value=0)):
                with self.assertRaises(Exception):
                    self.reference()

    def test_endpoint_identity_mismatch(self):
        for key in EXPECTED.keys() - {"lifecycle_start_id"}:
            with self.subTest(key=key):
                self.client.endpoint = {**EXPECTED, key: "wrong"}
                with self.assertRaisesRegex(RuntimeError, "AUTHENTICATED_IDENTITY_MISMATCH"):
                    observation.bind_owner(self.client, EXPECTED)
        self.api.OpenProcess.assert_not_called()

    def test_health_scope_and_start_mismatch(self):
        for key, value in (("lifecycle_start_id", "wrong"), ("process", {}),
                           ("execution_scope", "REAL_FIXED_STANDARD"), ("simulation", False),
                           ("process_fixture_enabled", True), ("backends", []), ("backend", "standard")):
            with self.subTest(key=key):
                self.client.health.return_value = {**HEALTH, key: value}
                with self.assertRaises(RuntimeError):
                    observation.bind_owner(self.client, EXPECTED)

    def test_second_health_changed(self):
        self.client.health.side_effect = [HEALTH, {**HEALTH, "lifecycle_start_id": "wrong"}]
        with self.assertRaises(RuntimeError):
            observation.bind_owner(self.client, EXPECTED)
        self.api.CloseHandle.assert_called_once_with(123)

    def test_exits_during_binding(self):
        for sequence in ([0], [258, 0]):
            with self.subTest(sequence=sequence):
                self.api.WaitForSingleObject.side_effect = sequence
                with self.assertRaises(RuntimeError):
                    observation.bind_owner(self.client, EXPECTED)

    def test_job_true_and_query_unknown(self):
        for mode in ("member", "unknown"):
            with self.subTest(mode=mode):
                def query(handle, job, result):
                    result._obj.value = 1
                    return mode != "unknown"
                self.api.IsProcessInJob.side_effect = query
                with self.assertRaises(RuntimeError):
                    observation.bind_owner(self.client, EXPECTED)

    def test_wait_and_code_unknown(self):
        ref = self.reference()
        self.api.WaitForSingleObject.return_value = -1
        with self.assertRaises(Exception):
            observation.observe_exit(ref)
        self.api.WaitForSingleObject.return_value = 0
        self.api.GetExitCodeProcess.side_effect = None
        self.api.GetExitCodeProcess.return_value = 0
        with self.assertRaises(Exception):
            observation.observe_exit(ref)

    def test_nonzero_and_timeout_no_retry(self):
        ref = self.reference()
        self.api.WaitForSingleObject.return_value = 0
        def nonzero(handle, code):
            code._obj.value = 1
            return 1
        self.api.GetExitCodeProcess.side_effect = nonzero
        with self.assertRaisesRegex(RuntimeError, "OWNER_EXIT_NONZERO"):
            observation.observe_exit(ref)
        self.api.WaitForSingleObject.return_value = 258
        with patch.object(observation.time, "monotonic", side_effect=[0, 11]):
            with self.assertRaisesRegex(RuntimeError, "OWNER_EXIT_UNKNOWN"):
                observation.observe_exit(ref)
        self.api.OpenProcess.assert_called_once()
        self.api.CloseHandle.assert_not_called()

    def test_ipc_unknown_no_reopen(self):
        self.client.health.side_effect = [HEALTH, RuntimeError("COMMUNICATION_UNKNOWN")]
        with self.assertRaisesRegex(RuntimeError, "COMMUNICATION_UNKNOWN"):
            observation.bind_owner(self.client, EXPECTED)
        self.api.OpenProcess.assert_called_once()
        self.assertEqual(self.client.health.call_count, 2)

    def test_close_failure_not_claimed(self):
        ref = self.reference()
        self.api.CloseHandle.return_value = 0
        with self.assertRaisesRegex(RuntimeError, "HANDLE_CLOSE_UNKNOWN"):
            observation.close_checked(ref)
        self.assertEqual(ref.handle, 123)

    def test_host_probe_both_handles_and_no_job(self):
        image = str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe")
        console = Mock(identity={"image_path": image}, handle=321, api=self.api)
        controller = Mock(identity=IDENTITY, handle=123, api=self.api)
        console.exit_evidence.return_value = controller.exit_evidence.return_value = None
        with patch.object(process_handles, "ProcessReference", side_effect=[console, controller]), \
                patch.object(observation, "ordinary_token") as token:
            result = observation.host_probe(42)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual([c.args[0] for c in self.api.IsProcessInJob.call_args_list], [321, 123])
        self.assertEqual(token.call_count, 2)
        self.assertFalse(result["owner_started"])
        self.assertEqual(self.api.CloseHandle.call_count, 2)

    def test_host_probe_job_or_elevation_blocks(self):
        image = str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe")
        for failure in ("console_job", "controller_job", "token_unknown"):
            with self.subTest(failure=failure):
                console = Mock(identity={"image_path": image}, handle=321, api=self.api)
                controller = Mock(identity=IDENTITY, handle=123, api=self.api)
                console.exit_evidence.return_value = controller.exit_evidence.return_value = None
                def jobs(handle, job, result):
                    result._obj.value = int((failure == "console_job" and handle == 321)
                                           or (failure == "controller_job" and handle == 123))
                    return 1
                self.api.IsProcessInJob.side_effect = jobs
                with patch.object(process_handles, "ProcessReference", side_effect=[console, controller]), \
                        patch.object(observation, "ordinary_token",
                                     side_effect=RuntimeError("TOKEN_QUERY_UNKNOWN")
                                     if failure == "token_unknown" else None):
                    result = observation.host_probe(42)
                self.assertEqual(result["status"], "BLOCKED")
                expected = {"console_job": "CONSOLE_JOB_MEMBERSHIP",
                            "controller_job": "CONTROLLER_JOB_MEMBERSHIP",
                            "token_unknown": "CONSOLE_TOKEN_SETUP"}[failure]
                self.assertEqual(result["primary_failure_stage"], expected)
                self.assertIsNone(result["cleanup_failure_stage"])

    def host_refs(self):
        image = str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe")
        console = Mock(identity={"image_path": image}, handle=321, api=self.api)
        controller = Mock(identity=IDENTITY, handle=123, api=self.api)
        console.exit_evidence.return_value = controller.exit_evidence.return_value = None
        return console, controller

    def mock_host(self, console=None, controller=None):
        if console is None:
            console, controller = self.host_refs()
        with patch.object(process_handles, "ProcessReference", side_effect=[console, controller]):
            return observation.host_probe(42)

    def assert_receipt(self, value, primary=None, cleanup=None):
        self.assertEqual(value, {"status": "BLOCKED" if primary or cleanup else "PASS",
                                 "primary_failure_stage": primary, "cleanup_failure_stage": cleanup,
                                 "owner_started": False, "retry": False})

    def test_f2_complete_pass_real_token_function_mocked_api(self):
        self.assert_receipt(self.mock_host())
        self.assertEqual(self.api.OpenProcessToken.call_count, 2)
        for call in self.api.OpenProcessToken.call_args_list:
            self.assertEqual(call.args[1], 0x8)
        for call in self.api.GetTokenInformation.call_args_list:
            self.assertEqual(call.args[1], 20)
            self.assertEqual(call.args[3], 4)
        self.assertEqual(self.api.CloseHandle.call_count, 4)

    def test_f2_environment_and_file_stages(self):
        with patch.object(observation.sys, "executable", "synthetic-invalid"):
            self.assert_receipt(observation.host_probe(42), "ENV_INTERPRETER")
        with patch.object(observation.sys, "version_info", (3, 11, 0)):
            self.assert_receipt(observation.host_probe(42), "ENV_VERSION")
        with patch.object(Path, "read_bytes", side_effect=OSError("PRIVATE_PATH_CANARY")):
            self.assert_receipt(observation.host_probe(42), "CANDIDATE_FILE_READ")
        with patch.object(Path, "read_bytes", return_value=b"synthetic-tamper"):
            self.assert_receipt(observation.host_probe(42), "CANDIDATE_DIGEST")
        self.api.OpenProcess.assert_not_called()

    def test_f2_module_import_failure(self):
        import builtins
        original = builtins.__import__
        def importing(name, *args, **kwargs):
            if name == "abqjobpilot.execution.process_handles":
                raise ImportError("PRIVATE_PATH_CANARY")
            return original(name, *args, **kwargs)
        with patch.object(builtins, "__import__", side_effect=importing):
            self.assert_receipt(observation.host_probe(42), "AF_MODULE_IMPORT")

    def test_f2_console_controller_reference_and_image(self):
        with patch.object(process_handles, "ProcessReference", side_effect=OSError("private")):
            self.assert_receipt(observation.host_probe(42), "CONSOLE_REFERENCE")
        console, _ = self.host_refs()
        with patch.object(process_handles, "ProcessReference", side_effect=[console, OSError("private")]):
            self.assert_receipt(observation.host_probe(42), "CONTROLLER_REFERENCE")
        console, controller = self.host_refs()
        console.identity["image_path"] = "synthetic-wrong-image"
        self.assert_receipt(self.mock_host(console, controller), "CONSOLE_IMAGE")

    def test_f2_live_and_final_live_stages(self):
        for target in ("CONSOLE_LIVE", "CONTROLLER_LIVE", "CONSOLE_FINAL_LIVE"):
            with self.subTest(target=target):
                console, controller = self.host_refs()
                if target == "CONSOLE_FINAL_LIVE":
                    console.exit_evidence.side_effect = [None, RuntimeError("private")]
                else:
                    ref = console if target == "CONSOLE_LIVE" else controller
                    ref.exit_evidence.return_value = {"exit_code": 0}
                self.assert_receipt(self.mock_host(console, controller), target)

    def test_f2_job_query_failures_both_subjects(self):
        for subject, target_handle in (("CONSOLE", 321), ("CONTROLLER", 123)):
            with self.subTest(subject=subject):
                def query(handle, job, result):
                    result._obj.value = 0
                    return handle != target_handle
                self.api.IsProcessInJob.side_effect = query
                self.assert_receipt(self.mock_host(), subject + "_JOB_QUERY")

    def test_f2_token_setup_open_read_elevation_failures(self):
        for subject, target_handle in (("CONSOLE", 321), ("CONTROLLER", 123)):
            for failure in ("TOKEN_SETUP", "TOKEN_OPEN", "TOKEN_READ", "TOKEN_ELEVATION"):
                with self.subTest(subject=subject, failure=failure):
                    state = {"selected": False}
                    def token(handle, access, value):
                        state["selected"] = handle == target_handle
                        if failure == "TOKEN_OPEN" and state["selected"]:
                            return 0
                        return Kernel.token(handle, access, value)
                    def elevation(token, info, value, size, length):
                        Kernel.elevation(token, info, value, size, length)
                        if state["selected"]:
                            if failure == "TOKEN_READ":
                                return 0
                            if failure == "TOKEN_ELEVATION":
                                value._obj.value = 1
                        return 1
                    self.api.OpenProcessToken.side_effect = token
                    self.api.GetTokenInformation.side_effect = elevation
                    console, controller = self.host_refs()
                    dll_values = [self.api, self.api]
                    if failure == "TOKEN_SETUP":
                        dll_values[0 if subject == "CONSOLE" else 1] = OSError("PRIVATE_PATH_CANARY")
                    with patch.object(ctypes, "WinDLL", side_effect=dll_values):
                        self.assert_receipt(self.mock_host(console, controller), subject + "_" + failure)

    def test_f2_token_primary_and_cleanup_preserved(self):
        self.api.GetTokenInformation.side_effect = OSError("TOKEN_SECRET_CANARY")
        self.api.CloseHandle.return_value = 0
        self.assert_receipt(self.mock_host(), "CONSOLE_TOKEN_READ", "CONSOLE_TOKEN_CLOSE")
        # Token close and both acquired process closes are attempted exactly once.
        self.assertEqual(self.api.CloseHandle.call_count, 3)

    def test_f2_cleanup_only_and_both_handle_failures(self):
        for failed_handles, expected in (({900}, "CONSOLE_TOKEN_CLOSE"),
                                         ({123}, "CONTROLLER_HANDLE_CLOSE"),
                                         ({321}, "CONSOLE_HANDLE_CLOSE"),
                                         ({123, 321}, "CONTROLLER_HANDLE_CLOSE")):
            with self.subTest(expected=expected, handles=failed_handles):
                self.api.CloseHandle.reset_mock()
                self.api.CloseHandle.side_effect = lambda handle: (
                    (handle.value if isinstance(handle, ctypes.c_void_p) else handle) not in failed_handles)
                self.assert_receipt(self.mock_host(), cleanup=expected)
                process_closes = [c.args[0] for c in self.api.CloseHandle.call_args_list
                                  if isinstance(c.args[0], int)]
                self.assertEqual(process_closes, [123, 321])

    def test_f2_first_primary_not_masked_by_process_cleanup(self):
        console, controller = self.host_refs()
        console.exit_evidence.side_effect = KeyboardInterrupt("PRIVATE_ID_CANARY")
        self.api.CloseHandle.side_effect = OSError("PRIVATE_PATH_CANARY")
        self.assert_receipt(self.mock_host(console, controller), "CONSOLE_LIVE", "CONTROLLER_HANDLE_CLOSE")
        self.api.IsProcessInJob.assert_not_called()
        self.api.OpenProcessToken.assert_not_called()
        self.assertEqual(self.api.CloseHandle.call_count, 2)

    def test_f2_cli_safe_json_and_bad_arguments(self):
        from contextlib import redirect_stdout, redirect_stderr
        cases = [([], "ARGUMENTS"), (["--help"], "ARGUMENTS"),
                 (["--console-pid", "PRIVATE_ID_CANARY"], "ARGUMENTS"),
                 (["--console-pid", "42"], "UNEXPECTED")]
        for argv, stage in cases:
            with self.subTest(stage=stage):
                out, err = io.StringIO(), io.StringIO()
                with patch.object(observation, "host_probe", side_effect=RuntimeError("TOKEN_SECRET_CANARY")), \
                        redirect_stdout(out), redirect_stderr(err):
                    code = observation.main(argv)
                self.assertEqual(code, 2)
                self.assertEqual(err.getvalue(), "")
                self.assert_receipt(json.loads(out.getvalue()), stage)

    def test_f2_cli_pass_and_primary_cleanup_json(self):
        from contextlib import redirect_stdout, redirect_stderr
        for expected in (observation.receipt(), observation.receipt("CONSOLE_LIVE", "CONSOLE_HANDLE_CLOSE")):
            out, err = io.StringIO(), io.StringIO()
            with patch.object(observation, "host_probe", return_value=expected), \
                    redirect_stdout(out), redirect_stderr(err):
                code = observation.main(["--console-pid", "42"])
            self.assertEqual(code, 0 if expected["status"] == "PASS" else 2)
            self.assertEqual(json.loads(out.getvalue()), expected)
            self.assertEqual(err.getvalue(), "")
        self.assert_receipt(observation.receipt("PRIVATE_ID_CANARY", "TOKEN_SECRET_CANARY"),
                            "UNEXPECTED", "UNEXPECTED")

    def test_business_import_and_sqlite_denied(self):
        for module in ("abqjobpilot.execution.standard_contract", "abqjobpilot.product_project",
                       "abqjobpilot.service_lifecycle", "abqjobpilot.execution.store"):
            with self.subTest(module=module), self.assertRaises(RuntimeError):
                __import__(module)
        import sqlite3
        with self.assertRaisesRegex(RuntimeError, "E4F_SIDE_EFFECT_DENIED"):
            sqlite3.connect(":memory:")


if __name__ == "__main__":
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    print(json.dumps({"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                      "failed_tests": [test.id().split(".")[-1] for test, _ in result.failures + result.errors],
                      "installed_candidate_import": True, "native_calls": "MOCKED",
                      "database_connections_created": 0, "owner_started": False,
                      "grant_increment": 0, "denied_events": DENIED}, sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
