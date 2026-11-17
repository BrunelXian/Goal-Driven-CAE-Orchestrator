"""The operator pin, time and exact operation are independent of request claims."""
import hashlib
import json

import pytest

from aegiscae.interfaces import fixture_scope
from aegiscae.interfaces.fixture_scope import Scope, authorize


def provision(tmp_path, **options):
    path = tmp_path / "scope.json"
    receipt = authorize(path, tmp_path / "research", **options)
    return path, Scope(path, receipt["binding_sha256"]), receipt


def test_pin_expiry_and_project_are_checked_at_every_call(tmp_path, monkeypatch):
    path, scope, receipt = provision(tmp_path, operations=["gdcae_workflow_status"])
    record = scope.read("gdcae_workflow_status", receipt["project_id"])
    with pytest.raises(ValueError, match="OPERATION_DENIED"):
        scope.read("gdcae_workflow_advance", receipt["project_id"])
    with pytest.raises(ValueError, match="PROJECT_MISMATCH"):
        scope.read("gdcae_workflow_status", "rp_" + "0" * 32)
    with monkeypatch.context() as patch:
        patch.setattr(fixture_scope.time, "time", lambda: record["expires"])
        with pytest.raises(ValueError, match="SCOPE_EXPIRED"):
            scope.read("gdcae_workflow_status")
    record["operations"].append("gdcae_workflow_advance")
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="BINDING_CHANGED"):
        scope.read("gdcae_workflow_advance")


def test_scope_creation_never_binds_an_existing_project(tmp_path):
    path, scope, receipt = provision(tmp_path)
    record = scope.read("gdcae_project_open")
    project = scope.project(record, create=True)
    assert project.research_project_id == receipt["project_id"]
    assert scope.project(record, create=True).storage_generation == project.storage_generation
    with pytest.raises(ValueError, match="ROOT_EXISTS"):
        authorize(tmp_path / "another.json", tmp_path / "research")
    with pytest.raises(ValueError, match="PROJECT_MISMATCH"):
        scope.project(dict(record, project_id="rp_" + "0" * 32))


@pytest.mark.parametrize("field,value", [("solver_budget", 1), ("tolerance_mm", "1"),
                                          ("channel", "remote"), ("max_executions", True)])
def test_even_pinned_invalid_scope_fails_closed(tmp_path, field, value):
    path, unused_scope, receipt = provision(tmp_path)
    record = json.loads(path.read_bytes())
    record[field] = value
    raw = json.dumps(record).encode()
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="INVALID_SCOPE"):
        Scope(path, hashlib.sha256(raw).hexdigest()).read("gdcae_project_open")


def test_no_parent_traversal_or_overwrite(tmp_path):
    with pytest.raises(ValueError, match="INVALID_ROOT"):
        authorize(tmp_path / "scope", tmp_path / ".." / "research")
    path, _, _ = provision(tmp_path)
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        authorize(path, tmp_path / "another")
    assert path.read_bytes() == original
