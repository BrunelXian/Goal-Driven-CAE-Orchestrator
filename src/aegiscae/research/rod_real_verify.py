"""Independent checking of the original AF owner-record acquisition envelope.

This consumes the public acquisition, not AF parser PASS. The unqualified local
transport cannot authenticate a Solver or Operator, so no fixture or caller field
can promote V2/V3. Receipt/Run/event versions are original, not D3's fixed revision.
"""

import copy
from pathlib import PureWindowsPath
import re

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research.rod_evidence import af_digest, opaque
from aegiscae.research.rod_preview_dat import verify_dat
from aegiscae.research.rod_preview_rules import BASELINE, PROFILE, exact, sha, token
from aegiscae.research.rod_real_project import BACKEND, NUMERICAL_POLICY, PIN_FIELDS, RESOURCES

SCHEMA = "af-rod-owner-evidence-v1"
EVENTS = ("REQUEST_ACCEPTED", "START_INTENT", "STANDARD_LAUNCH_INTENT", "STANDARD_CREATED",
          "STANDARD_MANAGED_COMPLETED", "STANDARD_RESULT_RECORDED")
READ_LIMITS = {"dat_bytes": 16384, "events": 64, "dat_lines": 512,
               "normalized_line_characters": 1024, "hex_chunks": 32,
               "hex_chunk_characters": 1024}


def _preflight_path(raw):
    require(type(raw) is str and 0 < len(raw) <= 512
            and not any(c in raw for c in '\x00\r\n%!?&|<>^"'), "A_PREFLIGHT_PATH_INVALID")
    path = PureWindowsPath(raw)
    require(path.is_absolute() and re.fullmatch(r"[A-Za-z]:", path.drive) is not None
            and not any(part in (".", "..") for part in re.split(r"[\\/]", raw))
            and all(part not in (".", "..") and not part.endswith((" ", "."))
                    and ":" not in part and not PureWindowsPath(part).is_reserved()
                    for part in path.parts[1:])
            and not path.is_reserved(), "A_PREFLIGHT_PATH_INVALID")
    return path


def verify_a_preflight(preflight, candidate, binding):
    """Check the public preflight snapshot; this cannot authenticate an Operator.

    No filesystem read or AF private-store access. Live server-side revalidation
    remains necessary before future human approval and original AF dispatch.
    """
    exact(binding, PIN_FIELDS)
    for key in ("project_id", "project_instance_id", "plan_id", "request_key", "request_nonce"):
        token(binding[key])
    for key in ("plan_digest", "input_digest", "resources_digest", "output_identity",
                "candidate_output_identity"):
        sha(binding[key])
    require(candidate["step"] == "A" and candidate["load_n"] == "1"
            and binding["backend_id"] == BACKEND
            and binding["input_digest"] == candidate["input_digest"]
            and binding["candidate_output_identity"] == candidate["output_identity"]
            and binding["resources_digest"] == af_digest(RESOURCES), "A_PREFLIGHT_BINDING_MISMATCH")
    exact(preflight, ("schema", "status", "project_id", "project_instance_id", "plan_id",
        "plan_digest", "research_contract", "resources", "input_path", "load_n",
        "runtime_binding_digest", "engineering", "scratch", "output_key", "expires_at",
        "gate_version", "declared_outputs", "execution_authorized", "host_qualification",
        "operator_deployment", "real_a_output", "source_authentication"))
    require(preflight["schema"] == "af-rod-preflight-v1"
            and preflight["status"] == "PRECONDITIONS_CHECKED"
            and preflight["execution_authorized"] is False
            and preflight["host_qualification"] == preflight["operator_deployment"]
            == preflight["source_authentication"] == "NOT_VERIFIED"
            and preflight["real_a_output"] == "NOT_PRODUCED", "A_PREFLIGHT_NOT_AUTHORITY")
    require(all(preflight[k] == binding[k] for k in
                ("project_id", "project_instance_id", "plan_id", "plan_digest"))
            and preflight["output_key"] == binding["output_identity"], "A_PREFLIGHT_BINDING_MISMATCH")
    expected = {"research_project_id": candidate["research_project_id"],
        "contract_digest": candidate["contract_digest"], "research_revision": candidate["admitted_revision"],
        "candidate_id": candidate["candidate_id"], "request_nonce": binding["request_nonce"],
        "input_digest": candidate["input_digest"]}
    require(canonical_json(preflight["research_contract"]) == canonical_json(expected)
            and preflight["load_n"] == candidate["load_n"], "A_PREFLIGHT_RESEARCH_MISMATCH")
    require(canonical_json(preflight["resources"]) == canonical_json(RESOURCES),
            "A_PREFLIGHT_RESOURCES_MISMATCH")
    sha(preflight["runtime_binding_digest"])
    _positive(preflight["expires_at"])
    require(type(preflight["gate_version"]) is int and 0 <= preflight["gate_version"] < 2**63,
            "A_PREFLIGHT_GATE_INVALID")
    root = _preflight_path(preflight["engineering"])
    require(_preflight_path(preflight["input_path"]) == root / "axial_bar.inp"
            and _preflight_path(preflight["scratch"]) == root / "scratch", "A_PREFLIGHT_PATH_INVALID")
    outputs = preflight["declared_outputs"]
    require(type(outputs) is list and len(outputs) == 3, "A_PREFLIGHT_OUTPUTS_INVALID")
    job = None
    for output, extension in zip(outputs, ("dat", "sta", "msg"), strict=True):
        exact(output, ("logical_ref", "path", "binding"))
        path = _preflight_path(output["path"])
        require(output["logical_ref"] == "output:" + extension
                and output["binding"] == "ORIGINAL_RUN_ATTEMPT_INTENT_AND_COLLECTOR_DIGEST"
                and path.parent == root and path.suffix == "." + extension
                and re.fullmatch(r"rod_[a-f0-9]{32}", path.stem) is not None,
                "A_PREFLIGHT_OUTPUTS_INVALID")
        job = path.stem if job is None else job
        require(path.stem == job, "A_PREFLIGHT_OUTPUTS_INVALID")
    require(preflight["output_key"] == af_digest({"cwd": preflight["engineering"].casefold(),
                                                 "job": job}), "A_PREFLIGHT_OUTPUTS_INVALID")
    return {"status": "CONSISTENCY_CHECKED_NOT_AUTHORITY",
            "preflight_digest": digest_bytes(canonical_json(preflight)),
            "execution_authorized": False}


