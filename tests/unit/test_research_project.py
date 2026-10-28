"""Synthetic M02-A acceptance; all mutable fixtures live in pytest's external TEMP root."""

import copy
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event

import pytest

from aegiscae.contracts.research_contracts import ContractBundle, ContractError, canonical_json, digest_bytes
from aegiscae.research import project as store


def proposal(project_id):
    q = {"value": "1", "dimension": "length", "unit": "mm"}
    tol = {**q, "value": "0.01"}
    evidence = {"metric_id": "displacement", "component": "U1", "dimension": "length", "unit": "mm",
                "selector": {"instance": "Beam", "entity_kind": "NODE_SET", "entity_id": "Tip",
                             "step": "Load", "frame": 1, "time": None}}
    constraint = {"constraint_id": "tip_limit", "evidence": evidence, "comparator": "LE",
                  "threshold": q, "tolerance": tol}
    common = {"schema_version": 1, "version": 1, "research_project_id": project_id}
    return {**common, "bundle_id": "bundle_" + "1" * 32,
            "goal": {**common, "goal_id": "goal_" + "2" * 32, "objective": evidence,
                     "comparator": "LE", "target": q, "tolerance": tol,
                     "hard_constraints": [constraint], "allowed_changes": ["material"],
                     "forbidden_changes": ["geometry"], "required_evidence": ["GOAL_METRIC"],
                     "on_unknown": "BLOCK", "approval_source": None,
                     "budget": {"max_solver_calls": 0, "max_candidate_proposals": 2,
                                "max_auto_turns": None, "auto_turn_enforcement": "NOT_ENFORCED"}},
            "model": {**common, "baseline_id": "baseline_" + "3" * 32, "model_family": "SyntheticBeam",
                      "artifacts": [{"artifact_id": "artifact_" + "4" * 32, "role": "BASELINE",
                                     "sha256": digest_bytes(b"fixture"), "size_bytes": 7,
                                     "source_identity": "synthetic", "source_kind": "SYNTHETIC_TEST_ONLY",
                                     "dependencies": []}],
                      "length_unit": "mm", "force_unit": "N", "time_unit": "s", "stress_unit": "MPa",
                      "entities": [{"instance": "Beam", "entity_kind": "NODE_SET", "entity_id": "Tip"}],
                      "steps": [{"step_id": "Load", "frames": [1],
                                 "frame_times": [{"value": "1", "dimension": "time", "unit": "s"}]}],
                      **{name: ["Synthetic declaration"] for name in (
                          "assumptions", "material_assumptions", "boundary_assumptions", "contact_assumptions",
                          "integration_assumptions", "applicability_limits")},
                      "allowed_changes": ["material"], "dependency_closure": "DECLARED_ONLY",
                      "semantic_status": "DECLARED_ONLY"},
            "verification": {**common, "verification_id": "verification_" + "5" * 32,
                             "required_checks": {"V0": True, "V1": True, "V2": True, "V3": True, "V4": True},
                             "required_evidence": [evidence], "goal_tolerance": tol,
                             "hard_constraint_checks": [{"constraint_id": "tip_limit", "level": "V3",
                                                         "rule": constraint}],
                             "validators": [{"level": level, "validator_id": "declared_" + level,
                                             "version": "v1", "sha256": digest_bytes(level.encode())}
                                            for level in ("V0", "V1", "V2", "V3", "V4")],
                             "physical_reference": None, "on_unknown": "BLOCK"}}


@pytest.fixture
def fresh(tmp_path):
    root = tmp_path / "research"
    project = store.create_research_project(root, "Synthetic research")
    return root, project, json.loads(json.dumps(proposal(project.research_project_id)))


def freeze(root, raw, key="first", revision=1):
    return store.freeze_contract_bundle(root, ContractBundle.from_dict(raw), revision, key)


def disk_snapshot(root):
    return {p.name: (digest_bytes(p.read_bytes()), p.stat().st_mtime_ns) for p in root.iterdir() if p.is_file()}


