"""One E4-G acceptance, not a launcher. Only original AF Lifecycle may start/stop.

Import has no runtime action. --execute-approved-single-attempt is for a separate
human authorization; this development task must NEVER run that option.
GUI is a read-only observer, not a second lifecycle writer. No retry/recovery.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import time

E2 = Path(r"C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-R2F-E2-20261101-A01")
ENV = E2 / "env02"
AF = Path(r"D:\Projects\abqjobpilot_dev")
TASK = E2.parent / "GDCAE-D7-E4G-20261102-A01"
PROJECT = TASK / "af-test-only"
POLICY = "e4g-supervised-session-test-only-v1"
MANIFEST_SHA = "036afc76901f24267f8ee59f379994ada54dc4b6aa01c72eb5865a355fcb0b4c"
GUI_SHA = "667406eebceadab2441b3fad7f66fd23b7eb3524433504bccea412ae501793c8"
PYTHON_SHA = "0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14"
BASE_PYTHON = Path(r"D:\Program Files\Python312\python.exe")
BASE_SHA = "4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a"
ZERO_TABLES = ("jobs", "plans", "grants", "management_grants", "runs", "receipts", "consumption")


def need(value):
    if not value:
        raise RuntimeError("E4G_CHECK_FAILED")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def no_links(path):
    need(path.is_absolute())
    need(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)))


def verify_runtime():
    """Files/imports only. No Tk, host probe, Project, Owner or dependency install."""
    need(Path(sys.executable).resolve() == (ENV / "Scripts/python.exe").resolve())
    need(sys.version_info[:3] == (3, 12, 10) and struct.calcsize("P") == 8)
    for path in (ENV, AF, TASK.parent):
        no_links(path)
    need(sha(ENV / "Scripts/python.exe") == PYTHON_SHA and sha(BASE_PYTHON) == BASE_SHA)
    manifest_path = E2 / "candidate02/D7-R2F-E2_CANDIDATE_MANIFEST.json"
    raw = manifest_path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA)
    files = json.loads(raw)["selections"]["af_develop"]["files"]
    need(len(files) == 123)
    for relative, expected in files.items():
        for root in (AF, ENV / "Lib/site-packages"):
            path = root / relative
            no_links(path)
            need(path.resolve().is_relative_to(root.resolve()) and sha(path) == expected)
    need(sha(AF / "launch_gui.py") == GUI_SHA)
    from abqjobpilot import service_lifecycle as lifecycle
    from abqjobpilot import application_runtime
    need(Path(lifecycle.__file__).resolve() == (ENV / "Lib/site-packages/abqjobpilot/service_lifecycle.py").resolve())
    need(application_runtime.console_interpreter() == ENV / "Scripts/python.exe")
    need(lifecycle.owner_interpreter({"process_config": None}) == ENV / "Scripts/python.exe")


class Journal:
    """Exclusive task-local evidence files; existing/partial attempt is never reused."""
    def __init__(self, root):
        no_links(root)
        root.mkdir()  # parents=False, exist_ok=False: one durable reservation.
        self.root = root
        self.sequence = 0
        self.write("RESERVED", {"policy": POLICY})

    def claim(self):
        with (self.root / "single-operation.json").open("x", encoding="utf-8") as stream:
            stream.write('{"single_attempt":true}')
            stream.flush()
            os.fsync(stream.fileno())

    def write(self, stage, evidence=None):
        path = self.root / f"{self.sequence:02d}-{stage}.json"
        with path.open("x", encoding="utf-8") as stream:
            json.dump({"stage": stage, "evidence": evidence}, stream, sort_keys=True, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        self.sequence += 1


def check_health(client, context, health, started):
    endpoint = client.endpoint
    need(all(endpoint[k] == getattr(context, k) for k in
             ("project_id", "project_instance_id", "context_digest", "execution_store")))
    need(endpoint["owner_id"] == started["owner_id"])
    need(health["lifecycle_start_id"] == started["start_id"] and health["process"] == endpoint["process"])
    need(health["execution_scope"] == "TEST_ONLY" and health["simulation"] is True)
    need(health["backend"] == "fake-v1" and health["backends"] == [{"backend_id": "fake-v1", "version": 1}])
    need(health["process_fixture_enabled"] is False and "lifecycle_stop" in health["operations"])


def job_observation(ref):
    """New finite-session contract: require a successful query, record either value.

    Does not reuse or change the old E4-F2 no-Job contract or its BLOCKED record.
    """
    api = ref.api
    api.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    api.IsProcessInJob.restype = ctypes.c_int
    value = ctypes.c_int()
    need(api.IsProcessInJob(ref.handle, None, ctypes.byref(value)))
    return {"in_any_job": bool(value.value), "outer_hierarchy": "UNKNOWN",
            "session_exit_survival": "NOT_PROMISED"}


class AFPort:
    """Narrow binding to existing installed AF, no direct process creation."""
    def prepare(self):
        from abqjobpilot.product_project import create_project
        from abqjobpilot.service_lifecycle import ServiceLifecycleManager
        need(not PROJECT.exists())
        create_project(PROJECT, "GDCAE E4-G TEST ONLY")
        self.manager = ServiceLifecycleManager(PROJECT)
        self.context = self.manager.context
        self.counts(0)
        need(self.manager._current() is None and self.manager.inspect()["state"] == "NOT_RUNNING")

    def counts(self, management_receipts):
        from abqjobpilot.execution.store import open_existing_read_only
        profile = self.manager._profile()
        need(profile["process_config"] is None and "standard_extension" not in profile)
        with open_existing_read_only(self.context).read() as conn:
            need(all(conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] == 0 for table in ZERO_TABLES))
            need(conn.execute("SELECT state FROM dispatch_gate WHERE id=1").fetchone()[0] == "PAUSED")
            need(conn.execute("SELECT run_id FROM slot WHERE id=1").fetchone()[0] is None)
            need(conn.execute("SELECT COUNT(*) FROM management_receipts").fetchone()[0] == management_receipts)
        return {"plans": 0, "grants": 0, "runs": 0, "gate": "PAUSED", "management_receipts": management_receipts}

    def start(self):
        return self.manager.start(wait_seconds=8)

    def connect(self):
        return self.manager.connect()  # Original discover authenticates endpoint + live identity.

    def records(self, started, identity):
        from abqjobpilot.service_discovery import read_document
        current = self.manager._current()
        need(current["start_id"] == started["start_id"] and current["context_digest"] == self.context.context_digest)
        ready = read_document(self.manager._path(started["start_id"] + "/ready.json"))
        host = read_document(self.manager._path(started["start_id"] + "/host.json"))
        need(ready["start_id"] == started["start_id"] and ready["owner_id"] == started["owner_id"])
        need(ready["process"] == host["process"] == identity)
        need(type(host["in_any_job"]) is bool and host["output_file_types"] == {"stdout": 1, "stderr": 1})
        need(Path(identity["executable"]).resolve() == (ENV / "Scripts/python.exe").resolve())
        need(Path(identity["image_path"]).resolve() == BASE_PYTHON.resolve())
        return {"start_id": started["start_id"], "owner_id": started["owner_id"],
                "process": identity, "owner_host": host}

    def bind(self, identity):
        from abqjobpilot.execution.process_handles import ProcessReference
        return ProcessReference(identity["pid"], identity, cleanup=False)

    def stop(self, started, key):
        return self.manager.stop(owner_id=started["owner_id"], operation_key=key)

    def durable_stop(self):
        # _stopped checks stopped.json against owner.json and the ORIGINAL SQLite receipt.
        value = self.manager._stopped(self.manager._current())
        need(value is not None)
        return value


def run_once(port, journal, confirm, *, monotonic=time.monotonic, sleep=time.sleep):
    """One start / one stop; UNKNOWN never invokes compensating stop or retry."""
    ref = None
    stage = "PREPARE"
    failure = cleanup = None
    start_called = False
    try:
        journal.claim()
        journal.write("PREPARE_INTENT")  # Same journal cannot be invoked twice.
        port.prepare()
        journal.write("PREPARED", port.counts(0))
        need(confirm() is True)  # Operator opens existing GUI before any Owner exists.
        stage = "START"
        journal.write("START_INTENT")
        start_called = True
        started = port.start()
        need(started.get("state") == "CONNECTED" and started.get("created") is True)
        journal.write("START_CONNECTED", started)
        stage = "AUTHENTICATE"
        client, context, health = port.connect()
        check_health(client, context, health, started)
        identity = dict(health["process"])
        records = port.records(started, identity)
        port.counts(0)
        stage = "BIND"
        ref = port.bind(identity)
        need(ref.exit_evidence() is None)
        job = job_observation(ref)
        check_health(client, context, client.health(), started)
        need(client.endpoint["process"] == identity and ref.exit_evidence() is None)
        journal.write("BOUND", {**records, "job": job})
        # Brief bounded period for the original GUI's read-only refresh; no UI PASS claimed.
        sleep(3)
        stage = "BEFORE_STOP"
        check_health(client, context, client.health(), started)
        need(client.endpoint["process"] == identity and ref.exit_evidence() is None)
        port.counts(0)
        key = "e4g_stop_" + started["start_id"]
        journal.write("STOP_INTENT", {"key": key, "owner_id": started["owner_id"]})
        stage = "STOP"
        result = port.stop(started, key)
        need(result.get("replayed") is False)
        receipt = result["receipt"]
        need(receipt["state"] == "STOP_COMMITTED" and receipt["action"] == "lifecycle_stop_idle_v1")
        need(receipt["owner_id"] == started["owner_id"] and receipt["start_id"] == started["start_id"]
             and receipt["operation_key"] == key and receipt["project_instance_id"] == context.project_instance_id)
        journal.write("STOP_COMMITTED", receipt)
        stage = "EXIT"
        deadline = monotonic() + 10
        while True:
            exited = ref.exit_evidence()
            if exited is not None:
                need(exited["exit_source"] == "retained_windows_handle" and exited["exit_code"] == 0)
                need(all(exited[k] == identity[k] for k in ("pid", "creation_time_100ns", "image_path")))
                break
            need(monotonic() < deadline)
            sleep(0.05)
        journal.write("EXIT_OBSERVED", exited)
        stage = "PERSISTENT_RECEIPT"
        durable = port.durable_stop()
        need(durable["receipt"] == receipt and durable["start_id"] == started["start_id"]
             and durable["context_digest"] == context.context_digest)
        journal.write("VERIFIED", port.counts(1))
    except BaseException:
        failure = stage
    finally:
        if ref is not None and ref.handle:
            try:
                need(ref.api.CloseHandle(ref.handle))
                ref.handle = None
            except BaseException:
                cleanup = "HANDLE_CLOSE"
    output = {"status": "E4G_SESSION_PASS" if failure is None and cleanup is None else "E4G_UNKNOWN_OR_BLOCKED",
              "failure_stage": failure, "cleanup_failure_stage": cleanup,
              "start_called": start_called, "retry": False, "policy": POLICY,
              "gui_display": "OPERATOR_OBSERVATION_NOT_ATTESTED",
              "managed_scope": "NOT_TESTED", "solver": "NOT_RUN"}
    try:
        journal.write("RESULT", output)
    except BaseException:
        output.update(status="E4G_UNKNOWN_OR_BLOCKED", failure_stage=failure or "RESULT_WRITE")
    return output


def main():
    if sys.argv[1:] != ["--execute-approved-single-attempt"]:
        print(json.dumps({"status": "E4G_PREPARATION_ONLY", "owner_started": False, "retry": False}))
        return 2
    try:
        verify_runtime()
        need(input("Separate approval required. Type E4G SINGLE TEST_ONLY: ") == "E4G SINGLE TEST_ONLY")
        journal = Journal(TASK)
        def confirm():
            print("PROJECT_PREPARED. Use the approved existing GUI in read-only mode; do not click Start/Stop.")
            return input("Keep GUI and Windows session open. Type GUI READY: ") == "GUI READY"
        result = run_once(AFPort(), journal, confirm)
    except BaseException:
        result = {"status": "E4G_UNKNOWN_OR_BLOCKED", "failure_stage": "PREFLIGHT_OR_RESERVATION",
                  "retry": False}
    print(json.dumps(result, sort_keys=True))  # Never print arbitrary exception or private evidence.
    return 0 if result["status"] == "E4G_SESSION_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
