"""New real-intent rod contracts on the existing ResearchProject transaction log.

This is not a dispatcher or an authority provider. Old schema-1 synthetic and
schema-2 preview records are unchanged. A fresh contract may declare real intent;
only independently qualified source/Operator evidence may authorize execution.
"""

import copy
from pathlib import Path
import time

from aegiscae.contracts.research_contracts import (
    ContractBundle, canonical_json, digest_bytes, require,
)
from aegiscae.research import project as store
from aegiscae.research.budget_rules import counters
from aegiscae.research.rod_evidence import af_digest
from aegiscae.research.rod_preview_rules import (
    BASELINE, PROFILE, TEMPLATE, RodPreviewContract, candidate_bytes, exact, sha, token,
)

VERSION = "rod-real-workflow-v1"
BACKEND = "abaqus-standard-rod-cload-v1"
PIN_FIELDS = ("project_id", "project_instance_id", "plan_id", "plan_digest",
              "input_digest", "resources_digest", "output_identity", "backend_id",
              "candidate_output_identity", "request_key", "request_nonce")
RESOURCES = {"slots": 1, "cpus": 1, "gpus": 0, "memory_mb": 2048,
             "observation_seconds": 300, "launch_budget": 1}
NUMERICAL_POLICY = {"schema": "rod-frozen-numerical-policy-v1", "units": "N_mm_MPa",
    "step": 1, "increment": 1, "node": 2, "element": 1, "integration_point": 1,
    "displacement_tolerance_mm": "0.000001", "stress_tolerance_mpa": "0.0001",
    "reaction_tolerance_n": "0.0001", "zero_tolerance_mm": "0.00000001",
    "balance_tolerance_n": "0.0002", "goal_min_mm": "0.019", "goal_max_mm": "0.021"}


def implementation_hashes():
    """Frozen byte identity, not a signature or authenticated publisher claim."""
    root = Path(__file__).resolve().parent
    files = {"V0": root / "rod_real_verify.py", "V1": root / "rod_preview_rules.py",
             "V2": root / "rod_preview_dat.py", "V3": root / "rod_real_project.py",
             "V4": root.parent / "contracts/research_contracts.py"}
    return {level: digest_bytes(path.read_bytes()) for level, path in files.items()}


def _id(prefix, project_id):
    return prefix + "_" + digest_bytes((VERSION + project_id + prefix).encode())[7:39]