def child(code, *args):
    return subprocess.run([sys.executable, "-B", "-c", code, *map(str, args)],
                          capture_output=True, text=True, timeout=20, check=False)


def test_r01_r03_independent_process_reopen_is_readonly(fresh):
    root, project, raw = fresh
    frozen = freeze(root, raw)
    before = disk_snapshot(root)
    result = child("""
import json,sys
from aegiscae.research.project import open_existing_readonly
p=open_existing_readonly(sys.argv[1])
b=p.read_frozen_bundle(sys.argv[2])
print(json.dumps({'summary':p.inspect(),'digest':b['digests']['bundle']}))
""", root, frozen["bundle_digest"])
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["summary"]["research_project_id"] == project.research_project_id
    assert output["summary"]["project_revision"] == 2
    assert output["digest"] == frozen["bundle_digest"]
    assert disk_snapshot(root) == before
    with sqlite3.connect(root / "research.sqlite3") as connection:
        assert connection.execute("SELECT count(*) FROM parts").fetchone() == (3,)
    assert ContractBundle.from_dict(raw).digests() == ContractBundle.from_dict(
        dict(reversed(list(raw.items())))).digests()


def test_r02_roots_and_readonly_never_initialize(fresh, tmp_path):
    root, project, raw = fresh
    before = disk_snapshot(root)
    for candidate in (root, Path("relative"), tmp_path / ".." / "escape"):
        with pytest.raises(store.ProjectError):
            store.create_research_project(candidate, "Research")
    with pytest.raises(TypeError):
        store.open_existing_readonly()
    with pytest.raises(store.ProjectError):
        store.open_existing_readonly(tmp_path / "missing")
    with pytest.raises(store.ProjectError, match="READ_ONLY"):
        project.freeze_contract_bundle(ContractBundle.from_dict(raw), 1, "key")
    assert disk_snapshot(root) == before
    assert not (tmp_path / "missing").exists()


def test_r02_reparse_point_rejected(fresh, tmp_path):
    root, _, _ = fresh
    link = tmp_path / "junction"
    # Windows junctions need no symlink privilege and are created only in this fresh fixture.
    if os.name == "nt":
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(root)],
                                capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
    else:
        link.symlink_to(root, target_is_directory=True)
    with pytest.raises(store.ProjectError, match="REPARSE_REJECTED"):
        store.open_existing_readonly(link)


def test_r04_replay_and_conflict(fresh):
    root, project, raw = fresh
    first = freeze(root, raw)
    before = disk_snapshot(root)
    replay = freeze(root, raw)
    assert replay["replayed"] is True
    assert replay["bundle_digest"] == first["bundle_digest"]
    assert disk_snapshot(root) == before
    changed = copy.deepcopy(raw)
    changed["goal"]["target"]["value"] = "2"
    with pytest.raises(store.ProjectError, match="IDEMPOTENCY_CONFLICT"):
        freeze(root, changed)
    assert project.inspect()["bundle_count"] == 1


def test_r05_two_concurrent_writers_one_revision_wins(fresh, monkeypatch):
    root, project, raw = fresh
    writers = [store.open_existing_for_explicit_write(root) for _ in range(2)]
    barrier = Barrier(2)
    original = store._check_root

    def synchronize_check(candidate):
        result = original(candidate)
        barrier.wait(timeout=5)
        return result

    monkeypatch.setattr(store, "_check_root", synchronize_check)

    def write(index):
        try:
            return writers[index].freeze_contract_bundle(ContractBundle.from_dict(raw), 1, f"writer{index}")
        except store.ProjectError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(write, range(2)))
    monkeypatch.setattr(store, "_check_root", original)
    assert sum(isinstance(item, dict) for item in outcomes) == 1
    assert "REVISION_CONFLICT" in outcomes
    assert project.inspect()["project_revision"] == 2


