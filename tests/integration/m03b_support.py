"""M03-B trusted TEST harness only. Never imported by product or MCP.

AF originals and TEST_ORACLE metrics live in separate records. SyntheticReceipt
is an admission projection, not an AF receipt. No cross-store atomicity claim.
"""

import copy
import json
import os
import secrets
import sys
import tempfile
import time
from dataclasses import asdict, replace
from pathlib import Path

from aegiscae.adapters.abaqus.af_evidence import EvidenceBridge
from aegiscae.contracts.af_evidence import ProjectBinding
from aegiscae.contracts.research_contracts import Quantity, digest_bytes
from aegiscae.research import mutation, project, workflow
from aegiscae.research.workflow_rules import (
    SyntheticEvidence, SyntheticMetric, SyntheticReceipt, WorkflowDefinition, plain, request_for,
)


def check(value, code):
    if not value:
        raise ValueError(code)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value):
    return digest_bytes(encoded(value))


def write_new(path, value):
    with path.open("xb") as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())


def read(path):
    project._path(path, directory=False, scope=False)
    check(path.stat().st_size <= 262144, "FIXTURE_FILE_LIMIT")
    return json.loads(path.read_bytes())


def deadline(root):
    check(time.time() < read(root / "manifest.json")["deadline_utc_epoch"], "TEST_DEADLINE_EXPIRED")


def fresh_root(path):
    path = Path(path)
    check(path.is_absolute() and path.parent == Path(tempfile.gettempdir()).resolve()
          and path.name.startswith("gdcae-m03b-") and not path.exists(), "FRESH_TEMP_REQUIRED")
    project._path(path, exists=False)
    path.mkdir()
    return path


def load_af():
    check(os.environ.get("GDCAE_M03B_LIVE") == "APPROVED_TEST_ONLY", "LIVE_OPT_IN_REQUIRED")
    source = Path(os.environ["GDCAE_AF_SOURCE"])
    check(source == Path("D:/Projects/abqjobpilot_dev"), "EXPLICIT_AUDITED_SOURCE_REQUIRED")
    for folder in (source, source / "tests"):
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))


def health_ok(health):
    check(health["backend"] == "fake-v1" and health["simulation"] is True
          and health["execution_scope"] == "TEST_ONLY"
          and health["backends"] == [{"backend_id": "fake-v1", "version": 1}]
          and health["process_fixture_enabled"] is False
          and health["dispatch_enabled"] is True, "FAKE_OPEN_OWNER_REQUIRED")


