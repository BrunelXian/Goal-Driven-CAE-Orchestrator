"""Independent bounded consumption of AF public TEST_ONLY evidence bundles.

The public port owns acquisition. No AF import, filesystem access, private Store,
Grant, launcher or new persistent schema is introduced here. A matching digest
proves internal consistency, not origin authentication or execution authority.
"""

import copy

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research.rod_evidence import (
    af_digest, check_fake_evidence, check_plan_ref, opaque, seal_envelope, verify_envelope,
)
from aegiscae.research.rod_preview import RealPreviewAdapter
from aegiscae.research.rod_preview_rules import RodPreviewContract, exact, sha, token


BUNDLE_FIELDS = ("schema", "source", "rod_plan_ref", "rod_plan_ref_digest",
    "contract_revisions", "fake_plan", "receipt", "run", "events", "validations",
    "synthetic_envelope", "raw_solver_logs", "real_solver_executed",
    "real_source_authentication", "V2", "V4", "ODB", "bindings_digest")
PUBLIC_FAKE_FIELDS = ("schema", "source", "project_id", "project_instance_id", "plan_id",
    "plan_digest", "backend_id", "backend_version", "input_digest", "input_size",
    "resources_digest", "output_identity", "configuration_digest", "execution_authorized")
SOURCES = ("AF_FAKE_IPC_PLUS_SYNTHETIC_DAT",
           "OFFLINE_PUBLIC_PORT_FIXTURE_PLUS_SYNTHETIC_DAT")
GOAL_COMPONENT = ("goal_min_mm", "goal_max_mm", "target_entity", "units")
MODEL_COMPONENT = ("profile", "baseline_digest", "load_min_n", "load_max_n", "units")


def _component_digest(contract, fields):
    return digest_bytes(canonical_json({key: contract[key] for key in fields}))


def _public_plan(plan, expected):
    exact(plan, PUBLIC_FAKE_FIELDS)
    require(plan["schema"] == "af-public-fake-plan-v1"
            and plan["source"] == "PERSISTED_FAKE_PLAN"
            and plan["backend_id"] == "fake-v1"
            and type(plan["backend_version"]) is int and plan["backend_version"] == 1
            and plan["execution_authorized"] is False, "PUBLIC_FAKE_PLAN_REQUIRED")
    for key in ("project_id", "project_instance_id", "plan_id"):
        opaque(plan[key])
    for key in ("plan_digest", "input_digest", "resources_digest", "output_identity",
                "configuration_digest"):
        sha(plan[key])
    require(type(plan["input_size"]) is int and 0 < plan["input_size"] <= 1048576,
            "PUBLIC_FAKE_INPUT_INVALID")
    require(all(plan[key] == expected[key] for key in ("project_id", "project_instance_id",
            "plan_id", "plan_digest", "input_digest", "output_identity")),
            "PUBLIC_FAKE_PLAN_MISMATCH")


