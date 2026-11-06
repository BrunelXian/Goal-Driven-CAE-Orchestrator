"""Research-only agreement events in an explicitly opted-in ResearchProject audit stream."""
import re

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research import project as store

SCHEMA = "research-agreement-v1"
SECTIONS = (
    ("研究目标", ("question", "stage_goal")),
    ("研究范围与约束", ("variables", "variable_ranges", "comparison")),
    ("评价与验证标准", ("criteria", "evidence")),
    ("结论强度与适用边界", ("claim", "limits", "unknowns", "revision_triggers")),
)
LABELS = dict(question="研究问题", stage_goal="阶段目标", variables="变量", variable_ranges="变量范围",
              comparison="比较条件", criteria="判据", evidence="证据引用", claim="允许的主张",
              limits="适用范围", unknowns="关键 UNKNOWN", revision_triggers="修订条件")
def empty_state():
    return {"versions": {}, "active": None, "confirmed": {}, "keys": {}, "attributions": {}}

def text_field(value):
    require(type(value) is str and 0 < len(value.strip()) <= 512 and value.isprintable(), "INVALID_AGREEMENT_TEXT")

def sha(value):
    return digest_bytes(canonical_json(value))

def validate_terms(terms, bundle):
    require(type(terms) is dict and set(terms) == set(LABELS), "INVALID_RESEARCH_TERMS")
    for key in terms.keys() - {"variables","evidence","unknowns"}:
        text_field(terms[key])
    for key in ("variables", "unknowns", "evidence"):
        require(type(terms[key]) is list and len(terms[key]) <= 32, "INVALID_RESEARCH_TERMS")
    for value in terms["variables"] + terms["unknowns"]:
        text_field(value)
    require(set(terms["variables"]) <= set(bundle.goal.allowed_changes)
            and len(set(terms["variables"])) == len(terms["variables"]), "VARIABLE_OUTSIDE_CONTRACT")
    anchors = {a.artifact_id:a.sha256 for a in bundle.model.artifacts}
    seen = set()
    for ref in terms["evidence"]:
        require(type(ref) is dict and set(ref) == {"artifact_id","sha256"} and
                type(ref["artifact_id"]) is str and ref["artifact_id"] in anchors and
                anchors[ref["artifact_id"]] == ref["sha256"] and ref["artifact_id"] not in seen, "INVALID_EVIDENCE_REFERENCE")
        seen.add(ref["artifact_id"])

def apply_agreement(state, request, bundle, revision):
    """Used identically before writing and during strict audit replay."""
    common = {"schema","project","expected_revision","key","op"}
    fields = {"propose":{"base","refs","terms","reason","impact","standing"},
              "confirm":{"proposal","decision"}, "attribute":{"agreement","kind","identity","sha256"}}
    if isinstance(request, dict) and request.get("kind") == "result":
        fields["attribute"].add("source_candidate")
    require(type(request) is dict and type(request.get("op")) is str and request["op"] in fields
            and set(request) == common | fields[request["op"]] and request["schema"] == SCHEMA, "INVALID_AGREEMENT_REQUEST")
    require(request["project"] == bundle.research_project_id, "PROJECT_IDENTITY_MISMATCH")
    require(type(request["expected_revision"]) is int and request["expected_revision"] == revision, "REVISION_CONFLICT")
    key = request["key"]
    store._validate_key(key)
    require(key not in state["keys"], "IDEMPOTENCY_CONFLICT")
    op = request["op"]
    active = state["active"]
    if op == "propose":
        require(request["base"] == active and request["refs"] == bundle.digests(), "STALE_BASE_OR_CONTRACT_REFERENCE")
        validate_terms(request["terms"], bundle)
        for field in ("reason","impact"):
            text_field(request[field])
        require(request["standing"] in ("PROVISIONAL","CONFIRMED"), "INVALID_STANDING")
        record = sha(request)
        state["versions"][record] = {"version":len(state["versions"])+1, "proposal":record, **request}
    elif op == "confirm":
        record = request["proposal"]
        require(type(record) is str and record in state["versions"] and request["decision"] == "CONFIRM_RESEARCH_ONLY",
                "EXPLICIT_PROPOSAL_CONFIRMATION_REQUIRED")
        proposal = state["versions"][record]
        require(proposal["base"] == active and proposal["refs"] == bundle.digests(), "STALE_BASE_OR_CONTRACT_REFERENCE")
        state["confirmed"][record] = revision + 1
        state["active"] = record
    else:
        record = request["agreement"]
        require(request["kind"] in ("candidate","result") and type(request["identity"]) is str
                and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}",request["identity"])
                and type(request["sha256"]) is str and re.fullmatch(r"sha256:[0-9a-f]{64}",request["sha256"]),
                "INVALID_ATTRIBUTION")
        target = request["kind"] + "/" + request["identity"]
        require(target not in state["attributions"], "IMMUTABLE_ATTRIBUTION")
        source = request.get("source_candidate")
        if request["kind"] == "candidate":
            require(active is not None and record == active and state["versions"][active]["refs"] == bundle.digests(),
                    "CURRENT_AGREEMENT_REQUIRED")
        else:
            require(type(source) is dict and set(source) == {"identity","sha256"} and type(source["identity"]) is str,
                    "SOURCE_CANDIDATE_REQUIRED")
            candidate = state["attributions"].get("candidate/"+source["identity"])
            require(candidate is not None and candidate["sha256"] == source["sha256"] and
                    candidate["agreement"] == record, "CANDIDATE_ORIGIN_MISMATCH")
        state["attributions"][target] = {"agreement":record,"sha256":request["sha256"],"declared_at_revision":revision+1,
                                         "source_candidate":source,"provenance":"RESEARCHER_DECLARED"}
    response = {"agreement":record,"project_revision":revision+1,"execution_authorized":False}
    state["keys"][key] = (sha(request), response)
    return response