def _positive(value):
    require(type(value) is int and 0 < value < 2**63, "OWNER_SEQUENCE_INVALID")


def verify_owner_evidence(envelope, candidate, binding):
    # This verifier is also a public pure entry point. Do not rely solely on a
    # prior Project reservation having validated its caller-supplied references.
    exact(binding, PIN_FIELDS)
    for key in ("project_id", "project_instance_id", "plan_id", "request_key", "request_nonce"):
        token(binding[key])
    for key in ("plan_digest", "input_digest", "resources_digest", "output_identity",
                "candidate_output_identity"):
        sha(binding[key])
    require(binding["backend_id"] == BACKEND
            and binding["input_digest"] == candidate["input_digest"]
            and binding["candidate_output_identity"] == candidate["output_identity"]
            and binding["resources_digest"] == af_digest(RESOURCES), "OWNER_EXPECTED_BINDING_MISMATCH")
    require(canonical_json(candidate["verification_policy"]) == canonical_json(NUMERICAL_POLICY),
            "REAL_VERIFICATION_POLICY_CHANGED")
    exact(envelope, ("schema", "source", "source_authentication", "collector_version", "collected_at",
        "acquired_at", "plan", "receipt", "run", "events", "artifact", "validation_ref", "V2", "V3", "V4", "ODB"))
    require(envelope["schema"] == SCHEMA and envelope["source"] == "AF_OWNER_RECORD_CHAIN"
            and envelope["source_authentication"] == "NOT_VERIFIED"
            and envelope["collector_version"] == "rod-owner-collector-v1"
            and (envelope["V2"], envelope["V3"], envelope["V4"], envelope["ODB"])
            == ("NOT_VERIFIED", "INCONCLUSIVE", "NOT_ASSESSED", "NOT_VERIFIED"), "OWNER_SOURCE_UNQUALIFIED")
    _positive(envelope["collected_at"])
    _positive(envelope["acquired_at"])
    require(envelope["collected_at"] <= envelope["acquired_at"], "OWNER_COLLECTION_TIME_INVALID")
    opaque(envelope["validation_ref"])
    plan, receipt, run, artifact = (envelope[k] for k in ("plan", "receipt", "run", "artifact"))
    exact(plan, ("plan_id", "plan_digest", "backend_id", "backend_version", "project_id", "project_instance_id",
                 "resources", "output_key", "rod_contract", "validation_policy"))
    exact(receipt, ("request_id", "request_digest", "idempotency_key", "run_id", "accepted_sequence"))
    exact(run, ("run_id", "project_id", "project_instance_id", "plan_id", "plan_digest", "grant_id",
                "phase_attempt_id", "phase", "revision", "simulation", "execution", "backend_outcome",
                "reconciliation", "managed_completion"))
    exact(artifact, ("logical_ref", "dat_bytes", "sha256", "size", "input_digest", "step", "increment", "units"))
    require(plan["backend_id"] == BACKEND and type(plan["backend_version"]) is int and plan["backend_version"] == 1
            and plan["validation_policy"] == "axial-rod-owner-dat-v1"
            and plan["resources"] == RESOURCES and all(type(v) is int for v in plan["resources"].values())
            and af_digest(plan["resources"]) == binding["resources_digest"]
            and plan["output_key"] == binding["output_identity"], "OWNER_PLAN_MISMATCH")
    for key in ("plan_id", "plan_digest", "project_instance_id"):
        require(plan[key] == run[key] == binding[key], "OWNER_PLAN_MISMATCH")
    require(plan["project_id"] == run["project_id"] == binding["project_id"], "OWNER_PROJECT_MISMATCH")
    require(receipt["idempotency_key"] == binding["request_key"] and receipt["run_id"] == run["run_id"],
            "OWNER_RECEIPT_MISMATCH")
    for key in ("request_id", "idempotency_key", "run_id"):
        opaque(receipt[key])
    for key in ("run_id", "project_id", "project_instance_id", "plan_id", "grant_id", "phase_attempt_id"):
        opaque(run[key])
    sha(receipt["request_digest"])
    _positive(receipt["accepted_sequence"])
    _positive(run["revision"])
    require(run["phase"] == "STANDARD_ANALYSIS" and run["simulation"] is False
            and run["execution"] == "FINISHED" and run["backend_outcome"] == "COMPLETED"
            and run["reconciliation"] == "NONE" and run["managed_completion"] == "COMMITTED_EMPTY_SCOPE",
            "OWNER_EXECUTION_UNRESOLVED")
    contract = plan["rod_contract"]
    exact(contract, ("research_project_id", "contract_digest", "research_revision", "candidate_id",
                     "request_nonce", "phase", "candidate"))
    require(contract["research_project_id"] == candidate["research_project_id"]
            and contract["contract_digest"] == candidate["contract_digest"]
            and type(contract["research_revision"]) is int and contract["research_revision"] == candidate["admitted_revision"]
            and contract["candidate_id"] == candidate["candidate_id"] and contract["phase"] == candidate["step"]
            and contract["request_nonce"] == binding["request_nonce"], "OWNER_RESEARCH_MISMATCH")
    expected = {"profile": PROFILE, "schema": "rod-candidate-v1", "baseline_digest": BASELINE,
        "input_digest": candidate["input_digest"], "load_n": candidate["load_n"], "unit": "N",
        "minimum_n": "0.5", "maximum_n": "2.5", "mutable_entity": {"keyword": "CLOAD", "node": 2, "dof": 1},
        "dimensions": {"length_mm": "10", "area_mm2": "1", "modulus_mpa": "1000"}}
    expected["candidate_digest"] = af_digest(expected)
    require(canonical_json(contract["candidate"]) == canonical_json(expected), "OWNER_CANDIDATE_MISMATCH")
    events = envelope["events"]
    require(type(events) is list and 6 <= len(events) <= READ_LIMITS["events"], "OWNER_HISTORY_INCOMPLETE")
    previous_project, previous_run, kinds = 0, 0, []
    for event in events:
        exact(event, ("type", "project_sequence", "run_sequence", "run_id"))
        _positive(event["project_sequence"])
        _positive(event["run_sequence"])
        require(event["project_sequence"] > previous_project and event["run_sequence"] == previous_run + 1
                and event["run_id"] == run["run_id"] and type(event["type"]) is str, "OWNER_HISTORY_MISMATCH")
        previous_project, previous_run = event["project_sequence"], event["run_sequence"]
        kinds.append(event["type"])
    require(all(kinds.count(kind) == 1 for kind in EVENTS), "OWNER_HISTORY_INCOMPLETE")
    positions = [kinds.index(kind) for kind in EVENTS]
    require(positions == sorted(positions)
            and events[positions[0]]["project_sequence"] == receipt["accepted_sequence"], "OWNER_CAUSAL_ORDER")
    data = artifact["dat_bytes"]
    require(type(data) is bytes and type(artifact["size"]) is int
            and 0 < len(data) == artifact["size"] <= READ_LIMITS["dat_bytes"]
            and artifact["sha256"] == digest_bytes(data) and artifact["input_digest"] == candidate["input_digest"]
            == binding["input_digest"], "OWNER_ARTIFACT_MISMATCH")
    require(artifact["logical_ref"] == "output:dat" and type(artifact["step"]) is int
            and type(artifact["increment"]) is int and artifact["step"] == artifact["increment"] == 1
            and artifact["units"] == {"length": "mm", "force": "N", "stress": "MPa"}, "OWNER_UNITS_OR_SELECTOR")
    metrics = verify_dat(data, candidate["load_n"], candidate["verification_policy"])
    return {"schema": "gdcae-owner-independent-check-v1", "source_authentication": "NOT_VERIFIED",
            "V0": "RECORD_CHAIN_CHECKED_UNAUTHENTICATED", "V1": "MODEL_CONTRACT_CHECKED",
            "V2": "NOT_VERIFIED", "V3": "INCONCLUSIVE", "V4": "NOT_ASSESSED", "ODB": "NOT_VERIFIED",
            "numerical_bytes_check": "PASS", "metrics": metrics,
            "run_id": run["run_id"], "receipt_id": receipt["request_id"], "phase_attempt_id": run["phase_attempt_id"],
            "output_digest": artifact["sha256"], "plan_digest": plan["plan_digest"],
            "causal_records_digest": af_digest({"receipt": receipt, "run": run, "events": events}),
            "execution_authorized": False, "real_goal": "INCONCLUSIVE"}


