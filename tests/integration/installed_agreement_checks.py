"""Developer rehearsal from the installed PowerShell entry. Requires a fresh external directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

# Reuse the unit suite's synthetic engineering bundle. Never present it as a real project contract.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"unit"))
from test_research_project import proposal
from test_research_agreement import sample_terms
from aegiscae.contracts.research_contracts import ContractBundle

def verify(args):
    out=args.output.resolve()
    out.mkdir()
    project=out/"research"
    seen=[]
    def call(name, params, error=None):
        tool=[shutil.which("pwsh") or shutil.which("powershell"),"-NoProfile","-NonInteractive","-File",
              str(args.installed.resolve()/"scripts/launch.ps1"),*map(str,params)]
        run=subprocess.run(tool,capture_output=True,text=True,env={**os.environ,"LOCALAPPDATA":str(out/"settings")})
        if error:
            assert run.returncode==2 and error in run.stdout+run.stderr,(name,run.stdout,run.stderr)
            result={"blocked":error}
        else:
            assert run.returncode==0,(name,run.stdout,run.stderr)
            result=json.loads(run.stdout)
        (out/(name+".json")).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        seen.append(name)
        return result
    bind=call("bind",["-Action","bind","-PythonExe",sys.executable,"-ManifestSha256",args.manifest_pin])
    pin=bind["binding_sha256"]
    def agreement(label,operation,body=None,sel=None,error=None):
        flags=["-Action","agreement","-BindingSha256",pin,"-ProjectRoot",project,"-Operation",operation]
        if body is not None:
            path=out/(label+"-input.json")
            path.write_text(json.dumps(body))
            flags+=["-InputFile",path]
        if sel:flags+=["-Selector",sel]
        return call(label,flags,error)
    new=agreement("create","new",{"name":"Synthetic Example","schema":"research-agreement-project-v3"})
    pid=new["research_project_id"]
    base={"schema":"research-agreement-v1","project":pid}
    agreement("no-bundle","propose",dict(base,op="propose",key="one"),error="FROZEN_BUNDLE_REQUIRED")
    bundle=proposal(pid)
    freeze=agreement("freeze","freeze",dict(bundle=bundle,key="bundle",expected_revision=1))
    body=dict(base,key="one",expected_revision=2,op="propose",standing="PROVISIONAL",refs=freeze["refs"],
              terms=sample_terms(ContractBundle.from_dict(bundle)),base=None,reason="Initial proposal",impact="Exploratory only")
    v1=agreement("propose-one","propose",body)["agreement"]
    assert agreement("pending-before-first-confirm","overview")["current"] is None
    confirm=dict(base,key="yes1",expected_revision=3,op="confirm",proposal=v1,decision="CONFIRM_RESEARCH_ONLY")
    c=agreement("confirm-one","confirm",confirm)
    assert c["current_hint"]["current"]==v1 and not c["execution_authorized"]
    assert agreement("confirm-replay","confirm",confirm)["replayed"]
    for i,kind in enumerate(("candidate","result")):
        att=dict(base,key=kind,op="attribute",expected_revision=4+i,agreement=v1,kind=kind,
                 identity="first",sha256="sha256:"+hashlib.sha256(kind.encode()).hexdigest())
        if kind=="result":att["source_candidate"]={"identity":"first","sha256":"sha256:"+hashlib.sha256(b"candidate").hexdigest()}
        agreement("bind-"+kind,"attribute",att)
    two=dict(body,key="two",expected_revision=6,base=v1,standing="CONFIRMED",reason="Tighter scope",
             impact="Restrict supported claim",terms=dict(body["terms"],claim="Only sampled range"))
    v2=agreement("propose-two","propose",two)["agreement"]
    diff=agreement("diff-two","diff",sel=v2)
    assert diff["current"]==v1 and diff["changes"]["claim"]["new"]=="Only sampled range"
    assert "Tighter scope" in diff["markdown"] and "Restrict supported claim" in diff["markdown"]
    agreement("confirm-two","confirm",dict(confirm,key="yes2",proposal=v2,expected_revision=7))
    late=dict(att,key="late",expected_revision=8,identity="late-result")
    agreement("wrong-late-attribution","attribute",dict(late,agreement=v2),error="CANDIDATE_ORIGIN_MISMATCH")
    agreement("late-result-for-v1","attribute",late)
    db=project/"research.sqlite3"
    before=db.read_bytes()
    overview=agreement("overview","overview")
    detail=agreement("detail","detail")
    hint=agreement("hint","hint")
    old=agreement("historical","detail",sel=v1)
    assert overview["sections"]==detail["sections"] and set(overview["sections"])=={
        "研究目标","研究范围与约束","评价与验证标准","结论强度与适用边界"}
    assert all(heading in overview["markdown"] for heading in overview["sections"])
    assert v1==old["agreement"] and v2==hint["current"] and "v2" in hint["markdown"]
    assert old["status"]=="HISTORICAL" and len(old["attributions"])==3 and detail["record"]["refs"]==freeze["refs"]
    assert old["attributions"]["result/late-result"]["agreement"]==v1 and not detail["attributions"]
    assert "UNKNOWN independent reference" in hint["markdown"]
    for k in ("goal","model","verification","bundle"):
        assert freeze["refs"][k] in detail["markdown"]
    sp=out/"historical-report"
    call("important-SP-reply",["-Action","main","-BindingSha256",pin,"-ProjectRoot",args.historical_project.resolve(),
         "-OutputDirectory",sp,"-AgreementRoot",project])
    report=json.loads((sp/"report.json").read_bytes())
    assert report["research_agreement_hint"]==hint and hint["markdown"] in (sp/"report.md").read_text(encoding="utf-8")
    assert db.read_bytes()==before
    assert sorted(x.name for x in project.iterdir())==["research.sqlite3"]
    summary=dict(passed=seen,count=len(seen),production_calls=0,research_project=pid,v1=v1,v2=v2)
    (out/"checks.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary))

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("installed","output","historical-project"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--manifest-pin",required=True)
    verify(parser.parse_args())
