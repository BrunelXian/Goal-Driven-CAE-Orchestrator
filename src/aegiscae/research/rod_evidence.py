"""Bounded G2 evidence contracts; no file access, AF imports or execution authority.

The public AF reader owns path confinement and stable file acquisition. This
module independently checks the returned bindings and numerical bytes. A Fake
Run transports no rod result: numerical fixtures and Fake execution stay distinct.
"""

import copy
import json
import re
from dataclasses import asdict
from decimal import Decimal

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research.rod_preview_dat import verify_dat
from aegiscae.research.rod_preview_rules import (
    PROFILE, RodPreviewContract, candidate_bytes, decimal, exact, sha, token,
)

PLAN_FIELDS = ("schema", "source", "profile", "project_id", "project_instance_id",
    "plan_id", "plan_digest", "candidate_id", "candidate_digest", "input_digest",
    "input_size", "resources", "resources_digest", "output_identity", "input_path",
    "output_path", "contract_digest", "research_project_id", "research_revision",
    "phase", "expires_at", "load_n", "tolerances", "verification_policy_digest",
    "authorization_state", "execution_authorized")
LINK_FIELDS = ("source", "project_id", "project_instance_id", "plan_id", "plan_digest",
               "run_id", "phase_attempt_id", "receipt_id", "input_digest")
SELECTOR = {"step": 1, "increment": 1, "node": 2, "dof": 1,
            "element": 1, "integration_point": 1}
UNITS = {"displacement": "mm", "stress": "MPa", "reaction": "N"}
FAKE_PLAN_FIELDS = ("schema", "source", "phase", "project_id", "project_instance_id",
                    "plan_id", "plan_digest", "input_digest", "grant_id", "request_key",
                    "output_identity")
REAL_FIELDS = ("schema", "source", "profile", "backend_id", "project_id", "project_instance_id",
    "plan_id", "plan_digest", "candidate_id", "input_digest", "grant_id", "receipt_id", "run_id",
    "phase_attempt_id", "phase", "resources_digest", "output_identity", "output_digest",
    "output_size", "verification_policy_digest", "selector", "units", "solver_exit_code",
    "execution", "reconciliation", "managed_scope", "stable_read")


def _selector(raw):
    require(type(raw) is dict and raw == SELECTOR
            and all(type(value) is int for value in raw.values()), "EVIDENCE_SELECTOR_MISMATCH")


def validate_real_source_contract(record, expected_binding):
    """Future real-source metadata contract, exercised only with original fixtures.

    Matching declarations, hashes and stable-read flags do not authenticate AF,
    Grant consumption, Operator isolation or a Solver. This never enables reads.
    """
    exact(record, REAL_FIELDS)
    exact(expected_binding, REAL_FIELDS)
    canonical_json(record)
    require(record == expected_binding, "REAL_BINDING_MISMATCH")
    require(record["schema"] == "af-real-rod-source-contract-v1"
            and record["source"] in ("TEST_ONLY_REAL_SCHEMA_FIXTURE", "AF_REAL_DECLARATION")
            and record["profile"] == PROFILE
            and record["backend_id"] == "abaqus-standard-rod-preview-v1"
            and record["phase"] in ("A", "B"), "REAL_SCHEMA_MISMATCH")
    for key in ("project_id", "project_instance_id", "plan_id", "candidate_id", "grant_id",
                "receipt_id", "run_id", "phase_attempt_id"):
        opaque(record[key])
    for key in ("plan_digest", "input_digest", "resources_digest", "output_identity",
                "output_digest", "verification_policy_digest"):
        sha(record[key])
    _selector(record["selector"])
    require(record["units"] == UNITS and type(record["output_size"]) is int
            and 0 < record["output_size"] <= 1048576
            and type(record["solver_exit_code"]) is int and record["solver_exit_code"] == 0
            and record["execution"] == "FINISHED" and record["reconciliation"] == "NONE"
            and record["managed_scope"] == "COMMITTED_EMPTY_SCOPE"
            and record["stable_read"] is True, "REAL_STATUS_UNCONFIRMED")
    return {"schema_valid": True, "source_authentication": "NOT_VERIFIED",
            "V2": "NOT_VERIFIED", "live_read_enabled": False,
            "execution_authorized": False, "ODB": "ODB_NOT_VERIFIED", "V4": "NOT_ASSESSED"}


def af_digest(value):
    """AF's documented UTF-8 canonical JSON, after local bounded type validation."""
    canonical_json(value)
    return digest_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                  separators=(",", ":"), allow_nan=False).encode("utf-8"))


