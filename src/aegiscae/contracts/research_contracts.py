"""Version 1 research proposals: deterministic data, never execution authority."""

import hashlib
import json
import re
import types
from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal
from typing import Literal, get_args, get_origin, get_type_hints


class ContractError(ValueError):
    """Only a fixed code is exposed, never submitted data or paths."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code="INVALID_CONTRACT"):
    if not condition:
        raise ContractError(code)


def _bounded(value):
    count = 0

    def visit(item, depth):
        nonlocal count
        count += 1
        require(count <= 8192 and depth <= 16, "INPUT_LIMIT")
        if type(item) is dict:
            for key, child in item.items():
                require(type(key) is str and len(key) <= 64)
                visit(child, depth + 1)
        elif type(item) in (tuple, list):
            require(len(item) <= 128, "INPUT_LIMIT")
            for child in item:
                visit(child, depth + 1)
        elif type(item) is str:
            require(len(item) <= 1024 and "\x00" not in item, "INPUT_LIMIT")
        else:
            require(item is None or type(item) is bool
                    or (type(item) is int and 0 <= item < 2**63), "INVALID_NUMBER")

    visit(value, 0)


def canonical_json(value):
    _bounded(value)
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False).encode("ascii")
    require(len(encoded) <= 65536, "INPUT_LIMIT")
    return encoded


def digest_bytes(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def strict_json(value):
    require(type(value) in (bytes, str) and len(value) <= 65536, "INPUT_LIMIT")

    def pairs(items):
        result = {}
        for key, item in items:
            require(key not in result, "DUPLICATE_KEY")
            result[key] = item
        return result

    try:
        result = json.loads(value, object_pairs_hook=pairs)
        _bounded(result)
        return result
    except ContractError:
        raise
    except (ValueError, TypeError, RecursionError):
        raise ContractError("INVALID_JSON") from None


def _parse(kind, value):
    origin, args = get_origin(kind), get_args(kind)
    if origin is Literal:
        require(any(type(value) is type(option) and value == option for option in args))
    elif origin is types.UnionType:
        if value is None and type(None) in args:
            return None
        return _parse(next(arg for arg in args if arg is not type(None)), value)
    elif origin is tuple:
        require(type(value) is list)
        return tuple(_parse(args[0], item) for item in value)
    elif is_dataclass(kind):
        require(type(value) is dict and set(value) == {f.name for f in fields(kind)},
                "INVALID_KEYS")
        hints = get_type_hints(kind)
        return kind(**{name: _parse(hints[name], item) for name, item in value.items()})
    else:
        require(type(value) is kind, "INVALID_TYPE")
    return value


def identifier(value, prefix):
    require(type(value) is str and re.fullmatch(prefix + r"_[0-9a-f]{32}", value)
            is not None, "INVALID_ID")


def token(value):
    require(type(value) is str and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", value)
            is not None, "INVALID_LABEL")


def digest(value):
    require(type(value) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None,
            "INVALID_DIGEST")


def _text(value):
    require(type(value) is str and 0 < len(value) <= 256, "INVALID_METADATA")
    require(not re.search(r"[\\/]|[A-Za-z]:|(?i:credential|password|secret|token|dpapi)", value),
            "UNSAFE_METADATA")


UNITS = {"length": {"m", "mm"}, "force": {"N"}, "stress": {"Pa", "MPa"},
         "time": {"s"}, "dimensionless": {"1"}}
METRICS = {"displacement": ("length", {"U1", "U2", "U3", "magnitude"}),
           "stress": ("stress", {"S11", "S22", "S33", "mises"}),
           "reaction_force": ("force", {"RF1", "RF2", "RF3", "magnitude"}),
           "strain": ("dimensionless", {"E11", "E22", "E33"})}
CATEGORIES = {"geometry", "mesh", "material", "boundary", "load", "contact",
              "step", "integration", "postprocess"}


@dataclass(frozen=True)
class Quantity:
    value: str
    dimension: str
    unit: str

    def validate(self, nonnegative=False):
        require(type(self.value) is str and len(self.value) <= 64
                and re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?", self.value)
                is not None and self.value != "-0", "NONCANONICAL_DECIMAL")
        number = Decimal(self.value)
        require(number.is_finite() and (not nonnegative or number >= 0), "INVALID_NUMBER")
        require(self.unit in UNITS.get(self.dimension, set()), "UNIT_MISMATCH")


@dataclass(frozen=True)
class Selector:
    instance: str
    entity_kind: Literal["NODE_SET", "ELEMENT_SET", "REGION"]
    entity_id: str
    step: str
    frame: int
    time: Quantity | None


@dataclass(frozen=True)
class EvidenceRequirement:
    metric_id: str
    component: str
    selector: Selector
    dimension: str
    unit: str


@dataclass(frozen=True)
class ScientificConstraint:
    constraint_id: str
    evidence: EvidenceRequirement
    comparator: Literal["LE", "GE", "EQ"]
    threshold: Quantity
    tolerance: Quantity


@dataclass(frozen=True)
class BudgetPolicy:
    max_solver_calls: int
    max_candidate_proposals: int
    max_auto_turns: int | None
    auto_turn_enforcement: Literal["NOT_ENFORCED"]


@dataclass(frozen=True)
class GoalContract:
    schema_version: Literal[1]
    goal_id: str
    version: int
    research_project_id: str
    objective: EvidenceRequirement
    comparator: Literal["LE", "GE", "EQ"]
    target: Quantity
    tolerance: Quantity
    hard_constraints: tuple[ScientificConstraint, ...]
    allowed_changes: tuple[str, ...]
    forbidden_changes: tuple[str, ...]
    required_evidence: tuple[str, ...]
    on_unknown: Literal["BLOCK"]
    budget: BudgetPolicy
    approval_source: str | None


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    role: Literal["BASELINE", "INCLUDE", "AUXILIARY"]
    sha256: str
    size_bytes: int
    source_identity: str
    source_kind: Literal["SYNTHETIC_TEST_ONLY", "DECLARED_EXTERNAL"]
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class Entity:
    instance: str
    entity_kind: Literal["NODE_SET", "ELEMENT_SET", "REGION"]
    entity_id: str


@dataclass(frozen=True)
class AnalysisStep:
    step_id: str
    frames: tuple[int, ...]
    frame_times: tuple[Quantity, ...]


@dataclass(frozen=True)
class ModelContract:
    schema_version: Literal[1]
    baseline_id: str
    version: int
    research_project_id: str
    model_family: str
    artifacts: tuple[Artifact, ...]
    length_unit: Literal["m", "mm"]
    force_unit: Literal["N"]
    time_unit: Literal["s"]
    stress_unit: Literal["Pa", "MPa"]
    entities: tuple[Entity, ...]
    steps: tuple[AnalysisStep, ...]
    assumptions: tuple[str, ...]
    material_assumptions: tuple[str, ...]
    boundary_assumptions: tuple[str, ...]
    contact_assumptions: tuple[str, ...]
    integration_assumptions: tuple[str, ...]
    applicability_limits: tuple[str, ...]
    allowed_changes: tuple[str, ...]
    dependency_closure: Literal["DECLARED_ONLY", "INCOMPLETE"]
    semantic_status: Literal["DECLARED_ONLY"]


@dataclass(frozen=True)
class RequiredChecks:
    V0: Literal[True]
    V1: Literal[True]
    V2: Literal[True]
    V3: Literal[True]
    V4: bool


@dataclass(frozen=True)
class ValidatorReference:
    level: Literal["V0", "V1", "V2", "V3", "V4"]
    validator_id: str
    version: str
    sha256: str


@dataclass(frozen=True)
class PhysicalReference:
    reference_id: str
    kind: Literal["ANALYTIC", "BENCHMARK", "EXPERIMENTAL", "INDEPENDENT_MODEL"]
    sha256: str
    applicability: tuple[str, ...]


@dataclass(frozen=True)
class HardConstraintCheck:
    """A declared V3 rule, never a computed verification result."""

    constraint_id: str
    level: Literal["V3"]
    rule: ScientificConstraint


@dataclass(frozen=True)
class VerificationContract:
    schema_version: Literal[1]
    verification_id: str
    version: int
    research_project_id: str
    required_checks: RequiredChecks
    required_evidence: tuple[EvidenceRequirement, ...]
    hard_constraint_checks: tuple[HardConstraintCheck, ...]
    goal_tolerance: Quantity
    validators: tuple[ValidatorReference, ...]
    physical_reference: PhysicalReference | None
    on_unknown: Literal["BLOCK"]


@dataclass(frozen=True)
class ContractBundle:
    schema_version: Literal[1]
    bundle_id: str
    version: int
    research_project_id: str
    goal: GoalContract
    model: ModelContract
    verification: VerificationContract

    @classmethod
    def from_dict(cls, value):
        # Detached data, no mutable references retained from caller-owned maps.
        parsed = _parse(cls, strict_json(canonical_json(value)))
        parsed.validate()
        return parsed

    def canonical_bytes(self):
        parsed = self.from_dict(asdict(self))
        return canonical_json(asdict(parsed))

    def digests(self):
        raw = strict_json(self.canonical_bytes())
        return {**{name: digest_bytes(canonical_json(raw[name]))
                   for name in ("goal", "model", "verification")},
                "bundle": digest_bytes(canonical_json(raw))}

    def validate(self):
        identifier(self.research_project_id, "rp")
        identifier(self.bundle_id, "bundle")
        for item, name, prefix in ((self.goal, "goal_id", "goal"),
                                   (self.model, "baseline_id", "baseline"),
                                   (self.verification, "verification_id", "verification")):
            identifier(vars(item)[name], prefix)
            require(item.research_project_id == self.research_project_id, "PROJECT_MISMATCH")
            require(1 <= item.version <= 1000000, "INVALID_VERSION")
        require(1 <= self.version <= 1000000, "INVALID_VERSION")
        goal, model, verification = self.goal, self.model, self.verification
        token(model.model_family)
        require((model.length_unit, model.stress_unit) in {("m", "Pa"), ("mm", "MPa")},
                "UNIT_SYSTEM_MISMATCH")
        for group in (goal.allowed_changes, goal.forbidden_changes, model.allowed_changes):
            require(len(set(group)) == len(group) and set(group) <= CATEGORIES, "INVALID_CATEGORY")
        require(not set(goal.allowed_changes) & set(goal.forbidden_changes)
                and set(goal.allowed_changes) <= set(model.allowed_changes), "CHANGE_SCOPE_CONFLICT")
        require(goal.required_evidence and len(set(goal.required_evidence)) == len(goal.required_evidence)
                and set(goal.required_evidence) <= {"PROVENANCE", "MODEL_INTEGRITY", "SOLVER_REPORT",
                                                   "NUMERICAL_CHECK", "GOAL_METRIC", "PHYSICS_REFERENCE"})
        for value in (goal.budget.max_solver_calls, goal.budget.max_candidate_proposals,
                      goal.budget.max_auto_turns):
            require(value is None or 0 <= value <= 1000000, "INVALID_BUDGET")
        if goal.approval_source is not None:
            _text(goal.approval_source)
        require(model.artifacts and len({a.artifact_id for a in model.artifacts}) == len(model.artifacts))
        require(sum(a.role == "BASELINE" for a in model.artifacts) == 1)
        for artifact in model.artifacts:
            identifier(artifact.artifact_id, "artifact")
            digest(artifact.sha256)
            token(artifact.source_identity)
            require(artifact.size_bytes <= 64 * 1024 * 1024, "ARTIFACT_LIMIT")
            require(len(set(artifact.dependencies)) == len(artifact.dependencies)
                    and artifact.artifact_id not in artifact.dependencies, "INVALID_DEPENDENCY")
            for dependency in artifact.dependencies:
                identifier(dependency, "artifact")
        require(model.entities and len(set(model.entities)) == len(model.entities), "AMBIGUOUS_ENTITY")
        for entity in model.entities:
            token(entity.instance)
            token(entity.entity_id)
        require(model.steps and len({s.step_id for s in model.steps}) == len(model.steps),
                "AMBIGUOUS_STEP")
        for step in model.steps:
            token(step.step_id)
            require(step.frames and len(set(step.frames)) == len(step.frames), "AMBIGUOUS_FRAME")
            require(len(step.frames) == len(step.frame_times), "AMBIGUOUS_FRAME")
            for frame_time in step.frame_times:
                frame_time.validate(nonnegative=True)
                require(frame_time.dimension == "time" and frame_time.unit == model.time_unit,
                        "UNIT_MISMATCH")
        for group in (model.assumptions, model.material_assumptions, model.boundary_assumptions,
                      model.contact_assumptions, model.integration_assumptions, model.applicability_limits):
            require(bool(group), "MISSING_DECLARATION")
            for value in group:
                _text(value)
        _evidence(goal.objective, model)
        _quantities(goal.objective, goal.target, goal.tolerance)
        require(len({c.constraint_id for c in goal.hard_constraints}) == len(goal.hard_constraints))
        for constraint in goal.hard_constraints:
            token(constraint.constraint_id)
            _evidence(constraint.evidence, model)
            _quantities(constraint.evidence, constraint.threshold, constraint.tolerance)
        require(verification.required_evidence and goal.objective in verification.required_evidence,
                "VERIFICATION_SCOPE_MISMATCH")
        for evidence in verification.required_evidence:
            _evidence(evidence, model)
        checks = verification.hard_constraint_checks
        require(len({c.constraint_id for c in checks}) == len(checks)
                and {c.constraint_id for c in checks}
                == {c.constraint_id for c in goal.hard_constraints}, "UNCOVERED_HARD_CONSTRAINT")
        rules = {c.constraint_id: c for c in goal.hard_constraints}
        for check in checks:
            require(check.rule == rules[check.constraint_id]
                    and check.rule.evidence in verification.required_evidence,
                    "HARD_CONSTRAINT_RULE_MISMATCH")
        require(verification.goal_tolerance == goal.tolerance, "VERIFICATION_TOLERANCE_MISMATCH")
        require(len(verification.validators) == 5
                and {v.level for v in verification.validators} == {"V0", "V1", "V2", "V3", "V4"},
                "MISSING_VALIDATOR")
        for validator in verification.validators:
            token(validator.validator_id)
            token(validator.version)
            digest(validator.sha256)
        if verification.physical_reference is not None:
            ref = verification.physical_reference
            token(ref.reference_id)
            digest(ref.sha256)
            require(bool(ref.applicability))
            for declaration in ref.applicability:
                _text(declaration)


def _evidence(evidence, model):
    dimension, components = METRICS.get(evidence.metric_id, (None, set()))
    require(dimension == evidence.dimension and evidence.component in components, "METRIC_MISMATCH")
    expected = {"length": model.length_unit, "stress": model.stress_unit,
                "force": model.force_unit, "dimensionless": "1"}
    require(evidence.unit == expected.get(dimension), "UNIT_MISMATCH")
    selector = evidence.selector
    require(Entity(selector.instance, selector.entity_kind, selector.entity_id) in model.entities,
            "ENTITY_MISMATCH")
    require(any(s.step_id == selector.step and selector.frame in s.frames for s in model.steps),
            "FRAME_MISMATCH")
    if selector.time is not None:
        selector.time.validate(nonnegative=True)
        require(selector.time.dimension == "time" and selector.time.unit == model.time_unit,
                "UNIT_MISMATCH")
        step = next(s for s in model.steps if s.step_id == selector.step)
        require(selector.time == step.frame_times[step.frames.index(selector.frame)], "TIME_MISMATCH")


def _quantities(evidence, target, tolerance):
    target.validate()
    tolerance.validate(nonnegative=True)
    require((target.dimension, target.unit) == (evidence.dimension, evidence.unit)
            == (tolerance.dimension, tolerance.unit), "UNIT_MISMATCH")
