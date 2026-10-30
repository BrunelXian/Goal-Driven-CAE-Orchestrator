"""Versioned, bounded rod contracts and replay. No AF authority or execution.

G1 observations are explicitly offline substitutes. AF_REAL is intentionally
blocked until a qualified public live evidence adapter and operator seam exist.
"""

import copy
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research.rod_preview_dat import verify_dat

PROFILE = "axial_rod_cload_v1"
MODE = "REAL_ABAQUS_ROD_PREVIEW"
SOURCE = "OFFLINE_AF_SUBSTITUTE"
VERSION = "rod-preview-event-v1"
TEMPLATE = (
    "*HEADING\nR010 axial bar a19d17ea - N mm MPa\n*NODE\n1,0,0,0\n2,10,0,0\n"
    "*ELEMENT, TYPE=T3D2, ELSET=BAR\n1,1,2\n*MATERIAL, NAME=LINEAR\n*ELASTIC\n"
    "1000,0.3\n*SOLID SECTION, ELSET=BAR, MATERIAL=LINEAR\n1\n*STEP\n*STATIC\n"
    "1,1,0.00001,1\n*BOUNDARY\n1,1,3,0\n2,2,3,0\n*CLOAD\n2,1,1\n"
    "*NODE PRINT, FREQUENCY=1, SUMMARY=NO, TOTALS=NO, GLOBAL=YES\nU\nRF\n"
    "*EL PRINT, ELSET=BAR, FREQUENCY=1, POSITION=INTEGRATION POINTS, SUMMARY=NO, TOTALS=NO\n"
    "S\n*END STEP\n"
).encode("ascii")
BASELINE = "sha256:e2f91730b68f3af72b8054bc168d31b72a3f21ae186e899d64ab4b6b761523a3"


def exact(raw, keys):
    require(type(raw) is dict and set(raw) == set(keys), "INVALID_PREVIEW_FIELDS")


def token(value):
    require(type(value) is str and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", value)
            is not None and not value.startswith("fake_"), "INVALID_PREVIEW_ID")
    return value


def sha(value):
    require(type(value) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", value)
            is not None, "INVALID_DIGEST")
    return value


def decimal(value):
    require(type(value) is str and len(value) <= 32 and
            re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value) is not None,
            "INVALID_DECIMAL")
    return Decimal(value)


def timestamp(value):
    require(type(value) is str and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", value) is not None,
        "INVALID_TIMESTAMP")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        require(False, "INVALID_TIMESTAMP")
    return value


@dataclass(frozen=True)
class RodPreviewContract:
    """Immutable v1 model/goal/verification policy, never a human approval."""

    schema_version: str = "rod-preview-contract-v1"
    mode: str = MODE
    profile: str = PROFILE
    baseline_digest: str = BASELINE
    goal_min_mm: str = "0.019"
    goal_max_mm: str = "0.021"
    load_min_n: str = "0.5"
    load_max_n: str = "2.5"
    displacement_tolerance_mm: str = "0.000001"
    stress_tolerance_mpa: str = "0.0001"
    reaction_tolerance_n: str = "0.0001"
    max_solver_calls: int = 2
    target_entity: str = "node2_U1_step1_increment1"
    units: str = "N_mm_MPa"
    evidence_mode: str = SOURCE
    required_v4: bool = False
    required_odb: bool = False

    @classmethod
    def from_dict(cls, raw):
        exact(raw, cls.__dataclass_fields__)
        result = cls(**raw)
        require(result.schema_version == "rod-preview-contract-v1" and result.mode == MODE
                and result.profile == PROFILE and result.baseline_digest == BASELINE
                and digest_bytes(TEMPLATE) == BASELINE, "INVALID_PROFILE")
        require(result.evidence_mode == SOURCE, "LIVE_AF_SOURCE_UNQUALIFIED")
        require(type(result.max_solver_calls) is int and result.max_solver_calls == 2
                and result.target_entity == "node2_U1_step1_increment1"
                and result.units == "N_mm_MPa", "INVALID_POLICY")
        require(result.required_v4 is False and result.required_odb is False,
                "REQUIRED_EVIDENCE_UNAVAILABLE")
        require(Decimal("0.5") <= decimal(result.load_min_n)
                < decimal(result.load_max_n) <= Decimal("2.5"), "LOAD_RANGE")
        require(0 <= decimal(result.goal_min_mm) <= decimal(result.goal_max_mm)
                <= Decimal("1"), "GOAL_RANGE")
        for value, maximum in ((result.displacement_tolerance_mm, "0.000001"),
                               (result.stress_tolerance_mpa, "0.0001"),
                               (result.reaction_tolerance_n, "0.0001")):
            require(0 < decimal(value) <= Decimal(maximum), "INVALID_TOLERANCE")
        return result

    def digest(self):
        return digest_bytes(canonical_json(asdict(self)))