class PublicRodEvidence:
    """Read-only verifier; returned public acquisition records are not approvals."""

    def __init__(self, preview):
        require(type(preview) is RealPreviewAdapter, "INVALID_PREVIEW_ADAPTER")
        self.preview = preview

    def frozen_identity(self):
        """Derive component identities from one committed combined-contract freeze.

        goal_revision/model_revision in the AF interface are request pins. Both
        mean this shared bundle's freeze project revision, not independently
        versioned GoalContract/ModelContract records. No historical data changes.
        """
        state = self.preview.inspect()
        events = []
        for offset in range(0, 1024, 64):
            page = self.preview.project.audit_events(offset, 64)
            events.extend(page)
            if len(page) < 64:
                break
        require(len(events) < 1024, "AUDIT_LIMIT")
        freezes = [e for e in events if e["kind"] == "WORKFLOW_RECORDED"
                   and e["workflow"].get("action") == "FREEZE"]
        require(len(freezes) == 1, "UNIQUE_FREEZE_REQUIRED")
        event = freezes[0]
        require(event["project_revision"] == 2
                and event["workflow"]["before_project_revision"] == 1
                and event["workflow"]["data"] == state["contract"]
                and event["bundle_digest"] == state["contract_digest"],
                "FROZEN_COMPONENT_MISMATCH")
        contract = RodPreviewContract.from_dict(state["contract"])
        require(contract.digest() == state["contract_digest"], "FROZEN_COMPONENT_MISMATCH")
        require(self.preview.inspect() == state, "RESEARCH_CHANGED_DURING_READ")
        return {"schema": "gdcae-rod-frozen-component-identity-v1",
            "research_project_id": state["research_project_id"],
            "contract_digest": state["contract_digest"],
            "shared_bundle_freeze_revision": event["project_revision"],
            "goal_component_digest": _component_digest(state["contract"], GOAL_COMPONENT),
            "model_component_digest": _component_digest(state["contract"], MODEL_COMPONENT),
            "freeze_event_digest": digest_bytes(canonical_json(event)),
            "current_project_revision": state["project_revision"]}

    def _context(self, revision, fake_evidence):
        require(type(revision) is int, "INVALID_REVISION")
        state = self.preview.inspect()
        require(state["project_revision"] == revision, "REVISION_CONFLICT")
        require(state.get("bridge_version") == "rod-preview-event-v2"
                and "A" in state["attempts"], "PUBLIC_A_CONTEXT_REQUIRED")
        attempt = state["attempts"]["A"]
        require(attempt["status"] in ("G2_INTENT", "G2_UNKNOWN", "G2_OBSERVED")
                and attempt["inert_plan"] is not None, "PUBLIC_A_CONTEXT_REQUIRED")
        require(state["budget"]["held_or_charged"] in (1, 2)
                and state["real_solver_calls"] == 0, "INVALID_BUDGET_STATE")
        proof = check_fake_evidence(fake_evidence, attempt["binding"])
        identity = self.frozen_identity()
        require(identity["current_project_revision"] == revision, "REVISION_CONFLICT")
        return state, attempt, proof, identity

    def verify(self, bundle, *, expected_revision, fake_evidence, expected_identity=None):
        """Check raw public records, exact committed identities and numerical bytes.

        expected_identity optionally pins a previously derived frozen identity.
        Caller-supplied PASS, real-source labels or revision claims cannot unlock
        Solver verification, B execution or an independent Operator approval.
        """
        bundle, raw = copy.deepcopy(bundle), copy.deepcopy(fake_evidence)
        exact(bundle, BUNDLE_FIELDS)
        require(bundle["schema"] == "af-rod-public-evidence-bundle-v1"
                and bundle["source"] in SOURCES
                and bundle["raw_solver_logs"] == "ABSENT_NOT_REAL_SOLVER"
                and bundle["real_solver_executed"] is False
                and bundle["real_source_authentication"] == bundle["V2"] == "NOT_VERIFIED"
                and bundle["V4"] == "NOT_ASSESSED" and bundle["ODB"] == "NOT_VERIFIED",
                "PUBLIC_SOURCE_UNQUALIFIED")
        state, attempt, proof, identity = self._context(expected_revision, raw)
        if expected_identity is not None:
            require(expected_identity == identity, "FROZEN_COMPONENT_MISMATCH")
        revisions = bundle["contract_revisions"]
        exact(revisions, ("goal_revision", "model_revision", "research_revision"))
        require(all(type(value) is int for value in revisions.values())
                and revisions["goal_revision"] == revisions["model_revision"]
                == identity["shared_bundle_freeze_revision"]
                and revisions["research_revision"] == attempt["inert_plan"]["research_revision"],
                "PUBLIC_REVISION_MISMATCH")
        plan = bundle["rod_plan_ref"]
        require(plan == attempt["inert_plan"] and bundle["rod_plan_ref_digest"] == af_digest(plan),
                "PUBLIC_ROD_PLAN_MISMATCH")
        contract = RodPreviewContract.from_dict(state["contract"])
        check_plan_ref(plan, candidate=attempt["candidate"], contract=contract,
            research_project_id=state["research_project_id"],
            research_revision=attempt["inert_plan"]["research_revision"])
        _public_plan(bundle["fake_plan"], attempt["binding"])
        for key in ("receipt", "run", "events", "validations"):
            require(bundle[key] == raw[key], "PUBLIC_RAW_RECORD_MISMATCH")
        run = bundle["run"]
        require(type(run.get("revision")) is int and run["revision"] == 4
                and "retry_of" in run
                and run.get("process_observation") == "NOT_APPLICABLE"
                and run.get("exit_verification") == "NOT_APPLICABLE",
                "PUBLIC_RUN_REVISION_INVALID")
        require(len(bundle["events"]) == 4, "PUBLIC_HISTORY_INCOMPLETE")
        for index, event in enumerate(bundle["events"], 1):
            # Some AF project events have no attempt field. If present, it must
            # agree; Run and validation always require the exact attempt.
            require(event.get("phase_attempt_id") in (None, proof["binding"]["phase_attempt_id"]),
                    "PUBLIC_ATTEMPT_MISMATCH")
            require(type(event.get("run_sequence")) is int and event["run_sequence"] == index
                    and type(event.get("payload")) is dict
                    and type(event["payload"].get("revision")) is int
                    and event["payload"]["revision"] == index, "PUBLIC_HISTORY_INCOMPLETE")
        final_refs = bundle["events"][-1].get("evidence_refs")
        require(type(final_refs) is list and 0 < len(final_refs) <= 32,
                "PUBLIC_EVIDENCE_REFS_MISSING")
        for ref in final_refs:
            opaque(ref)
        for validation in bundle["validations"]:
            refs = validation.get("evidence_refs")
            require(type(refs) is list and 0 < len(refs) <= 8, "PUBLIC_EVIDENCE_REFS_MISSING")
            opaque(validation.get("validation_id"))
            for ref in refs:
                opaque(ref)
            require(set(refs + [validation["validation_id"]]) <= set(final_refs),
                    "PUBLIC_EVIDENCE_REFS_MISMATCH")
        envelope = bundle["synthetic_envelope"]
        sealed = seal_envelope(envelope)
        projection = {key: value for key, value in bundle.items() if key != "bindings_digest"}
        projection["synthetic_envelope"] = {key: value for key, value in envelope.items()
                                            if key != "dat_bytes"}
        require(bundle["bindings_digest"] == af_digest(projection), "PUBLIC_BUNDLE_DIGEST_MISMATCH")
        numerical = verify_envelope(sealed, expected_plan=plan, expected_link=proof["binding"],
                                    candidate=attempt["candidate"], contract=contract)
        if attempt["status"] == "G2_OBSERVED":
            require(raw == attempt["fake_evidence"] and sealed == attempt["observation"],
                    "PUBLIC_OBSERVATION_CONFLICT")
        require(self.preview.inspect() == state, "RESEARCH_CHANGED_DURING_READ")
        return {"schema": "gdcae-rod-public-verification-v1", "source": bundle["source"],
            "frozen_identity": identity, "bindings_digest": bundle["bindings_digest"],
            "public_fake_plan_digest": af_digest(bundle["fake_plan"]),
            "raw_evidence_digest": proof["raw_evidence_digest"],
            "receipt_digest": proof["receipt_digest"], "run_digest": af_digest(run),
            "events_digest": af_digest(bundle["events"]),
            "validations_digest": af_digest(bundle["validations"]),
            "output_digest": numerical["output_digest"],
            "acquisition_checks": "PASS_TEST_ONLY", "real_provenance": "NOT_VERIFIED",
            "V0": "NOT_VERIFIED", "V1": "MODEL_CONTRACT_CHECKED", "V2": "NOT_VERIFIED",
            "V3": "INCONCLUSIVE", "V4": "NOT_ASSESSED", "ODB": "NOT_VERIFIED",
            "fixture_checks": numerical["fixture_checks"], "metrics": numerical["metrics"],
            "raw_solver_logs": "ABSENT_NOT_REAL_SOLVER", "real_goal": "INCONCLUSIVE",
            "real_solver_calls": 0, "execution_authorized": False,
            "human_approval": "NOT_ESTABLISHED", "public_record_persisted": False}

    def read(self, port, *, expected_revision, fake_evidence, evidence_key,
             output_digest, at_time):
        """Read an offline or retained immutable public snapshot exactly once.

        A live IPC bundle must first be acquired while its Owner is alive, then
        the Owner closed and its actual close proof supplied to ``verify``. This
        convenience method does not reopen an Owner after it has been closed.
        """
        raw = copy.deepcopy(fake_evidence)
        state, attempt, proof, identity = self._context(expected_revision, raw)
        token(evidence_key)
        sha(output_digest)
        require(type(at_time) is int and at_time >= 0, "INVALID_TIME")
        link = proof["binding"]
        bundle = port.read_test_evidence(rod_plan_ref=copy.deepcopy(attempt["inert_plan"]),
            fake_plan_ref=copy.deepcopy(attempt["binding"]), run_id=link["run_id"],
            receipt_id=link["receipt_id"], phase_attempt_id=link["phase_attempt_id"],
            evidence_key=evidence_key, output_digest=output_digest,
            goal_revision=identity["shared_bundle_freeze_revision"],
            model_revision=identity["shared_bundle_freeze_revision"], at_time=at_time)
        require(self.preview.inspect() == state, "RESEARCH_CHANGED_DURING_READ")
        result = self.verify(bundle, expected_revision=expected_revision, fake_evidence=raw,
                             expected_identity=identity)
        require(bundle["synthetic_envelope"]["evidence_key"] == evidence_key
                and result["output_digest"] == output_digest, "PUBLIC_LOOKUP_MISMATCH")
        return result