def verify_owner_artifact_set(envelope, candidate, binding):
    """Check bounded DAT/STA/MSG bytes against the original acquisition records.

    This additive public schema leaves the v1 observation format unchanged. It
    checks supplied records, not OS handles or the identity of their publisher;
    matching hashes and timestamps cannot authenticate Solver provenance.
    """
    exact(envelope, ("schema", "source", "source_authentication", "owner_evidence",
                     "launch_intent", "artifacts"))
    require(envelope["schema"] == "af-rod-owner-artifact-set-v1"
            and envelope["source"] == "AF_OWNER_RECORD_CHAIN"
            and envelope["source_authentication"] == "NOT_VERIFIED", "OWNER_SOURCE_UNQUALIFIED")
    base = envelope["owner_evidence"]
    result = verify_owner_evidence(base, candidate, binding)
    run, intent = base["run"], envelope["launch_intent"]
    exact(intent, ("run_id", "plan_digest", "phase_attempt_id", "project_instance_id",
                   "output_key", "owner_id", "intent_at_ns", "state"))
    require(all(intent[k] == run[k] for k in
                ("run_id", "plan_digest", "phase_attempt_id", "project_instance_id"))
            and intent["output_key"] == base["plan"]["output_key"]
            and intent["state"] == "START_INTENT", "OWNER_LAUNCH_INTENT_MISMATCH")
    opaque(intent["owner_id"])
    _positive(intent["intent_at_ns"])
    artifacts = envelope["artifacts"]
    require(type(artifacts) is list and len(artifacts) == 3, "OWNER_ARTIFACT_SET_INCOMPLETE")
    payloads, summaries = {}, {}
    for artifact in artifacts:
        exact(artifact, ("logical_ref", "bytes", "sha256", "size", "run_id",
                         "phase_attempt_id", "project_instance_id", "plan_digest",
                         "input_digest", "collected_record"))
        ref, raw, record = artifact["logical_ref"], artifact["bytes"], artifact["collected_record"]
        require(type(ref) is str and ref in ("output:dat", "output:sta", "output:msg")
                and ref not in payloads, "OWNER_ARTIFACT_SET_INCOMPLETE")
        require(all(artifact[k] == run[k] for k in
                    ("run_id", "phase_attempt_id", "project_instance_id", "plan_digest"))
                and artifact["input_digest"] == binding["input_digest"], "OWNER_ARTIFACT_IDENTITY_MISMATCH")
        require(type(raw) is bytes and type(artifact["size"]) is int
                and 0 < len(raw) == artifact["size"] <= 1048576
                and artifact["sha256"] == digest_bytes(raw), "OWNER_ARTIFACT_MISMATCH")
        exact(record, ("logical_ref", "digest", "size", "device", "inode", "mtime_ns", "read_at"))
        require(record["logical_ref"] == ref and record["digest"] == artifact["sha256"]
                and type(record["size"]) is int and record["size"] == len(raw)
                and all(type(record[k]) is int and 0 <= record[k] < 2**128
                        for k in ("device", "inode")), "OWNER_COLLECTOR_MISMATCH")
        _positive(record["mtime_ns"])
        _positive(record["read_at"])
        require(intent["intent_at_ns"] <= record["mtime_ns"]
                < (record["read_at"] + 1) * 1_000_000_000
                and record["read_at"] <= base["acquired_at"], "OWNER_COLLECTION_TIME_INVALID")
        payloads[ref] = raw
        summaries[ref] = {k: v for k, v in artifact.items() if k != "bytes"}
    dat = base["artifact"]
    require(payloads["output:dat"] == dat["dat_bytes"]
            and summaries["output:dat"]["sha256"] == dat["sha256"]
            and summaries["output:dat"]["size"] == dat["size"]
            and summaries["output:dat"]["collected_record"]["read_at"] == base["collected_at"],
            "OWNER_DAT_ACQUISITION_MISMATCH")
    require(b"THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in payloads["output:sta"]
            and b"THE ANALYSIS HAS BEEN COMPLETED" in payloads["output:msg"]
            and all(b"***ERROR" not in raw for raw in payloads.values())
            and all(b"HAS NOT BEEN COMPLETED" not in raw for raw in payloads.values()),
            "OWNER_COMPLETION_TEXT_UNRESOLVED")
    # Windows file IDs may be 128-bit; canonical research integers are signed
    # 63-bit. Encode only these two validated identities as decimal strings in
    # the digest projection, retaining the original acquisition unmodified.
    projection = copy.deepcopy(summaries)
    for artifact in projection.values():
        for key in ("device", "inode"):
            artifact["collected_record"][key] = str(artifact["collected_record"][key])
    return {**result,
            "artifact_set_check": "RECORDS_AND_COMPLETION_TEXT_CHECKED_UNAUTHENTICATED",
            "artifact_set_digest": digest_bytes(canonical_json({"launch_intent": intent,
                                                                 "artifacts": projection}))}


