"""E4-F test-only read-only observation. No start, stop, Project or issuer API.

CLI is exclusively a host probe, to be run manually from independent WinPS 5.1.
Owner helpers accept an already authenticated client; they cannot launch an Owner.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(r"C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-R2F-E2-20261101-A01")
ENV = ROOT / "env02"
PINS = {
    "Scripts/python.exe": "0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14",
    "Lib/site-packages/abqjobpilot/execution/process_handles.py": "1c3f7961c49c72d55c011d095404413668ea606488db49e05d5c182ad99e453d",
    "Lib/site-packages/abqjobpilot/service_lifecycle.py": "8834b2df2291c8d9861aa5ef23ce25cb376d40a993c1e051c81d7dbed1c57270",
    "Lib/site-packages/abqjobpilot/service_owner.py": "554a7b6efcb1a2882736f281b4b778f3a13336dd29a2ef3d351dabeb697953eb",
}
# Historical E4-F receipt and identity remain unchanged in the approval report.
# F2 only projects fixed diagnostic stages, never exception strings or OS identity.
STAGES = frozenset({
    "ARGUMENTS", "UNEXPECTED", "ENV_INTERPRETER", "ENV_VERSION",
    "CANDIDATE_FILE_READ", "CANDIDATE_DIGEST", "AF_MODULE_IMPORT",
    "CONSOLE_REFERENCE", "CONSOLE_IMAGE", "CONTROLLER_REFERENCE", "CONSOLE_FINAL_LIVE",
} | {f"{subject}_{step}" for subject in ("CONSOLE", "CONTROLLER")
     for step in ("LIVE", "JOB_QUERY", "JOB_MEMBERSHIP", "TOKEN_SETUP", "TOKEN_OPEN",
                  "TOKEN_READ", "TOKEN_ELEVATION", "TOKEN_CLOSE", "HANDLE_CLOSE")})


def mark(diagnostic, stage):
    if diagnostic is not None:
        diagnostic["stage"] = stage if stage in STAGES else "UNEXPECTED"


def primary_failure(diagnostic):
    if diagnostic["primary"] is None and diagnostic["cleanup"] is None:
        diagnostic["primary"] = diagnostic["stage"]


def cleanup_failure(diagnostic, stage):
    if diagnostic["cleanup"] is None:
        diagnostic["cleanup"] = stage if stage in STAGES else "UNEXPECTED"


def receipt(primary=None, cleanup=None):
    primary = primary if primary is None or primary in STAGES else "UNEXPECTED"
    cleanup = cleanup if cleanup is None or cleanup in STAGES else "UNEXPECTED"
    return {"status": "PASS" if primary is None and cleanup is None else "BLOCKED",
            "primary_failure_stage": primary, "cleanup_failure_stage": cleanup,
            "owner_started": False, "retry": False}


def require(value, code):
    if not value:
        raise RuntimeError(code)


def candidate_check(diagnostic=None):
    mark(diagnostic, "ENV_INTERPRETER")
    require(Path(sys.executable).resolve() == (ENV / "Scripts/python.exe").resolve(), "ENV02_MISMATCH")
    mark(diagnostic, "ENV_VERSION")
    require(sys.version_info[:3] == (3, 12, 10), "PYTHON_VERSION_MISMATCH")
    for relative, expected in PINS.items():
        mark(diagnostic, "CANDIDATE_FILE_READ")
        actual = hashlib.sha256((ENV / relative).read_bytes()).hexdigest()
        mark(diagnostic, "CANDIDATE_DIGEST")
        require(actual == expected, "CANDIDATE_DRIFT")


def no_job(api, handle, diagnostic=None, subject="CONSOLE"):
    mark(diagnostic, f"{subject}_JOB_QUERY")
    api.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    api.IsProcessInJob.restype = ctypes.c_int
    result = ctypes.c_int()
    require(api.IsProcessInJob(handle, None, ctypes.byref(result)), "JOB_QUERY_UNKNOWN")
    mark(diagnostic, f"{subject}_JOB_MEMBERSHIP")
    require(result.value == 0, "JOB_CONDITIONS_UNPROVEN")


def close_checked(ref):
    if ref.handle:
        require(ref.api.CloseHandle(ref.handle), "HANDLE_CLOSE_UNKNOWN")
        ref.handle = None


def health_matches(client, health, expected):
    # expected is frozen from connect's authenticated context/endpoint and start intent,
    # NEVER from an untrusted PID or a task name. Caller must also check DB/gate counts.
    for key in ("owner_id", "project_id", "project_instance_id", "context_digest", "execution_store", "process"):
        require(client.endpoint.get(key) == expected[key], "AUTHENTICATED_IDENTITY_MISMATCH")
    for key in ("lifecycle_start_id", "process"):
        require(health.get(key) == expected[key], "AUTHENTICATED_IDENTITY_MISMATCH")
    require(health.get("execution_scope") == "TEST_ONLY" and health.get("simulation") is True,
            "SCOPE_MISMATCH")
    require(health.get("backend") == "fake-v1"
            and health.get("backends") == [{"backend_id": "fake-v1", "version": 1}]
            and health.get("process_fixture_enabled") is False,
            "BACKEND_MISMATCH")


def bind_owner(client, expected):
    from abqjobpilot.execution.process_handles import ProcessReference
    health_matches(client, client.health(), expected)
    identity = expected["process"]
    ref = ProcessReference(identity["pid"], identity, cleanup=False)
    try:
        require(ref.exit_evidence() is None, "OWNER_ALREADY_EXITED")
        no_job(ref.api, ref.handle)
        health_matches(client, client.health(), expected)
        require(ref.exit_evidence() is None, "OWNER_EXITED_DURING_BIND")
        return ref  # Caller retains this exact object across original Lifecycle.stop.
    except BaseException:
        close_checked(ref)
        raise


def observe_exit(ref, seconds=10.0):
    require(0 < seconds <= 30, "INVALID_WAIT_BOUND")
    deadline = time.monotonic() + seconds
    while True:
        evidence = ref.exit_evidence()
        if evidence is not None:
            require(evidence["exit_code"] == 0, "OWNER_EXIT_NONZERO")
            return evidence
        require(time.monotonic() < deadline, "OWNER_EXIT_UNKNOWN")
        time.sleep(0.05)


def ordinary_token(kernel, process_handle, diagnostic, subject):
    mark(diagnostic, f"{subject}_TOKEN_SETUP")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.OpenProcessToken.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)]
    advapi.GetTokenInformation.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p,
                                         ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
    token = ctypes.c_void_p()
    mark(diagnostic, f"{subject}_TOKEN_OPEN")
    require(advapi.OpenProcessToken(process_handle, 0x8, ctypes.byref(token)), "TOKEN_QUERY_UNKNOWN")
    failed = False
    try:
        mark(diagnostic, f"{subject}_TOKEN_READ")
        elevation, length = ctypes.c_uint32(), ctypes.c_uint32()
        require(advapi.GetTokenInformation(token, 20, ctypes.byref(elevation), 4,
                                          ctypes.byref(length)), "TOKEN_QUERY_UNKNOWN")
        mark(diagnostic, f"{subject}_TOKEN_ELEVATION")
        require(elevation.value == 0, "ELEVATED_HOST_FORBIDDEN")
    except BaseException:
        failed = True
        primary_failure(diagnostic)
        raise
    finally:
        try:
            require(kernel.CloseHandle(token), "TOKEN_CLOSE_UNKNOWN")
        except BaseException:
            cleanup_failure(diagnostic, f"{subject}_TOKEN_CLOSE")
            if not failed:
                raise  # Abort forward checks, but do not replace an earlier failure.


def host_probe(console_pid):
    diagnostic = {"stage": "UNEXPECTED", "primary": None, "cleanup": None}
    console = controller = None
    try:
        candidate_check(diagnostic)
        mark(diagnostic, "AF_MODULE_IMPORT")
        from abqjobpilot.execution.process_handles import ProcessReference
        mark(diagnostic, "CONSOLE_REFERENCE")
        console = ProcessReference(console_pid, cleanup=False)
        mark(diagnostic, "CONSOLE_IMAGE")
        expected_image = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        require(Path(console.identity["image_path"]).resolve() == expected_image.resolve(), "CONSOLE_IMAGE_MISMATCH")
        mark(diagnostic, "CONTROLLER_REFERENCE")
        controller = ProcessReference(os.getpid(), cleanup=False)
        for subject, ref in (("CONSOLE", console), ("CONTROLLER", controller)):
            mark(diagnostic, f"{subject}_LIVE")
            require(ref.exit_evidence() is None, "HOST_NOT_LIVE")
            no_job(ref.api, ref.handle, diagnostic, subject)
            mark(diagnostic, f"{subject}_TOKEN_SETUP")
            ordinary_token(ref.api, ref.handle, diagnostic, subject)
        mark(diagnostic, "CONSOLE_FINAL_LIVE")
        require(console.exit_evidence() is None, "CONSOLE_EXITED_DURING_PROBE")
    except BaseException:
        primary_failure(diagnostic)
    finally:
        for subject, ref in (("CONTROLLER", controller), ("CONSOLE", console)):
            if ref is not None:
                try:
                    close_checked(ref)
                except BaseException:
                    cleanup_failure(diagnostic, f"{subject}_HANDLE_CLOSE")
    # First primary and first cleanup failure are retained independently.
    return receipt(diagnostic["primary"], diagnostic["cleanup"])


class ProbeArguments(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("ARGUMENTS")  # Never echo argv/private text to stderr.


def main(argv=None):
    try:
        parser = ProbeArguments(add_help=False)
        parser.add_argument("--console-pid", type=int, required=True)
        args = parser.parse_args(argv)
    except BaseException:
        output = receipt("ARGUMENTS")
    else:
        try:
            output = host_probe(args.console_pid)
        except BaseException:
            output = receipt("UNEXPECTED")
    print(json.dumps(output, sort_keys=True))
    return 0 if output["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