def candidate_bytes(load_n, contract, unit="N"):
    contract = RodPreviewContract.from_dict(asdict(contract))
    require(unit == "N", "WRONG_UNIT")
    require(decimal(contract.load_min_n) <= decimal(load_n) <= decimal(contract.load_max_n),
            "LOAD_RANGE")
    # Rendering and independent reconstruction accept exactly one numeric token.
    rendered = format(decimal(load_n), "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    prefix, suffix = TEMPLATE.split(b"*CLOAD\n2,1,1\n")
    return prefix + b"*CLOAD\n2,1," + rendered.encode() + b"\n" + suffix


def check_candidate(data, load_n, contract):
    require(type(data) is bytes and data == candidate_bytes(load_n, contract),
            "MODEL_MUTATION_REJECTED")
    return digest_bytes(data)


def validate_binding(raw, candidate):
    exact(raw, ("source", "managed_scope", "project_id", "project_instance_id", "plan_digest",
                "input_digest", "request_key", "output_identity", "resources_digest",
                "authorization_digest", "authorization_kind", "attempt_allowance"))
    require(raw["source"] == SOURCE, "LIVE_AF_SOURCE_UNQUALIFIED")
    require(raw["managed_scope"] is True and raw["authorization_kind"] == "TEST_ONLY"
            and type(raw["attempt_allowance"]) is int and raw["attempt_allowance"] == 1,
            "APPROVAL_UNVERIFIED")
    for field in ("project_id", "project_instance_id", "request_key", "output_identity"):
        token(raw[field])
    for field in ("plan_digest", "input_digest", "resources_digest", "authorization_digest"):
        sha(raw[field])
    require(raw["input_digest"] == candidate["input_digest"], "PLAN_INPUT_MISMATCH")
    return copy.deepcopy(raw)


def _causal(state):
    a = state["attempts"]["A"]
    require(a["status"] == "OBSERVED" and a["decision"]["V3"] == "NOT_SATISFIED"
            and all(a["decision"][v] == "PASS" for v in ("V0", "V1", "V2")),
            "A_NOT_ELIGIBLE")
    return {"a_run_id": a["observation"]["run_id"],
            "a_output_digest": a["observation"]["output_digest"],
            "a_decision_digest": digest_bytes(canonical_json(a["decision"])),
            "a_metric_mm": a["decision"]["displacement_mm"],
            "contract_digest": state["contract_digest"],
            "a_observed_revision": a["observed_revision"]}


def causal_reference(state):
    return copy.deepcopy(_causal(state))


def apply_preview(state, payload, project_id, revision, at_utc):
    """Replay performs every semantic check, not only JSON digest verification."""
    if type(payload) is dict and payload.get("schema_version") == "rod-preview-event-v2":
        from aegiscae.research.rod_bridge import apply_bridge
        return apply_bridge(state, payload, project_id, revision, at_utc)
    require(state is None or "bridge_version" not in state, "PREVIEW_ROUTE_MISMATCH")
    exact(payload, ("schema_version", "before_project_revision", "action", "key", "data"))
    require(payload["schema_version"] == VERSION
            and type(payload["before_project_revision"]) is int
            and payload["before_project_revision"] == revision, "REVISION_CONFLICT")
    token(payload["key"])
    timestamp(at_utc)
    action, data = payload["action"], payload["data"]
    if action == "FREEZE":
        require(state is None and revision == 1, "NEW_PROJECT_REQUIRED")
        contract = RodPreviewContract.from_dict(data)
        state = {"contract": asdict(contract), "contract_digest": contract.digest(),
                 "research_project_id": project_id, "attempts": {}, "keys": {},
                 "last_at_utc": at_utc, "mode": MODE, "evidence_mode": SOURCE}
    else:
        require(state is not None and at_utc >= state["last_at_utc"], "PREVIEW_NOT_FROZEN")
        state = copy.deepcopy(state)
        contract = RodPreviewContract.from_dict(state["contract"])
        if action == "ADMIT":
            exact(data, ("candidate_id", "step", "load_n", "unit", "input_digest",
                        "contract_digest", "research_project_id", "project_revision",
                        "created_at_utc", "causal"))
            token(data["candidate_id"])
            require(data["step"] in ("A", "B") and data["step"] not in state["attempts"],
                    "ATTEMPT_EXISTS")
            require(data["contract_digest"] == state["contract_digest"]
                    and data["research_project_id"] == project_id
                    and type(data["project_revision"]) is int
                    and data["project_revision"] == revision, "PROPOSAL_BINDING_MISMATCH")
            require(state["last_at_utc"] <= timestamp(data["created_at_utc"]) <= at_utc,
                    "PROPOSAL_ORDER_MISMATCH")
            require(data["input_digest"] == digest_bytes(candidate_bytes(
                data["load_n"], contract, data["unit"])), "INPUT_DIGEST_MISMATCH")
            if data["step"] == "A":
                require(not state["attempts"] and data["causal"] is None, "INVALID_A")
            else:
                require(data["causal"] == _causal(state), "CAUSAL_EVIDENCE_MISMATCH")
                require(data["candidate_id"] != state["attempts"]["A"]["candidate"]["candidate_id"]
                        and data["input_digest"] != state["attempts"]["A"]["candidate"]["input_digest"],
                        "NEW_CANDIDATE_REQUIRED")
            state["attempts"][data["step"]] = {"candidate": copy.deepcopy(data),
                "status": "ADMITTED", "binding": None, "observation": None, "decision": None}
        elif action == "INTENT":
            exact(data, ("step", "binding"))
            require(data["step"] in state["attempts"], "CANDIDATE_MISSING")
            attempt = state["attempts"][data["step"]]
            require(attempt["status"] == "ADMITTED", "INTENT_ALREADY_RECORDED")
            require(not any(a["status"] in ("INTENT", "UNKNOWN")
                            for a in state["attempts"].values()), "PENDING_OR_UNKNOWN")
            require(sum(a["binding"] is not None for a in state["attempts"].values()) < 2,
                    "BUDGET_EXHAUSTED")
            binding = validate_binding(data["binding"], attempt["candidate"])
            for other in state["attempts"].values():
                if other["binding"]:
                    require(all(binding[k] != other["binding"][k] for k in
                        ("project_id", "project_instance_id", "request_key", "output_identity",
                         "plan_digest", "authorization_digest")), "ATTEMPT_IDENTITY_REUSED")
            attempt.update(status="INTENT", binding=binding)
        elif action == "UNKNOWN":
            exact(data, ("step",))
            require(data["step"] in state["attempts"], "CANDIDATE_MISSING")
            attempt = state["attempts"][data["step"]]
            require(attempt["status"] == "INTENT", "UNKNOWN_STATE_CONFLICT")
            attempt["status"] = "UNKNOWN"
        elif action == "OBSERVE":
            exact(data, ("step", "observation"))
            require(data["step"] in state["attempts"], "CANDIDATE_MISSING")
            attempt = state["attempts"][data["step"]]
            require(attempt["status"] in ("INTENT", "UNKNOWN"), "NO_PENDING_INTENT")
            observation = data["observation"]
            exact(observation, ("binding", "run_id", "attempt_id", "receipt_digest",
                "output_digest", "solver_exit_code", "source", "dat_hex_chunks"))
            require(observation["binding"] == attempt["binding"]
                    and observation["source"] == SOURCE, "EVIDENCE_BINDING_MISMATCH")
            token(observation["run_id"])
            token(observation["attempt_id"])
            sha(observation["receipt_digest"])
            sha(observation["output_digest"])
            require(type(observation["solver_exit_code"]) is int
                    and observation["solver_exit_code"] == 0, "SOLVER_NOT_COMPLETED")
            chunks = observation["dat_hex_chunks"]
            require(type(chunks) is list and 1 <= len(chunks) <= 32
                    and all(type(c) is str and 0 < len(c) <= 1024
                            and len(c) % 2 == 0 and re.fullmatch(r"[0-9a-f]+", c)
                            for c in chunks), "INVALID_DAT_ARTIFACT")
            raw_dat = bytes.fromhex("".join(chunks))
            require(digest_bytes(raw_dat) == observation["output_digest"], "OUTPUT_DIGEST_MISMATCH")
            for other in state["attempts"].values():
                if other["observation"]:
                    require(all(observation[k] != other["observation"][k] for k in
                        ("run_id", "attempt_id", "receipt_digest", "output_digest")),
                        "OLD_OUTPUT_REUSED")
            metric = verify_dat(raw_dat, attempt["candidate"]["load_n"], asdict(contract))
            decision = {"V0": "PASS", "V1": "PASS", "V2": "PASS",
                "V3": "SATISFIED" if decimal(contract.goal_min_mm) <= Decimal(metric["displacement_mm"])
                    <= decimal(contract.goal_max_mm) else "NOT_SATISFIED",
                "V4": "NOT_ASSESSED", "ODB": "NOT_VERIFIED", **metric,
                "source": SOURCE, "real_goal": "INCONCLUSIVE", "execution_authorized": False}
            attempt.update(status="OBSERVED", observation=copy.deepcopy(observation),
                           decision=decision, observed_revision=revision + 1)
        else:
            require(False, "INVALID_PREVIEW_ACTION")
        state["last_at_utc"] = at_utc
    require(payload["key"] not in state["keys"], "DUPLICATE_EVENT_KEY")
    state["keys"][payload["key"]] = digest_bytes(canonical_json(
        {"action": action, "data": data}))
    return state
