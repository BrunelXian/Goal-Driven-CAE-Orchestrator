"""Synthetic verified Host receipts; no production service or scientific execution."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json

import pytest

from aegiscae.contracts.research_contracts import ContractError
from aegiscae.research import capability_discovery, project, task_cards, task_roles


@pytest.fixture
def case(tmp_path, monkeypatch):
    root = tmp_path / "research"
    project.create_research_project(root, "LoadInv", research_agreements=True)
    handle = project.open_agreement_project(root, write=True)
    key = hashlib.sha256(b"gdcae-main-handoff-v1\nlocal\ndesktop").hexdigest()
    folder = tmp_path / "settings/GDCAE/project-main-handoffs/v1"
    folder.mkdir(parents=True)
    receipt = folder / (key + ".json")
    receipt.write_text(json.dumps(dict(schema="gdcae-main-handoff-v1", host_id="local", project_id="desktop",
        request_id=key, thread_id="main-1", state="VERIFIED", title="LoadInv Main")))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "settings"))
    monkeypatch.setenv("CODEX_THREAD_ID", "main-1")
    drafts = {key: dict(goal=key + " target", criterion=key + " criterion",
                        deliverable=key + " output", refs=[]) for key in ("T01", "T02")}
    req = dict(project=handle.research_project_id, host="local", desktop_project="desktop",
               expected_revision=1, key="intake", data={"summary": "1 mm +/- 0.1 mm", "drafts": drafts})
    return root, handle, req, receipt


def test_register_reopen_update_and_arbitrate(case):
    root, handle, req, _ = case
    assert task_cards.view(handle)["tasks"] == []
    receipt = task_cards.record(handle, req, "task-init")
    assert receipt["revision"] == 2
    start = task_cards.view(project.open_agreement_project(root))
    assert [c["task_id"] for c in start["tasks"]] == ["T01", "T02"]
    assert start["tasks"][0]["deliverable"] == "T01 output" and start["tasks"][1]["criterion"] == "T02 criterion"
    assert [c["responsible"] for c in start["tasks"]] == ["CAE", "Diagnostics"]
    create = dict(req, key="validation", expected_revision=2, data=dict(task_id="T03", kind="independent-review",
        goal="Compare independent measurement", criterion="Frozen error limit", deps=["T01"], refs=[]))
    task_cards.record(handle, create, "task-create")
    update = dict(req, key="work", expected_revision=3, data=dict(task_id="T03", execution="IN_PROGRESS", evidence=[]))
    with pytest.raises(ContractError, match="UNMET_TASK_DEPENDENCY"):
        task_cards.record(handle, update, "task-update")
    update["data"]["task_id"] = "T01"
    task_cards.record(handle, update, "task-update")
    submit = dict(req, key="submit", expected_revision=4, data=dict(task_id="T01", execution="SUBMITTED", evidence=[]))
    with pytest.raises(ContractError, match="TASK_EVIDENCE_REQUIRED"):
        task_cards.record(handle, submit, "task-update")
    submit["data"]["evidence"] = [dict(reference="synthetic observation", sha256="a" * 64)]
    task_cards.record(handle, submit, "task-update")
    view = task_cards.view(project.open_agreement_project(root))
    assert view["revision"] == 5 and view["tasks"][0]["verification"] == "NOT_VERIFIED"
    assert view["tasks"][0]["scientific_decision"] == "NOT_ASSESSED" and not view["execution_authorized"]
    assert task_cards.record(handle, req, "task-init") == receipt


def test_request_conflicts_and_concurrent_retry(case):
    _, handle, req, _ = case
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(lambda _: task_cards.record(handle, req, "task-init"), range(2)))
    assert receipts[0] == receipts[1] and task_cards.view(handle)["revision"] == 2
    other = deepcopy(req)
    other["data"]["summary"] = "different study"
    with pytest.raises(ContractError, match="REQUEST_KEY_CONFLICT"):
        task_cards.record(handle, other, "task-init")
    with pytest.raises(ContractError, match="TASK_EVENT_CONFLICT"):
        task_cards.record(handle, dict(req, key="stale"), "task-init")


@pytest.mark.parametrize("problem", ["absent", "pending", "wrong-thread", "wrong-project", "wrong-key"])
def test_unverified_identity_cannot_write(case, monkeypatch, problem):
    _, handle, req, path = case
    doc = json.loads(path.read_text())
    if problem == "absent":
        path.unlink()
    elif problem == "wrong-thread":
        monkeypatch.setenv("CODEX_THREAD_ID", "setup")
    else:
        field = {"pending": "state", "wrong-project": "project_id", "wrong-key": "request_id"}[problem]
        doc[field] = "different"
        path.write_text(json.dumps(doc))
    with pytest.raises(ContractError, match="MAIN_"):
        task_cards.record(handle, req, "task-init")
    assert task_cards.view(handle)["revision"] == 1


def test_reply_lost_after_commit(case, monkeypatch):
    _, handle, req, _ = case
    original = project.ResearchProject._snapshot
    def lose(self, **kwargs):
        if not kwargs.get("write"):
            raise TimeoutError("lost readback")
        return original(self, **kwargs)
    monkeypatch.setattr(project.ResearchProject, "_snapshot", lose)
    with pytest.raises(TimeoutError):
        task_cards.record(handle, req, "task-init")
    monkeypatch.setattr(project.ResearchProject, "_snapshot", original)
    assert task_cards.record(handle, req, "task-init")["revision"] == 2
    assert len(task_cards.view(handle)["tasks"]) == 2


def test_registry_extension_and_role_isolation():
    roles = (*task_roles.DEFINITIONS, task_roles.RoleDefinition("Metrology", "sensor-review", "sensor",
             "calibration record", ("evidence-read",), "calibration digest"))
    match = task_roles.match("sensor-review", roles)
    assert match["role"] == "Metrology" and match["session_status"] == "BLOCKED_HOST_ROLE_BINDING"
    assert task_roles.match("independent-review")["tools"] != task_roles.match("result-extraction")["tools"]
    with pytest.raises(ContractError):
        task_roles.match("solve")


def test_discovery_distinguishes_inventory_and_authority(tmp_path):
    root = tmp_path / "backend"
    spec = dict(abaqus_launcher=None, abqjobpilot_root=str(root))
    assert capability_discovery.discover(spec)["abqjobpilot"] == "MISSING_AT_SUPPLIED_PATH"
    package = root / "abqjobpilot"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("__version__ = '0.2.2'\nraise Exception('must not execute')\n")
    result = capability_discovery.discover(spec)
    assert result["version"] == "0.2.2" and result["public_tools"] == []
    assert result["service"] == "BLOCKED_INTERFACE_UNVERIFIED" and result["project"] == "UNVERIFIED"
    (package / "mcp").mkdir()
    (package / "mcp/server.py").write_text("@server.tool()\ndef abq_list_jobs(): pass\n")
    result = capability_discovery.discover(spec)
    assert result["public_tools"] == ["abq_list_jobs"] and result["authorization"] == "NOT_GRANTED"
    assert not result["execution_authorized"] and result["abaqus"] == "UNKNOWN"


def test_intake_all_or_nothing_and_freeze_after_registration(case):
    from aegiscae.contracts.research_contracts import ContractBundle
    from test_research_project import proposal
    _, handle, req, _ = case
    broken = deepcopy(req)
    broken["data"]["drafts"]["T02"]["refs"] = [{"reference": "asset", "sha256": "bad"}]
    with pytest.raises(ContractError, match="INVALID_TASK_REFS"):
        task_cards.record(handle, broken, "task-init")
    assert task_cards.view(handle)["tasks"] == []
    task_cards.record(handle, req, "task-init")
    bundle = ContractBundle.from_dict(proposal(handle.research_project_id))
    handle.freeze_contract_bundle(bundle, 2, "freeze")
    create = dict(req, key="odb", expected_revision=3, data=dict(task_id="T03", kind="result-extraction",
        goal="Read output", criterion="Quantity, units and selector", deps=[], refs=[]))
    task_cards.record(handle, create, "task-create")
    view = task_cards.view(handle)
    assert view["tasks"][0]["agreement_digest"] is None
    assert view["tasks"][2]["agreement_digest"] == bundle.digests()["bundle"]


def test_extended_session_catalog_requires_reviewed_definition(case, tmp_path):
    from pathlib import Path
    from aegiscae.research.scoped_sessions import load_roles, SessionHub
    _, handle, _, _ = case
    sample = Path(__file__).resolve().parents[2] / "plugins/gdcae-aoo/agents/gdcae-cae.toml"
    (tmp_path / "metrology.toml").write_text(sample.read_text().replace("gdcae-cae", "metrology"))
    roles = load_roles(tmp_path, {"metrology": "Metrology"})
    with pytest.raises(ContractError, match="ROLE_CATALOG_INVALID"):
        SessionHub(handle, roles)
    with pytest.raises(ContractError, match="ROLE_BINDING_CHANGED"):
        SessionHub(handle, roles, approved_role_digests={"metrology": "wrong"})
    pins = {"metrology": roles["metrology"]["definition_digest"]}
    assert list(SessionHub(handle, roles, approved_role_digests=pins).roles) == ["metrology"]
