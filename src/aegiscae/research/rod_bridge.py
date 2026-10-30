"""G2 public-port bridge and additive event-v2 replay in the existing Project.

No AF imports, private database reads, process launch or Grant issuer. Existing
event-v1 histories keep their semantics. New event-v2 records fail closed in old
readers. Inert rod Plans, Fake IPC Runs and synthetic numerical data are separate.
"""

import copy
from decimal import Decimal, ROUND_HALF_EVEN, localcontext

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research import project as store
from aegiscae.research.rod_evidence import (
    check_fake_evidence, check_fake_plan, check_plan_ref, seal_envelope,
    tolerances, verify_envelope,
)
from aegiscae.research.rod_preview import RealPreviewAdapter
from aegiscae.research.rod_preview_rules import (
    TEMPLATE, RodPreviewContract, candidate_bytes, decimal, exact, timestamp, token,
)

EVENT_VERSION = "rod-preview-event-v2"


def _causal(state):
    require("A" in state["attempts"], "A_NOT_ELIGIBLE")
    a = state["attempts"]["A"]
    require(a["status"] == "G2_OBSERVED"
            and a["decision"]["fixture_checks"] == {
                "provenance": "PASS", "numerical": "PASS", "goal": "NOT_SATISFIED"},
            "A_NOT_ELIGIBLE")
    return {"schema": "gdcae-synthetic-causal-v2", "source": "SYNTHETIC_DAT",
            "a_run_id": a["fake_evidence"]["binding"]["run_id"],
            "a_receipt_digest": a["fake_proof"]["receipt_digest"],
            "a_output_digest": a["decision"]["output_digest"],
            "a_verification_digest": digest_bytes(canonical_json(a["decision"])),
            "a_metric_mm": a["decision"]["metrics"]["displacement_mm"],
            "contract_digest": state["contract_digest"],
            "a_observed_revision": a["observed_revision"]}


def numeric_reference(state, step):
    attempt = state["attempts"][step]
    if step == "A":
        require(attempt["inert_plan"] is not None, "INERT_PLAN_MISSING")
        return copy.deepcopy(attempt["inert_plan"])
    require(step == "B", "INVALID_PHASE")
    candidate = attempt["candidate"]
    body = {"schema": "gdcae-synthetic-numeric-ref-v1", "source": "SYNTHETIC_NOT_REGISTERED",
            "research_project_id": state["research_project_id"],
            "contract_digest": state["contract_digest"], "candidate_id": candidate["candidate_id"],
            "input_digest": candidate["input_digest"], "phase": "B",
            "causal_digest": digest_bytes(canonical_json(candidate["causal"]))}
    return {**body, "output_identity": digest_bytes(canonical_json(body))}


