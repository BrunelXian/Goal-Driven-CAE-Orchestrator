"""Explicitly opted-in M01-B TEST-only IPC qualification; never part of default startup.

Run alone with GDCAE_M01B_ROOT naming a new direct child of TEMP and
GDCAE_AF_SOURCE naming the audited Develop checkout. All privileged imports and
fixture writes stay in this test module, outside the production EvidenceBridge.
"""

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict, replace

import pytest

from aegiscae.adapters.abaqus.af_evidence import EvidenceBridge
from aegiscae.contracts.af_evidence import ProjectBinding

pytestmark = pytest.mark.skipif(
    os.environ.get("GDCAE_M01B_LIVE") != "APPROVED_TEST_ONLY",
    reason="Explicit M01-B approval, fresh TEMP root and isolated invocation required",
)

TABLES = ("plans", "grants", "runs", "receipts", "events", "validations", "observations",
          "consumption", "management_grants", "management_receipts", "control_events",
          "dispatch_gate", "slot", "meta", "configuration", "reconciliations")
READ_RPCS = {"health", "project_view", "run", "receipt", "events", "validations", "diagnose"}


def check(condition, label):
    # No raw objects/secrets in pytest's assertion introspection or exception text.
    if not condition:
        raise RuntimeError(label)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2), encoding="utf-8")


def wait_for(predicate, seconds=12):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.025)
    raise RuntimeError("BOUNDED_WAIT_EXPIRED")


def fresh_root():
    root = Path(os.environ["GDCAE_M01B_ROOT"])
    temp = Path(os.environ["TEMP"])
    check(root.is_absolute() and root.parent == temp and root.name.startswith("gdcae-m01b-"),
          "EXPLICIT_TEMP_CHILD_REQUIRED")
    check(not root.exists(), "EXISTING_ROOT_REJECTED")
    for parent in (temp, *temp.parents):
        info = parent.lstat()
        check(not stat.S_ISLNK(info.st_mode) and not (info.st_file_attributes & 0x400),
              "REPARSE_PARENT_REJECTED")
        for marker in (".git", "agent_project.json", "experiment.json", "project.json"):
            check(not (parent / marker).exists(), "PROJECT_OR_REPOSITORY_ANCESTOR_REJECTED")
    check(root.resolve().parent == temp.resolve(), "RESOLVED_ROOT_ESCAPE")
    root.mkdir(exist_ok=False)
    check(not any(root.iterdir()), "NEW_ROOT_NOT_EMPTY")
    return root


