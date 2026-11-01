"""Minimum A-only OS review request; mocked rights are never real authority."""

import copy
import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "d6_preview", Path(__file__).parents[2] / "operator_deployment/preview.py")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def request():
    return preview.a_only_deployment_request(af_code_sha256="a" * 64,
                                             gd_code_sha256="b" * 64,
                                             config_sha256="c" * 64)


def mock_access():
    return {"source": "MOCK_ACCESS_DECISIONS", "research_admin": False,
            "same_principal": False, "capability_read": "DENIED",
            "code_config_write": "DENIED", "issuer_control": "DENIED",
            "model_output_write": "DENIED"}


def test_minimum_human_issuer_is_separate_without_new_scheduler_or_authority():
    raw = request()
    assert set(raw["account_proposals"]) == {"research", "issuer"}
    assert raw["account_proposals"]["research"] != raw["account_proposals"]["issuer"]
    assert raw["budget"]["general_cross_project_scheduler_required_before_A"] is False
    assert "REAL_A" in raw["budget"]["B"]
    assert not raw["service_created"] and not raw["existing_accounts_modified"]
    assert "NOT_ESTABLISHED" in raw["supported_api"]["os_peer_identity"]
    result = preview.review_a_only_deployment(raw, mock_access())
    assert result["mock_policy"] == "PASS"
    assert result["HIL_ENFORCEMENT"] == "BLOCKED"
    assert result["effective_windows_access"] == "NOT_TESTED"
    assert not result["deployment_authorized"] and not result["execution_authorized"]


@pytest.mark.parametrize("field,value", [("research_admin", True), ("same_principal", True),
    *[(field, value) for field in ("capability_read", "code_config_write", "issuer_control",
                                  "model_output_write") for value in ("ALLOWED", "UNKNOWN")]])
def test_unsafe_or_unknown_mock_access_rejects_policy(field, value):
    rights = mock_access()
    rights[field] = value
    result = preview.review_a_only_deployment(request(), rights)
    assert result["mock_policy"] == "REJECT"
    assert not result["execution_authorized"]


@pytest.mark.parametrize("path,value", [
    (("account_proposals", "issuer", "name"), "GDCAEResearch"),
    (("dacl_proposal", "research", "capability"), "READ"),
    (("supported_api", "ordinary_agent_approval"), "ALLOW"),
    (("supported_api", "approval"), "CALLER_TRUE"),
    (("supported_api", "owner"), "SECOND_SOLVER_OWNER"),
    (("approval_action", "max_validity_seconds"), 601),
    (("approval_action", "single_use"), False),
    (("budget", "unknown"), "RETRY_NEW_KEY"),
    (("budget", "B"), "AUTOMATIC_2N"),
    (("threat_limits", "strong_os_exclusivity"), "PASS"),
    (("execution_authorized",), True),
    (("deployment_authorized",), True),
])
def test_unreviewed_scope_change_refuses_even_with_benign_mock_rights(path, value):
    raw = copy.deepcopy(request())
    target = raw
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(preview.ReviewBlocked, match="UNREVIEWED_A_ONLY_DEPLOYMENT"):
        preview.review_a_only_deployment(raw, mock_access())


@pytest.mark.parametrize("field,value", [("source", "REAL_TOKEN_VERIFIED"),
    ("research_admin", 0), ("same_principal", None), ("capability_read", {}),
    ("issuer_control", ["DENIED"])])
def test_mock_self_report_cannot_be_relabelled_actual_authority(field, value):
    rights = mock_access()
    rights[field] = value
    with pytest.raises(preview.ReviewBlocked, match="INVALID_ACCESS_REVIEW"):
        preview.review_a_only_deployment(request(), rights)
