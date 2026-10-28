"""Versioned synthetic scalar admission. No filesystem access or execution authority."""

import re
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Literal

from aegiscae.contracts.research_contracts import (
    ContractBundle, ContractError, Quantity, _parse, canonical_json, digest, digest_bytes,
    identifier, require, strict_json,
)


@dataclass(frozen=True)
class FrozenRefs:
    bundle: str
    goal: str
    model: str
    verification: str


@dataclass(frozen=True)
class MutationRequest:
    schema_version: Literal["synthetic-load-v1"]
    operation: Literal["SET_LOAD_N"]
    candidate_id: str
    idempotency_key: str
    workspace_id: str
    output_identity: str
    research_project_id: str
    project_revision: int
    refs: FrozenRefs
    artifact_id: str
    baseline_digest: str
    baseline_size: int
    source_filename: Literal["baseline.txt"]
    instance: Literal["Beam"]
    entity_kind: Literal["NODE_SET"]
    entity_id: Literal["Tip"]
    step: Literal["Load"]
    frame: Literal[1]
    dof: Literal[1]
    anchor: Literal["load_tip"]
    parameter: Literal["load_magnitude"]
    old_value: Quantity
    new_value: Quantity
    lower: Quantity
    upper: Quantity

    @classmethod
    def from_dict(cls, value):
        result = _parse(cls, strict_json(canonical_json(value)))
        for field, prefix in (("candidate_id", "candidate"), ("workspace_id", "synthetic"),
                              ("output_identity", "stage"), ("research_project_id", "rp"),
                              ("artifact_id", "artifact")):
            identifier(vars(result)[field], prefix)
        require(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", result.idempotency_key) is not None,
                "INVALID_KEY")
        require(1 <= result.project_revision <= 1024 and 0 < result.baseline_size <= 8192,
                "INPUT_LIMIT")
        for value in (*asdict(result.refs).values(), result.baseline_digest):
            digest(value)
        for quantity in (result.old_value, result.new_value, result.lower, result.upper):
            quantity.validate(nonnegative=True)
            require((quantity.dimension, quantity.unit) == ("force", "N"), "UNIT_MISMATCH")
        require(result.lower.value == "0" and result.upper.value == "100", "PROFILE_LIMITS")
        require(all(Decimal("0") <= Decimal(q.value) <= Decimal("100")
                    for q in (result.old_value, result.new_value)), "OUT_OF_RANGE")
        require(result.old_value != result.new_value, "NO_CHANGE")
        return result

    def canonical_bytes(self):
        return canonical_json(asdict(self.from_dict(asdict(self))))


PREFIX = (
    b"GDCAE_SYNTHETIC_V1 NOT_ABAQUS_QUALIFIED\n"
    b"UNITS mm N s MPa\nMATERIAL E=210000\nBC FIXED=Base\n"
    b"MESH FIXED=mesh1\nCONTACT NONE\nSTEP Load\nENTITY Beam.Tip NODE_SET\n"
    b"FRAME 1\nDOF 1\nANCHOR load_tip\n"
)
PATTERN = re.compile(re.escape(PREFIX) + rb"(?:COMMENT [\x20-\x7e]{0,128}\n)?"
                     rb"LOAD_N (?P<value>[0-9.]{1,64})\nEND\n")


def parse_fixture(body):
    require(type(body) is bytes and len(body) <= 8192, "INPUT_LIMIT")
    match = PATTERN.fullmatch(body)
    require(match is not None, "UNSUPPORTED_GRAMMAR")
    value = match.group("value").decode("ascii")
    Quantity(value, "force", "N").validate(nonnegative=True)
    require(Decimal("0") <= Decimal(value) <= Decimal("100"), "OUT_OF_RANGE")
    return value, match.start("value"), match.end("value")


def validate_parent(bundle, request):
    require(type(bundle) is ContractBundle and type(request) is MutationRequest, "INVALID_TYPE")
    bundle.canonical_bytes()
    request.canonical_bytes()
    require(bundle.research_project_id == request.research_project_id
            and bundle.digests() == asdict(request.refs), "CONTRACT_BINDING_MISMATCH")
    require("load" in bundle.model.allowed_changes and "load" in bundle.goal.allowed_changes
            and "load" not in bundle.goal.forbidden_changes, "LOAD_CHANGE_FORBIDDEN")
    artifacts = bundle.model.artifacts
    require(len(artifacts) == 1 and not artifacts[0].dependencies
            and bundle.model.dependency_closure == "DECLARED_ONLY", "UNSUPPORTED_DEPENDENCIES")
    artifact = artifacts[0]
    require(artifact.role == "BASELINE" and artifact.source_kind == "SYNTHETIC_TEST_ONLY"
            and artifact.artifact_id == request.artifact_id
            and artifact.sha256 == request.baseline_digest
            and artifact.size_bytes == request.baseline_size, "BASELINE_BINDING_MISMATCH")
    require((bundle.model.length_unit, bundle.model.stress_unit) == ("mm", "MPa"), "UNIT_MISMATCH")
    require(any((e.instance, e.entity_kind, e.entity_id) == ("Beam", "NODE_SET", "Tip")
                for e in bundle.model.entities), "ENTITY_MISMATCH")
    require(any(s.step_id == "Load" and 1 in s.frames for s in bundle.model.steps), "FRAME_MISMATCH")