def real_bundle(project_id):
    """Explicitly declared external model; no true-model/physical PASS claim."""
    common = {"schema_version": 1, "version": 1, "research_project_id": project_id}
    def quantity(value):
        return {"value": value, "dimension": "length", "unit": "mm"}
    objective = {"metric_id": "displacement", "component": "U1", "dimension": "length", "unit": "mm",
        "selector": {"instance": "Rod", "entity_kind": "NODE_SET", "entity_id": "Node2",
                     "step": "Step1", "frame": 1, "time": None}}
    constraints = [{"constraint_id": name, "evidence": objective, "comparator": comparator,
                    "threshold": quantity(value), "tolerance": quantity("0")}
                   for name, comparator, value in (("target_min", "GE", "0.019"),
                                                    ("target_max", "LE", "0.021"))]
    implementations = implementation_hashes()
    raw = {**common, "bundle_id": _id("bundle", project_id),
        "goal": {**common, "goal_id": _id("goal", project_id), "objective": objective,
            "comparator": "EQ", "target": quantity("0.02"), "tolerance": quantity("0.001"),
            "hard_constraints": constraints, "allowed_changes": ["load"],
            "forbidden_changes": ["geometry", "mesh", "material", "boundary", "contact",
                                  "step", "integration", "postprocess"],
            "required_evidence": ["PROVENANCE", "MODEL_INTEGRITY", "SOLVER_REPORT", "NUMERICAL_CHECK", "GOAL_METRIC"],
            "on_unknown": "BLOCK", "approval_source": None,
            "budget": {"max_solver_calls": 2, "max_candidate_proposals": 2,
                       "max_auto_turns": None, "auto_turn_enforcement": "NOT_ENFORCED"}},
        "model": {**common, "baseline_id": _id("baseline", project_id), "model_family": PROFILE,
            "artifacts": [{"artifact_id": _id("artifact", project_id), "role": "BASELINE",
                "sha256": BASELINE, "size_bytes": len(TEMPLATE), "source_identity": "CODE_DECLARED_ROD",
                "source_kind": "DECLARED_EXTERNAL", "dependencies": []}],
            "length_unit": "mm", "force_unit": "N", "time_unit": "s", "stress_unit": "MPa",
            "entities": [{"instance": "Rod", "entity_kind": "NODE_SET", "entity_id": "Node2"}],
            "steps": [{"step_id": "Step1", "frames": [1], "frame_times": [
                {"value": "1", "dimension": "time", "unit": "s"}]}],
            "assumptions": ["T3D2 axial rod length 10 mm area 1 square mm", "Only node 2 DOF 1 CLOAD scalar 0.5 through 2.5 N"],
            "material_assumptions": ["Elastic E 1000 MPa Poisson 0.3"],
            "boundary_assumptions": ["Node 1 fixed and node 2 transverse displacements fixed"],
            "contact_assumptions": ["No contact"],
            "integration_assumptions": ["One T3D2 element and one integration point",
                "Frozen numerical policy " + digest_bytes(canonical_json(NUMERICAL_POLICY)),
                "U1 tolerance 0.000001 mm S11 tolerance 0.0001 MPa RF1 tolerance 0.0001 N",
                "Zero displacement tolerance 0.00000001 mm and balance tolerance 0.0002 N"],
            "applicability_limits": ["Linear static axial load only", "Physical verification and real execution unqualified"],
            "allowed_changes": ["load"], "dependency_closure": "DECLARED_ONLY", "semantic_status": "DECLARED_ONLY"},
        "verification": {**common, "verification_id": _id("verification", project_id),
            "required_checks": {"V0": True, "V1": True, "V2": True, "V3": True, "V4": False},
            "required_evidence": [objective], "goal_tolerance": quantity("0.001"),
            "hard_constraint_checks": [{"constraint_id": item["constraint_id"], "level": "V3", "rule": item}
                                       for item in constraints],
            "validators": [{"level": level, "validator_id": "rod_source_" + level,
                "version": "d4_v1", "sha256": implementations[level]}
                           for level in ("V0", "V1", "V2", "V3", "V4")],
            "physical_reference": None, "on_unknown": "BLOCK"}}
    return ContractBundle.from_dict(raw)


def _candidate(project_id, contract_digest, step, load, causal=None):
    data = candidate_bytes(load, RodPreviewContract())
    identity = digest_bytes(canonical_json({"project": project_id, "contract": contract_digest,
                                          "step": step, "input": digest_bytes(data)}))
    return {"candidate_id": "candidate_" + identity[7:39], "step": step, "load_n": load, "unit": "N",
            "research_project_id": project_id, "contract_digest": contract_digest,
            "admitted_revision": 3,
            "verification_policy": copy.deepcopy(NUMERICAL_POLICY),
            "input_digest": digest_bytes(data), "input_size": len(data),
            "output_identity": digest_bytes((identity + "fresh-output").encode()), "causal": causal}


def _budget(state):
    return counters({"limit": 2, "reservations": state["reservations"]})


