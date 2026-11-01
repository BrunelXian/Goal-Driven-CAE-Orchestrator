"""Pure Operator preview/adversarial tests; no system configuration or capabilities."""

import copy
import importlib.util
from pathlib import Path

import pytest


def load(name):
    path = Path(__file__).parents[2] / "operator_deployment" / (name + ".py")
    spec = importlib.util.spec_from_file_location("d4_operator_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preview = load("preview")
audit = load("audit")


def fixture():
    return preview.proposal(af_code_sha256="a" * 64, gd_code_sha256="b" * 64,
                            config_sha256="c" * 64)


def test_preview_has_three_distinct_principals_no_system_actions_or_authority():
    value = fixture()
    assert len(set(value["principals"].values())) == 3
    result = preview.review(value)
    assert result["HIL_ENFORCEMENT"] == "BLOCKED"
    assert not result["execution_authorized"] and not result["deployment_authorized"]
    assert value["issuer_runtime"] == "EXISTING_AF_OWNER_NO_SECOND_SOLVER_OWNER"
    assert value["new_windows_service"] is False


@pytest.mark.parametrize("path,value", [
    (("principals", "issuer"), "EXISTING_CODEX_PRINCIPAL_MAPPING_PENDING"),
    (("rights", "research", "capability"), "READ_USE"),
    (("rights", "human_reviewer", "capability"), "READ_USE"),
    (("rights", "research", "code"), "WRITE"),
    (("request_protocol", "peer"), "CALLER_ROLE"),
    (("request_protocol", "nonce"), "REUSABLE"),
    (("request_protocol", "max_validity_seconds"), 601),
    (("request_protocol", "max_validity_seconds"), True),
    (("request_protocol", "unknown"), "RETRY"),
    (("request_protocol", "human_action"), "LLM_PASS"),
    (("request_protocol", "arbitrary_shell"), True),
    (("request_protocol", "tuple"), ["plan_id"]),
    (("HIL_ENFORCEMENT",), "PASS"),
    (("execution_authorized",), True),
    (("deployment_authorized",), True),
    (("credential_source",), "CALLER_SECRET"),
    (("rollback",), ["DELETE_AUDIT"]),
])
def test_adversarial_deployment_changes_are_rejected(path, value):
    raw = copy.deepcopy(fixture())
    target = raw
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(preview.ReviewBlocked):
        preview.review(raw)


def test_no_agent_supplied_authority_field_or_missing_identity_can_pass():
    raw = fixture()
    raw["real_grant"] = True
    with pytest.raises(preview.ReviewBlocked):
        preview.review(raw)
    raw = fixture()
    del raw["principals"]["issuer"]
    with pytest.raises(preview.ReviewBlocked):
        preview.review(raw)


class FakeToken:
    def risk(self):
        return {"elevated": True, "admin_or_linked_admin": True}

    def access(self, _path, _mask):
        return "ALLOWED"


def canaries(tmp_path):
    root = tmp_path / "d4-operator-canary"
    root.mkdir()
    for name in audit.RESOURCES:
        (root / name).write_bytes(b"NEW_SYNTHETIC_NON_SECRET")
    return root


def test_current_token_access_is_not_protected_operator_qualification(tmp_path):
    root = canaries(tmp_path)
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    result = audit.inspect_fixture(root, FakeToken())
    assert result["HIL_ENFORCEMENT"] == "BLOCKED"
    assert result["current_token_risk"]["admin_or_linked_admin"]
    assert not result["credential_bytes_read"] and not result["acl_modified"]
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}


def test_denied_fixture_access_still_does_not_qualify_hil(tmp_path):
    class Denied(FakeToken):
        def access(self, _path, _mask):
            return "DENIED"
    assert audit.inspect_fixture(canaries(tmp_path), Denied())["HIL_ENFORCEMENT"] == "BLOCKED"


def test_wrong_directory_missing_resource_and_wrong_backend_types_reject(tmp_path):
    with pytest.raises(audit.AuditBlocked):
        audit.inspect_fixture(tmp_path, FakeToken())
    root = canaries(tmp_path)
    (root / "capability.canary").unlink()
    with pytest.raises(audit.AuditBlocked):
        audit.inspect_fixture(root, FakeToken())


def test_post_deployment_checker_is_read_only_and_never_promotes_one_token(monkeypatch):
    monkeypatch.setattr(audit, "_probe_presence", lambda _path: "NOT_DEPLOYED")
    result = audit.inspect_protected_layout(FakeToken())
    assert set(result["effective_rights"].values()) == {"NOT_DEPLOYED"}
    assert result["HIL_ENFORCEMENT"] == "BLOCKED"
    assert result["cross_principal_qualification"] == "NOT_VERIFIED"


def test_post_deployment_checker_rejects_reparse_ancestry(monkeypatch):
    monkeypatch.setattr(audit, "_probe_presence", lambda _path: "REGULAR_FILE")
    monkeypatch.setattr(Path, "is_symlink", lambda _self: True)
    with pytest.raises(audit.AuditBlocked):
        audit.inspect_protected_layout(FakeToken())


def test_inaccessible_protected_path_is_not_reported_absent():
    class Inaccessible:
        def stat(self, **_kwargs):
            raise PermissionError()
    assert audit._probe_presence(Inaccessible()) == "NOT_OBSERVED_ACCESS_DENIED"