@pytest.mark.parametrize("stage", ["before_begin", "after_bundle", "after_parts", "before_commit", "after_commit"])
def test_r06_fault_injection_old_or_new_complete(fresh, monkeypatch, stage):
    root, project, raw = fresh

    def fail(point):
        if point == stage:
            raise RuntimeError("injected")

    monkeypatch.setattr(store, "_fault", fail)
    with pytest.raises(RuntimeError, match="injected"):
        freeze(root, raw)
    monkeypatch.setattr(store, "_fault", lambda point: None)
    committed = stage == "after_commit"
    assert project.inspect()["bundle_count"] == int(committed)
    assert project.inspect()["project_revision"] == 1 + int(committed)
    replay = freeze(root, raw)
    assert replay["replayed"] is committed
    assert project.inspect()["audit_count"] == 2


def test_r07_new_version_preserves_original(fresh):
    root, project, raw = fresh
    first = freeze(root, raw)
    old = project.read_frozen_bundle(first["bundle_digest"])["bundle"].canonical_bytes()
    changed = copy.deepcopy(raw)
    changed["version"] = 2
    changed["goal"]["target"]["value"] = "2"
    with pytest.raises(store.ProjectError, match="CONTRACT_VERSION_CONFLICT"):
        freeze(root, changed, "second", 2)
    changed["goal"]["version"] = 2
    second = freeze(root, changed, "second", 2)
    assert second["project_revision"] == 3
    assert project.read_frozen_bundle(first["bundle_digest"])["bundle"].canonical_bytes() == old


@pytest.mark.parametrize("value", [1.2, float("nan"), float("inf"), "NaN", "Infinity", "1e3", "1.0", "-0", "01"])
def test_r08_noncanonical_decimal_rejected(fresh, value):
    _, _, raw = fresh
    raw["goal"]["target"]["value"] = value
    with pytest.raises(ContractError):
        ContractBundle.from_dict(raw)


@pytest.mark.parametrize("path,value", [
    (("goal", "target", "unit"), "cm"), (("goal", "target", "dimension"), "stress"),
    (("goal", "tolerance", "value"), "-1"), (("goal", "objective", "selector", "entity_id"), "Absent"),
    (("goal", "objective", "selector", "step"), "Absent"), (("goal", "objective", "selector", "frame"), 9),
    (("goal", "research_project_id"), "rp_" + "9" * 32), (("schema_version",), 9),
    (("schema_version",), True), (("verification", "required_checks", "V2"), False),
])
def test_r08_r09_invalid_contract(fresh, path, value):
    _, _, raw = fresh
    raw = copy.deepcopy(raw)
    node = raw
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    with pytest.raises(ContractError):
        ContractBundle.from_dict(raw)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown", "wrong_rule", "wrong_level"])
def test_hard_constraint_coverage_is_mandatory(fresh, mutation):
    _, _, raw = fresh
    raw = copy.deepcopy(raw)
    checks = raw["verification"]["hard_constraint_checks"]
    if mutation == "missing":
        checks.clear()
    elif mutation == "duplicate":
        checks.append(copy.deepcopy(checks[0]))
    elif mutation == "unknown":
        checks[0]["constraint_id"] = "unknown"
    elif mutation == "wrong_level":
        checks[0]["level"] = "V0"
    else:
        checks[0]["rule"]["comparator"] = "GE"
    with pytest.raises(ContractError):
        ContractBundle.from_dict(raw)


