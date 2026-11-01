"""Pure foundation-deployment plan; no accounts, ACL writes, subprocess or authority.

Actual identities are stored only in a task-private plan. A checksum pins bytes,
not a trustworthy publisher. Windows enforcement still requires separate approval.
"""

import hashlib
import json
from pathlib import PurePosixPath
import re

SCHEMA = "gdcae-operator-foundation-v1"
CODE = "C:/Program Files/GDCAE Operator"
STATE = "C:/ProgramData/GDCAE Operator"
ACCOUNTS = ["GDCAEResearch", "GDCAEIssuer"]
BLOCKERS = ["FIXED_INTERPRETER_OUTSIDE_CODE_ROOT", "RUNTIME_NOT_LOAD_QUALIFIED",
            "PROTECTED_OPERATOR_CONSOLE_NOT_IMPLEMENTED", "CROSS_SID_EVIDENCE_NOT_QUALIFIED",
            "CUSTODY_ACE_INHERIT_ONLY_UNRECONCILED"]


def need(value, code):
    if not value:
        raise ValueError(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_files(files):
    need(type(files) is list and 0 < len(files) <= 20000, "BOUNDED_INVENTORY_REQUIRED")
    seen, size = set(), 0
    for item in files:
        need(type(item) is dict and set(item) == {"source", "destination", "size", "sha256"},
             "EXACT_FILE_RECORD_REQUIRED")
        destination = item["destination"]
        need(type(destination) is str and re.fullmatch(r"[A-Za-z0-9_./-]+", destination) and "\\" not in destination
             and ":" not in destination and not destination.startswith("/")
             and all(x not in ("", ".", "..") and not x.endswith((".", " "))
                     for x in destination.split("/")), "UNSAFE_DESTINATION")
        need(not any(re.match(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", x, re.I)
                     for x in destination.split("/")), "UNSAFE_DESTINATION")
        path = PurePosixPath(destination)
        need(path.suffix.lower() in (".py", ".pyd", ".dll", ".exe"), "UNAPPROVED_FILE_TYPE")
        need(destination.casefold() not in seen, "DUPLICATE_DESTINATION")
        seen.add(destination.casefold())
        need(type(item["source"]) is str and re.match(r"^[A-Za-z]:[/\\]", item["source"])
             and not any(x in item["source"] for x in ("\n", "\r", "\x00")), "ABSOLUTE_SOURCE_REQUIRED")
        need(type(item["size"]) is int and 0 <= item["size"] <= 67108864, "FILE_BOUND_EXCEEDED")
        need(type(item["sha256"]) is str and re.fullmatch(r"[a-f0-9]{64}", item["sha256"]),
             "EXACT_FILE_HASH_REQUIRED")
        size += item["size"]
    need(size <= 1073741824, "INVENTORY_TOO_LARGE")


def build_plan(host_sha256, current_sid, files, scripts):
    need(type(host_sha256) is str and re.fullmatch(r"[a-f0-9]{64}", host_sha256), "HOST_PIN_REQUIRED")
    need(type(current_sid) is str and re.fullmatch(r"S-1-5-21-(?:[0-9]+-){3}[0-9]+", current_sid),
         "CURRENT_ACTUAL_PRINCIPAL_REQUIRED")
    validate_files(files)
    need(type(scripts) is dict and set(scripts) == {
        "Deploy-Operator.ps1", "Undo-Operator.ps1", "Operator.Common.ps1", "identity_probe.py", "audit.py"}
        and all(type(v) is str and re.fullmatch(r"[a-f0-9]{64}", v) for v in scripts.values()),
        "SCRIPT_PINS_REQUIRED")
    return {"schema": SCHEMA, "scope": "FOUNDATION_ONLY_NO_ACTIVATION",
            "host_sha256": host_sha256, "original_agent_sid": current_sid,
            "accounts": ACCOUNTS, "code_root": CODE, "state_root": STATE,
            "staging_root": "C:/ProgramData/GDCAE Operator Preparation",
            "directories": ["config", "projects", "audit", "review", "deployment"],
            "source_files": files, "scripts": scripts, "activation_blockers": BLOCKERS,
            "create_service": False, "create_project": False, "create_capability": False,
            "start_owner": False, "issue_grant": False, "execute_solver": False,
            "research_identity_requirement": "ACTUAL_CODEX_TOOL_TOKEN_MUST_EQUAL_NEW_RESEARCH_SID",
            "rollback": "DISABLE_ONLY_EXACT_CREATED_ACCOUNTS_PRESERVE_ALL_FILES"}


def validate_plan(value):
    expected = build_plan(value["host_sha256"], value["original_agent_sid"],
                          value["source_files"], value["scripts"])
    need(canonical(value) == canonical(expected), "UNREVIEWED_DEPLOYMENT_CHANGE")
    return sha(canonical(value))


def admission(plan, observation, *, apply=False, approved_sha256=None):
    """Offline decision model, never an OS executor or a grant of authority."""
    digest = validate_plan(plan)
    need(type(apply) is bool, "BOOLEAN_MODE_REQUIRED")
    need(observation["host_sha256"] == plan["host_sha256"], "WRONG_HOST")
    need(observation["accounts_absent"] is True and observation["roots_absent"] is True,
         "EXISTING_OBJECT_CONFLICT")
    need(observation["sources_verified"] is True, "SOURCE_CHANGED")
    if apply:
        need(approved_sha256 == digest, "EXACT_APPROVAL_REQUIRED")
        need(observation["elevated"] is True and observation["in_job"] is False
             and observation["impersonating"] is False, "INDEPENDENT_ADMIN_CONSOLE_REQUIRED")
        need(observation["human_console_confirmed"] is True, "HUMAN_ADMIN_CONFIRMATION_REQUIRED")
    return {"mode": "APPROVAL_GATES_CHECKED" if apply else "DRY_RUN",
            "mutation_performed": False, "operator_activation": "BLOCKED"}


ROLE_CHECKS = {
    "research": {"code_read": True, "code_write": False, "rules_write": False,
                 "config_read": False, "capability_read": False, "project_write": False,
                 "grant_store_write": False},
    "issuer": {"code_read": True, "code_write": False, "rules_write": False,
               "config_read": True, "config_write": False, "capability_read": True,
               "project_write": True},
}


def review_role_observations(role, identity, expected_sid, observations):
    """Review a diagnostic record, never attest the record's publisher or grant authority.

    Real acceptance additionally requires the actual Codex tool invocation under
    research, and an independent human issuer login with trusted probe/runtime.
    """
    need(role in ROLE_CHECKS, "UNKNOWN_PRINCIPAL_ROLE")
    need(type(expected_sid) is str and re.fullmatch(r"S-1-5-21-(?:[0-9]+-){3}[0-9]+", expected_sid),
         "DEPLOYED_SID_REQUIRED")
    need(identity["sid"] == expected_sid and identity["admin_or_linked_admin"] is False
         and identity["elevated"] is False and identity["impersonating"] is False,
         "WRONG_OR_PRIVILEGED_ACTUAL_SUBJECT")
    need(type(observations) is dict and set(observations) == set(ROLE_CHECKS[role])
         and all(type(v) is bool for v in observations.values()), "REAL_ACCESS_OBSERVATIONS_INCOMPLETE")
    need(observations == ROLE_CHECKS[role], "UNSAFE_EFFECTIVE_ACCESS")
    return {"policy_consistency": "PASS_DIAGNOSTIC_ONLY", "windows_access_authenticated": False,
            "actual_codex_context": "INDEPENDENT_TOOL_INVOCATION_REVIEW_REQUIRED",
            "operator_activation": "BLOCKED", "execution_authorized": False}
