"""Read-only, prospective real rod evidence contract. No live source is registered.

This checks schema, causal relationships and numerical bytes independently of AF.
Neither an AF_REAL label, a digest, nor a successful offline check authenticates
acquisition. Existing frozen OFFLINE_AF_SUBSTITUTE contracts remain unchanged.
"""

import copy
from dataclasses import asdict
from decimal import Decimal

from aegiscae.contracts.research_contracts import digest_bytes, require
from aegiscae.research.rod_evidence import SELECTOR, UNITS, af_digest, opaque, tolerances
from aegiscae.research.rod_preview import RealPreviewAdapter
from aegiscae.research.rod_preview_dat import verify_dat
from aegiscae.research.rod_preview_rules import (
    PROFILE, RodPreviewContract, candidate_bytes, decimal, exact, sha,
)
from aegiscae.research.rod_public_evidence import PublicRodEvidence

BACKEND = "abaqus-standard-rod-preview-v1"
PLAN_FIELDS = ("schema", "profile", "backend_id", "project_id", "project_instance_id",
    "plan_id", "plan_digest", "candidate_id", "input_digest", "input_size",
    "resources_digest", "output_identity", "contract_digest", "research_project_id",
    "research_revision", "phase", "load_n", "verification_policy_digest")
RECEIPT_FIELDS = ("request_id", "idempotency_key", "project_id", "project_instance_id",
    "plan_id", "plan_digest", "run_id", "grant_id", "request_status", "accepted_sequence")
RUN_FIELDS = ("run_id", "project_id", "project_instance_id", "plan_id", "plan_digest",
    "grant_id", "phase_attempt_id", "backend_id", "phase", "attempt_no", "retry_of",
    "simulation", "execution", "reconciliation", "backend_outcome", "solver_exit_code",
    "input_digest", "output_identity", "revision", "managed_scope")
ARTIFACT_FIELDS = ("filename", "dat_bytes", "size", "sha256", "run_id", "phase_attempt_id",
    "input_digest", "output_identity", "selector", "units", "stable_read")


def bundle_digest(bundle):
    """Checksum only; the separately checked digest binds the omitted byte payload."""
    projection = {key: value for key, value in bundle.items() if key != "bindings_digest"}
    projection["artifact"] = {key: value for key, value in bundle["artifact"].items()
                              if key != "dat_bytes"}
    return af_digest(projection)


def _positive(value):
    require(type(value) is int and 0 < value <= 1000000000, "REAL_SEQUENCE_INVALID")