def apply_real_workflow(state, payload, bundle, revision, latest):
    """Pure replay; all state is derived from versioned committed events."""
    exact(payload, ("schema_version", "action", "key", "before_project_revision", "data"))
    require(payload["schema_version"] == VERSION and type(payload["before_project_revision"]) is int
            and payload["before_project_revision"] == revision, "REAL_REVISION_CONFLICT")
    token(payload["key"])
    require(bundle.canonical_bytes() == real_bundle(bundle.research_project_id).canonical_bytes(),
            "REAL_FROZEN_CONTRACT_MISMATCH")
    contract_digest = bundle.digests()["bundle"]
    require(latest == contract_digest, "REAL_FROZEN_CONTRACT_MISMATCH")
    action, data = payload["action"], payload["data"]
    if action == "INITIALIZE":
        exact(data, ("verification_policy",))
        require(canonical_json(data["verification_policy"]) == canonical_json(NUMERICAL_POLICY),
                "REAL_VERIFICATION_POLICY_CHANGED")
        require(state is None and revision == 2, "NEW_FROZEN_PROJECT_REQUIRED")
        state = {"version": VERSION, "research_project_id": bundle.research_project_id,
            "contract_digest": contract_digest, "candidates": {"A": _candidate(bundle.research_project_id, contract_digest, "A", "1")},
            "reservations": {}, "observations": {}, "keys": {}, "real_a": "NOT_READY"}
    else:
        require(type(state) is dict and state.get("version") == VERSION, "REAL_ROUTE_MISMATCH")
        state = copy.deepcopy(state)
        require(state["contract_digest"] == contract_digest, "REAL_FROZEN_CONTRACT_MISMATCH")
        if action in ("RESERVE_A", "RESERVE_A_APPLICATION_V1"):
            application = None
            if action == "RESERVE_A_APPLICATION_V1":
                from aegiscae.research.rod_real_verify import verify_a_preflight
                exact(data, ("binding", "preflight"))
                application = copy.deepcopy(data)
                verify_a_preflight(data["preflight"], state["candidates"]["A"], data["binding"])
                binding = data["binding"]
            else:
                binding = data
            exact(binding, PIN_FIELDS)
            require("A" not in state["reservations"] and not state["reservations"], "REAL_ATTEMPT_ALREADY_RESERVED")
            for key in ("project_id", "project_instance_id", "plan_id", "request_key", "request_nonce"):
                token(binding[key])
            for key in ("plan_digest", "input_digest", "resources_digest", "output_identity"):
                sha(binding[key])
            require(binding["backend_id"] == BACKEND and binding["input_digest"] == state["candidates"]["A"]["input_digest"]
                    and binding["candidate_output_identity"] == state["candidates"]["A"]["output_identity"]
                    and binding["resources_digest"] == af_digest(RESOURCES), "REAL_PLAN_BINDING_MISMATCH")
            require(_budget(state)["available"] >= 1, "BUDGET_EXHAUSTED")
            state["reservations"]["A"] = {"state": "RESERVED", "request": {"cost": 1}, "binding": copy.deepcopy(binding)}
            if application is not None:
                state["reservations"]["A"]["application"] = application
        elif action in ("INTENT_A", "UNKNOWN_A"):
            exact(data, ())
            reservation = state["reservations"].get("A")
            require(reservation is not None, "REAL_RESERVATION_REQUIRED")
            expected = "RESERVED" if action == "INTENT_A" else "SUBMISSION_INTENT_RECORDED"
            require(reservation["state"] == expected, "REAL_PENDING_OR_UNKNOWN")
            reservation["state"] = "SUBMISSION_INTENT_RECORDED" if action == "INTENT_A" else "ACCEPTANCE_UNKNOWN"
        elif action == "OBSERVE_A":
            from aegiscae.research.rod_real_verify import validate_observation_record
            reservation = state["reservations"].get("A")
            require(reservation is not None and reservation["state"] in {
                "SUBMISSION_INTENT_RECORDED", "ACCEPTANCE_UNKNOWN"}, "REAL_INTENT_REQUIRED")
            validate_observation_record(data, state["candidates"]["A"], reservation["binding"])
            require("A" not in state["observations"], "REAL_OBSERVATION_ALREADY_RECORDED")
            state["observations"]["A"] = copy.deepcopy(data)
            # Unqualified provenance never charges/releases or admits a successor.
            reservation["state"] = "ACCEPTANCE_UNKNOWN"
        elif action == "PROPOSE_B":
            require(False, "AUTHENTICATED_REAL_A_REQUIRED")
        else:
            require(False, "REAL_ACTION_INVALID")
    request = digest_bytes(canonical_json({"action": action, "data": data}))
    require(payload["key"] not in state["keys"], "REAL_DUPLICATE_EVENT")
    state["keys"][payload["key"]] = request
    _budget(state)
    return state


def _fault(stage):
    """Trusted test-only exception seam; no external action is invoked."""


