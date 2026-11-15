"""Purpose-bound research assessments replayed in the v3 ResearchProject audit."""
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
import re

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require, strict_json
from aegiscae.research import project

PROFILE = "synthetic-axial-compliance-mm-N-v1"
# Independent closed-form reference for the single educational fixture,
# 100 mm bar, 200000 MPa, 1 mm². No empirical or Abaqus claim.
REFERENCE = {"force_N": [0, 20, 40], "displacement_mm": ["0", "0.01", "0.02"]}
FIELDS = ("identity", "geometry", "mesh", "material", "region", "step", "load",
          "bc", "interaction", "outputs", "units", "dependencies", "assumptions")
CARDS = {"geometry": ("PART", "ASSEMBLY"), "mesh": ("NODE", "ELEMENT"),
         "material": ("MATERIAL", "ELASTIC", "PLASTIC"), "region": ("SOLID SECTION", "SHELL SECTION"),
         "step": ("STEP",), "load": ("CLOAD", "DLOAD"), "bc": ("BOUNDARY",),
         "interaction": ("CONTACT", "CONTACT PAIR"), "outputs": ("OUTPUT", "NODE OUTPUT", "ELEMENT OUTPUT"),
         "dependencies": ("INCLUDE",)}
BAR = {"schema": PROFILE, "length_mm": 100, "area_mm2": 1, "modulus_MPa": 200000,
       "bc": "fixed-free", "load": "axial-tip", "regime": "uniaxial-linear-elastic"}


def observe(folder, filename):
    """Read only an explicitly supplied sibling asset. Never follow model dependencies."""
    require(isinstance(filename, str) and re.fullmatch(r"[\w -]{1,96}\.(inp|cae|py|odb|json)", filename, re.I),
            "EXPLICIT_SIBLING_ASSET_REQUIRED")
    path = project._path(Path(folder) / filename, directory=False)
    require(path.stat().st_size <= 64 * 1024 * 1024, "ASSET_SIZE_LIMIT")
    with path.open("rb") as stream:
        data = stream.read(64 * 1024 * 1024 + 1)
    require(len(data) <= 64 * 1024 * 1024, "ASSET_SIZE_LIMIT")
    kind = path.suffix.lower()
    observation = {"format": kind, "sha256": digest_bytes(data), "size": len(data), "cards": [], "bar": None}
    if kind == ".inp":
        # Only keyword presence is retained. No claim about effective state, region membership or values.
        keywords = {m.group(1).strip().upper() for m in re.finditer(
            rb"(?m)^[ \t]*\*([A-Za-z][A-Za-z ]*)(?=,|[ \t]*\r?$)", data)}
        observation["cards"] = sorted(card for cards in CARDS.values() for card in cards if card.encode() in keywords)
    if kind == ".json" and len(data) <= 65536:
        decoded = strict_json(data)
        if canonical_json(decoded) == canonical_json(BAR):
            observation["bar"] = BAR
    return observation


