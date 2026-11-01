"""Synthetic deployment declarations are neither host evidence nor authority."""

import ast
from pathlib import Path

import pytest

from aegiscae.contracts.research_contracts import ContractError, canonical_json, digest_bytes
from aegiscae.research.operator_deployment import (
    deployment_review_template, validate_deployment_contract,
)


def fixture():
    return deployment_review_template(
        "sha256:" + "a" * 64, "sha256:" + "b" * 64,
        code_root="C:/Program Files/GDCAE Operator",
        state_root="C:/ProgramData/GDCAE Operator")


def test_static_fixture_pass_never_qualifies_os_or_grant():
    result = validate_deployment_contract(fixture())
    assert result["HIL_PROTOCOL"] == "PASS_OFFLINE"
    assert result["HIL_OS_ENFORCEMENT"] == "BLOCKED_HIL_DEPLOYMENT"
    assert all(result[key] is False for key in (
        "host_identity_verified", "installed_code_verified", "deployment_authorized",
        "real_grant_issued", "execution_authorized"))
    assert result["contract_digest"] == digest_bytes(canonical_json(fixture()))


def test_template_instances_do_not_share_mutable_permissions():
    first = fixture()
    first["permission_matrix"]["research"]["capability"].append("read")
    assert validate_deployment_contract(fixture())["HIL_PROTOCOL"] == "PASS_OFFLINE"
    with pytest.raises(ContractError, match="UNSAFE_PERMISSION_MATRIX"):
        validate_deployment_contract(first)


def test_roots_are_explicit_inputs_not_machine_defaults():
    raw = deployment_review_template(
        "sha256:" + "a" * 64, "sha256:" + "b" * 64,
        code_root="D:/Program Files/GDCAE Operator",
        state_root="D:/ProgramData/GDCAE Operator")
    assert validate_deployment_contract(raw)["HIL_PROTOCOL"] == "PASS_OFFLINE"
    with pytest.raises(TypeError):
        deployment_review_template("sha256:" + "a" * 64, "sha256:" + "b" * 64)


def test_mismatched_root_volumes_are_not_the_reviewed_layout():
    raw = fixture()
    raw["installation"]["state_root"] = "D:/ProgramData/GDCAE Operator"
    with pytest.raises(ContractError, match="PROTECTED_ROOT_DECLARATION_REQUIRED"):
        validate_deployment_contract(raw)


@pytest.mark.parametrize("role,resource,right", [
    ("research", "trusted_code", "write"),
    ("research", "trusted_config", "write"),
    ("research", "capability", "read"),
    ("research", "capability", "use"),
    ("research", "grant_endpoint", "trusted_af_only"),
    ("research", "dispatch_endpoint", "trusted_af_only"),
    ("research", "audit", "delete"),
    ("operator", "trusted_code", "write"),
    ("operator", "trusted_config", "write"),
    ("operator", "audit", "delete"),
])
def test_permission_escalation_is_rejected(role, resource, right):
    raw = fixture()
    raw["permission_matrix"][role][resource].append(right)
    with pytest.raises(ContractError, match="UNSAFE_PERMISSION_MATRIX"):
        validate_deployment_contract(raw)


@pytest.mark.parametrize("path", [
    "../operator", "C:/Program Files/GDCAE Operator/../Other",
    "//server/share/operator", "\\\\?\\C:\\Program Files\\GDCAE Operator",
    "C:/Program Files/GDCAE Operator:stream", "C:/Program Files/GDCAE Operator.",
    "C:/Program Files/GDCAE Operator ", "C:/Users/Public/Operator",
    "%PROGRAMFILES%/GDCAE Operator", "C:/ProgramData/GDCAE Operator",
])
def test_unsafe_or_wrong_code_path_is_rejected(path):
    raw = fixture()
    raw["installation"]["code_root"] = path
    with pytest.raises(ContractError):
        validate_deployment_contract(raw)


