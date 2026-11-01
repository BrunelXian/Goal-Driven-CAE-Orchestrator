"""Non-executable Operator deployment proposal, no accounts/ACLs/services/Grants."""

import hashlib
import json
import re


class ReviewBlocked(ValueError):
    pass


def need(value, code):
    if not value:
        raise ReviewBlocked(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def proposal(*, af_code_sha256, gd_code_sha256, config_sha256):
    hashes = {"af_code": af_code_sha256, "gd_code": gd_code_sha256, "config": config_sha256}
    need(all(type(v) is str and re.fullmatch(r"[a-f0-9]{64}", v) for v in hashes.values()),
         "EXACT_REVIEWED_HASHES_REQUIRED")
    return {
        "schema": "gdcae-operator-deployment-preview-v1", "mode": "PREVIEW_ONLY",
        "principals": {
            "research": "EXISTING_CODEX_PRINCIPAL_MAPPING_PENDING",
            "human_reviewer": "PROPOSED_GDCAE_REVIEWER_NONADMIN",
            "issuer": "PROPOSED_GDCAE_ISSUER_NONADMIN",
        },
        "private_sid_mapping": "REQUIRES_ADMIN_REVIEW_NOT_SUPPLIED",
        "reviewed_hashes": hashes,
        "layout": {"code": "C:/Program Files/GDCAE Operator",
                   "state": "C:/ProgramData/GDCAE Operator"},
        "rights": {
            "research": {"code": "READ_ONLY", "config": "NONE", "capability": "NONE",
                         "audit": "NONE", "endpoint": "REQUEST_AND_OWN_STATUS_ONLY"},
            "human_reviewer": {"code": "READ_EXECUTE", "config": "READ", "capability": "NONE",
                               "audit": "READ_SANITIZED", "endpoint": "EXACT_APPROVE_OR_DENY"},
            "issuer": {"code": "READ_EXECUTE", "config": "READ", "capability": "READ_USE",
                       "audit": "APPEND", "endpoint": "EXISTING_AF_TRUSTED_AUTHORITY"},
        },
        "issuer_runtime": "EXISTING_AF_OWNER_NO_SECOND_SOLVER_OWNER",
        "startup": "EXPLICIT_HUMAN_START_UNDER_ISSUER_AFTER_DEPLOYMENT_APPROVAL",
        "credential_source": "ISSUER_SCOPED_DPAPI_NO_AGENT_EXPORT",
        "license_access": "SEPARATE_HOST_QUALIFICATION_REQUIRED",
        "new_windows_service": False,
        "request_protocol": {
            "peer": "OS_TOKEN_NOT_CALLER_ROLE", "transport": "LOCAL_ONLY_REVIEWED_AF_INTERFACE",
            "arbitrary_shell": False, "arbitrary_paths": False, "max_payload_bytes": 65536,
            "human_action": "EXACT_APPROVE_OR_TERMINAL_DENY", "nonce": "ATOMIC_ONE_USE",
            "max_validity_seconds": 600, "unknown": "HOLD_NO_RETRY",
            "tuple": ["project_id", "project_instance_id", "contract_digest", "candidate_id",
                      "plan_id", "plan_digest", "revision", "input_digest", "backend",
                      "resources_digest", "working_directory", "scratch_identity",
                      "output_identity", "deadline", "nonce", "one_attempt"],
        },
        "system_change_preview": ["APPROVE_DISTINCT_NONADMIN_IDENTITIES",
                                  "APPROVE_PROTECTED_CODE_CONFIG_AND_STATE_LAYOUT",
                                  "APPROVE_EXISTING_AF_ISSUER_START_METHOD",
                                  "INDEPENDENT_EFFECTIVE_RIGHTS_AND_ADVERSARIAL_QUALIFICATION"],
        "rollback": ["DISABLE_NEW_REQUESTS", "REVOKE_UNUSED_AUTHORITY",
                     "RECONCILE_ONLY_ORIGINAL_OWNED_HANDLES", "PRESERVE_AUDIT",
                     "ADMIN_RESTORE_APPROVED_PRIOR_SECURITY_STATE"],
        "execution_authorized": False, "deployment_authorized": False,
        "HIL_ENFORCEMENT": "BLOCKED", "administrator_bypass": "NOT_RESISTED",
    }


def review(value):
    """Strict preview shape, no self-reported actual enforcement or capability."""
    need(type(value) is dict, "INVALID_PREVIEW")
    hashes = value.get("reviewed_hashes")
    need(type(hashes) is dict and set(hashes) == {"af_code", "gd_code", "config"},
         "INVALID_REVIEWED_HASHES")
    expected = proposal(af_code_sha256=hashes["af_code"], gd_code_sha256=hashes["gd_code"],
                        config_sha256=hashes["config"])
    need(canonical(value) == canonical(expected), "UNREVIEWED_DEPLOYMENT_CHANGE")
    return {"schema": "gdcae-operator-preview-review-v1",
            "preview_sha256": hashlib.sha256(canonical(value)).hexdigest(),
            "status": "PASS_PREVIEW_ONLY", "HIL_ENFORCEMENT": "BLOCKED",
            "execution_authorized": False, "deployment_authorized": False}


def deployment_request(*, af_code_sha256, gd_code_sha256, config_sha256):
    """Exact proposed changes for a human administrator; never applies them.

    Account names are proposals, not discovered identities. SID resolution and
    effective access qualification are mandatory in the separately approved task.
    No credential, command, OS API or executable deployment action is returned.
    """
    base = proposal(af_code_sha256=af_code_sha256, gd_code_sha256=gd_code_sha256,
                    config_sha256=config_sha256)
    return {
        "schema": "gdcae-operator-os-request-v1", "preview": base,
        "status": "NOT_AUTHORIZED", "identities_exist": "NOT_VERIFIED",
        "account_proposals": {
            "research": {"name": "GDCAEResearch", "type": "LOCAL_STANDARD_USER",
                         "interactive": True, "administrator": False},
            "human_reviewer": {"name": "GDCAEReviewer", "type": "LOCAL_STANDARD_USER",
                               "interactive": True, "administrator": False},
            "issuer": {"name": "GDCAEIssuer", "type": "LOCAL_STANDARD_USER",
                       "interactive": True, "administrator": False},
        },
        "administrative_executor": "HUMAN_ADMINISTRATOR_OUTSIDE_AGENT_SESSION",
        "existing_accounts_modified": False, "service_created": False,
        "startup": "HUMAN_RUN_AS_PROPOSED_ISSUER_WITH_EXISTING_AF_OWNER",
        "roots": {
            "code": "C:/Program Files/GDCAE Operator",
            "config": "C:/ProgramData/GDCAE Operator/config",
            "capability": "C:/ProgramData/GDCAE Operator/capability",
            "af_project": "C:/ProgramData/GDCAE Operator/project",
            "engineering": "C:/ProgramData/GDCAE Operator/engineering",
            "audit": "C:/ProgramData/GDCAE Operator/audit",
            "review_surface": "C:/ProgramData/GDCAE Operator/review",
        },
        "dacl_proposal": {
            "inheritance": "DISABLED_EXPLICIT_ALLOW_ONLY_ON_NEW_ROOTS",
            "owner": "BUILTIN_ADMINISTRATORS",
            "system_and_administrators": "FULL_CONTROL_ALL_ROOTS",
            "research": {"code": "READ_EXECUTE"},
            "human_reviewer": {"code": "READ_EXECUTE", "config": "READ",
                               "review_surface": "READ"},
            "issuer": {"code": "READ_EXECUTE", "config": "READ",
                       "capability": "READ", "af_project": "MODIFY",
                       "engineering": "MODIFY", "audit": "MODIFY",
                       "review_surface": "MODIFY"},
            "unlisted_principal_rights": "NONE",
            "unlisted_resource_rights": "NONE",
            "capability_provisioner": "HUMAN_ADMINISTRATOR_AND_QUALIFIED_AF_ISSUER_ONLY",
        },
        "integrity_limits": {
            "administrator_bypass": "NOT_RESISTED",
            "issuer_audit_mutability": "MODIFY_NOT_APPEND_ONLY_OR_TAMPER_PROOF",
            "approval_surface": "PROTECTED_NON_AGENT_UI_ADAPTER_NOT_DEPLOYED",
            "peer_authentication": "OS_TOKEN_BINDING_REQUIRED_NOT_QUALIFIED",
            "existing_same_user_canary": "BLOCKED_NOT_REPAIRED_BY_THIS_DOCUMENT",
        },
        "credential_policy": {
            "passwords": "HUMAN_MANAGED_NO_AGENT_INPUT_OR_EXPORT",
            "capability": "NEW_ISSUER_CURRENT_USER_DPAPI_AFTER_SEPARATE_APPROVAL",
            "existing_dpapi_copy": False,
            "licensing": "NEW_ISSUER_PROFILE_LICENSE_ACCESS_MUST_BE_QUALIFIED",
            "sessions": "NO_EXISTING_CODEX_OR_ABAQUS_SESSION_TAKEOVER",
        },
        "approval_action": {
            "options": ["APPROVE_EXACT", "DENY_TERMINAL"],
            "display": base["request_protocol"]["tuple"],
            "max_validity_seconds": 600, "single_use": True,
            "decision_source": "INDEPENDENT_HUMAN_UI_AND_OS_PEER",
            "free_text_or_agent_boolean": "NOT_AUTHORITY",
        },
        "rollback": ["DISABLE_NEW_REQUESTS_AND_REVOKE_UNUSED_GRANTS",
                     "RECONCILE_ONLY_ORIGINAL_OWNED_HANDLES",
                     "PRESERVE_AND_EXPORT_SANITIZED_AUDIT",
                     "HUMAN_DISABLE_NEW_ACCOUNTS",
                     "HUMAN_RESTORE_RECORDED_NEW_ROOT_SECURITY_DESCRIPTORS",
                     "DO_NOT_DELETE_PROJECTS_OR_UNKNOWN_PROCESS_EVIDENCE"],
        "execution_authorized": False, "deployment_authorized": False,
    }


def review_deployment_request(value):
    need(type(value) is dict and type(value.get("preview")) is dict, "INVALID_OS_REQUEST")
    review(value["preview"])
    hashes = value["preview"]["reviewed_hashes"]
    expected = deployment_request(af_code_sha256=hashes["af_code"],
                                  gd_code_sha256=hashes["gd_code"],
                                  config_sha256=hashes["config"])
    need(canonical(value) == canonical(expected), "UNREVIEWED_OS_CHANGE")
    return {"schema": "gdcae-operator-os-request-review-v1",
            "request_sha256": hashlib.sha256(canonical(value)).hexdigest(),
            "status": "PASS_PREVIEW_ONLY", "deployment_authorized": False,
            "execution_authorized": False, "HIL_ENFORCEMENT": "BLOCKED"}


def a_only_deployment_request(*, af_code_sha256, gd_code_sha256, config_sha256):
    """D6 minimum human issuer console; preserves the historical D5 proposal.

    The operator is independent of the Agent, not an automated third-principal
    review service. This is a change-request parser, never runtime authority.
    """
    previous = deployment_request(af_code_sha256=af_code_sha256,
                                  gd_code_sha256=gd_code_sha256,
                                  config_sha256=config_sha256)
    return {
        "schema": "gdcae-a-only-deployment-request-v1", "status": "NOT_AUTHORIZED",
        "source_hashes": previous["preview"]["reviewed_hashes"],
        "account_proposals": {role: previous["account_proposals"][role]
                              for role in ("research", "issuer")},
        "identities_exist": "NOT_VERIFIED", "roots": previous["roots"],
        "human_review": "HUMAN_AT_PROTECTED_ISSUER_CONSOLE_OUTSIDE_AGENT_CONTEXT",
        "optional_reviewer": "READ_ONLY_OBSERVER_NO_ISSUANCE_AUTHORITY",
        "dacl_proposal": {key: value for key, value in previous["dacl_proposal"].items()
                          if key != "human_reviewer"},
        "startup": previous["startup"], "service_created": False,
        "existing_accounts_modified": False,
        "trusted_runtime": {
            "interpreter": "EXACT_BINARY_HASH_IN_ADMIN_PROTECTED_ROOT_PENDING",
            "source": "EXACT_REVIEWED_SNAPSHOT_ADMIN_OWNED_READ_EXECUTE_ONLY",
            "dependencies": "PINNED_PROTECTED_IMPORT_ROOTS_NO_AGENT_WRITABLE_PATH",
            "environment": "ISOLATED_START_NO_AGENT_PYTHONPATH_OR_SITE_INJECTION",
        },
        "supported_api": {
            "owner": "ORIGINAL_AF_SINGLE_OWNER",
            "channel": "EXISTING_LOCAL_CAPABILITY_IPC",
            "os_peer_identity": "NOT_ESTABLISHED_BY_BEARER_IPC",
            "approval": "EXACT_A_ONLY_DURABLE_APPROVE_OR_TERMINAL_DENY",
            "grant": "EXISTING_AF_SINGLE_USE_EXACT_PLAN_ISSUER",
            "ordinary_agent_approval": "REJECT",
            "missing_or_unqualified_deployment": "REJECT",
        },
        "approval_action": previous["approval_action"] | {
            "decision_source": "HUMAN_PROTECTED_ISSUER_CONSOLE_AND_SERVER_CUSTODY_CHECK",
        },
        "budget": {"A": "ONE_RESEARCH_PROJECT_HOLD_ONE_EXACT_GRANT",
                   "unknown": "HOLD_QUERY_FIRST_NO_NEW_KEY",
                   "B": "BLOCK_UNTIL_REAL_A_CAUSALITY_SEPARATE_APPROVAL_AND_TOTAL_LIMIT",
                   "general_cross_project_scheduler_required_before_A": False},
        "threat_limits": {
            "administrator_bypass": "NOT_RESISTED",
            "ordinary_shell_solver_access": "NOT_QUALIFIED_BLOCKS_EXCLUSIVITY_CLAIM",
            "strong_os_exclusivity": "NOT_VERIFIED",
            "issuer_trusted": "CAN_MUTATE_AF_STATE_NOT_TAMPER_PROOF",
            "current_host_same_user": "NOT_PROTECTED_OPERATOR",
        },
        "required_negative_access_checks": ["RESEARCH_CANNOT_READ_CAPABILITY",
            "RESEARCH_CANNOT_WRITE_TRUSTED_CODE_CONFIG_OR_DEPENDENCIES",
            "RESEARCH_CANNOT_CONTROL_ISSUER_ACCOUNT_OR_START_CONFIG_STOP_SERVICE",
            "RESEARCH_CANNOT_WRITE_AF_PROJECT_INPUT_OR_OUTPUT",
            "WRONG_SID_ELEVATED_OR_ADMIN_TOKEN_REJECTED",
            "ORDINARY_SHELL_SOLVER_ACCESS_MEASURED_NOT_ASSUMED"],
        "credential_policy": previous["credential_policy"],
        "rollback": previous["rollback"],
        "deployment_authorized": False, "execution_authorized": False,
    }


def review_a_only_deployment(value, access_observations):
    """Offline mock parser only. Even all DENIED does not establish OS custody."""
    need(type(value) is dict and type(value.get("source_hashes")) is dict,
         "INVALID_A_ONLY_DEPLOYMENT")
    hashes = value["source_hashes"]
    need(set(hashes) == {"af_code", "gd_code", "config"}, "INVALID_REVIEWED_HASHES")
    expected = a_only_deployment_request(af_code_sha256=hashes["af_code"],
                                         gd_code_sha256=hashes["gd_code"],
                                         config_sha256=hashes["config"])
    need(canonical(value) == canonical(expected), "UNREVIEWED_A_ONLY_DEPLOYMENT")
    need(type(access_observations) is dict and set(access_observations) == {
        "source", "research_admin", "same_principal", "capability_read",
        "code_config_write", "issuer_control", "model_output_write"}, "INVALID_ACCESS_REVIEW")
    need(access_observations["source"] == "MOCK_ACCESS_DECISIONS"
         and type(access_observations["research_admin"]) is bool
         and type(access_observations["same_principal"]) is bool
         and all(type(access_observations[k]) is str
                 and access_observations[k] in {"ALLOWED", "DENIED", "UNKNOWN"}
                 for k in ("capability_read", "code_config_write", "issuer_control",
                           "model_output_write")), "INVALID_ACCESS_REVIEW")
    safe_mock = not (access_observations["research_admin"]
                    or access_observations["same_principal"]) and all(
        access_observations[k] == "DENIED" for k in ("capability_read", "code_config_write",
                                                   "issuer_control", "model_output_write"))
    return {"schema": "gdcae-a-only-deployment-review-v1",
            "request_sha256": hashlib.sha256(canonical(value)).hexdigest(),
            "mock_policy": "PASS" if safe_mock else "REJECT",
            "source": "MOCK_ACCESS_DECISIONS", "HIL_ENFORCEMENT": "BLOCKED",
            "effective_windows_access": "NOT_TESTED", "deployment_authorized": False,
            "execution_authorized": False}