def check_fake_plan(raw, step):
    exact(raw, FAKE_PLAN_FIELDS)
    require(raw["schema"] == "af-fake-plan-ref-v1" and raw["source"] == "FAKE_TEST_ONLY"
            and raw["phase"] == step, "FAKE_SOURCE_REQUIRED")
    for key in ("project_id", "project_instance_id", "plan_id", "grant_id", "request_key"):
        opaque(raw[key])
    for key in ("plan_digest", "input_digest", "output_identity"):
        sha(raw[key])
    return copy.deepcopy(raw)


def check_fake_evidence(raw, expected_plan):
    """Check immutable raw IPC receipt/run/event/validation relationships."""
    exact(raw, ("schema", "source", "phase", "project_directory", "plan_ref", "binding",
                "receipt", "run", "events", "validations", "real_solver_executed",
                "all_owned_processes_exited", "owned_process_count", "normal_exit",
                "raw_handle_proof", "runtime_origin"))
    canonical_json(raw)
    require(raw["schema"] == "af-fake-evidence-v1" and raw["source"] == "FAKE_TEST_ONLY"
            and raw["phase"] == expected_plan["phase"] and raw["plan_ref"] == expected_plan
            and raw["real_solver_executed"] is False
            and raw["all_owned_processes_exited"] is True and raw["normal_exit"] is True
            and type(raw["owned_process_count"]) is int and raw["owned_process_count"] == 1,
            "FAKE_LIFECYCLE_UNCONFIRMED")
    origin = raw["runtime_origin"]
    exact(origin, ("schema", "scope", "package_path", "service_path", "supervisor_path"))
    require(origin["schema"] == "af-g2-runtime-origin-v1" and origin["scope"] == "FAKE_TEST_ONLY",
            "FAKE_ORIGIN_MISMATCH")
    for key in ("package_path", "service_path", "supervisor_path"):
        require(type(origin[key]) is str and 0 < len(origin[key]) <= 1024
                and not any(c in origin[key] for c in "\x00\n\r"), "FAKE_ORIGIN_MISMATCH")
    package = origin["package_path"].replace("\\", "/").rstrip("/")
    require(origin["service_path"].replace("\\", "/") == package + "/execution/service.py"
            and origin["supervisor_path"].replace("\\", "/") == package + "/execution/supervisor.py",
            "FAKE_ORIGIN_MISMATCH")
    link = check_fake_link(raw["binding"])
    require(all(link[k] == expected_plan[k] for k in ("project_id", "project_instance_id",
            "plan_id", "plan_digest", "input_digest")), "FAKE_PLAN_MISMATCH")
    receipt, run = raw["receipt"], raw["run"]
    require(type(receipt) is dict and type(run) is dict, "FAKE_EVIDENCE_INVALID")
    require(receipt.get("request_id") == link["receipt_id"]
            and receipt.get("idempotency_key") == expected_plan["request_key"]
            and receipt.get("run_id") == link["run_id"]
            and receipt.get("request_status") == "ACCEPTED", "FAKE_RECEIPT_MISMATCH")
    require(all(run.get(k) == link[k] for k in ("project_id", "project_instance_id",
            "plan_id", "plan_digest", "run_id", "phase_attempt_id"))
            and run.get("grant_id") == expected_plan["grant_id"]
            and type(run.get("attempt_no")) is int and run["attempt_no"] == 1
            and run.get("retry_of") is None and run.get("backend_id") == "fake-v1"
            and run.get("simulation") is True and run.get("solver_conclusion") == "NOT_RUN"
            and run.get("phase") == "FAKE" and run.get("backend_outcome") == "COMPLETED"
            and run.get("execution") == "FINISHED" and run.get("artifact_validation") == "VALID"
            and run.get("reconciliation") == "NONE", "FAKE_RUN_MISMATCH")
    validations, events = raw["validations"], raw["events"]
    require(type(validations) is list and len(validations) == 1 and type(validations[0]) is dict,
            "FAKE_VALIDATION_MISSING")
    validation = validations[0]
    require(validation.get("run_id") == link["run_id"]
            and validation.get("phase_attempt_id") == link["phase_attempt_id"]
            and validation.get("scope") == "simulation"
            and validation.get("policy_id") == "fake-result-v1"
            and validation.get("verdict") == "PASS", "FAKE_VALIDATION_MISMATCH")
    require(type(events) is list and 4 <= len(events) <= 64
            and all(type(e) is dict and e.get("run_id") == link["run_id"]
                    and type(e.get("project_sequence")) is int for e in events),
            "FAKE_EVENTS_MISMATCH")
    sequences = [e["project_sequence"] for e in events]
    require(sequences == sorted(set(sequences)) and sequences[0] > 0,
            "FAKE_EVENTS_MISMATCH")
    accepted = [e for e in events if e.get("type") == "REQUEST_ACCEPTED"]
    started = [e for e in events if e.get("type") == "START_INTENT"]
    produced = [e for e in events if e.get("type") == "FAKE_COMPLETED"]
    completed = [e for e in events if e.get("type") == "VALIDATION_RECORDED"]
    require(len(accepted) == len(started) == len(produced) == len(completed) == 1
            and accepted[0]["project_sequence"] == receipt.get("accepted_sequence")
            and accepted[0]["project_sequence"] < started[0]["project_sequence"]
            < produced[0]["project_sequence"] < completed[0]["project_sequence"],
            "FAKE_EVENTS_MISMATCH")
    return {"binding": link, "receipt_digest": af_digest(receipt),
            "raw_evidence_digest": af_digest(raw), "source": "FAKE_TEST_ONLY",
            "runtime_origin_digest": af_digest(origin),
            "real_solver_executed": False, "all_owned_processes_exited": True}


