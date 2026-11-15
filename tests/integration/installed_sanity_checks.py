"""Exercise the public ZIP launcher in new A-only projects. Never load CAE or a solver."""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
from test_research_project import proposal
from test_research_agreement import sample_terms
from aegiscae.contracts.research_contracts import ContractBundle, canonical_json, digest_bytes


def verify(plugin, pin, out):
    out.mkdir()
    shell = shutil.which("pwsh") or shutil.which("powershell")
    project = out / "research"
    env = dict(os.environ, LOCALAPPDATA=str(out / "settings"))
    env.pop("PYTHONPATH", None)
    results = {}

    def call(label, flags, expected=None):
        run = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-File", str(plugin/"scripts/launch.ps1"),
                              *map(str, flags)], env=env, capture_output=True, text=True, timeout=50)
        decoded = json.loads(run.stdout)
        assert run.returncode == (2 if expected else 0), (label,decoded,run.stderr)
        if expected:
            assert decoded["error"] == expected, (label,decoded)
        results[label] = {"exit":run.returncode, "output":decoded}
        return decoded

    binding = call("bind", ["-Action","bind","-ManifestSha256",pin,"-PythonExe",sys.executable])["binding_sha256"]
    def agreement(label, op, data=None, expected=None):
        flags = ["-Action","agreement","-BindingSha256",binding,"-Operation",op,"-ProjectRoot",project]
        if data is not None:
            path = out / (label + "-input.json")
            path.write_bytes(canonical_json(data))
            flags += ["-InputFile",path]
        return call(label,flags,expected)

    pid = agreement("new","new",dict(name="Sanity Qualification Test",schema="research-agreement-project-v3"))["research_project_id"]
    def triage(label, availability, file=None, concerns=None, result="NONE"):
        return agreement(label,"sanity-triage",dict(schema="research-sanity-v1",op="sanity-triage",
            use="Small-Punch material inversion", availability=availability, asset_file=file,
            concerns=concerns or [],result_scope=result))
    db = project / "research.sqlite3"
    initial = db.read_bytes()
    (out/"supplied.inp").write_bytes(b"*PART, NAME=A\n*MATERIAL, NAME=M\n*BOUNDARY\n")
    pending = triage("model-without-validation","EXISTING","supplied.inp")
    assert pending["status"] == "QUALIFICATION_PENDING" and "material" in pending["facts"] and "material" in pending["unknowns"]
    absent = triage("no-model","NONE")
    assert absent["status"] == "CANDIDATE" and "geometry" in absent["recommendation"]
    assert triage("unknown-availability","UNKNOWN")["status"] == "QUALIFICATION_PENDING"
    (out/"opened.cae").write_bytes(b"opaque synthetic bytes, reported opened by user")
    doubts = triage("reported-open-but-doubtful","EXISTING","opened.cae",["material","bc"])
    assert doubts["status"] == "INCONCLUSIVE" and doubts["level"] == "L0" and set(doubts["facts"]) == {"identity"}
    (out/"unresolved.inp").write_bytes(b"*NODE\n1,0,0,0\n")
    assert triage("automatic-definition-gaps","EXISTING","unresolved.inp")["inferences"]
    (out/"prior.odb").write_bytes(b"synthetic placeholder for result identity only")
    old = triage("result-outside-claim","EXISTING","prior.odb",result="OUTSIDE_USE")
    assert old["status"] == "INCONCLUSIVE" and old["validation"] is None and db.read_bytes() == initial

    scope = "synthetic-axial-compliance-mm-N-v1"
    fixture = dict(schema=scope,length_mm=100,area_mm2=1,modulus_MPa=200000,bc="fixed-free",
                   load="axial-tip",regime="uniaxial-linear-elastic")
    raw = canonical_json(fixture)
    (out/"bar.json").write_bytes(raw)
    ref = {"force_N":[0,20,40],"displacement_mm":["0","0.01","0.02"]}
    bundle = proposal(pid)
    bundle["model"]["model_family"] = "SyntheticAxialBar"
    bundle["model"]["artifacts"][0].update(sha256=digest_bytes(raw),size_bytes=len(raw))
    bundle["verification"]["physical_reference"] = dict(reference_id="bar_analytic",kind="ANALYTIC",
        sha256=digest_bytes(canonical_json(ref)),applicability=[scope])
    frozen = agreement("freeze","freeze",dict(bundle=bundle,key="freeze",expected_revision=1))
    base = dict(schema="research-sanity-v1",project=pid,refs=frozen["refs"])
    req = dict(base,op="sanity-assess",key="inspect",expected_revision=2,use=scope,availability="EXISTING",
               asset_file="bar.json",concerns=[],result_scope="NONE")
    assessed = agreement("qualified-scoped","sanity-assess",req)
    assert assessed["status"] == "QUALIFIED" and assessed["contract_status"] == "DECLARED_ONLY"
    assert assessed["validation"]["computed_mm"] == ["0","0.01","0.02"] and not assessed["execution_authorized"]
    assert agreement("replay","sanity-assess",req)["replayed"]
    agreement("forged-observation","sanity-assess",dict(req,observation={}),"EXPLICIT_ASSET_FIELD_REQUIRED")
    agreement("traversal","sanity-assess",dict(req,asset_file="../bar.json"),"EXPLICIT_SIBLING_ASSET_REQUIRED")
    ag = dict(schema="research-agreement-v1",project=pid)
    v = agreement("propose","propose",dict(ag,op="propose",key="prop",expected_revision=3,standing="PROVISIONAL",
        terms=sample_terms(ContractBundle.from_dict(bundle)),refs=frozen["refs"],base=None,reason="Fixture",impact="Scoped"))["agreement"]
    agreement("confirm","confirm",dict(ag,op="confirm",key="yes",expected_revision=4,proposal=v,decision="CONFIRM_RESEARCH_ONLY"))
    candidate = digest_bytes(b"synthetic candidate")
    agreement("attribute","attribute",dict(ag,op="attribute",key="cand",expected_revision=5,agreement=v,
              kind="candidate",identity="fixture-B",sha256=candidate))
    link = dict(base,op="sanity-reference",key="link",expected_revision=6,use=scope,assessment=assessed["assessment"],candidate="fixture-B")
    agreement("wrong-use","sanity-reference",dict(link,use="Small-Punch"),"QUALIFIED_BASELINE_REQUIRED")
    linked = agreement("candidate-lineage","sanity-reference",link)
    assert linked["baseline_version"] == 1 and linked["candidate_sha256"] == candidate and linked["contract_refs"] == frozen["refs"]
    assert agreement("detail","detail")["sanity_references"]["fixture-B"]["assessment"] == assessed["assessment"]
    assert "QUALIFIED" in agreement("hint","hint")["markdown"]
    wrong = agreement("other-use","sanity-assess",dict(req,use="Small-Punch",key="other",expected_revision=7))
    assert wrong["status"] != "QUALIFIED"
    agreement("stale-baseline","sanity-reference",dict(link,key="stale",expected_revision=8),"QUALIFIED_BASELINE_REQUIRED")
    (out/"bar.json").write_bytes(raw + b" ")
    altered = agreement("changed-bytes","sanity-assess",dict(req,key="changed",expected_revision=8))
    assert altered["status"] == "INCONCLUSIVE"
    (out/"bar.json").write_bytes(raw)
    revision_two = deepcopy(bundle)
    revision_two["version"] = revision_two["model"]["version"] = 2
    revision_two["model"]["dependency_closure"] = "INCOMPLETE"
    next_bundle = agreement("freeze-v2","freeze",dict(bundle=revision_two,key="freeze-v2",expected_revision=9))
    agreement("old-contract-reference","sanity-reference",dict(link,key="after-v2",expected_revision=10),
              "STALE_SANITY_CONTEXT")
    incomplete = agreement("incomplete-contract","sanity-assess",dict(req,key="v2",expected_revision=10,refs=next_bundle["refs"]))
    assert incomplete["status"] == "QUALIFICATION_PENDING" and incomplete["dependency_closure"] == "INCOMPLETE"
    historical = agreement("v1-lineage-after-v2","detail")["sanity_references"]["fixture-B"]
    assert historical["baseline_version"] == 1 and historical["contract_refs"] == frozen["refs"]
    (out/"checks.json").write_text(json.dumps(results,indent=2,ensure_ascii=True))
    print(json.dumps(dict(checks=len(results),names=list(results),manifest=pin)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--installed",type=Path,required=True)
    parser.add_argument("--manifest-pin",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    assert hashlib.sha256((args.installed/"package-manifest.json").read_bytes()).hexdigest() == args.manifest_pin
    verify(args.installed.resolve(),args.manifest_pin,args.output.resolve())