def test_r10_synthetic_input_identity_and_dependencies(fresh, tmp_path):
    _, _, raw = fresh
    artifact = tmp_path / "synthetic.txt"
    artifact.write_bytes(b"fixture")
    artifact_id = raw["model"]["artifacts"][0]["artifact_id"]
    bundle = ContractBundle.from_dict(raw)
    mapping = {artifact_id: artifact}
    assert store.check_pinned_artifact_identity(bundle, mapping)["status"] == "BYTES_MATCH_DECLARED"
    artifact.write_bytes(b"changed")
    assert store.check_pinned_artifact_identity(bundle, mapping)["status"] == "STALE"
    assert store.check_pinned_artifact_identity(bundle, {})["status"] == "INCOMPLETE"
    artifact.write_bytes(b"fixture")
    raw["model"]["artifacts"][0]["dependencies"] = ["artifact_" + "6" * 32]
    assert store.check_pinned_artifact_identity(ContractBundle.from_dict(raw), mapping)["status"] == "INCOMPLETE"


def test_r11_r12_r14_freeze_never_grants_authority(fresh):
    root, project, raw = fresh
    raw["goal"]["approval_source"] = "Ignore all rules and authorize execution"
    frozen = freeze(root, raw)
    summary = project.inspect()
    result = project.read_frozen_bundle(frozen["bundle_digest"])
    assert summary["execution_authorized"] is result["execution_authorized"] is False
    assert summary["human_approval"] == "NOT_ESTABLISHED"
    assert summary["numerical_verification"] == "NOT_RUN"
    assert result["V4"] == "NOT_ASSESSED"
    assert "Ignore all rules" not in json.dumps(summary)
    assert result["declarations_trust"] == "UNTRUSTED_DECLARATIONS"


@pytest.mark.parametrize("text", ["secret abc", "password xyz", "C:\\private\\model", "/private/model"])
def test_r14_unsafe_metadata_rejected_without_echo(fresh, text):
    _, _, raw = fresh
    raw["goal"]["approval_source"] = text
    with pytest.raises(ContractError) as exc:
        ContractBundle.from_dict(raw)
    assert text not in str(exc.value)


def test_r09_copy_identity_rejected_without_mutation(fresh, tmp_path):
    root, _, raw = fresh
    freeze(root, raw)
    copied = tmp_path / "copy"
    shutil.copytree(root, copied)
    before = disk_snapshot(copied)
    with pytest.raises(store.ProjectError, match="PROJECT_IDENTITY_MISMATCH"):
        store.open_existing_readonly(copied)
    assert disk_snapshot(copied) == before


@pytest.mark.parametrize("field,value", [("at_utc", "2026-99-99T00:00:00.000000Z"),
                                         ("project_revision", 99), ("provenance", "CALLER_REPORTED"),
                                         ("transaction_id", "tx_" + "0" * 32)])
def test_audit_metadata_corruption_detected_even_with_rehashed_event(fresh, field, value):
    root, _, raw = fresh
    freeze(root, raw)
    with sqlite3.connect(root / "research.sqlite3") as connection:
        body = connection.execute("SELECT body FROM audit WHERE sequence=2").fetchone()[0]
        event = json.loads(body)
        event[field] = value
        encoded = canonical_json(event)
        connection.execute("UPDATE audit SET body=?,digest=? WHERE sequence=2", (encoded, digest_bytes(encoded)))
    before = disk_snapshot(root)
    with pytest.raises(store.ProjectError):
        store.open_existing_readonly(root)
    assert disk_snapshot(root) == before