def opaque(value):
    require(type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value),
            "INVALID_AF_ID")
    return value


def tolerances(contract):
    return {"displacement_mm": contract.displacement_tolerance_mm,
            "stress_mpa": contract.stress_tolerance_mpa,
            "reaction_n": contract.reaction_tolerance_n,
            # Match the already-frozen profile and the existing independent oracle.
            "balance_n": format(decimal(contract.reaction_tolerance_n) * 2, "f"),
            "zero_mm": "0.00000001"}


def check_plan_ref(raw, *, candidate, contract, research_project_id, research_revision):
    """Validate an exact public persisted Plan projection, never a Grant."""
    exact(raw, PLAN_FIELDS)
    contract = RodPreviewContract.from_dict(asdict(contract))
    require(raw["schema"] == "af-rod-plan-ref-v1" and raw["source"] == "INERT_ROD_PLAN"
            and raw["profile"] == PROFILE and raw["phase"] == "A"
            and raw["authorization_state"] == "NOT_AUTHORIZED"
            and raw["execution_authorized"] is False, "INERT_PLAN_REQUIRED")
    for key in ("project_id", "project_instance_id", "plan_id"):
        opaque(raw[key])
    for key in ("plan_digest", "candidate_digest", "input_digest", "resources_digest",
                "output_identity", "verification_policy_digest"):
        sha(raw[key])
    body = candidate_bytes(candidate["load_n"], contract)
    require(raw["research_project_id"] == research_project_id
            and raw["contract_digest"] == contract.digest()
            and type(raw["research_revision"]) is int
            and raw["research_revision"] == research_revision
            and raw["candidate_id"] == candidate["candidate_id"]
            and raw["input_digest"] == candidate["input_digest"] == digest_bytes(body)
            and type(raw["input_size"]) is int and raw["input_size"] == len(body)
            and decimal(raw["load_n"]) == decimal(candidate["load_n"]),
            "PLAN_CANDIDATE_MISMATCH")
    require(type(raw["expires_at"]) is int and raw["expires_at"] > 0,
            "PLAN_EXPIRY_INVALID")
    for key in ("input_path", "output_path"):
        require(type(raw[key]) is str and 0 < len(raw[key]) <= 1024
                and not any(c in raw[key] for c in "\x00\n\r"), "INVALID_PLAN_PATH")
    require(type(raw["resources"]) is dict
            and digest_bytes(canonical_json(raw["resources"])) == raw["resources_digest"]
            and raw["tolerances"] == tolerances(contract)
            and digest_bytes(canonical_json(raw["tolerances"])) == raw["verification_policy_digest"],
            "PLAN_POLICY_MISMATCH")
    return copy.deepcopy(raw)


def check_fake_link(raw):
    exact(raw, LINK_FIELDS)
    require(raw["source"] == "FAKE_TEST_ONLY", "FAKE_SOURCE_REQUIRED")
    for key in set(LINK_FIELDS) - {"source", "plan_digest", "input_digest"}:
        opaque(raw[key])
    sha(raw["plan_digest"])
    sha(raw["input_digest"])
    return copy.deepcopy(raw)