def prepare(root):
    """Before owner launch: two exact Plans/Grants, bounded inputs and oracle."""
    load_af()
    from abqjobpilot.execution import ConfigSnapshot, ExecutionService, ExperimentStore, create_experiment
    from abqjobpilot.execution.models import canonical_json
    from execution_helpers import Harness, inventory
    from supervisor_helpers import ProcessHarness
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
    from test_synthetic_workflow import workflow_case

    project._path(root)
    check(not any(root.iterdir()), "EMPTY_CASE_REQUIRED")
    write_new(root / "manifest.json", {"purpose": "M03-B TEST_ONLY Fake IPC",
        "interpreter": sys.executable, "backend": "fake-v1", "owner_limit": 1,
        "launcher_limit": 1, "coordinator_children_limit": 2,
        "children": [str(root / name) for name in ("af", "research", "synthetic")],
        "deadline_utc_epoch": int(time.time()) + 180,
        "cleanup": "graceful stop.json; retained original OS handles; no replacement owner"})
    case = workflow_case(root, start=False)
    af = root / "af"
    af.mkdir()
    # Closely scoped equivalent of existing ProcessHarness.__init__; reuse its
    # unchanged launch, identity handshake and retained-handle cleanup methods.
    harness = ProcessHarness.__new__(ProcessHarness)
    harness.root, harness.children, harness.process_config = af, [], None
    (af / "recent-fixture.json").write_text('{"untouched":true}', encoding="utf-8")
    harness.context = create_experiment(af, af / "project")
    store = ExperimentStore(harness.context)
    plans, rows = [], []
    try:
        service = ExecutionService(harness.context, store, client_namespace="stable-test-client")
        config = ConfigSnapshot.from_dict({"config_revision": 1, "values": {"label": "M03-B TEST_ONLY"}})
        harness.requests = []
        for step, template in zip(("A", "B"), case.definition.candidates):
            body = mutation.edit_scalar(case.source.read_bytes(), template)
            mutation.check_diff(case.source.read_bytes(), body, template, case.bundle)
            path = af / (step + ".txt")
            with path.open("xb") as stream:
                stream.write(body)
            helper = Harness(af, harness.context, store, service, path, config)
            plan = helper.plan(helper.spec(job_id="job_" + step))
            grant = helper.grant(plan)
            request = helper.request(plan, grant, "fake_" + case.definition.workflow_id[9:] + "_" + step)
            harness.requests.append(request)
            plans.append(plan.to_dict())
            rows.append({"step_id": step, "candidate_id": template.candidate_id,
                         "candidate_digest": digest_bytes(body), "input_path": str(path),
                         "request": request, "plan": plan.to_dict()})
        harness.credential = secrets.token_hex(32)
        harness.bootstrap, harness.endpoint_file = af / "private-bootstrap.json", af / "endpoint.json"
        harness.bootstrap.write_text(canonical_json({"context": harness.context.to_dict(),
            "authority_instance": store._session.authority_instance,
            "credential": harness.credential, "client_namespace": "stable-test-client",
            "endpoint_file": str(harness.endpoint_file)}), encoding="utf-8")
    finally:
        store.close()
    harness.recent = inventory(af)["recent-fixture.json"]
    oracle = {"schema": "m03b-test-oracle-v1", "metric_source": "TEST_ORACLE",
        "physical_evidence_eligible": False, "research_project_id": case.project.research_project_id,
        "frozen_refs": case.bundle.digests(), "workflow_id": case.definition.workflow_id,
        "rows": [{"step_id": r["step_id"], "candidate_id": r["candidate_id"],
                  "candidate_digest": r["candidate_digest"], "value": value,
                  "requirements": [asdict(e) for e in case.bundle.verification.required_evidence]}
                 for r, value in zip(rows, ("2", "0.5"))]}
    mapping = {"schema": "m03b-test-mapping-v1", "source": "AF_TEST_ONLY",
        "research_project_id": case.project.research_project_id, "workflow_id": case.definition.workflow_id,
        "frozen_refs": case.bundle.digests(), "context": harness.context.to_dict(),
        "context_digest": harness.context.context_digest, "client_namespace": "stable-test-client",
        "oracle_digest": digest(oracle), "rows": rows}
    write_new(root / "oracle.json", oracle)
    write_new(root / "provisioning.json", mapping)
    case.harness, case.fixture_root = harness, root
    case.coordinator_children = []
    return case


def start(case, **options):
    harness = case.harness
    deadline(case.fixture_root)
    owner = harness.owner(**options)  # Exactly once per fresh fixture; never restart.
    client = harness.client()
    health_ok(client.health())
    private = harness.root / "private"
    private.mkdir()
    write_new(private / "connection.json", {"endpoint": client.endpoint, "credential": harness.credential})
    mapping = read(case.fixture_root / "provisioning.json")
    mapping["owner_endpoint"] = client.endpoint
    case.definition = replace(case.definition, source_id="syntheticport_" + digest(mapping)[7:39])
    write_new(case.fixture_root / "mapping.json", mapping)
    write_new(case.fixture_root / "definition.json", plain(case.definition))
    write_new(case.fixture_root / "owner-binding.json", {"endpoint": client.endpoint,
        "mapping_digest": digest(mapping),
        "source_id": case.definition.source_id})
    workflow.create_workflow(case.writer, case.definition, 2)
    case.port = AFTestPort(case.fixture_root, case.writer, case.workspace)
    case.coordinator = workflow.WorkflowCoordinator(case.writer, case.workspace,
        case.definition.workflow_id, case.port, case.port)
    return owner