@pytest.mark.parametrize("section,key,value,code", [
    ("installation", "inheritance", "INHERIT_USERS_WRITE", "PROTECTED_LAYOUT_REQUIRED"),
    ("installation", "reparse_policy", "ALLOW", "PROTECTED_LAYOUT_REQUIRED"),
    ("installation", "reparse_observed", "VERIFIED", "UNVERIFIED_HOST_CLAIM"),
    ("installation", "installed_bytes_observed", "VERIFIED", "UNVERIFIED_HOST_CLAIM"),
    ("installation", "actual_sid_mapping", "VERIFIED", "UNVERIFIED_HOST_CLAIM"),
    ("installation", "code_digest", "not-a-digest", "INVALID_DEPLOYMENT_DIGEST"),
    ("channel", "remote_clients", True, "UNSAFE_REQUEST_CHANNEL"),
    ("channel", "remote_clients", 0, "UNSAFE_REQUEST_CHANNEL"),
    ("channel", "arbitrary_paths", True, "UNSAFE_REQUEST_CHANNEL"),
    ("channel", "peer_identity", "CALLER_LABEL", "UNSAFE_REQUEST_CHANNEL"),
    ("channel", "max_payload_bytes", 1048576, "UNSAFE_REQUEST_CHANNEL"),
    ("approval_protocol", "human_exact_tuple_required", False, "UNSAFE_APPROVAL_PROTOCOL"),
    ("approval_protocol", "deny_supported", False, "UNSAFE_APPROVAL_PROTOCOL"),
    ("approval_protocol", "max_attempts", 2, "UNSAFE_APPROVAL_PROTOCOL"),
    ("approval_protocol", "max_validity_seconds", 601, "UNSAFE_APPROVAL_PROTOCOL"),
    ("approval_protocol", "nonce_consumption", "REUSABLE", "UNSAFE_APPROVAL_PROTOCOL"),
    ("approval_protocol", "unknown_outcome", "RETRY", "UNSAFE_APPROVAL_PROTOCOL"),
    ("approval_protocol", "changed_tuple", "ALLOW", "UNSAFE_APPROVAL_PROTOCOL"),
    ("approval_protocol", "denied_request", "RETRY_NEW_KEY", "UNSAFE_APPROVAL_PROTOCOL"),
    ("approval_protocol", "expired_request", "ALLOW", "UNSAFE_APPROVAL_PROTOCOL"),
    ("lifecycle", "windows_service", True, "UNSAFE_OPERATOR_LIFECYCLE"),
    ("lifecycle", "capability_export", True, "UNSAFE_OPERATOR_LIFECYCLE"),
    ("lifecycle", "research_can_delete_audit", True, "UNSAFE_OPERATOR_LIFECYCLE"),
    ("lifecycle", "rollback_order", ["DELETE_AUDIT"], "UNSAFE_OPERATOR_LIFECYCLE"),
])
def test_host_protocol_and_lifecycle_claims_fail_closed(section, key, value, code):
    raw = fixture()
    raw[section][key] = value
    with pytest.raises(ContractError, match=code):
        validate_deployment_contract(raw)


def test_same_principal_remains_unsafe():
    raw = fixture()
    raw["principals"]["operator"]["alias"] = raw["principals"]["research"]["alias"]
    with pytest.raises(ContractError, match="DISTINCT_PRINCIPALS_REQUIRED"):
        validate_deployment_contract(raw)


@pytest.mark.parametrize("value", [True, 0, "false"])
def test_principal_admin_flag_is_strict_false(value):
    raw = fixture()
    raw["principals"]["research"]["administrator"] = value
    with pytest.raises(ContractError, match="NONADMIN_PRINCIPALS_REQUIRED"):
        validate_deployment_contract(raw)


def test_real_identity_string_is_not_a_fixture_alias():
    raw = fixture()
    raw["principals"]["operator"]["alias"] = "REAL_PRINCIPAL_DECLARATION"
    with pytest.raises(ContractError, match="SYNTHETIC_PRINCIPAL_REQUIRED"):
        validate_deployment_contract(raw)


@pytest.mark.parametrize("key", ["approved", "grant", "execution_authorized"])
def test_agent_authority_claims_are_not_fields(key):
    raw = fixture()
    raw[key] = True
    with pytest.raises(ContractError, match="INVALID_DEPLOYMENT_FIELDS"):
        validate_deployment_contract(raw)


def test_missing_section_cannot_gain_qualification():
    raw = fixture()
    del raw["permission_matrix"]
    with pytest.raises(ContractError, match="INVALID_DEPLOYMENT_FIELDS"):
        validate_deployment_contract(raw)


@pytest.mark.parametrize("source", ["REAL_WINDOWS_AUDIT", "AF_REAL_DECLARATION"])
def test_real_source_labels_do_not_turn_fixture_into_host_evidence(source):
    raw = fixture()
    raw["source"] = source
    with pytest.raises(ContractError, match="DEPLOYMENT_SOURCE_NOT_SYNTHETIC"):
        validate_deployment_contract(raw)


def test_module_has_no_process_os_ipc_or_file_access():
    path = Path(__file__).parents[2] / "src/aegiscae/research/operator_deployment.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module)
    assert imported == {"pathlib", "re", "aegiscae.contracts.research_contracts"}
    forbidden = {"open", "read_text", "read_bytes", "write_text", "write_bytes",
                 "mkdir", "unlink", "replace", "Popen", "run", "connect", "execute"}
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                and ((isinstance(node.func, ast.Name) and node.func.id in forbidden)
                     or (isinstance(node.func, ast.Attribute) and node.func.attr in forbidden))]