def coverage(bundle):
    """Derived coverage, not a reinterpretation or execution of frozen V3 rules."""
    bundle.canonical_bytes()
    rules = [
        {"id": "input_identity", "owner": "V0", "state": "REQUIRED_FOR_MUTATION"},
        {"id": "scalar_diff", "owner": "V1", "state": "REQUIRED_FOR_MUTATION"},
        {"id": "numerical_health", "owner": "V2", "state": "NOT_RUN"},
        {"id": "metric_acceptance", "owner": "V3", "state": "NOT_RUN"},
        {"id": "physical_support", "owner": "V4", "state": "NOT_ASSESSED"},
        {"id": "resource_authority", "owner": "Policy", "state": "NOT_ENFORCED_NO_EXECUTION"},
    ]
    edges = [
        {"constraint": "model.artifacts", "rules": ["input_identity", "scalar_diff"]},
        {"constraint": "goal.allowed_forbidden_changes", "rules": ["scalar_diff"]},
        {"constraint": "model.allowed_changes", "rules": ["scalar_diff"]},
        {"constraint": "verification.required_checks.V2", "rules": ["numerical_health"]},
        {"constraint": "goal.objective", "rules": ["metric_acceptance"]},
        {"constraint": "verification.required_checks.V4", "rules": ["physical_support"]},
        {"constraint": "goal.budget", "rules": ["resource_authority"]},
    ]
    edges.extend({"constraint": "goal.hard_constraints." + c.constraint_id,
                  "rules": ["metric_acceptance"]} for c in bundle.goal.hard_constraints)
    return {"schema_version": "mutation-coverage-v1", "rules": rules, "constraints": edges,
            "on_unknown": "BLOCK_REQUIRING_DECISION", "execution_authorized": False}


def edit_scalar(before, request):
    """Editor: fixed parser-selected token only. Never accepts a caller patch."""
    value, start, end = parse_fixture(before)
    require(value == request.old_value.value, "OLD_VALUE_MISMATCH")
    return before[:start] + request.new_value.value.encode("ascii") + before[end:]


def check_diff(before, after, request, bundle):
    """Independent byte/line oracle: does not call or trust the editor."""
    validate_parent(bundle, request)
    require(len(before) == request.baseline_size
            and digest_bytes(before) == request.baseline_digest, "STALE_BASELINE")
    old, start, end = parse_fixture(before)
    new, new_start, new_end = parse_fixture(after)
    require(old == request.old_value.value and new == request.new_value.value, "VALUE_MISMATCH")
    old_lines, new_lines = before.splitlines(keepends=True), after.splitlines(keepends=True)
    differences = [i for i, (left, right) in enumerate(zip(old_lines, new_lines)) if left != right]
    require(len(old_lines) == len(new_lines) and len(differences) == 1, "UNAPPROVED_DIFF")
    line = differences[0]
    require(old_lines[line] == b"LOAD_N " + old.encode() + b"\n"
            and new_lines[line] == b"LOAD_N " + new.encode() + b"\n"
            and start == new_start and before[:start] == after[:new_start]
            and before[end:] == after[new_end:], "UNAPPROVED_DIFF")
    return {"schema_version": "mutation-diff-v1", "candidate_id": request.candidate_id,
            "request_digest": digest_bytes(request.canonical_bytes()),
            "baseline_digest": digest_bytes(before), "output_digest": digest_bytes(after),
            "output_size": len(after), "byte_offset": start, "line": line + 1,
            "before_length": end - start, "after_length": new_end - new_start,
            "prefix_digest": digest_bytes(before[:start]), "suffix_digest": digest_bytes(before[end:]),
            "parameter": "load_magnitude", "qualification": "NOT_ABAQUS_QUALIFIED",
            "claim": "MODEL_MUTATION_PERMITTED_ONLY", "coverage": coverage(bundle)}


def validate_record(record, bundle):
    """Validate a historical publication record; no current file-integrity claim."""
    require(type(record) is dict and set(record) == {"schema_version", "request", "manifest",
            "workspace_binding"} and record["schema_version"] == "candidate-publication-v1",
            "INVALID_CANDIDATE_RECORD")
    request = MutationRequest.from_dict(record["request"])
    validate_parent(bundle, request)
    manifest = record["manifest"]
    require(type(manifest) is dict and set(manifest) == {
        "schema_version", "candidate_id", "request_digest", "baseline_digest", "output_digest",
        "output_size", "byte_offset", "line", "before_length", "after_length", "prefix_digest",
        "suffix_digest", "parameter", "qualification", "claim", "coverage"}, "INVALID_MANIFEST")
    require(manifest["schema_version"] == "mutation-diff-v1"
            and manifest["candidate_id"] == request.candidate_id
            and manifest["request_digest"] == digest_bytes(request.canonical_bytes())
            and manifest["baseline_digest"] == request.baseline_digest
            and manifest["parameter"] == "load_magnitude"
            and manifest["qualification"] == "NOT_ABAQUS_QUALIFIED"
            and manifest["claim"] == "MODEL_MUTATION_PERMITTED_ONLY"
            and manifest["coverage"] == coverage(bundle), "INVALID_MANIFEST")
    for key in ("output_digest", "prefix_digest", "suffix_digest"):
        digest(manifest[key])
    for key in ("output_size", "byte_offset", "line", "before_length", "after_length"):
        require(type(manifest[key]) is int and 0 < manifest[key] <= 8192, "INVALID_MANIFEST")
    require(manifest["before_length"] == len(request.old_value.value)
            and manifest["after_length"] == len(request.new_value.value)
            and manifest["output_size"] == request.baseline_size - manifest["before_length"]
            + manifest["after_length"], "INVALID_MANIFEST")
    digest(record["workspace_binding"])
    return request


def rejection(error):
    """Errors never interpolate submitted values, filesystem paths or exception text."""
    code = error.code if isinstance(error, ContractError) else "IO_OR_STATE_UNAVAILABLE"
    return {"admissibility": "UNSUPPORTED" if code.startswith("UNSUPPORTED") else "REJECTED",
            "reason": code, "execution_authorized": False}