def close(case):
    harness = case.harness
    connection = harness.root / "private" / "connection.json"
    if connection.exists():
        project._path(connection, directory=False, scope=False)
        check(connection.resolve().is_relative_to(harness.root.resolve()), "CLEANUP_SCOPE")
        connection.unlink()  # Only this invocation's exact temporary handoff, no historic credentials.
    harness.close()
    rows = read(harness.root / "lifecycle.json")
    check(len(rows) == 1 and all(r["exited"] and r["actual_process_handle_signaled"]
          and not r["terminated_by_owned_handle"] and r["exit_code"] == 0 for r in rows),
          "CLEANUP_PARTIAL_STOP_ALL_TESTING")
    return rows


class CaptureReads:
    """Seven explicit read methods only; raw capture at the Bridge response boundary."""
    def __init__(self, client):
        self.client, self.endpoint, self.raw = client, client.endpoint, {}

    def _save(self, name, value):
        self.raw[name] = copy.deepcopy(value)
        return value

    def health(self):
        return self._save("health", self.client.health())

    def project_view(self, **kw):
        return self._save("project_view", self.client.project_view(**kw))

    def receipt(self, key):
        return self._save("receipt", self.client.receipt(key))

    def run(self, run_id):
        return self._save("run", self.client.run(run_id))

    def events(self, **kw):
        return self._save("events", self.client.events(**kw))

    def validations(self, run_id):
        return self._save("validations", self.client.validations(run_id))

    def diagnose(self, run_id):
        return self._save("diagnose", self.client.diagnose(run_id))


