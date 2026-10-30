"""Explicit offline real-preview contract adapter using ResearchProject transactions.

No dispatcher, scheduler, AF Store import, network, process launch or grant minting.
Only a newly created schema-2 Project can use this path. The existing synthetic
schema-1 coordinator and its records are unchanged. Live dispatch remains blocked.
"""

from dataclasses import asdict

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research import project as store
from aegiscae.research.rod_preview_rules import (
    SOURCE, VERSION, RodPreviewContract, apply_preview, candidate_bytes,
    causal_reference, token,
)


def _fault(stage):
    """Trusted offline fault injection seam, not a caller-supplied callback."""


def _replay(meta, events):
    require(meta["schema_version"] == 2, "PREVIEW_SCHEMA_REQUIRED")
    state = None
    for event in events:
        if event["kind"] == "WORKFLOW_RECORDED":
            state = apply_preview(state, event["workflow"], meta["research_project_id"],
                                  event["project_revision"] - 1, event["at_utc"])
    return state


def _view(state, meta):
    require(state is not None, "PREVIEW_NOT_FROZEN")
    pending = any(a["status"] in ("INTENT", "UNKNOWN", "G2_INTENT", "G2_UNKNOWN")
                  for a in state["attempts"].values())
    held = sum(a["binding"] is not None for a in state["attempts"].values())
    return {**state, "project_revision": meta["project_revision"],
            "budget": {"maximum": 2, "held_or_charged": held, "available": 2 - held},
            "pending_or_unknown": pending, "real_goal": "INCONCLUSIVE",
            "human_approval": "NOT_ESTABLISHED", "execution_authorized": False,
            "live_dispatch": "BLOCKED_LIVE_DISPATCH_UNREGISTERED",
            "hil_isolation": "BLOCKED_HIL_STRONG_ISOLATION"}


def create_preview(explicit_new_root, name, contract):
    require(type(contract) is RodPreviewContract, "INVALID_PREVIEW_CONTRACT")
    contract = RodPreviewContract.from_dict(asdict(contract))
    store.create_research_project(explicit_new_root, name, rod_preview=True)
    project = store.open_existing_for_explicit_write(explicit_new_root)
    adapter = RealPreviewAdapter(project)
    adapter._record("FREEZE", asdict(contract), 1, "freeze-preview")
    return adapter


class RealPreviewAdapter:
    """Bounded v1 persistence seam; an intent is never an execution permission."""

    def __init__(self, project):
        require(type(project) is store.ResearchProject, "INVALID_PROJECT")
        self.project = project

    def inspect(self):
        with self.project._snapshot() as (_, meta, _bundles, events):
            return _view(_replay(meta, events), meta)

    def causal_reference(self):
        return causal_reference(self.inspect())

    def candidate_input(self, step):
        state = self.inspect()
        require(step in state["attempts"], "CANDIDATE_MISSING")
        return candidate_bytes(state["attempts"][step]["candidate"]["load_n"],
                               RodPreviewContract.from_dict(state["contract"]))

    def _record(self, action, data, expected_revision, key, *, event_version=VERSION):
        require(type(expected_revision) is int and 1 <= expected_revision <= 1023,
                "INVALID_REVISION")
        token(key)
        request_digest = digest_bytes(canonical_json({"action": action, "data": data}))
        with self.project._snapshot(write=True) as (connection, meta, _bundles, events):
            state = _replay(meta, events)
            if state and key in state["keys"]:
                require(state["keys"][key] == request_digest, "IDEMPOTENCY_CONFLICT")
                return {**_view(state, meta), "replayed": True}
            require(meta["project_revision"] == expected_revision, "REVISION_CONFLICT")
            payload = {"schema_version": event_version, "before_project_revision": expected_revision,
                       "action": action, "key": key, "data": data}
            at_utc = store._utc()
            state = apply_preview(state, payload, meta["research_project_id"],
                                  expected_revision, at_utc)
            store._commit_workflow_event(connection, meta, state["contract_digest"], payload,
                                         at_utc=at_utc)
            _fault("preview_before_commit")
            connection.commit()
            _fault("preview_after_commit")
            return {**_view(state, meta), "replayed": False}

    def admit(self, proposal, expected_revision, key):
        return self._record("ADMIT", proposal, expected_revision, key)

    def record_intent(self, step, binding, expected_revision, key):
        return self._record("INTENT", {"step": step, "binding": binding}, expected_revision, key)

    def mark_unknown(self, step, expected_revision, key):
        return self._record("UNKNOWN", {"step": step}, expected_revision, key)

    def observe(self, step, observation, expected_revision, key):
        """G1 accepts only explicitly marked substitutes, never Agent-asserted AF_REAL."""
        require(type(observation) is dict and observation.get("source") == SOURCE,
                "LIVE_AF_SOURCE_UNQUALIFIED")
        return self._record("OBSERVE", {"step": step, "observation": observation},
                            expected_revision, key)