def record_change(project, request):
    state = {}
    with project._snapshot(write=True, agreement_state=state) as (connection, meta, bundles, _):
        require(type(request) is dict and type(request.get("key")) is str, "INVALID_AGREEMENT_REQUEST")
        previous = state["keys"].get(request["key"])
        if previous:
            require(previous[0] == sha(request), "IDEMPOTENCY_CONFLICT")
            return dict(previous[1], replayed=True)
        require(bundles, "FROZEN_BUNDLE_REQUIRED")
        bundle, digest = bundles[-1][:2]
        response = apply_agreement(state, request, bundle, meta["project_revision"])
        store._commit_workflow_event(connection, meta, digest, request)
        store._fault("agreement_before_commit")
        connection.commit()
        return dict(response, replayed=False)

def view(project, mode="overview", selector=None):
    require(mode in ("overview","detail","diff","hint"), "UNKNOWN_VIEW")
    state = {}
    with project._snapshot(agreement_state=state) as (_, meta, bundles, _events):
        active = state["active"]
        record = selector if selector is not None else active
        if record is None and mode=="diff":
            require(False, "PROPOSAL_ID_REQUIRED")
        version = state["versions"].get(record)
        require(record is None or version is not None, "AGREEMENT_NOT_FOUND")
        status = "NO_CONFIRMED_AGREEMENT"
        if version:
            if record == active:
                status = version["standing"]
            elif record in state["confirmed"]:
                status = "HISTORICAL"
            elif version["base"] == active and bundles[-1][1] == version["refs"]["bundle"]:
                status = "PROPOSED"
            else:
                status = "STALE_PROPOSAL"
        result = {"project":meta["research_project_id"], "project_revision":meta["project_revision"],
                  "agreement":record,"current":active,"version":version and version["version"],"status":status,
                  "unknowns":version["terms"]["unknowns"] if version else ["UNKNOWN"],"execution_authorized":False}
        if mode == "detail" and version:
            result["record"] = version
            result["confirmation_revision"] = state["confirmed"].get(record)
            result["attributions"] = {k:v for k,v in state["attributions"].items() if v["agreement"]==record}
        if mode == "diff":
            old = state["versions"].get(version["base"])
            result.update(base=version["base"],reason=version["reason"],impact=version["impact"])
            after = dict(version["terms"],refs=version["refs"],standing=version["standing"])
            before = dict(old["terms"],refs=old["refs"],standing=old["standing"]) if old else {}
            result["changes"] = {k:{"old":before.get(k),"new":v} for k,v in after.items() if v!=before.get(k)}
        if version and mode in ("overview","detail"):
            result["sections"] = {heading:{LABELS[k]:version["terms"][k] for k in keys} for heading,keys in SECTIONS}
        return result
