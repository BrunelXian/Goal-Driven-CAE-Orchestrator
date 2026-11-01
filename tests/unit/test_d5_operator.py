"""Non-executable exact OS change request, not an effective permission test."""

import copy
import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "d5_operator_preview", Path(__file__).parents[2] / "operator_deployment/preview.py")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def request():
    return preview.deployment_request(af_code_sha256="a" * 64, gd_code_sha256="b" * 64,
                                      config_sha256="c" * 64)


def test_exact_three_proposed_principals_and_explicit_bypass_limits():
    raw = request()
    result = preview.review_deployment_request(raw)
    assert result["status"] == "PASS_PREVIEW_ONLY"
    assert result["HIL_ENFORCEMENT"] == "BLOCKED"
    assert raw["status"] == "NOT_AUTHORIZED"
    assert raw["identities_exist"] == "NOT_VERIFIED"
    assert len({v["name"] for v in raw["account_proposals"].values()}) == 3
    assert all(not v["administrator"] for v in raw["account_proposals"].values())
    assert not raw["existing_accounts_modified"] and not raw["service_created"]
    assert raw["integrity_limits"]["administrator_bypass"] == "NOT_RESISTED"
    assert "NOT_APPEND_ONLY" in raw["integrity_limits"]["issuer_audit_mutability"]
    assert raw["dacl_proposal"]["research"] == {"code": "READ_EXECUTE"}
    assert "capability" not in raw["dacl_proposal"]["human_reviewer"]
    assert not result["deployment_authorized"] and not result["execution_authorized"]


@pytest.mark.parametrize("path,value", [
    (("account_proposals", "research", "administrator"), True),
    (("account_proposals", "issuer", "name"), "GDCAEResearch"),
    (("dacl_proposal", "research", "capability"), "READ"),
    (("dacl_proposal", "issuer", "code"), "MODIFY"),
    (("dacl_proposal", "inheritance"), "INHERIT_EVERYONE"),
    (("roots", "af_project"), "C:/Users/Public/unsafe"),
    (("integrity_limits", "approval_surface"), "AGENT_APPROVED"),
    (("integrity_limits", "existing_same_user_canary"), "PASS"),
    (("credential_policy", "existing_dpapi_copy"), True),
    (("approval_action", "single_use"), False),
    (("approval_action", "max_validity_seconds"), 601),
    (("approval_action", "options"), ["APPROVE_EXACT"]),
    (("approval_action", "decision_source"), "CALLER_BOOLEAN"),
    (("existing_accounts_modified",), True),
    (("service_created",), True),
    (("deployment_authorized",), True),
    (("execution_authorized",), True),
    (("rollback",), ["KILL_UNKNOWN_AND_DELETE_HISTORY"]),
])
def test_unreviewed_system_authority_changes_rejected(path, value):
    raw = copy.deepcopy(request())
    target = raw
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(preview.ReviewBlocked, match="UNREVIEWED_OS_CHANGE"):
        preview.review_deployment_request(raw)


def test_request_digest_binds_code_configuration_and_no_extra_boolean_can_authorize():
    raw = request()
    before = preview.review_deployment_request(raw)["request_sha256"]
    other = preview.deployment_request(af_code_sha256="d" * 64, gd_code_sha256="b" * 64,
                                        config_sha256="c" * 64)
    assert preview.review_deployment_request(other)["request_sha256"] != before
    raw["approved"] = True
    with pytest.raises(preview.ReviewBlocked):
        preview.review_deployment_request(raw)