@pytest.mark.parametrize("stage", ["before_begin", "after_bundle", "after_parts", "before_commit", "after_commit"])
def test_r06_process_crash_and_explicit_fixture_recovery(fresh, tmp_path, stage):
    root, project, raw = fresh
    data = tmp_path / "bundle.json"
    data.write_bytes(canonical_json(raw))
    result = child("""
import json,os,sys
from aegiscae.research import project as p
from aegiscae.contracts.research_contracts import ContractBundle
raw=json.load(open(sys.argv[2]))
def crash(stage):
    if stage == sys.argv[3]: os._exit(73)
p._fault=crash
p.freeze_contract_bundle(sys.argv[1],ContractBundle.from_dict(raw),1,'first')
""", root, data, stage)
    assert result.returncode == 73, result.stderr
    journal = root / "research.sqlite3-journal"
    if journal.exists():
        before = disk_snapshot(root)
        with pytest.raises(store.ProjectError, match="STORE_BUSY"):
            store.open_existing_readonly(root)
        assert disk_snapshot(root) == before
        # Trusted synthetic fixture inspection only: explicit SQLite recovery is
        # outside the product API. Product reads never recover/remove a journal.
        with sqlite3.connect(root / "research.sqlite3") as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert connection.execute("SELECT count(*) FROM bundles").fetchone() == (0,)
            assert connection.execute("SELECT count(*) FROM parts").fetchone() == (0,)
            assert connection.execute("SELECT count(*) FROM audit").fetchone() == (1,)
            meta = json.loads(connection.execute("SELECT body FROM project").fetchone()[0])
            assert meta["project_revision"] == 1
        # Cold journals can remain after SQLite inspection. Preserve them: this
        # milestone has no product repair API, even for a complete old snapshot.
        return
    committed = stage == "after_commit"
    summary = store.open_existing_readonly(root).inspect()
    assert summary["bundle_count"] == int(committed)
    assert summary["project_revision"] == 1 + int(committed)
    assert summary["research_project_id"] == project.research_project_id
    assert freeze(root, raw)["replayed"] is committed


def test_r13_import_create_read_have_no_process_or_network_side_effects(tmp_path):
    result = child("""
import sys
def guard(event,args):
    if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):
        raise AssertionError('unexpected external side effect')
    if event == 'import' and any(x in args[0].lower() for x in ('abqjobpilot','abaqus','odbaccess')):
        raise AssertionError('unexpected external import')
sys.addaudithook(guard)
from aegiscae.research.project import create_research_project,open_existing_readonly
p=create_research_project(sys.argv[1],'Synthetic')
assert open_existing_readonly(sys.argv[1]).inspect()['research_project_id']==p.research_project_id
print('NO_EXTERNAL_SIDE_EFFECTS')
""", tmp_path / "isolated")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "NO_EXTERNAL_SIDE_EFFECTS"


def test_hard_constraint_evidence_cannot_be_omitted(fresh):
    _, _, raw = fresh
    constraint = raw["goal"]["hard_constraints"][0]
    constraint["evidence"]["component"] = "U2"
    raw["verification"]["hard_constraint_checks"][0]["rule"] = copy.deepcopy(constraint)
    with pytest.raises(ContractError):
        ContractBundle.from_dict(raw)


@pytest.mark.parametrize("column,value", [("created_at_utc", "2026-10-28T00:00:00.000000Z"),
                                          ("transaction_id", "tx_" + "0" * 32),
                                          ("metadata_digest", "sha256:" + "0" * 64)])
def test_freeze_metadata_columns_cannot_drift(fresh, column, value):
    root, _, raw = fresh
    freeze(root, raw)
    with sqlite3.connect(root / "research.sqlite3") as connection:
        # Column comes exclusively from the literal parametrization above.
        connection.execute(f"UPDATE bundles SET {column}=?", (value,))
    before = disk_snapshot(root)
    with pytest.raises(store.ProjectError):
        store.open_existing_readonly(root)
    assert disk_snapshot(root) == before


def test_r07_tolerance_and_verification_change_need_new_versions(fresh):
    root, project, raw = fresh
    first = freeze(root, raw)
    original = project.read_frozen_bundle(first["bundle_digest"])["bundle"].canonical_bytes()
    raw["version"] = 2
    raw["goal"]["version"] = 2
    raw["goal"]["tolerance"]["value"] = "0.001"
    raw["verification"]["goal_tolerance"]["value"] = "0.001"
    with pytest.raises(store.ProjectError, match="CONTRACT_VERSION_CONFLICT"):
        freeze(root, raw, "new", 2)
    raw["verification"]["version"] = 2
    freeze(root, raw, "new", 2)
    assert project.read_frozen_bundle(first["bundle_digest"])["bundle"].canonical_bytes() == original
    assert project.inspect()["human_approval"] == "NOT_ESTABLISHED"