def _records(bundle, expected_plan):
    exact(bundle, ("schema", "source", "plan", "receipt", "run", "events", "artifact",
                   "bindings_digest"))
    require(bundle["schema"] == "af-rod-real-evidence-v1"
            and bundle["source"] in ("OFFLINE_REAL_SCHEMA_FIXTURE", "AF_REAL_DECLARATION"),
            "REAL_SOURCE_SCHEMA_INVALID")
    plan, receipt, run, artifact = (bundle[key] for key in ("plan", "receipt", "run", "artifact"))
    exact(plan, PLAN_FIELDS)
    exact(expected_plan, PLAN_FIELDS)
    exact(receipt, RECEIPT_FIELDS)
    exact(run, RUN_FIELDS)
    exact(artifact, ARTIFACT_FIELDS)
    require(plan == expected_plan, "REAL_PLAN_PIN_MISMATCH")
    require(plan["schema"] == "af-rod-real-plan-projection-v1"
            and plan["profile"] == PROFILE and plan["backend_id"] == BACKEND
            and plan["phase"] in ("A", "B"), "REAL_PLAN_SCHEMA_INVALID")
    for key in ("project_id", "project_instance_id", "plan_id", "candidate_id", "research_project_id"):
        opaque(plan[key])
    for key in ("plan_digest", "input_digest", "resources_digest", "output_identity",
                "contract_digest", "verification_policy_digest"):
        sha(plan[key])
    _positive(plan["research_revision"])
    require(type(plan["input_size"]) is int and 0 < plan["input_size"] <= 1048576,
            "REAL_INPUT_SIZE_INVALID")
    decimal(plan["load_n"])
    for record in (receipt, run):
        require(all(record[key] == plan[key] for key in
                    ("project_id", "project_instance_id", "plan_id", "plan_digest")),
                "REAL_RECORD_PLAN_MISMATCH")
        opaque(record["run_id"])
        opaque(record["grant_id"])
    opaque(receipt["request_id"])
    opaque(receipt["idempotency_key"])
    opaque(run["phase_attempt_id"])
    require(receipt["request_status"] == "ACCEPTED" and receipt["run_id"] == run["run_id"]
            and receipt["grant_id"] == run["grant_id"], "REAL_RECEIPT_MISMATCH")
    _positive(receipt["accepted_sequence"])
    require(run["backend_id"] == BACKEND and run["phase"] == "STANDARD"
            and run["simulation"] is False and run["retry_of"] is None
            and type(run["attempt_no"]) is int and run["attempt_no"] == 1
            and type(run["revision"]) is int and run["revision"] == 3
            and type(run["solver_exit_code"]) is int and run["solver_exit_code"] == 0
            and run["execution"] == "FINISHED" and run["reconciliation"] == "NONE"
            and run["managed_scope"] == "COMMITTED_EMPTY_SCOPE"
            and run["backend_outcome"] == "COMPLETED", "REAL_RUN_UNCONFIRMED")
    require(all(run[key] == artifact[key] == plan[key] for key in
                ("input_digest", "output_identity")), "REAL_ARTIFACT_PLAN_MISMATCH")
    require(all(artifact[key] == run[key] for key in ("run_id", "phase_attempt_id")),
            "REAL_ARTIFACT_RUN_MISMATCH")
    require(artifact["filename"] == "axial_rod.dat" and artifact["stable_read"] is True
            and artifact["selector"] == SELECTOR and type(artifact["selector"]) is dict
            and all(type(value) is int for value in artifact["selector"].values())
            and artifact["units"] == UNITS, "REAL_ARTIFACT_SELECTOR_MISMATCH")
    body = artifact["dat_bytes"]
    require(type(body) is bytes and 0 < len(body) <= 16384
            and type(artifact["size"]) is int and artifact["size"] == len(body)
            and artifact["sha256"] == digest_bytes(body), "REAL_ARTIFACT_BYTES_MISMATCH")
    events = bundle["events"]
    require(type(events) is list and len(events) == 3, "REAL_HISTORY_INCOMPLETE")
    previous = 0
    for index, (event, kind) in enumerate(zip(events,
            ("REQUEST_ACCEPTED", "START_INTENT", "ROD_DAT_COMMITTED")), 1):
        exact(event, ("type", "project_sequence", "run_sequence", "run_id", "phase_attempt_id"))
        _positive(event["project_sequence"])
        require(event["type"] == kind and event["project_sequence"] > previous
                and type(event["run_sequence"]) is int and event["run_sequence"] == index
                and event["run_id"] == run["run_id"]
                and event["phase_attempt_id"] == run["phase_attempt_id"], "REAL_HISTORY_MISMATCH")
        previous = event["project_sequence"]
    require(events[0]["project_sequence"] == receipt["accepted_sequence"], "REAL_RECEIPT_ORDER")
    require(bundle["bindings_digest"] == bundle_digest(bundle), "REAL_BUNDLE_DIGEST_MISMATCH")
    return plan, receipt, run, artifact