def assess(bundle, request):
    """Compute qualification from captured evidence. No user-settable status or acceptance flag."""
    require(set(request) == {"schema", "op", "project", "expected_revision", "key", "use", "availability",
                            "observation", "concerns", "result_scope", "refs"}, "INVALID_SANITY_FIELDS")
    use, availability, obs = request["use"], request["availability"], request["observation"]
    require(isinstance(use, str) and use.isprintable() and 0 < len(use.strip()) <= 180, "INVALID_USE")
    require(availability in ("EXISTING", "NONE", "UNKNOWN") and (obs is None or availability == "EXISTING"),
            "ASSET_STATUS_CONFLICT")
    concerns = request["concerns"]
    require(isinstance(concerns, list) and all(x in FIELDS for x in concerns) and
            request["result_scope"] in ("NONE", "UNREVIEWED", "OUTSIDE_USE"), "INVALID_EVIDENCE_SCOPE")
    model = bundle.model if bundle else None
    baseline = next(a for a in model.artifacts if a.role == "BASELINE") if model else None
    facts, findings = {}, []
    status, level = "QUALIFICATION_PENDING", None
    next_step = "Identify the explicit baseline and request independent evidence matched to the intended use."
    if availability == "NONE":
        status, next_step = "CANDIDATE", "Draft geometry, material law, boundary/contact conditions, outputs and an independent comparison before building."
    if obs is not None:
        require(type(obs) is dict and set(obs) == {"format","sha256","size","cards","bar"}, "INVALID_OBSERVATION")
        require(obs["format"] in (".cae",".inp",".odb",".py",".json") and re.fullmatch(r"sha256:[0-9a-f]{64}",obs["sha256"])
                and type(obs["size"]) is int and 0 <= obs["size"] <= 64*1024*1024, "INVALID_OBSERVATION")
        facts["identity"] = obs["sha256"]
        level = "L0"
        for field, allowed in CARDS.items():
            present = sorted(set(obs["cards"]).intersection(allowed))
            if present:
                facts[field] = {"keyword_presence_only": present}
        if obs["cards"]:
            level = "L1_KEYWORDS_ONLY"
        if obs["format"] == ".inp" and "INCLUDE" not in obs["cards"]:
            for field in ("material", "bc"):
                if field not in facts:
                    findings.append(field + ": no recognized definition in the supplied deck; check alternative formulations")
        if obs["format"] == ".odb" or (baseline and (obs["sha256"], obs["size"]) != (baseline.sha256, baseline.size_bytes)):
            status = "INCONCLUSIVE"
    validation = None
    ref = bundle.verification.physical_reference if bundle else None
    if (bundle and obs and obs["format"] == ".json" and obs["bar"] == BAR and use == PROFILE and status != "INCONCLUSIVE"
            and (obs["sha256"], obs["size"]) == (digest_bytes(canonical_json(BAR)),len(canonical_json(BAR)))
            and model.model_family == "SyntheticAxialBar" and model.dependency_closure == "DECLARED_ONLY"
            and len(model.artifacts) == 1 and not baseline.dependencies and baseline.source_kind == "SYNTHETIC_TEST_ONLY"
            and (model.length_unit, model.force_unit, model.stress_unit) == ("mm","N","MPa")
            and ref and ref.kind == "ANALYTIC" and ref.sha256 == digest_bytes(canonical_json(REFERENCE))
            and ref.applicability == (PROFILE,) and not concerns and request["result_scope"] == "NONE"):
        bar = obs["bar"]
        predicted = [Decimal(f)*bar["length_mm"]/(bar["area_mm2"]*Decimal(bar["modulus_MPa"])) for f in REFERENCE["force_N"]]
        accepted = predicted == list(map(Decimal, REFERENCE["displacement_mm"]))
        validation = {"profile": PROFILE, "analytic_reference": REFERENCE, "reference_sha256": ref.sha256,
                      "computed_mm": list(map(str, predicted)), "criterion": "exact decimal equality at all three forces",
                      "scope": "synthetic axial compliance arithmetic only; no FE mesh, real material or solver validation"}
        facts.update(geometry=[bar["length_mm"],bar["area_mm2"]], material=bar["modulus_MPa"], bc=bar["bc"],
                     load=bar["load"], assumptions=bar["regime"], units=["mm","N","MPa"], dependencies=[])
        status, level = ("QUALIFIED","L5_SCOPED") if accepted else ("INCONCLUSIVE","L1")
        next_step = "Reference this version only for the named analytical fixture."
    if concerns or findings or request["result_scope"] != "NONE":
        status, next_step = "INCONCLUSIVE", "Resolve the flagged definitions or obtain an independent result for this use."
    unknown = [f for f in FIELDS if f not in facts or isinstance(facts[f],dict)]
    return {"use": use, "availability": availability, "status": status, "level": level, "facts": facts,
            "inferences": findings, "unknowns": unknown, "reported_concerns": concerns, "result_scope": request["result_scope"],
            "recommendation": next_step, "baseline_id": model.baseline_id if model else None, "baseline_version": model.version if model else None,
            "artifacts": [asdict(a) for a in model.artifacts] if model else [], "contract_refs": bundle.digests() if bundle else None,
            "contract_status": model.semantic_status if model else None, "dependency_closure": model.dependency_closure if model else None,
            "allowed_changes": list(bundle.goal.allowed_changes) if bundle else [], "fixed_categories": list(bundle.goal.forbidden_changes) if bundle else [],
            "declared_conditions": {k: list(getattr(model,k)) for k in ("boundary_assumptions","contact_assumptions",
                                  "material_assumptions","applicability_limits")} if model else {}, "validation": validation,
            "permitted_work": ["discussion","qualification planning","separately authorized exploration"],
            "execution_authorized": False}


def apply_event(state, request, bundle, revision):
    require(request["project"] == bundle.research_project_id and request["refs"] == bundle.digests()
            and request["expected_revision"] == revision, "STALE_SANITY_CONTEXT")
    project._validate_key(request["key"])
    require(request["key"] not in state["keys"], "IDEMPOTENCY_CONFLICT")
    if request["op"] == "sanity-assess":
        result = assess(bundle, request)
        receipt = digest_bytes(canonical_json(request))
        state["assessments"][receipt] = dict(result, assessment=receipt)
        state["last_assessment"] = receipt
        result = state["assessments"][receipt]
    else:
        require(request["op"] == "sanity-reference" and set(request) == {"schema","op","project","expected_revision",
                "key","refs","use","assessment","candidate"}, "INVALID_SANITY_REFERENCE")
        baseline = state["assessments"].get(request["assessment"])
        require(baseline and baseline["status"] == "QUALIFIED" and baseline["use"] == request["use"]
                and baseline["contract_refs"] == request["refs"] and request["assessment"] == state["last_assessment"],
                "QUALIFIED_BASELINE_REQUIRED")
        candidate = state["attributions"].get("candidate/"+request["candidate"])
        require(candidate and state["active"] == candidate["agreement"] and
                state["versions"][candidate["agreement"]]["refs"] == request["refs"], "ATTRIBUTED_CANDIDATE_REQUIRED")
        require(request["candidate"] not in state["sanity_links"], "IMMUTABLE_BASELINE_REFERENCE")
        result = {"candidate": request["candidate"], "candidate_sha256": candidate["sha256"],
                  "assessment": request["assessment"], "baseline_version": baseline["baseline_version"],
                  "baseline_id":baseline["baseline_id"], "use": request["use"], "contract_refs": request["refs"],
                  "execution_authorized": False}
        state["sanity_links"][request["candidate"]] = result
    response = dict(result, project_revision=revision+1)
    state["keys"][request["key"]] = (digest_bytes(canonical_json(request)),response)
    return response