def snapshot(context):
    # Trusted TEST oracle only; production bridge never imports Store or SQLite.
    from abqjobpilot.execution.store import open_existing_read_only

    with open_existing_read_only(context).read() as connection:
        connection.execute("BEGIN")
        tables = {}
        for table in TABLES:
            rows = [tuple(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            encoded = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode()
            tables[table] = {"count": len(rows), "digest": hashlib.sha256(encoded).hexdigest()}
        revisions = [json.loads(row[0])["revision"] for row in
                     connection.execute("SELECT body FROM runs ORDER BY rowid")]
        sequence = connection.execute("SELECT COALESCE(MAX(sequence),0) FROM events").fetchone()[0]
        gate = tuple(connection.execute("SELECT state,version FROM dispatch_gate WHERE id=1")
                     .fetchone())
        slot = connection.execute("SELECT run_id FROM slot WHERE id=1").fetchone()[0]
    return {"tables": tables, "run_revisions": revisions, "highest_event_sequence": sequence,
            "gate": gate, "slot": slot}


def binding(context, owner_id):
    return ProjectBinding(context.root, context.project_id, context.project_instance_id,
                          context.context_digest, owner_id)


def fake_health(health):
    check(health["execution_scope"] == "TEST_ONLY" and health["simulation"] is True
          and health["backend"] == "fake-v1" and not health["process_fixture_enabled"]
          and health["backends"] == [{"backend_id": "fake-v1", "version": 1}],
          "NON_FAKE_OWNER_SECURITY_BLOCKER")


def safe_exit(value):
    return {key: value[key] for key in
            ("pid", "creation_time_100ns", "exit_code", "exit_source", "exit_observed_at")}


@contextmanager
def read_phase(context, forbidden_values, record):
    """Observe real transport; reject writes/startup without replacing its read responses."""
    from abqjobpilot.execution.client import FakeClient

    original = FakeClient.call
    before = snapshot(context)
    record["before"] = before
    operations = []

    def observed(client, operation, arguments):
        check(operation in READ_RPCS, "BRIDGE_WRITE_RPC_SECURITY_BLOCKER")
        operations.append(operation)
        return original(client, operation, arguments)

    def no_launch(*args, **kwargs):
        raise RuntimeError("BRIDGE_PROCESS_START_SECURITY_BLOCKER")

    def verify(result):
        encoded = json.dumps(asdict(result), ensure_ascii=True)
        for value in forbidden_values:
            if value:
                check(value not in encoded and json.dumps(value)[1:-1] not in encoded,
                      "BRIDGE_DISCLOSURE_SECURITY_BLOCKER")
        record.setdefault("reads", []).append({"operation": result.operation,
                                               "completeness": result.completeness,
                                               "error": asdict(result.error) if result.error else None})
        return result

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(FakeClient, "call", observed)
        patch.setattr("subprocess.Popen", no_launch)
        patch.setattr(os, "system", no_launch)
        try:
            yield verify
        finally:
            after = snapshot(context)
            record.update(before=before, after=after, business_state_unchanged=before == after,
                          rpc_operations=sorted(set(operations)), rpc_count=len(operations))
            check(before == after, "BRIDGE_BUSINESS_MUTATION_SECURITY_BLOCKER")


def success(result):
    check(result.error is None, "LIVE_READ_ERROR_" + result.operation + "_" +
          (result.error.code if result.error else "NONE"))
    check(result.completeness == "COMPLETE", "LIVE_INCOMPLETE_" + result.operation)
    check("not_atomic" in result.consistency, "ATOMICITY_MISREPRESENTED")
    return result


def rejection(result, codes):
    check(result.error is not None and result.error.code in codes and result.data is None,
          "EXPECTED_TYPED_REJECTION_MISSING")
    return result.error.code


def g1(root, evidence):
    from abqjobpilot.execution.process_handles import ProcessReference
    from abqjobpilot.product_project import create_project
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager

    directory = root / "g1-product"
    record = evidence["G1"] = {"status": "STARTED", "owner_start_calls": 0}
    create_project(directory, "GDCAE M01B SYNTHETIC EMPTY TEST")
    manager = ServiceLifecycleManager(directory)
    context = manager.context
    record["project_id"], record["project_instance_id"] = context.project_id, context.project_instance_id
    initial = snapshot(context)
    check(all(initial["tables"][key]["count"] == 0 for key in
              ("plans", "grants", "runs", "receipts", "validations"))
          and initial["gate"][0] == "PAUSED", "PRODUCT_NOT_EMPTY_PAUSED")
    check(not (Path(context.root) / "owner.json").exists(), "PREEXISTING_OWNER")
    profile = manager._profile()  # TEST preflight, never a production bridge import.
    check(profile["process_config"] is None and "standard_extension" not in profile,
          "UNEXPECTED_EXECUTION_EXTENSION")
    check(manager.inspect()["state"] == "NOT_RUNNING", "UNEXPECTED_INITIAL_OWNER")
    record["initial"] = initial
    refs, owner_id = [], None
    try:
        record["owner_start_calls"] += 1
        started = manager.start(wait_seconds=10)
        check(started["state"] == "CONNECTED" and started["created"] is True,
              "START_UNCONFIRMED_NO_RETRY")
        owner_id = started["owner_id"]
        client, context, health = manager.connect()
        identity = health["process"]
        refs.append(ProcessReference(identity["pid"], identity))
        created = json.loads(manager._path(started["start_id"] + "/created.json").read_text())
        transport_pid = created["transport_pid"]
        check(identity["pid"] == transport_pid or identity["parent_pid"] == transport_pid,
              "OWNER_CREATION_CHAIN_MISMATCH")
        if transport_pid != identity["pid"]:
            refs.append(ProcessReference(transport_pid))
        fake_health(health)
        record.update(owner_id=owner_id, owner_pid=identity["pid"], transport_pid=transport_pid,
                      owner_creation_time_100ns=identity["creation_time_100ns"],
                      health_scope=health["execution_scope"], backend=health["backend"])
        bound = binding(context, owner_id)
        facade = EvidenceBridge()
        missing = "r_" + "f" * 32
        with read_phase(context, [profile["credential"], str(directory)], record) as verify:
            caps = success(verify(facade.capabilities(bound)))
            check(caps.data["execution_authorized"] is False, "CAPABILITY_BECAME_PERMISSION")
            page = success(verify(facade.list_runs(bound)))
            check(page.data == () and page.next_cursor is None, "EMPTY_PAGE_MISMATCH")
            check(success(verify(facade.list_events(bound))).data == (), "EMPTY_EVENTS_MISMATCH")
            for result in (facade.get_run(bound, missing), facade.get_receipt(bound, "m01b-missing"),
                           facade.get_validations(bound, missing), facade.get_diagnostic(bound, missing)):
                rejection(verify(result), {"NOT_FOUND"})
            rejection(verify(facade.capabilities(replace(
                bound, project_instance_id="pi_" + "f" * 32))), {"PROJECT_IDENTITY_MISMATCH"})
            rejection(verify(facade.capabilities(replace(
                bound, owner_id="owner_" + "f" * 32))), {"ENDPOINT_IDENTITY_MISMATCH"})
        record["status"] = "READS_PASS"
    finally:
        if owner_id is not None:
            receipt = manager.stop(owner_id=owner_id, operation_key="m01b-g1-stop-once")["receipt"]
            record["stop_committed"] = receipt["state"] == "STOP_COMMITTED"
            record["exit_evidence"] = [safe_exit(wait_for(ref.exit_evidence, 15)) for ref in refs]
            check(all(item["exit_code"] == 0 for item in record["exit_evidence"]), "G1_OWNER_EXIT_FAILED")
            check(manager.inspect()["state"] == "NOT_RUNNING", "G1_STOP_NOT_CONFIRMED")
            record["cleanup_verified"] = True
        else:
            record["cleanup_verified"] = False
        for ref in refs:
            ref.close()
        save(root / "evidence.json", evidence)
    check(record["cleanup_verified"], "G1_CLEANUP_UNKNOWN_STOP_ALL_TESTING")
    record["offline_error"] = rejection(EvidenceBridge().capabilities(bound),
                                         {"OWNER_NOT_RUNNING", "PROCESS_IDENTITY_UNKNOWN"})
    record["status"] = "PASS"


def g2(root, evidence):
    from abqjobpilot.execution.process_handles import ProcessReference
    from supervisor_helpers import ProcessHarness, read_json

    directory = root / "g2-fixture"
    directory.mkdir(exist_ok=False)
    record = evidence["G2"] = {"status": "SETUP", "owner_start_calls": 0}
    # Existing AF trusted authority prepares only fake-v1 Plans/TEST_ONLY Grants.
    harness = ProcessHarness(directory, fake_jobs=70)
    check(harness.process_config is None, "PROCESS_FIXTURE_FORBIDDEN")
    record.update(project_id=harness.context.project_id,
                  project_instance_id=harness.context.project_instance_id)
    connection, ref = None, None
    started_at = time.monotonic()
    try:
        record["owner_start_calls"] += 1
        owner = harness.owner()
        ref = ProcessReference(owner.identity["pid"], owner.identity)
        client = harness.client()
        fake_health(client.health())
        check(len(harness.children) == 1, "EXTRA_FIXTURE_PROCESS")
        record.update(owner_pid=owner.identity["pid"], transport_pid=owner.process.pid,
                      owner_creation_time_100ns=owner.identity["creation_time_100ns"],
                      owner_id=client.endpoint["owner_id"])
        folder = directory / "private"
        folder.mkdir()
        connection = folder / "connection.json"
        save(connection, {"endpoint": read_json(harness.endpoint_file), "credential": harness.credential})
        # Setup writes end before read_phase; no validate_run or process fixture is needed.
        receipts = []
        for request in harness.requests:
            check(time.monotonic() - started_at < 120, "FIXTURE_SETUP_BUDGET_EXCEEDED")
            receipt = client.submit(request)["receipt"]
            harness.finished(receipt["run_id"])
            receipts.append(receipt)
        bound = binding(harness.context, client.endpoint["owner_id"])
        selected = receipts[0]["run_id"]
        original = client.receipt(harness.requests[0]["idempotency_key"])
        check(original["request_id"] == receipts[0]["request_id"]
              and original["idempotency_key"] == harness.requests[0]["idempotency_key"]
              and json.loads(original["namespace"]) == [harness.context.project_instance_id,
                                                         "stable-test-client", "submit"],
              "ORIGINAL_RECEIPT_SCOPE_MISMATCH")
        expected_run = client.run(selected)
        expected_validations = client.validations(selected)
        check(len(expected_validations) == 1 and expected_validations[0]["scope"] == "simulation",
              "FAKE_VALIDATION_SEED_MISSING")
        check(snapshot(harness.context)["slot"] is None, "FIXTURE_NOT_QUIESCENT")
        record["fixture_seed"] = {"fake_submissions": 70, "automatic_fake_validations": 70,
                                  "explicit_validate_run": 0, "management_issuance": 0}
        secrets = [harness.credential, str(directory), original["namespace"],
                   *[request["grant_id"] for request in harness.requests]]
        facade = EvidenceBridge()
        with read_phase(harness.context, secrets, record) as verify:
            caps = success(verify(facade.capabilities(bound)))
            check(len(caps.data["read_operations"]) == 7 and not caps.data["execution_authorized"],
                  "CAPABILITIES_MISMATCH")
            pages, ids, cursor = [], [], None
            for _ in range(4):
                page = success(verify(facade.list_runs(bound, cursor)))
                pages.append(len(page.data))
                ids.extend(row["run_id"] for row in page.data)
                cursor = page.next_cursor
                if cursor is None:
                    break
            check(pages == [32, 32, 6] and len(set(ids)) == 70, "LIVE_70_RUN_PAGING_MISMATCH")
            record["run_page_sizes"] = pages
            run = success(verify(facade.get_run(bound, selected)))
            for name in ("run_id", "execution", "revision", "backend_id", "simulation", "plan_digest"):
                check(run.data[name] == expected_run[name], "RUN_PROJECTION_MISMATCH_" + name)
            receipt = success(verify(facade.get_receipt(bound, "key-0")))
            check(receipt.data["request_id"] == original["request_id"], "RECEIPT_PROJECTION_MISMATCH")
            validations = success(verify(facade.get_validations(bound, selected)))
            check(validations.data[0]["validation_id"] == expected_validations[0]["validation_id"]
                  and validations.data[0]["recorded_verdict"] == expected_validations[0]["verdict"],
                  "VALIDATION_PROJECTION_MISMATCH")
            diagnostic = success(verify(facade.get_diagnostic(bound, selected)))
            check(diagnostic.data["run"]["run_id"] == selected
                  and diagnostic.data["digest_verified"] is False, "DIAGNOSTIC_SCOPE_MISMATCH")
            # First 64 source events belong to early runs; last Run filter yields empty visible page.
            last = receipts[-1]["run_id"]
            raw = client.events(limit=64)
            filtered = success(verify(facade.list_events(bound, limit=64, run_id=last)))
            check(filtered.data == () and filtered.more_possible is True
                  and filtered.next_cursor.position == raw[-1]["project_sequence"],
                  "FILTERED_EMPTY_CURSOR_MISMATCH")
            record["filtered_empty_cursor"] = filtered.next_cursor.position
            events, cursor = [], None
            for _ in range(10):
                page = success(verify(facade.list_events(bound, cursor)))
                events.extend(page.data)
                cursor = page.next_cursor
                if not page.more_possible:
                    break
            expected_sequence = record["before"]["highest_event_sequence"]
            check(len(events) == expected_sequence and len({e["project_sequence"] for e in events})
                  == len(events), "EVENT_HISTORY_MISMATCH")
            record["event_count"] = len(events)
            second = success(verify(EvidenceBridge().get_run(bound, selected)))
            check(second.data == run.data and second.source == run.source, "SECOND_CLIENT_MISMATCH")
            rejection(verify(facade.get_receipt(bound, "m01b-never-accepted")), {"NOT_FOUND"})
            rejection(verify(facade.list_runs(bound, limit=33)), {"INVALID_REQUEST"})
            rejection(verify(facade.list_events(bound, limit=65)), {"INVALID_REQUEST"})
            for field, value, code in (
                ("project_id", "p_" + "f" * 32, "PROJECT_IDENTITY_MISMATCH"),
                ("owner_id", "owner_" + "f" * 32, "ENDPOINT_IDENTITY_MISMATCH"),
            ):
                rejection(verify(facade.capabilities(replace(bound, **{field: value}))), {code})
        # Metadata failure experiments modify only this isolated connection, outside measurement.
        original_connection = connection.read_bytes()
        try:
            damaged = json.loads(original_connection)
            damaged["credential"] = "M01B_INVALID_PRIVATE_CANARY"
            save(connection, damaged)
            record["bad_credential_error"] = rejection(facade.capabilities(bound),
                                                       {"AUTHENTICATION_FAILED"})
        finally:
            connection.write_bytes(original_connection)
        record["status"] = "READS_PASS"
    finally:
        # Removal of our handoff precedes existing harness's secret-removal audit.
        if connection is not None and connection.exists():
            connection.unlink()
        harness.close()  # Exact original OS handles only, documented owned-handle fallback.
        if ref is not None:
            exit_value = ref.exit_evidence()
            check(exit_value is not None, "G2_EXIT_UNCONFIRMED")
            record["exit_evidence"] = safe_exit(exit_value)
            ref.close()
        lifecycle = read_json(directory / "lifecycle.json")
        record["cleanup_verified"] = len(lifecycle) == 1 and all(
            row["exited"] and row["actual_process_handle_signaled"] for row in lifecycle)
        record["owned_handle_termination_used"] = any(row["terminated_by_owned_handle"] for row in lifecycle)
        save(root / "evidence.json", evidence)
    check(record["cleanup_verified"], "G2_CLEANUP_UNKNOWN")
    # Recreate only our old handoff after proven exit to test offline discovery, then remove it.
    connection.write_bytes(original_connection)
    try:
        record["offline_error"] = rejection(EvidenceBridge().capabilities(bound),
                                             {"OWNER_NOT_RUNNING", "PROCESS_IDENTITY_UNKNOWN"})
    finally:
        connection.unlink()
    manifest = Path(harness.context.root) / "experiment.json"
    original_manifest = manifest.read_bytes()
    try:
        document = json.loads(original_manifest)
        document["schema_version"] = 999
        save(manifest, document)
        record["unsupported_format_error"] = rejection(EvidenceBridge().capabilities(bound),
                                                        {"UNSUPPORTED_FORMAT"})
    finally:
        manifest.write_bytes(original_manifest)
    legacy = root / "legacy-negative"
    legacy.mkdir()
    save(legacy / "project.json", {})
    record["legacy_error"] = rejection(EvidenceBridge().capabilities(replace(bound, root=str(legacy))),
                                       {"LEGACY_PROJECT"})
    record["status"] = "PASS"


def test_g1_g2_real_authenticated_fake_only():
    check(sys.platform == "win32" and sys.version_info[:2] == (3, 12), "HOST_UNSUPPORTED")
    source = Path(os.environ["GDCAE_AF_SOURCE"])
    check(source.is_absolute() and (source / "tests" / "supervisor_helpers.py").is_file(),
          "EXPLICIT_AUDITED_SOURCE_REQUIRED")
    sys.path[:0] = [str(source), str(source / "tests")]
    from abqjobpilot.application_runtime import validate_runtime
    from abqjobpilot.service_host import observe_host

    check(validate_runtime() == Path(sys.executable).resolve(), "INTERPRETER_MISMATCH")
    host = observe_host()  # Read-only G0 OS observation, no child launch.
    root = fresh_root()
    manifest = {"purpose": "M01-B Fake-only live read qualification", "test_root": str(root),
                "python": sys.executable, "owner_modes": ["product TEST_ONLY/Fake", "fixture fake-v1"],
                "test_identifiers": ["G1", "G2", "B-01..B-12"],
                "maximum_owner_starts": 2, "maximum_concurrent_owners": 1,
                "maximum_owner_os_processes_including_venv_redirectors": 4,
                "maximum_wall_seconds": 300, "maximum_fixture_setup_seconds": 120,
                "cleanup": "G1 official idle stop + retained handles; G2 original ProcessHarness.close",
                "failure_policy": "No restart; no PID/name kill; G1 unknown exit prevents G2",
                "host_in_any_job": host["in_any_job"], "host_outer_job_hierarchy": "UNKNOWN"}
    save(root / "prestart-manifest.json", manifest)
    evidence = {"status": "RUNNING", "root_name": root.name, "python_version": sys.version.split()[0]}
    started = time.monotonic()
    try:
        g1(root, evidence)
        check(time.monotonic() - started < 150, "G1_WALL_BUDGET_EXCEEDED")
        g2(root, evidence)
        check(time.monotonic() - started < 300, "TOTAL_WALL_BUDGET_EXCEEDED")
        evidence["status"] = "AF_READ_COMPATIBILITY_VERIFIED"
    except Exception as exc:
        evidence["status"] = "PARTIAL"
        # Known labels only; arbitrary exception messages and repr remain private.
        evidence["failure_type"] = type(exc).__name__
        if isinstance(exc, RuntimeError) and str(exc).replace("_", "").isalnum():
            evidence["failure_label"] = str(exc)
        raise RuntimeError("M01B_LIVE_FAILURE_SEE_SANITIZED_EVIDENCE") from None
    finally:
        evidence["elapsed_seconds"] = round(time.monotonic() - started, 3)
        save(root / "evidence.json", evidence)
        print(json.dumps({"status": evidence["status"], "root_name": root.name,
                          "elapsed_seconds": evidence["elapsed_seconds"],
                          "G1": evidence.get("G1", {}).get("status"),
                          "G2": evidence.get("G2", {}).get("status")}))