class RealRodEvidence:
    """Prospective real-schema verification against an existing frozen Project.

    No mutation, source enrollment, live reads, execution or budget reservation.
    An expected Plan is a caller's pin, not proof it exists in authenticated AF.
    """

    def __init__(self, preview):
        require(type(preview) is RealPreviewAdapter, "INVALID_PREVIEW_ADAPTER")
        self.preview = preview

    def verify_declaration(self, bundle, *, expected_plan, expected_link, expected_revision):
        bundle, expected_plan = copy.deepcopy(bundle), copy.deepcopy(expected_plan)
        expected_link = copy.deepcopy(expected_link)
        plan, receipt, run, artifact = _records(bundle, expected_plan)
        exact(expected_link, ("request_id", "idempotency_key", "run_id", "grant_id", "phase_attempt_id"))
        require(all(receipt[key] == expected_link[key] for key in
                    ("request_id", "idempotency_key", "run_id", "grant_id"))
                and run["phase_attempt_id"] == expected_link["phase_attempt_id"],
                "REAL_EXPECTED_LINK_MISMATCH")
        state = self.preview.inspect()
        require(type(expected_revision) is int and state["project_revision"] == expected_revision,
                "REVISION_CONFLICT")
        identity = PublicRodEvidence(self.preview).frozen_identity()
        require(plan["research_project_id"] == state["research_project_id"]
                and plan["contract_digest"] == state["contract_digest"], "REAL_RESEARCH_BINDING_MISMATCH")
        require(plan["phase"] in state["attempts"], "REAL_CANDIDATE_MISSING")
        attempt = state["attempts"][plan["phase"]]
        candidate = attempt["candidate"]
        inert = attempt.get("inert_plan")
        if inert is not None:
            require(all(plan[key] == inert[key] for key in PLAN_FIELDS
                        if key not in ("schema", "backend_id")), "REAL_COMMITTED_PLAN_MISMATCH")
        else:
            require(plan["research_revision"] == expected_revision, "REAL_RESEARCH_BINDING_MISMATCH")
        contract = RodPreviewContract.from_dict(state["contract"])
        body = candidate_bytes(candidate["load_n"], contract)
        require(plan["candidate_id"] == candidate["candidate_id"]
                and plan["input_digest"] == candidate["input_digest"] == digest_bytes(body)
                and plan["input_size"] == len(body)
                and decimal(plan["load_n"]) == decimal(candidate["load_n"])
                and plan["verification_policy_digest"] == af_digest(tolerances(contract)),
                "REAL_CANDIDATE_BINDING_MISMATCH")
        metrics = verify_dat(artifact["dat_bytes"], candidate["load_n"], asdict(contract))
        fixture_goal = ("SATISFIED" if decimal(contract.goal_min_mm)
                        <= Decimal(metrics["displacement_mm"]) <= decimal(contract.goal_max_mm)
                        else "NOT_SATISFIED")
        require(self.preview.inspect() == state, "RESEARCH_CHANGED_DURING_READ")
        return {"schema": "gdcae-real-schema-verification-v1", "frozen_identity": identity,
            "bindings_digest": bundle["bindings_digest"], "plan_digest": plan["plan_digest"],
            "receipt_digest": af_digest(receipt), "run_digest": af_digest(run),
            "events_digest": af_digest(bundle["events"]), "output_digest": artifact["sha256"],
            "source": bundle["source"], "source_authentication": "NOT_VERIFIED",
            "schema_checks": "PASS", "numerical_fixture_checks": "PASS",
            "fixture_goal": fixture_goal, "metrics": metrics,
            "V0": "NOT_VERIFIED", "V1": "MODEL_CONTRACT_CHECKED", "V2": "NOT_VERIFIED",
            "V3": "INCONCLUSIVE", "V4": "NOT_ASSESSED", "ODB": "NOT_VERIFIED",
            "execution_authorized": False, "persisted": False,
            "committed_inert_plan_link": inert is not None,
            "real_contract_compatible": False, "real_source_acquisition": "NOT_RUN"}

    def require_real_b_admission(self, *, expected_revision):
        """Fail closed before creating any B Plan, including from forged PASS data.

        Only committed Project state is considered. Current frozen contracts and
        source adapter cannot represent accepted real A, so there is deliberately
        no success path. The later qualified adapter needs separate approval.
        """
        state = self.preview.inspect()
        require(type(expected_revision) is int and state["project_revision"] == expected_revision,
                "REVISION_CONFLICT")
        require(not state["pending_or_unknown"], "PENDING_OR_UNKNOWN")
        require(state["budget"]["maximum"] == 2 and state["budget"]["available"] > 0,
                "BUDGET_EXHAUSTED")
        require("B" not in state["attempts"], "B_ALREADY_EXISTS")
        a = state["attempts"].get("A")
        require(a is not None and a["status"] in ("OBSERVED", "G2_OBSERVED"), "A_NOT_OBSERVED")
        require(False, "AUTHENTICATED_REAL_A_AND_REAL_CONTRACT_REQUIRED")