class RealRodProject:
    def __init__(self, project):
        require(type(project) is store.ResearchProject, "INVALID_PROJECT")
        self.project = project

    def _read(self, meta, bundles, events):
        require(meta["schema_version"] == 1, "REAL_PROJECT_SCHEMA_REQUIRED")
        bundle = next((item[0] for item in bundles if item[0].model.model_family == PROFILE), None)
        require(bundle is not None, "REAL_FROZEN_CONTRACT_REQUIRED")
        state, latest = None, None
        for event in events:
            if event["kind"] == "BUNDLE_FROZEN":
                latest = event["bundle_digest"]
            elif event["kind"] == "WORKFLOW_RECORDED":
                state = apply_real_workflow(state, event["workflow"], bundle, event["project_revision"] - 1, latest)
            elif event["kind"] in {"BUDGET_RECORDED", "CANDIDATE_PUBLICATION_OBSERVED"}:
                require(False, "REAL_ROUTE_MISMATCH")
        require(latest == bundle.digests()["bundle"], "REAL_FROZEN_CONTRACT_MISMATCH")
        return bundle, state

    def _view(self, state, meta):
        require(state is not None, "REAL_PROJECT_NOT_INITIALIZED")
        return {**copy.deepcopy(state), "project_revision": meta["project_revision"], "budget": _budget(state),
            "execution_authorized": False, "human_approval": "NOT_ESTABLISHED", "HIL_ENFORCEMENT": "BLOCKED",
            "verification": {"V0": "NOT_VERIFIED", "V1": "MODEL_CONTRACT_CHECKED", "V2": "NOT_VERIFIED",
                             "V3": "INCONCLUSIVE", "V4": "NOT_ASSESSED", "ODB": "NOT_VERIFIED"}}

    def inspect(self):
        with self.project._snapshot() as (_, meta, bundles, events):
            _, state = self._read(meta, bundles, events)
            return self._view(state, meta)

    def candidate_input(self):
        state = self.inspect()
        data = candidate_bytes(state["candidates"]["A"]["load_n"], RodPreviewContract())
        require(digest_bytes(data) == state["candidates"]["A"]["input_digest"], "REAL_INPUT_CHANGED")
        return data

    def pre_a_dossier(self):
        """Read-only scientific draft; neither a dispatch request nor approval.

        This run's future DAT is a post-execution requirement, never a demand to
        produce impossible pre-A evidence. Source/authority mechanism qualification
        is a separate prerequisite. No live host or authentication is inferred.
        """
        from aegiscae.research.rod_real_verify import READ_LIMITS
        with self.project._snapshot() as (_, meta, bundles, events):
            bundle, state = self._read(meta, bundles, events)
            view = self._view(state, meta)
            candidate = view["candidates"]["A"]
            raw = candidate_bytes(candidate["load_n"], RodPreviewContract())
            require(digest_bytes(raw) == candidate["input_digest"], "REAL_INPUT_CHANGED")
            reservation = view["reservations"].get("A")
            return {"schema": "rod-pre-a-dossier-v1", "status": "NOT_EXECUTABLE",
                "research_project_id": bundle.research_project_id,
                "project_revision": meta["project_revision"], "contract_digest": view["contract_digest"],
                "candidate_a": copy.deepcopy(candidate), "input_size": len(raw),
                "scientific_contract": {"profile": PROFILE, "element": "T3D2", "elements": 1,
                    "nodes": 2, "length_mm": "10", "area_mm2": "1", "modulus_mpa": "1000",
                    "poisson": "0.3", "boundary": "NODE1_DOF1_2_3_ZERO_NODE2_DOF2_3_ZERO",
                    "units": "N_mm_MPa", "load_min_n": "0.5", "load_max_n": "2.5",
                    "proposed_a_n": "1", "goal_min_mm": "0.019", "goal_max_mm": "0.021"},
                "input_compliance": "FROZEN_TEMPLATE_CHECKED",
                "model_qualification": "DECLARED_ONLY_NOT_PHYSICALLY_VERIFIED",
                "pre_execution_prerequisites": ["PROTECTED_OPERATOR_DEPLOYMENT",
                    "EXACT_AF_PROJECT_PLAN_PATH_RESOURCE_IDENTITY", "HOST_AND_LICENSE_QUALIFICATION",
                    "SOURCE_ACQUISITION_MECHANISM_QUALIFICATION", "SEPARATE_EXACT_A_APPROVAL"],
                "post_execution_requirements": ["THIS_A_ORIGINAL_DAT_STA_MSG",
                    "EXACT_PLAN_RECEIPT_RUN_ATTEMPT_AND_MANAGED_COMPLETION",
                    "INDEPENDENT_V0_V3_NUMERICAL_REVIEW"],
                "real_a_output": "UNAUTHENTICATED_RECORD_ONLY" if view["observations"]
                                 else "NOT_AVAILABLE_TO_PROJECT",
                "read_limits": copy.deepcopy(READ_LIMITS), "budget": view["budget"],
                "budget_scope": "RESEARCH_PROJECT_ONLY",
                "campaign_budget_enforcement": "NOT_QUALIFIED",
                "first_a_budget_requirement": "ONE_EXACT_PROJECT_HOLD_AND_SINGLE_USE_AF_GRANT",
                "general_cross_project_scheduler_required_before_a": False,
                "later_b_prerequisites": ["AUTHENTICATED_A_AND_NATIVE_PROPOSAL",
                    "SINGLE_TOTAL_ATTEMPT_AUTHORITY_FOR_THIS_RESEARCH_PROJECT",
                    "REMAINING_TWO_ATTEMPT_BUDGET", "SEPARATE_EXACT_B_APPROVAL"],
                "reservation_state": reservation["state"] if reservation else "NOT_RESERVED",
                "query_first_required": bool(reservation),
                "b_state": "NO_CANDIDATE_PLAN_OR_GRANT",
                "b_policy": "AUTHENTICATED_A_THEN_NATIVE_PROPOSAL_AND_SEPARATE_ADMISSION",
                "verification": view["verification"], "execution_authorized": False,
                "human_approval": "NOT_ESTABLISHED", "HIL_ENFORCEMENT": "BLOCKED"}

    def _record(self, action, data, expected_revision, key):
        token(key)
        require(type(expected_revision) is int and expected_revision > 0, "INVALID_REVISION")
        data = copy.deepcopy(data)
        request = digest_bytes(canonical_json({"action": action, "data": data}))
        with self.project._snapshot(write=True) as (connection, meta, bundles, events):
            bundle, state = self._read(meta, bundles, events)
            if state is not None and key in state["keys"]:
                require(state["keys"][key] == request, "IDEMPOTENCY_CONFLICT")
                return {**self._view(state, meta), "replayed": True}
            require(meta["project_revision"] == expected_revision, "REVISION_CONFLICT")
            payload = {"schema_version": VERSION, "action": action, "key": key,
                       "before_project_revision": expected_revision, "data": data}
            state = apply_real_workflow(state, payload, bundle, expected_revision, bundle.digests()["bundle"])
            store._commit_workflow_event(connection, meta, bundle.digests()["bundle"], payload)
            _fault("before_commit")
            connection.commit()
            _fault("after_commit")
            return {**self._view(state, meta), "replayed": False}

    def reserve_a(self, binding, expected_revision, key):
        return self._record("RESERVE_A", binding, expected_revision, key)

    def hold_a_for_review(self, read_port, binding, expected_revision, key):
        """Persist one exact public preflight and budget hold, never submit A.

        The additive action leaves old RESERVE_A events unchanged. Response-loss
        replay returns the committed snapshot without a new remote query or key.
        UNKNOWN can be inspected/replayed but cannot cause another reservation.
        """
        from aegiscae.research.rod_real_verify import verify_a_preflight
        token(key)
        require(type(expected_revision) is int and expected_revision > 0, "INVALID_REVISION")
        binding = copy.deepcopy(binding)
        exact(binding, PIN_FIELDS)
        before = self.inspect()
        reserved = before["reservations"].get("A")
        if reserved is not None:
            original = reserved.get("application")
            require(original is not None, "REAL_APPLICATION_UNAVAILABLE")
            require(key in before["keys"], "REAL_ATTEMPT_ALREADY_RESERVED")
            require(canonical_json(binding) == canonical_json(original["binding"])
                    and before["keys"][key] == digest_bytes(canonical_json({
                        "action": "RESERVE_A_APPLICATION_V1", "data": original})),
                    "IDEMPOTENCY_CONFLICT")
            return self._a_application_view(before, replayed=True)
        require(before["project_revision"] == expected_revision, "REVISION_CONFLICT")
        candidate = before["candidates"]["A"]
        expected = {"research_project_id": candidate["research_project_id"],
            "contract_digest": candidate["contract_digest"], "research_revision": candidate["admitted_revision"],
            "candidate_id": candidate["candidate_id"], "request_nonce": binding["request_nonce"],
            "input_digest": candidate["input_digest"]}
        preflight = read_port.preflight_real(plan_id=binding["plan_id"],
            expected_plan_digest=binding["plan_digest"], expected_contract=expected)
        verify_a_preflight(preflight, candidate, binding)
        require(preflight["expires_at"] > int(time.time()), "A_PREFLIGHT_EXPIRED")
        state = self._record("RESERVE_A_APPLICATION_V1",
            {"binding": binding, "preflight": copy.deepcopy(preflight)}, expected_revision, key)
        return self._a_application_view(state, replayed=state["replayed"])

    @staticmethod
    def _a_application_view(state, *, replayed):
        reservation = state["reservations"].get("A")
        require(reservation is not None and "application" in reservation, "REAL_APPLICATION_UNAVAILABLE")
        original = copy.deepcopy(reservation["application"])
        form = {"schema": "gdcae-a-only-review-form-v1", "status": "NOT_EXECUTABLE",
            "research_project_id": state["research_project_id"], "contract_digest": state["contract_digest"],
            "candidate_a": copy.deepcopy(state["candidates"]["A"]), **original,
            "solver_attempts_requested": 1, "decision_options": ["APPROVE_EXACT_A", "DENY"],
            "human_approval": "NOT_ESTABLISHED", "source_authentication": "NOT_VERIFIED",
            "execution_authorized": False, "b_plan_or_grant": "NOT_REQUESTED",
            "requires_fresh_server_qualification": True,
            "snapshot_status": "ORIGINAL_COMMITTED_PREFLIGHT_NOT_LIVE_AUTHORITY"}
        return {"schema": "gdcae-a-only-application-v1", "form": form,
            "application_digest": digest_bytes(canonical_json(form)), "replayed": replayed,
            "project_revision": state["project_revision"], "budget": copy.deepcopy(state["budget"]),
            "reservation_state": reservation["state"],
            "query_first_required": reservation["state"] != "RESERVED",
            "execution_authorized": False}

    def a_only_application(self):
        """Read the held original application without refreshing or authorizing it."""
        return self._a_application_view(self.inspect(), replayed=True)

    def initialize_a(self):
        """Resume a newly frozen Project without replacing its contract or ID."""
        return self._record("INITIALIZE", {"verification_policy": copy.deepcopy(NUMERICAL_POLICY)},
                            2, "initialize-real-A")

    def record_intent_a(self, expected_revision, key):
        return self._record("INTENT_A", {}, expected_revision, key)

    def mark_unknown_a(self, expected_revision, key):
        return self._record("UNKNOWN_A", {}, expected_revision, key)

    def propose_b(self, proposal, expected_revision, key):
        return self._record("PROPOSE_B", proposal, expected_revision, key)

    def observe_a(self, read_port, expected_revision, key):
        """Acquire via a bound public read port, never accept caller DAT bytes."""
        from aegiscae.research.rod_real_verify import observation_record
        before = self.inspect()
        token(key)
        require(type(expected_revision) is int and expected_revision > 0, "INVALID_REVISION")
        if key in before["keys"]:
            prior = before["observations"].get("A")
            require(prior is not None and before["keys"][key] == digest_bytes(canonical_json({
                "action": "OBSERVE_A", "data": prior})), "IDEMPOTENCY_CONFLICT")
            return {**before, "replayed": True}
        require(before["project_revision"] == expected_revision, "REVISION_CONFLICT")
        reservation = before["reservations"].get("A")
        require(reservation is not None and reservation["state"] in {
            "SUBMISSION_INTENT_RECORDED", "ACCEPTANCE_UNKNOWN"}, "REAL_INTENT_REQUIRED")
        binding = reservation["binding"]
        evidence = read_port.read_real_artifact(plan_id=binding["plan_id"],
            expected_plan_digest=binding["plan_digest"], request_key=binding["request_key"])
        record = observation_record(evidence, before["candidates"]["A"], binding)
        return self._record("OBSERVE_A", record, expected_revision, key)


def create_real_research(explicit_new_root, name):
    project = store.create_research_project(explicit_new_root, name)
    project = store.open_existing_for_explicit_write(explicit_new_root)
    project.freeze_contract_bundle(real_bundle(project.inspect()["research_project_id"]), 1, "freeze-real-contract")
    result = RealRodProject(project)
    result.initialize_a()
    return result