def apply_bridge(state, payload, project_id, revision, at_utc):
    """Pure deterministic event-v2 replay; no migration or event-v1 reinterpretation."""
    exact(payload, ("schema_version", "before_project_revision", "action", "key", "data"))
    require(payload["schema_version"] == EVENT_VERSION and state is not None
            and type(payload["before_project_revision"]) is int
            and payload["before_project_revision"] == revision, "REVISION_CONFLICT")
    token(payload["key"])
    timestamp(at_utc)
    require(at_utc >= state["last_at_utc"] and
            (state.get("bridge_version") == EVENT_VERSION or not state["attempts"]),
            "PREVIEW_ROUTE_MISMATCH")
    state = copy.deepcopy(state)
    state.update(bridge_version=EVENT_VERSION, real_solver_calls=0)
    action, data = payload["action"], payload["data"]
    contract = RodPreviewContract.from_dict(state["contract"])
    if action == "G2_ADMIT":
        exact(data, ("candidate_id", "step", "load_n", "unit", "input_digest",
                    "contract_digest", "research_project_id", "project_revision",
                    "created_at_utc", "causal"))
        token(data["candidate_id"])
        require(data["step"] in ("A", "B") and data["step"] not in state["attempts"],
                "ATTEMPT_EXISTS")
        require(data["research_project_id"] == project_id
                and data["contract_digest"] == state["contract_digest"]
                and type(data["project_revision"]) is int and data["project_revision"] == revision
                and state["last_at_utc"] <= timestamp(data["created_at_utc"]) <= at_utc,
                "PROPOSAL_BINDING_MISMATCH")
        require(data["input_digest"] == digest_bytes(candidate_bytes(
            data["load_n"], contract, data["unit"])), "INPUT_DIGEST_MISMATCH")
        if data["step"] == "A":
            require(not state["attempts"] and data["causal"] is None, "INVALID_A")
        else:
            require(data["causal"] == _causal(state), "CAUSAL_EVIDENCE_MISMATCH")
            require(data["input_digest"] != state["attempts"]["A"]["candidate"]["input_digest"]
                    and data["candidate_id"] != state["attempts"]["A"]["candidate"]["candidate_id"],
                    "NEW_CANDIDATE_REQUIRED")
        state["attempts"][data["step"]] = {"candidate": copy.deepcopy(data),
            "status": "G2_ADMITTED", "binding": None, "inert_plan": None,
            "fake_evidence": None, "fake_proof": None, "observation": None, "decision": None}
    elif action == "G2_BIND_INERT_PLAN":
        exact(data, ("step", "plan_ref", "request_key"))
        token(data["request_key"])
        require(data["step"] == "A" and "A" in state["attempts"], "REAL_B_NOT_PREPARED")
        attempt = state["attempts"]["A"]
        require(attempt["status"] == "G2_ADMITTED" and attempt["inert_plan"] is None,
                "PLAN_ALREADY_BOUND")
        attempt["inert_plan"] = check_plan_ref(data["plan_ref"], candidate=attempt["candidate"],
            contract=contract, research_project_id=project_id, research_revision=revision)
        attempt["plan_request_key"] = data["request_key"]
    elif action == "G2_FAKE_INTENT":
        exact(data, ("step", "fake_plan_ref"))
        require(data["step"] in state["attempts"], "CANDIDATE_MISSING")
        attempt = state["attempts"][data["step"]]
        require(attempt["status"] == "G2_ADMITTED", "INTENT_ALREADY_RECORDED")
        require(not any(a["status"] in ("G2_INTENT", "G2_UNKNOWN")
                        for a in state["attempts"].values()), "PENDING_OR_UNKNOWN")
        require(sum(a["binding"] is not None for a in state["attempts"].values()) < 2,
                "BUDGET_EXHAUSTED")
        numeric = numeric_reference(state, data["step"])
        binding = check_fake_plan(data["fake_plan_ref"], data["step"])
        if data["step"] == "A":
            require(binding["project_instance_id"] != numeric["project_instance_id"]
                    and binding["plan_id"] != numeric["plan_id"], "FAKE_ROD_IDENTITY_CONFUSION")
        for other in state["attempts"].values():
            if other["binding"] is not None:
                require(all(binding[k] != other["binding"][k] for k in
                        ("project_id", "project_instance_id", "plan_id", "grant_id",
                         "request_key", "output_identity")), "ATTEMPT_IDENTITY_REUSED")
        attempt.update(status="G2_INTENT", binding=binding)
    elif action == "G2_UNKNOWN":
        exact(data, ("step",))
        require(data["step"] in state["attempts"], "CANDIDATE_MISSING")
        attempt = state["attempts"][data["step"]]
        require(attempt["status"] == "G2_INTENT", "UNKNOWN_STATE_CONFLICT")
        attempt["status"] = "G2_UNKNOWN"
    elif action == "G2_OBSERVE":
        exact(data, ("step", "fake_evidence", "envelope"))
        require(data["step"] in state["attempts"], "CANDIDATE_MISSING")
        attempt = state["attempts"][data["step"]]
        require(attempt["status"] in ("G2_INTENT", "G2_UNKNOWN"), "NO_PENDING_INTENT")
        proof = check_fake_evidence(data["fake_evidence"], attempt["binding"])
        decision = verify_envelope(data["envelope"], expected_plan=numeric_reference(state, data["step"]),
            expected_link=proof["binding"], candidate=attempt["candidate"], contract=contract)
        for other in state["attempts"].values():
            if other["decision"] is not None:
                require(other["decision"]["output_digest"] != decision["output_digest"]
                        and other["fake_proof"]["binding"]["run_id"] != proof["binding"]["run_id"],
                        "OLD_OUTPUT_REUSED")
        attempt.update(status="G2_OBSERVED", fake_evidence=copy.deepcopy(data["fake_evidence"]),
                       fake_proof=proof, observation=copy.deepcopy(data["envelope"]),
                       decision=decision, observed_revision=revision + 1)
    else:
        require(False, "INVALID_PREVIEW_ACTION")
    require(payload["key"] not in state["keys"], "DUPLICATE_EVENT_KEY")
    state["keys"][payload["key"]] = digest_bytes(canonical_json({"action": action, "data": data}))
    state["last_at_utc"] = at_utc
    return state