def seal_envelope(raw):
    """Convert bounded acquired bytes to persistent deterministic data, not LLM text."""
    require(type(raw) is dict and "dat_bytes" in raw and "dat_hex_chunks" not in raw,
            "INVALID_EVIDENCE_ENVELOPE")
    data = raw["dat_bytes"]
    require(type(data) is bytes and 0 < len(data) <= 16384, "DAT_LIMIT")
    result = copy.deepcopy({k: v for k, v in raw.items() if k != "dat_bytes"})
    hexadecimal = data.hex()
    result["dat_hex_chunks"] = [hexadecimal[i:i + 1024]
                               for i in range(0, len(hexadecimal), 1024)]
    return result


def verify_envelope(raw, *, expected_plan, expected_link, candidate, contract):
    """Recompute a versioned record. No source label can establish real V2."""
    exact(raw, ("schema", "source", "evidence_key", "plan_ref", "plan_ref_digest",
                "artifact", "execution_link", "real_solver_executed",
                "real_solver_status", "dat_hex_chunks"))
    contract = RodPreviewContract.from_dict(asdict(contract))
    require(raw["source"] == "SYNTHETIC_DAT"
            and raw["real_solver_executed"] is False
            and raw["real_solver_status"] == "NOT_RUN", "REAL_SOURCE_UNQUALIFIED")
    token(raw["evidence_key"])
    require(raw["plan_ref"] == expected_plan
            and raw["plan_ref_digest"] == af_digest(expected_plan),
            "EVIDENCE_PLAN_MISMATCH")
    require(raw["execution_link"] == expected_link, "EVIDENCE_EXECUTION_MISMATCH")
    check_fake_link(expected_link)
    if expected_plan["source"] == "INERT_ROD_PLAN":
        require(raw["schema"] == "af-rod-evidence-envelope-v1", "INVALID_EVIDENCE_ENVELOPE")
        require(expected_link["project_instance_id"] != expected_plan["project_instance_id"]
                and expected_link["plan_id"] != expected_plan["plan_id"],
                "FAKE_ROD_IDENTITY_CONFUSION")
    else:
        require(expected_plan["source"] == "SYNTHETIC_NOT_REGISTERED"
                and expected_plan["phase"] == "B"
                and raw["schema"] == "gdcae-synthetic-evidence-envelope-v1", "INVALID_NUMERIC_REFERENCE")
    artifact = raw["artifact"]
    exact(artifact, ("filename", "output_identity", "output_digest", "size", "stable_read",
                     "selector", "units"))
    acquired = expected_plan["source"] == "INERT_ROD_PLAN"
    _selector(artifact["selector"])
    require(artifact["filename"] == "synthetic.dat" and artifact["stable_read"] is acquired
            and artifact["output_identity"] == expected_plan["output_identity"]
            and artifact["selector"] == SELECTOR and artifact["units"] == UNITS,
            "EVIDENCE_ARTIFACT_MISMATCH")
    chunks = raw["dat_hex_chunks"]
    require(type(chunks) is list and 1 <= len(chunks) <= 32
            and all(type(c) is str and 0 < len(c) <= 1024 and len(c) % 2 == 0
                    and re.fullmatch(r"[0-9a-f]+", c) for c in chunks), "DAT_LIMIT")
    data = bytes.fromhex("".join(chunks))
    require(type(artifact["size"]) is int and artifact["size"] == len(data)
            and artifact["output_digest"] == digest_bytes(data), "EVIDENCE_BYTES_MISMATCH")
    metric = verify_dat(data, candidate["load_n"], asdict(contract))
    goal = "SATISFIED" if decimal(contract.goal_min_mm) <= Decimal(metric["displacement_mm"]) \
        <= decimal(contract.goal_max_mm) else "NOT_SATISFIED"
    return {"schema": "gdcae-rod-verification-v2", "source": "SYNTHETIC_DAT",
            "V0": "NOT_VERIFIED", "V1": "MODEL_CONTRACT_CHECKED", "V2": "NOT_VERIFIED",
            "V3": "INCONCLUSIVE", "V4": "NOT_ASSESSED", "ODB": "ODB_NOT_VERIFIED",
            "fixture_checks": {"provenance": "PASS", "numerical": "PASS", "goal": goal},
            "metrics": metric, "envelope_digest": digest_bytes(canonical_json(raw)),
            "plan_ref_digest": raw["plan_ref_digest"],
            "execution_link_digest": digest_bytes(canonical_json(expected_link)),
            "output_digest": artifact["output_digest"], "contract_digest": contract.digest(),
            "artifact_acquisition": "AF_PUBLIC_STABLE_READ" if acquired else "SYNTHETIC_BYTES_ONLY",
            "real_solver_calls": 0, "real_goal": "INCONCLUSIVE",
            "human_approval": "NOT_ESTABLISHED", "execution_authorized": False}