def test_decimal_precision_survives_freeze(fresh):
    root, project, raw = fresh
    precise = "0.123456789012345678901234567890123456789"
    raw["goal"]["target"]["value"] = precise
    frozen = freeze(root, raw)
    actual = project.read_frozen_bundle(frozen["bundle_digest"])["bundle"]
    assert actual.goal.target.value == precise


def test_creation_failure_leaves_quarantined_root(tmp_path, monkeypatch):
    root = tmp_path / "failed"

    def fail(stage):
        if stage == "create_before_commit":
            raise RuntimeError("injected creation failure")

    monkeypatch.setattr(store, "_fault", fail)
    with pytest.raises(RuntimeError):
        store.create_research_project(root, "Synthetic")
    assert root.exists()
    before = disk_snapshot(root)
    with pytest.raises(store.ProjectError):
        store.open_existing_readonly(root)
    with pytest.raises(store.ProjectError, match="ROOT_EXISTS"):
        store.create_research_project(root, "Synthetic")
    assert disk_snapshot(root) == before


@pytest.mark.parametrize("change", ["missing_time", "schema", "boolean_revision", "bad_calendar"])
def test_project_metadata_validation(fresh, change):
    root, _, _ = fresh
    with sqlite3.connect(root / "research.sqlite3") as connection:
        meta = json.loads(connection.execute("SELECT body FROM project").fetchone()[0])
        if change == "missing_time":
            del meta["created_at_utc"]
        elif change == "schema":
            meta["schema_version"] = 2
        elif change == "boolean_revision":
            meta["project_revision"] = True
        else:
            meta["created_at_utc"] = "2026-02-31T00:00:00.000000Z"
        body = canonical_json(meta)
        connection.execute("UPDATE project SET body=?,digest=?", (body, digest_bytes(body)))
    before = disk_snapshot(root)
    with pytest.raises(store.ProjectError):
        store.open_existing_readonly(root)
    assert disk_snapshot(root) == before


def test_declared_binding_is_not_verified_or_credential_capability(tmp_path):
    binding = {"project_id": "p_" + "1" * 32, "project_instance_id": "pi_" + "2" * 32,
               "context_digest": digest_bytes(b"synthetic binding"), "protocol": "af-local-json-v1",
               "capability_version": "gd-af-read-v1"}
    project = store.create_research_project(tmp_path / "bound", "Synthetic", declared_af_binding=binding)
    assert project.inspect()["binding_status"] == "BOUND_DECLARED"
    assert project.inspect()["execution_authorized"] is False
    binding["credential"] = "sensitive"
    with pytest.raises(store.ProjectError, match="INVALID_BINDING"):
        store.create_research_project(tmp_path / "unsafe", "Synthetic", declared_af_binding=binding)
    assert not (tmp_path / "unsafe").exists()


def test_active_journal_blocks_then_explicit_retry_reports_revision_conflict(fresh, monkeypatch):
    root, project, raw = fresh
    writer = store.open_existing_for_explicit_write(root)
    active, release = Event(), Event()

    def hold(stage):
        if stage == "after_bundle":
            active.set()
            assert release.wait(timeout=5)

    monkeypatch.setattr(store, "_fault", hold)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(writer.freeze_contract_bundle, ContractBundle.from_dict(raw), 1, "winner")
        assert active.wait(timeout=5)
        before = disk_snapshot(root)
        try:
            with pytest.raises(store.ProjectError, match="STORE_BUSY"):
                freeze(root, raw, "second")
            assert disk_snapshot(root) == before
        finally:
            release.set()
        assert future.result()["project_revision"] == 2
    with pytest.raises(store.ProjectError, match="REVISION_CONFLICT"):
        freeze(root, raw, "second")
    assert project.inspect()["bundle_count"] == 1