class RodBridge:
    """Narrow durable bridge; a configured public AF port owns its own persistence."""

    def __init__(self, preview):
        require(type(preview) is RealPreviewAdapter, "INVALID_PREVIEW_ADAPTER")
        self.preview = preview

    def inspect(self):
        return self.preview.inspect()

    def _record(self, action, data, revision, key):
        return self.preview._record(action, data, revision, key, event_version=EVENT_VERSION)

    def proposal(self, step, load_n, candidate_id):
        state = self.inspect()
        require(step in ("A", "B") and step not in state["attempts"], "ATTEMPT_EXISTS")
        contract = RodPreviewContract.from_dict(state["contract"])
        return {"candidate_id": token(candidate_id), "step": step, "load_n": load_n,
                "unit": "N", "input_digest": digest_bytes(candidate_bytes(load_n, contract)),
                "contract_digest": state["contract_digest"],
                "research_project_id": state["research_project_id"],
                "project_revision": state["project_revision"], "created_at_utc": store._utc(),
                "causal": _causal(state) if step == "B" else None}

    def admit(self, proposal, revision, key):
        return self._record("G2_ADMIT", proposal, revision, key)

    def prepare_a(self, port, *, revision, key, request_key, at_time, expires_at):
        state = self.inspect()
        require("A" in state["attempts"], "CANDIDATE_MISSING")
        attempt = state["attempts"]["A"]
        require(attempt["status"] == "G2_ADMITTED", "PLAN_STATE_CONFLICT")
        if attempt["inert_plan"] is not None:
            ref = attempt["inert_plan"]
            require(expires_at == ref["expires_at"], "PREPARATION_CONTENT_CONFLICT")
            require(port.inspect(ref["plan_id"], ref["plan_digest"], at_time=at_time) == ref,
                    "PLAN_REOPEN_MISMATCH")
            return self._record("G2_BIND_INERT_PLAN", {"step": "A", "plan_ref": ref,
                "request_key": request_key}, revision, key)
        require(state["project_revision"] == revision, "REVISION_CONFLICT")
        contract = RodPreviewContract.from_dict(state["contract"])
        ref = port.prepare(frozen_template=TEMPLATE,
            candidate_bytes=self.preview.candidate_input("A"), load_n=attempt["candidate"]["load_n"],
            research_project_id=state["research_project_id"], contract_digest=state["contract_digest"],
            research_revision=revision, candidate_id=attempt["candidate"]["candidate_id"],
            request_key=request_key, expires_at=expires_at, at_time=at_time,
            tolerances=tolerances(contract), phase="A")
        require(port.inspect(ref["plan_id"], ref["plan_digest"], at_time=at_time) == ref,
                "PLAN_REOPEN_MISMATCH")
        return self._record("G2_BIND_INERT_PLAN", {"step": "A", "plan_ref": ref,
            "request_key": request_key}, revision, key)

    def fake_intent(self, step, fake_plan_ref, revision, key):
        return self._record("G2_FAKE_INTENT", {"step": step, "fake_plan_ref": fake_plan_ref}, revision, key)

    def unknown(self, step, revision, key):
        return self._record("G2_UNKNOWN", {"step": step}, revision, key)

    def observe(self, step, fake_evidence, envelope, revision, key):
        return self._record("G2_OBSERVE", {"step": step, "fake_evidence": fake_evidence,
                                          "envelope": seal_envelope(envelope)}, revision, key)

    def numeric_reference(self, step):
        return numeric_reference(self.inspect(), step)

    def propose_b(self, candidate_id):
        state = self.inspect()
        basis = _causal(state)
        with localcontext() as context:
            context.prec = 40
            target = (decimal(state["contract"]["goal_min_mm"]) +
                      decimal(state["contract"]["goal_max_mm"])) / 2
            measured = Decimal(basis["a_metric_mm"])
            require(measured > 0, "INVALID_MEASURED_COMPLIANCE")
            force = (decimal(state["attempts"]["A"]["candidate"]["load_n"]) * target / measured)
            force = force.quantize(Decimal("0.000000001"), rounding=ROUND_HALF_EVEN)
        value = format(force, "f").rstrip("0").rstrip(".")
        return self.proposal("B", value, candidate_id)

    def public_summary(self):
        """No raw DAT, paths, Run identities or arbitrary event payloads for agents."""
        state = self.inspect()
        return {"schema": "gdcae-rod-public-summary-v1", "real_solver_calls": 0,
                "real_A": "NOT_RUN", "real_B": "NOT_RUN", "real_goal": "INCONCLUSIVE",
                "budget": copy.deepcopy(state["budget"]),
                "pending_or_unknown": state["pending_or_unknown"],
                "attempts": {step: {"state": value["status"],
                    "candidate_load_n": value["candidate"]["load_n"],
                    "numerical_source": "SYNTHETIC_DAT", "execution_source": "FAKE_TEST_ONLY",
                    "metrics": None if value["decision"] is None else {
                        k: value["decision"]["metrics"][k] for k in
                        ("displacement_mm", "stress_mpa", "reaction_n", "units", "step", "increment")},
                    "verification_digest": None if value["decision"] is None else
                        digest_bytes(canonical_json(value["decision"])),
                    "artifact_acquisition": None if value["decision"] is None else
                        value["decision"]["artifact_acquisition"],
                    "fixture_goal": None if value["decision"] is None else value["decision"]["fixture_checks"]["goal"],
                    "V2": "NOT_VERIFIED", "V4": "NOT_ASSESSED", "ODB": "ODB_NOT_VERIFIED"}
                    for step, value in state["attempts"].items()}}
