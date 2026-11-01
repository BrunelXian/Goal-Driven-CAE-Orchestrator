"""Pure offline Operator deployment review, never a signer or OS verifier.

Inputs are synthetic declarations. A matching permission matrix is not evidence
of Windows enforcement, a protected executable, human consent or a real Grant.
No filesystem, token, IPC, process, credential or AF execution access occurs.
"""

from pathlib import PureWindowsPath
import re

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require


SCHEMA = "g3-operator-deployment-review-v1"
MATRIX = {
    "research": {
        "trusted_code": ["read"], "trusted_config": [], "capability": [],
        "audit": [], "request_endpoint": ["submit_exact", "read_own_receipt"],
        "grant_endpoint": [], "dispatch_endpoint": [],
    },
    "operator": {
        "trusted_code": ["read_execute"], "trusted_config": ["read"],
        "capability": ["read_use"], "audit": ["append"],
        "request_endpoint": ["serve_exact"],
        "grant_endpoint": ["trusted_af_only"], "dispatch_endpoint": ["trusted_af_only"],
    },
}
CHANNEL = {
    "transport": "LOCAL_NAMED_PIPE", "remote_clients": False,
    "peer_identity": "WINDOWS_TOKEN_REQUIRED", "arbitrary_paths": False,
    "request_schema": "af-rod-approval-request-v1", "max_payload_bytes": 65536,
    "response": "SANITIZED_OWN_RECEIPT_ONLY",
}
APPROVAL = {
    "human_exact_tuple_required": True, "deny_supported": True,
    "max_attempts": 1, "max_validity_seconds": 600,
    "nonce_consumption": "ATOMIC_SINGLE_USE", "changed_tuple": "REJECT",
    "expired_request": "REJECT", "denied_request": "TERMINAL_DENY",
    "unknown_outcome": "HOLD_AND_RECONCILE_NO_RETRY",
    "real_grant_provider": "QUALIFIED_AF_OPERATOR_ONLY",
}
LIFECYCLE = {
    "startup": "HUMAN_STARTED_PROTECTED_PROCESS", "windows_service": False,
    "stop": "OWNED_HANDLE_GRACEFUL_THEN_OPERATOR_RECONCILIATION",
    "capability_generation": "PROTECTED_OPERATOR_ONLY",
    "capability_export": False, "audit_mode": "APPEND_WITH_IMMUTABLE_REQUEST_DIGEST",
    "research_can_delete_audit": False,
    "rollback_order": ["DISABLE_REQUEST_ENDPOINT", "REVOKE_CAPABILITY",
                       "RECONCILE_OWNED_PROCESS", "PRESERVE_AUDIT",
                       "ADMIN_RESTORE_PRIOR_SECURITY_STATE"],
}


def _exact(value, keys):
    require(type(value) is dict and set(value) == set(keys), "INVALID_DEPLOYMENT_FIELDS")


def _same(actual, expected, code):
    # Canonical bytes retain type differences such as False versus zero.
    require(canonical_json(actual) == canonical_json(expected), code)


def _path(value):
    require(type(value) is str and 0 < len(value) <= 512, "INVALID_DEPLOYMENT_PATH")
    require(not any(c in value for c in "\x00\n\r%?*<>|\""), "INVALID_DEPLOYMENT_PATH")
    require(not value.startswith(("\\\\", "//")), "INVALID_DEPLOYMENT_PATH")
    path = PureWindowsPath(value)
    require(path.is_absolute() and re.fullmatch(r"[A-Za-z]:", path.drive) is not None,
            "INVALID_DEPLOYMENT_PATH")
    require(all(part not in (".", "..") and not part.endswith((" ", "."))
                and ":" not in part for part in path.parts[1:]), "INVALID_DEPLOYMENT_PATH")
    require(not path.is_reserved(), "INVALID_DEPLOYMENT_PATH")
    return path.as_posix().casefold()


def _digest(value):
    require(type(value) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None,
            "INVALID_DEPLOYMENT_DIGEST")