class AFTestPort:
    """Only the two frozen test requests can reach submit. No plan/grant API here."""
    def __init__(self, root, research, workspace):
        self.root, self.research, self.workspace = Path(root), research, workspace
        self.definition = WorkflowDefinition.from_dict(read(self.root / "definition.json"))
        self.source_id = self.definition.source_id
        self.fault = None
        self._documents()

    def _documents(self):
        mapping, oracle, owner = (read(self.root / name) for name in
                                 ("mapping.json", "oracle.json", "owner-binding.json"))
        check("syntheticport_" + digest(mapping)[7:39] == self.source_id
              and owner["mapping_digest"] == digest(mapping)
              and owner["source_id"] == self.source_id
              and owner["endpoint"] == mapping["owner_endpoint"], "MAPPING_CHANGED")
        check(digest(oracle) == mapping["oracle_digest"], "ORACLE_CHANGED")
        return mapping, oracle, owner

    def _bound(self, request):
        deadline(self.root)
        mapping, oracle, owner = self._documents()
        rows = [r for r in mapping["rows"] if r["step_id"] == request.step_id]
        check(len(rows) == 1, "EXACT_ROLE_REQUIRED")
        row = rows[0]
        record = {"request": {"candidate_id": row["candidate_id"]},
                  "manifest": {"output_digest": row["candidate_digest"]}}
        check(request == request_for(self.definition, request.step_id, record), "EXACT_REQUEST_REQUIRED")
        check(row["request"]["idempotency_key"] == request.business_key, "KEY_CHANGED")
        template = self.definition.candidates[0 if request.step_id == "A" else 1]
        output = self.workspace._root / "staging" / template.output_identity / "candidate.txt"
        plan_input = Path(row["input_path"])
        check(plan_input.parent == self.root / "af", "INPUT_SCOPE")
        for path in (output, plan_input):
            project._path(path, directory=False, scope=False)
            check(digest_bytes(path.read_bytes()) == request.candidate_digest, "INPUT_DIGEST_CHANGED")
        check(row["plan"]["input_manifest"] == [{"path": str(plan_input),
              "size": plan_input.stat().st_size, "digest": request.candidate_digest}], "INPUT_NOT_EQUIVALENT")
        return mapping, oracle, owner, row

    def _discover(self, explicit_root):
        deadline(self.root)
        from abqjobpilot.service_discovery import discover
        client, context, health = discover(explicit_root)
        _, _, owner = self._documents()
        check(client.endpoint == owner["endpoint"], "OWNER_CHANGED")
        health_ok(health)
        self.capture = CaptureReads(client)
        self.capture.raw["health"] = copy.deepcopy(health)
        return self.capture, context, health

    def _read(self, method, binding, *args, **kwargs):
        envelope = getattr(EvidenceBridge(self._discover), method)(binding, *args, **kwargs)
        check(envelope.error is None and envelope.completeness == "COMPLETE", "AF_READ_INCOMPLETE")
        check(asdict(envelope.source) == {k: getattr(binding, k) for k in
              ("project_id", "project_instance_id", "context_digest", "owner_id")}, "SOURCE_CHANGED")
        return envelope, copy.deepcopy(self.capture.raw)

    def binding(self):
        mapping, _, owner = self._documents()
        ctx = mapping["context"]
        return ProjectBinding(ctx["root"], ctx["project_id"], ctx["project_instance_id"],
                              mapping["context_digest"], owner["endpoint"]["owner_id"])

    def accept(self, request):
        mapping, _, _, row = self._bound(request)
        current = workflow.WorkflowCoordinator(self.research, self.workspace,
                                               self.definition.workflow_id).inspect()
        check(current["state"] == "CLAIMED" and current["request"] == plain(request)
              and current["reservation_state"] == "SUBMISSION_INTENT_RECORDED", "INTENT_NOT_DURABLE")
        if request.step_id == "B":
            check(len(current["decisions"]) == 1 and current["decisions"][0]["decision"]["reason"]
                  == "VALID_SYNTHETIC_TARGET_MISS", "A_DECISION_REQUIRED")
        # Exclusive durable ticket precedes IPC. Never infer absence from a crash.
        write_new(self.root / (request.step_id + "-submit-ticket.json"), {
            "request": plain(request), "af_request": row["request"], "mapping_digest": digest(mapping),
            "research_revision": current["project_revision"], "reservation_id": current["reservation_id"],
            "prior_decisions": len(current["decisions"]), "source": "TEST_HARNESS_SUBMIT_INTENT"})
        from abqjobpilot.service_discovery import discover
        client, _, health = discover(mapping["context"]["root"])
        health_ok(health)
        check(client.endpoint == self._documents()[2]["endpoint"], "OWNER_CHANGED")
        client.submit(copy.deepcopy(row["request"]))
        if self.fault == "reply_lost":
            raise TimeoutError("TEST_SIDE_REPLY_DISCARDED_AFTER_AF_COMMIT")
        if self.fault == "exit_after_accept":
            os._exit(74)
        return None  # Authoritative facts only through a subsequent Bridge read.

    def collect(self, request):
        mapping, oracle, owner, row = self._bound(request)
        binding = self.binding()
        receipt_env, captured = self._read("get_receipt", binding, request.business_key)
        receipt = captured["receipt"]
        raw = {"health": captured["health"], "receipt": receipt}
        rid = receipt_env.data["run_id"]
        for method, name in (("get_run", "run"), ("get_validations", "validations"),
                             ("get_diagnostic", "diagnose")):
            _, captured = self._read(method, binding, rid)
            raw[name] = captured[name]
        event_env, captured = self._read("list_events", binding)
        check(not event_env.more_possible, "EVENT_PAGE_PARTIAL")
        raw["events"] = captured["events"]
        raw["source"] = asdict(receipt_env.source)
        raw["events_complete"] = True
        validate_facts(raw, mapping, owner, row)
        self._bound(request)  # Bytes checked again after independent IPC reads.
        if self.fault == "missing_evidence":
            raise ValueError("TEST_MISSING_EVIDENCE")
        snapshot = {"schema": "m03b-af-facts-v1", "source": "AF_TEST_ONLY",
            "physical_evidence_eligible": False, "mapping_digest": digest(mapping),
            "synthetic_request": plain(request), "raw": raw,
            "input_equivalence": "PROVEN_BYTES_AT_CHECKS", "oracle_digest": digest(oracle)}
        path = self.root / (request.step_id + "-facts-" + digest(snapshot)[7:] + ".json")
        if not path.exists():
            write_new(path, snapshot)
        else:
            check(read(path) == snapshot, "FACTS_CONFLICT")
        return snapshot

    def query(self, request):
        if self.fault == "query_unknown":
            return None
        snapshot = self.collect(request)
        return SyntheticReceipt("synthetic-receipt-v1", request, request.digest(),
            "syntheticreceipt_" + digest(snapshot["raw"]["receipt"])[7:39], True)

    def read_evidence(self, request, receipt):
        expected = self.query(request)
        check(expected == receipt, "ADMISSION_PROJECTION_CHANGED")
        _, oracle, _, row = self._bound(request)
        selected = [r for r in oracle["rows"] if r["step_id"] == request.step_id]
        check(len(selected) == 1 and selected[0]["candidate_id"] == request.candidate_id
              and selected[0]["candidate_digest"] == row["candidate_digest"], "ORACLE_IDENTITY")
        bundle = self.research.read_frozen_bundle(request.refs.bundle)["bundle"]
        check(selected[0]["requirements"] == [asdict(e) for e in bundle.verification.required_evidence],
              "ORACLE_SELECTOR_CHANGED")
        return SyntheticEvidence("synthetic-evidence-v1", receipt,
            "syntheticevidence_" + digest({"oracle": oracle, "step": request.step_id})[7:39],
            tuple(SyntheticMetric(e, Quantity(selected[0]["value"], e.dimension, e.unit))
                  for e in bundle.verification.required_evidence), True)


