"""Pure deployment-plan/denial fixtures; never invoke Windows account or ACL APIs."""

import copy
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "operator_preparation_subject", Path(__file__).parents[2] / "operator_deployment/preparation.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


@pytest.fixture
def plan():
    files = [{"source": "D:/Synthetic/source.py", "destination": "code/a.py", "size": 3,
              "sha256": "a" * 64}]
    scripts = {name: "b" * 64 for name in (
        "Deploy-Operator.ps1", "Undo-Operator.ps1", "Operator.Common.ps1", "identity_probe.py", "audit.py")}
    return p.build_plan("c" * 64, "S-1-5-21-1-2-3-1000", files, scripts)


@pytest.fixture
def observation():
    return {"host_sha256": "c" * 64, "accounts_absent": True, "roots_absent": True,
            "sources_verified": True, "elevated": True, "in_job": False,
            "impersonating": False, "human_console_confirmed": True}


def test_default_has_no_execution_or_mutation(plan, observation):
    assert p.admission(plan, observation) == {
        "mode": "DRY_RUN", "mutation_performed": False, "operator_activation": "BLOCKED"}
    assert not any(plan[k] for k in ("create_service", "create_project", "create_capability",
                                   "start_owner", "issue_grant", "execute_solver"))


def test_approved_plan_only_checks_gates_not_authority(plan, observation):
    result = p.admission(plan, observation, apply=True, approved_sha256=p.validate_plan(plan))
    assert not result["mutation_performed"] and result["operator_activation"] == "BLOCKED"


@pytest.mark.parametrize("field,value", [
    ("host_sha256", "d" * 64), ("accounts_absent", False), ("accounts_absent", "UNKNOWN"),
    ("roots_absent", False), ("sources_verified", False), ("elevated", False),
    ("in_job", True), ("in_job", "UNKNOWN"), ("impersonating", True),
    ("human_console_confirmed", False)])
def test_apply_refuses_unsafe_environment(plan, observation, field, value):
    observation[field] = value
    with pytest.raises(ValueError):
        p.admission(plan, observation, apply=True, approved_sha256=p.validate_plan(plan))


@pytest.mark.parametrize("field", ["create_service", "create_project", "create_capability", "start_owner", "issue_grant", "execute_solver"])
def test_scope_expansion_cannot_be_signed_by_plan(plan, field):
    plan[field] = True
    with pytest.raises(ValueError, match="UNREVIEWED_DEPLOYMENT_CHANGE"):
        p.validate_plan(plan)


def test_foreign_approval_hash_and_boolean_mode_rejected(plan, observation):
    with pytest.raises(ValueError, match="EXACT_APPROVAL_REQUIRED"):
        p.admission(plan, observation, apply=True, approved_sha256="0" * 64)
    with pytest.raises(ValueError, match="BOOLEAN_MODE_REQUIRED"):
        p.admission(plan, observation, apply=1)


@pytest.mark.parametrize("destination", ["../escape.py", "/outside.py", "C:/bad.py", "a//b.py",
    "a/./b.py", "a/../b.py", "a\\b.py", "CON.py", "a/NUL.py", "a/LPT1.dll", "a /b.py",
    "a\n/b.py", "a/b.py.", "a/file.db", "a/secret.json", "a/config.pth", "a/name:stream.py"])
def test_destination_restrictions(plan, destination):
    plan["source_files"][0]["destination"] = destination
    with pytest.raises(ValueError):
        p.validate_plan(plan)


@pytest.mark.parametrize("size", [True, -1, 67108865, "1"])
def test_file_size_bounds(plan, size):
    plan["source_files"][0]["size"] = size
    with pytest.raises(ValueError):
        p.validate_plan(plan)


def test_windows_case_duplicate_and_extra_manifest_fields(plan):
    plan["source_files"].append({**plan["source_files"][0], "destination": "CODE/A.PY"})
    with pytest.raises(ValueError, match="DUPLICATE_DESTINATION"):
        p.validate_plan(plan)
    plan["source_files"].pop()
    plan["execute"] = "unreviewed"
    with pytest.raises(ValueError, match="UNREVIEWED_DEPLOYMENT_CHANGE"):
        p.validate_plan(plan)


@pytest.mark.parametrize("role", ["research", "issuer"])
def test_real_identity_acceptance_is_not_a_self_reported_grant(role):
    sid = "S-1-5-21-1-2-3-1001"
    identity = {"sid": sid, "admin_or_linked_admin": False, "elevated": False, "impersonating": False}
    result = p.review_role_observations(role, identity, sid, copy.deepcopy(p.ROLE_CHECKS[role]))
    assert result["policy_consistency"] == "PASS_DIAGNOSTIC_ONLY"
    assert not result["windows_access_authenticated"] and not result["execution_authorized"]
    for name in p.ROLE_CHECKS[role]:
        observed = copy.deepcopy(p.ROLE_CHECKS[role])
        observed[name] = not observed[name]
        with pytest.raises(ValueError, match="UNSAFE_EFFECTIVE_ACCESS"):
            p.review_role_observations(role, identity, sid, observed)
    for name in ("admin_or_linked_admin", "elevated", "impersonating"):
        with pytest.raises(ValueError, match="WRONG_OR_PRIVILEGED_ACTUAL_SUBJECT"):
            p.review_role_observations(role, {**identity, name: True}, sid, p.ROLE_CHECKS[role])
    with pytest.raises(ValueError, match="WRONG_OR_PRIVILEGED_ACTUAL_SUBJECT"):
        p.review_role_observations(role, {**identity, "sid": "S-1-5-21-1-2-3-9999"}, sid, p.ROLE_CHECKS[role])
    with pytest.raises(ValueError, match="INCOMPLETE"):
        p.review_role_observations(role, identity, sid, {})