def deployment_review_template(code_digest, config_digest, *, code_root, state_root):
    """Return a fresh synthetic review fixture, not a deployment instruction."""
    _digest(code_digest)
    _digest(config_digest)
    # Round-trip yields independent nested values without sharing mutable constants.
    from aegiscae.contracts.research_contracts import strict_json

    return strict_json(canonical_json({
        "schema": SCHEMA, "source": "SYNTHETIC_DEPLOYMENT_REVIEW",
        "principals": {
            "research": {"alias": "SYNTHETIC_RESEARCH", "administrator": False},
            "operator": {"alias": "SYNTHETIC_OPERATOR", "administrator": False},
        },
        "installation": {
            "code_root": code_root, "state_root": state_root,
            "code_digest": code_digest, "config_digest": config_digest,
            "inheritance": "PROTECTED_EXPLICIT_ACL",
            "reparse_policy": "REJECT_AT_DEPLOYMENT", "reparse_observed": "NOT_CHECKED",
            "actual_sid_mapping": "PENDING_PRIVATE_ADMIN_MANIFEST",
            "installed_bytes_observed": "NOT_CHECKED",
        },
        "permission_matrix": MATRIX, "channel": CHANNEL,
        "approval_protocol": APPROVAL, "lifecycle": LIFECYCLE,
    }))


def validate_deployment_contract(raw):
    """Validate declared synthetic configuration; output cannot enable anything."""
    canonical_json(raw)
    _exact(raw, ("schema", "source", "principals", "installation", "permission_matrix",
                 "channel", "approval_protocol", "lifecycle"))
    require(raw["schema"] == SCHEMA and raw["source"] == "SYNTHETIC_DEPLOYMENT_REVIEW",
            "DEPLOYMENT_SOURCE_NOT_SYNTHETIC")
    principals = raw["principals"]
    _exact(principals, ("research", "operator"))
    for principal in principals.values():
        _exact(principal, ("alias", "administrator"))
        require(type(principal["alias"]) is str and re.fullmatch(
            r"SYNTHETIC_[A-Z][A-Z0-9_]{0,31}", principal["alias"]) is not None,
            "SYNTHETIC_PRINCIPAL_REQUIRED")
        require(principal["administrator"] is False, "NONADMIN_PRINCIPALS_REQUIRED")
    require(principals["research"]["alias"] != principals["operator"]["alias"],
            "DISTINCT_PRINCIPALS_REQUIRED")
    installation = raw["installation"]
    _exact(installation, ("code_root", "state_root", "code_digest", "config_digest",
                         "inheritance", "reparse_policy", "reparse_observed",
                         "actual_sid_mapping", "installed_bytes_observed"))
    code_path = PureWindowsPath(_path(installation["code_root"]))
    state_path = PureWindowsPath(_path(installation["state_root"]))
    require(code_path.parts[1:] == ("program files", "gdcae operator")
            and state_path.parts[1:] == ("programdata", "gdcae operator")
            and code_path.drive == state_path.drive,
            "PROTECTED_ROOT_DECLARATION_REQUIRED")
    for name in ("code_digest", "config_digest"):
        _digest(installation[name])
    require(installation["inheritance"] == "PROTECTED_EXPLICIT_ACL"
            and installation["reparse_policy"] == "REJECT_AT_DEPLOYMENT",
            "PROTECTED_LAYOUT_REQUIRED")
    require(installation["reparse_observed"] == "NOT_CHECKED"
            and installation["installed_bytes_observed"] == "NOT_CHECKED"
            and installation["actual_sid_mapping"] == "PENDING_PRIVATE_ADMIN_MANIFEST",
            "UNVERIFIED_HOST_CLAIM")
    _same(raw["permission_matrix"], MATRIX, "UNSAFE_PERMISSION_MATRIX")
    _same(raw["channel"], CHANNEL, "UNSAFE_REQUEST_CHANNEL")
    _same(raw["approval_protocol"], APPROVAL, "UNSAFE_APPROVAL_PROTOCOL")
    _same(raw["lifecycle"], LIFECYCLE, "UNSAFE_OPERATOR_LIFECYCLE")
    return {
        "schema": "g3-operator-deployment-review-result-v1",
        "contract_digest": digest_bytes(canonical_json(raw)),
        "HIL_PROTOCOL": "PASS_OFFLINE", "source": "SYNTHETIC_DEPLOYMENT_REVIEW",
        "HIL_OS_ENFORCEMENT": "BLOCKED_HIL_DEPLOYMENT",
        "host_identity_verified": False, "installed_code_verified": False,
        "deployment_authorized": False, "real_grant_issued": False,
        "execution_authorized": False,
    }