def projection_matches(projection, original):
    """AF diagnostic projection uses explicit null for absent optional fields."""
    if isinstance(projection, dict):
        return isinstance(original, dict) and all(
            projection_matches(v, original.get(k)) for k, v in projection.items())
    if isinstance(projection, list):
        return isinstance(original, list) and len(projection) == len(original) and all(
            projection_matches(p, o) for p, o in zip(projection, original))
    return type(projection) is type(original) and projection == original


def validate_facts(raw, mapping, owner, row):
    """Independent semantic checks of actual Bridge-captured originals; no IO."""
    from abqjobpilot.execution.models import CANONICAL, digest as af_digest, fixed_fake_content
    health_ok(raw["health"])
    ctx, expected, plan = mapping["context"], row["request"], row["plan"]
    check(af_digest({k: v for k, v in plan.items() if k != "plan_digest"}) == plan["plan_digest"],
          "PROVISIONED_PLAN_DIGEST")
    check(raw["source"] == {"project_id": ctx["project_id"],
        "project_instance_id": ctx["project_instance_id"], "context_digest": mapping["context_digest"],
        "owner_id": owner["endpoint"]["owner_id"]}, "AF_SOURCE_MISMATCH")
    receipt, run = raw["receipt"], raw["run"]
    semantic = {k: v for k, v in expected.items() if k != "idempotency_key"}
    semantic.update(context_digest=mapping["context_digest"], canonicalization=CANONICAL)
    check(receipt["request_digest"] == af_digest(semantic)
          and receipt["idempotency_key"] == expected["idempotency_key"]
          and json.loads(receipt["namespace"]) == [ctx["project_instance_id"], mapping["client_namespace"], "submit"]
          and receipt["request_status"] == "ACCEPTED", "RECEIPT_BINDING")
    check(run["run_id"] == receipt["run_id"] and run["project_id"] == ctx["project_id"]
          and run["project_instance_id"] == ctx["project_instance_id"]
          and run["owner_id"] == owner["endpoint"]["owner_id"]
          and all(run[k] == expected[k] for k in ("plan_id", "plan_digest", "grant_id", "job_id", "job_revision")),
          "RUN_BINDING")
    check(all(run.get(k) == v for k, v in {"execution": "FINISHED", "backend_outcome": "COMPLETED",
        "artifact_validation": "VALID", "validation_scope": "simulation", "solver_conclusion": "NOT_RUN",
        "reconciliation": "NONE", "backend_id": "fake-v1", "simulation": True}.items()), "RUN_NOT_COMPLETE_FAKE")
    events = raw["events"]
    check(raw["events_complete"] is True and [e["project_sequence"] for e in events]
          == list(range(1, len(events) + 1)), "EVENT_GAP")
    own = [e for e in events if e["run_id"] == run["run_id"]]
    check([e["type"] for e in own] == ["REQUEST_ACCEPTED", "START_INTENT", "FAKE_COMPLETED", "VALIDATION_RECORDED"]
          and own[0]["project_sequence"] == receipt["accepted_sequence"], "EVENT_CHRONOLOGY")
    vals = raw["validations"]
    check(len(vals) == 1, "VALIDATION_MISSING_OR_EXTRA")
    val = vals[0]
    check(all(val.get(k) == v for k, v in {"run_id": run["run_id"], "phase_attempt_id": run["phase_attempt_id"],
        "scope": "simulation", "verdict": "PASS", "policy_id": "fake-result-v1", "policy_version": 1,
        "validator_id": "fake-json-validator", "validator_version": 1}.items()), "VALIDATION_BINDING")
    diag = raw["diagnose"]["body"]
    check(diag["view"]["all_run_records_within_limits"] is True, "DIAGNOSTIC_PARTIAL")
    facts = diag["facts"]
    check({"run_id", "plan_id", "plan_digest", "phase_attempt_id", "execution", "artifact_validation",
           "solver_conclusion", "simulation", "owner_id"} <= facts["run"].keys()
          and projection_matches(facts["run"], run), "DIAGNOSTIC_CONTRADICTION")
    check(facts["plan"] == {k: plan[k] for k in
          ("plan_id", "plan_digest", "backend_id", "backend_version")}, "PLAN_CHANGED")
    check(set(facts["receipt"]) == {"request_id", "request_status", "accepted_at", "run_id",
          "accepted_sequence", "initial_queue_state"}
          and projection_matches(facts["receipt"], receipt), "DIAGNOSTIC_RECEIPT")
    check(facts["dispatch_gate"]["state"] == "OPEN"
          and facts["dispatch_gate"]["owner_id"] == owner["endpoint"]["owner_id"], "DIAGNOSTIC_GATE")
    minimum = {"validations": {"validation_id", "run_id", "phase_attempt_id", "scope", "verdict",
        "policy_id", "policy_version", "validator_id", "validator_version", "evidence_refs"},
        "events": {"event_id", "run_id", "project_sequence", "run_sequence", "type", "payload"}}
    for name, originals in (("validations", vals), ("events", own)):
        check(len(facts[name]) == len(originals) and all(
            minimum[name] <= projection.keys() and projection_matches(projection, original)
            for projection, original in zip(facts[name], originals)), "DIAGNOSTIC_" + name.upper())
    observations = facts["observations"]
    check(len(observations) == 1, "OBSERVATION_MISSING")
    obs = observations[0]
    check(val["evidence_refs"] == [obs["observation_id"]]
          and obs["run_id"] == run["run_id"] and obs["phase_attempt_id"] == run["phase_attempt_id"]
          and obs["binding_status"] == "MATCHED" and obs["provenance"] == "fake-v1"
          and obs["digest"] == digest_bytes(fixed_fake_content(plan, run)), "ARTIFACT_BINDING")


def reopen(root):
    load_af()
    root = Path(root)
    definition = WorkflowDefinition.from_dict(read(root / "definition.json"))
    writer = project.open_existing_for_explicit_write(root / "research")
    workspace = mutation.SyntheticWorkspace(root / "synthetic", definition.candidates[0].workspace_id)
    port = AFTestPort(root, writer, workspace)
    return workflow.WorkflowCoordinator(writer, workspace, definition.workflow_id, port, port)


def advance_until(coordinator, predicate, timeout=45):
    deadline = time.monotonic() + timeout
    for _ in range(80):
        current = coordinator.inspect()
        if predicate(current):
            return current
        check(time.monotonic() < deadline and current["state"] not in
              {"BLOCKED", "SYNTHETIC_TARGET_MET", "SYNTHETIC_TARGET_UNMET"}, "BOUNDED_WAIT_FAILED")
        coordinator.advance(current["project_revision"])
        time.sleep(0.02)
    raise AssertionError("ADVANCE_LIMIT")