def observation_record(envelope, candidate, binding):
    result = verify_owner_evidence(envelope, candidate, binding)
    encoded = copy.deepcopy(envelope)
    raw = encoded["artifact"].pop("dat_bytes").hex()
    encoded["artifact"]["dat_hex_chunks"] = [raw[i:i + 1024] for i in range(0, len(raw), 1024)]
    record = {"schema": "rod-owner-observation-v1", "evidence": encoded, "independent": result}
    canonical_json(record)
    return record


def validate_observation_record(record, candidate, binding):
    exact(record, ("schema", "evidence", "independent"))
    require(record["schema"] == "rod-owner-observation-v1", "OWNER_OBSERVATION_INVALID")
    envelope = copy.deepcopy(record["evidence"])
    chunks = envelope["artifact"].pop("dat_hex_chunks")
    require(type(chunks) is list and 0 < len(chunks) <= READ_LIMITS["hex_chunks"]
            and all(type(value) is str and 0 < len(value) <= READ_LIMITS["hex_chunk_characters"]
                    for value in chunks), "OWNER_OBSERVATION_INVALID")
    try:
        envelope["artifact"]["dat_bytes"] = bytes.fromhex("".join(chunks))
    except ValueError:
        require(False, "OWNER_OBSERVATION_INVALID")
    require(canonical_json(record["independent"])
            == canonical_json(verify_owner_evidence(envelope, candidate, binding)), "OWNER_REVIEW_FORGED")
    return record["independent"]
