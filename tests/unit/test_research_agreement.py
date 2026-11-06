"""Offline agreement-version and compatibility tests with fresh external projects."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import sqlite3
from threading import Barrier

import pytest
from aegiscae.contracts.research_contracts import ContractBundle, ContractError, canonical_json, digest_bytes, strict_json
from aegiscae.research import project, research_agreement as a
from test_research_project import proposal

def sample_terms(bundle):
    artifact=bundle.model.artifacts[0]
    return dict(question="Which parameter changes the response?",stage_goal="Compare fixtures",
                variables=["material"],variable_ranges="UNKNOWN",comparison="Hold geometry fixed",
                criteria="Use the frozen verification contract",claim="Exploratory comparison",
                limits="Synthetic example",unknowns=["UNKNOWN independent reference"],
                revision_triggers="Changing geometry requires review",
                evidence=[dict(artifact_id=artifact.artifact_id,sha256=artifact.sha256)])

@pytest.fixture
def setup(tmp_path):
    root=tmp_path/"study"
    ro=project.create_research_project(root,"Study",research_agreements=True)
    handle=project.open_agreement_project(root,write=True)
    bundle=ContractBundle.from_dict(proposal(ro.research_project_id))
    handle.freeze_contract_bundle(bundle,1,"bundle")
    request=dict(op="propose",key="one",schema=a.SCHEMA,project=ro.research_project_id,expected_revision=2,
                 base=None,terms=sample_terms(bundle),refs=bundle.digests(),standing="PROVISIONAL",reason="Initial",impact="Exploration")
    return root,handle,bundle,request

def confirmation(p,pin,rev,key="approval"):
    return {k:p[k] for k in ("project","schema")} | dict(op="confirm",key=key,proposal=pin,
                 expected_revision=rev,decision="CONFIRM_RESEARCH_ONLY")

def test_versions(setup):
    root,h,_,p=setup
    v1=a.record_change(h,p)["agreement"]
    assert a.view(h)["current"] is None and a.view(h,"diff",v1)["status"]=="PROPOSED"
    c=confirmation(p,v1,3)
    assert not a.record_change(h,c)["replayed"]
    assert a.record_change(h,c)["replayed"]
    for idx,kind in enumerate(("candidate","result")):
        r={k:p[k] for k in ("project","schema")} | dict(op="attribute",key=kind,expected_revision=4+idx,
              agreement=v1,kind=kind,identity="first",sha256=digest_bytes(kind.encode()))
        if kind=="result":r["source_candidate"]={"identity":"first","sha256":digest_bytes(b"candidate")}
        a.record_change(h,r)
    p2=dict(p,key="two",expected_revision=6,base=v1,terms=dict(p["terms"],claim="Narrow claim"),reason="Check scope")
    v2=a.record_change(h,p2)["agreement"]
    d=a.view(h,"diff",v2)
    assert d["changes"]["claim"]==dict(old="Exploratory comparison",new="Narrow claim") and d["current"]==v1
    a.record_change(h,confirmation(p,v2,7,"confirm2"))
    ro=project.open_agreement_project(root)
    assert a.view(ro)["agreement"]==v2 and a.view(ro)["sections"]==a.view(ro,"detail")["sections"]
    old=a.view(ro,"detail",v1)
    assert old["status"]=="HISTORICAL" and len(old["attributions"])==2
    assert all(v["agreement"]==v1 for v in old["attributions"].values())
    assert old["unknowns"]==p["terms"]["unknowns"] and not old["execution_authorized"]
    with pytest.raises(ContractError,match="IMMUTABLE_ATTRIBUTION"):
        a.record_change(h,dict(r,key="relabel",agreement=v2,expected_revision=8))
    assert ro.inspect()["project_revision"]==8
    late=dict(r,key="late",identity="late-result",expected_revision=8)
    with pytest.raises(ContractError,match="CANDIDATE_ORIGIN_MISMATCH"):
        a.record_change(h,dict(late,agreement=v2))
    with pytest.raises(ContractError,match="CANDIDATE_ORIGIN_MISMATCH"):
        a.record_change(h,dict(late,source_candidate={"identity":"first","sha256":digest_bytes(b"wrong")}))
    a.record_change(h,late)
    assert a.view(ro,"detail",v1)["attributions"]["result/late-result"]["agreement"]==v1
    assert a.view(ro,"detail",v2)["attributions"]=={}

@pytest.mark.parametrize("change,error",[
    ("cross_project","PROJECT_IDENTITY"),("wrong_refs","STALE_BASE"),("wrong_evidence","INVALID_EVIDENCE"),
    ("wrong_variables","VARIABLE_OUTSIDE"),("stale_revision","REVISION_CONFLICT")])
def test_invalid_reference(setup,change,error):
    _,h,_,p=setup
    bad=deepcopy(p)
    if change=="cross_project":bad["project"]="rp_"+"0"*32
    if change=="wrong_refs":bad["refs"]["verification"]=digest_bytes(b"missing")
    if change=="wrong_evidence":bad["terms"]["evidence"][0]["sha256"]=digest_bytes(b"wrong")
    if change=="wrong_variables":bad["terms"]["variables"]=["geometry"]
    if change=="stale_revision":bad["expected_revision"]=1
    with pytest.raises(ContractError,match=error):a.record_change(h,bad)
    assert h.inspect()["audit_count"]==2

def test_fault_and_stale(setup,monkeypatch):
    _,h,_,p=setup
    first=a.record_change(h,p)
    second=a.record_change(h,dict(p,key="second",expected_revision=3,reason="Alternate"))
    c=confirmation(p,first["agreement"],4)
    with monkeypatch.context() as m:
        def fail(stage):
            if stage=="agreement_before_commit":raise RuntimeError("fault")
        m.setattr(project,"_fault",fail)
        with pytest.raises(RuntimeError):a.record_change(h,c)
    assert h.inspect()["audit_count"]==4 and a.view(h)["current"] is None
    with pytest.raises(ContractError,match="EXPLICIT_PROPOSAL"):a.record_change(h,dict(c,decision="YES"))
    a.record_change(h,c)
    with pytest.raises(ContractError,match="STALE_BASE"):a.record_change(h,confirmation(p,second["agreement"],5,"confirm-second"))
    with pytest.raises(ContractError,match="IDEMPOTENCY_CONFLICT"):a.record_change(h,dict(c,decision="OTHER"))
    assert a.view(h,"diff",second["agreement"])["status"]=="STALE_PROPOSAL"

def test_concurrent_confirmation(setup):
    _,h,_,p=setup
    pin=a.record_change(h,p)["agreement"]
    c=confirmation(p,pin,3)
    barrier=Barrier(2)
    def worker():
        barrier.wait()
        try:return a.record_change(h,c)
        except project.ProjectError as exc:
            if exc.code!="STORE_BUSY":raise
            return None
    with ThreadPoolExecutor(2) as pool:
        futures=[pool.submit(worker) for _ in range(2)]
        results=[f.result() for f in futures]
    assert sum(r is not None and not r["replayed"] for r in results)==1
    assert a.record_change(h,c)["replayed"] and h.inspect()["audit_count"]==4

@pytest.mark.parametrize("rod",[False,True])
def test_legacy_opt_out(tmp_path,rod):
    root=tmp_path/"old"
    old=project.create_research_project(root,"Old",rod_preview=rod)
    db=root/"research.sqlite3"
    before=db.read_bytes()
    with pytest.raises(project.ProjectError,match="OPT_IN_REQUIRED"):project.open_agreement_project(root,write=True)
    assert db.read_bytes()==before and old.inspect()["schema_version"]==(2 if rod else 1)

def test_missing_bundle_and_legacy_writer(tmp_path):
    root=tmp_path/"empty"
    p=project.create_research_project(root,"Empty",research_agreements=True)
    h=project.open_agreement_project(root,write=True)
    assert a.view(p)["status"]=="NO_CONFIRMED_AGREEMENT"
    with pytest.raises(ContractError,match="FROZEN_BUNDLE_REQUIRED"):a.record_change(h,{"key":"x"})
    with pytest.raises(project.ProjectError,match="WRITE_SCOPE"):project.open_existing_for_explicit_write(root)
    with pytest.raises(project.ProjectError,match="WRITE_SCOPE"):h.record_reopen_failure_observation("STORE_BUSY")
    assert p.inspect()["project_revision"]==1

def test_changed_bundle_invalidates_unconfirmed_proposal(setup):
    _,h,_,p=setup
    pin=a.record_change(h,p)["agreement"]
    new=proposal(h.research_project_id)
    new["version"]=2
    h.freeze_contract_bundle(ContractBundle.from_dict(new),3,"freeze-next")
    with pytest.raises(ContractError,match="STALE_BASE_OR_CONTRACT_REFERENCE"):
        a.record_change(h,confirmation(p,pin,4))
    assert a.view(h,"diff",pin)["status"]=="STALE_PROPOSAL" and not a.view(h)["current"]

def test_rollback_after_failed_proposal_is_not_published(setup,monkeypatch):
    root,h,_,p=setup
    db=root/"research.sqlite3"
    before=db.read_bytes()
    def fail(stage):
        if stage=="agreement_before_commit":raise RuntimeError("injected")
    with monkeypatch.context() as m:
        m.setattr(project,"_fault",fail)
        with pytest.raises(RuntimeError,match="injected"):a.record_change(h,p)
    assert db.read_bytes()==before and a.view(project.open_agreement_project(root))["project_revision"]==2

@pytest.mark.parametrize("rod",[False,True])
def test_relabeling_old_metadata_does_not_enable_agreements(tmp_path,rod):
    root=tmp_path/"tampered-fixture"
    project.create_research_project(root,"Fixture",rod_preview=rod)
    db=root/"research.sqlite3"
    con=sqlite3.connect(db)
    try:
        meta=strict_json(con.execute("SELECT body FROM project").fetchone()[0])
        meta["schema_version"]=3
        body=canonical_json(meta)
        con.execute("UPDATE project SET body=?, digest=?",(body,digest_bytes(body)))
        con.commit()
    finally:con.close()
    before=db.read_bytes()
    with pytest.raises(project.ProjectError,match="INTEGRITY_ERROR"):project.open_agreement_project(root,write=True)
    assert db.read_bytes()==before
