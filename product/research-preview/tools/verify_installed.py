"""Rehearse the installed read-only entry against an explicitly supplied historical project."""
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def verify(installed, manifest_pin, project, out):
    if out.exists() or out.is_relative_to(project) or out.is_relative_to(installed):
        raise ValueError("fresh external test directory required")
    if sha(installed / "package-manifest.json") != manifest_pin:
        raise ValueError("package digest mismatch")
    manifest = read(installed / "package-manifest.json")
    for name, wanted in manifest["files"].items():
        if sha(installed / name) != wanted:
            raise ValueError(name)
    out.mkdir()
    shell = shutil.which("pwsh") or shutil.which("powershell")
    checks = []
    def invoke(label, args, *, error=None, plugin=installed, config=out/"local-config"):
        proc = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-File", str(plugin/"scripts/launch.ps1"),
                               *map(str,args)], env={**os.environ, "LOCALAPPDATA":str(config)},capture_output=True,text=True)
        output = proc.stdout + proc.stderr
        if error:
            if proc.returncode != 2 or error not in output:raise AssertionError((label, output))
        elif proc.returncode:raise AssertionError((label, output))
        checks.append(label)
        return None if error else json.loads(proc.stdout)
    def bind(pin=manifest_pin):
        return ["-Action","bind","-PythonExe",sys.executable,"-ManifestSha256",pin]
    binding=invoke("explicit interpreter bind",bind())
    pin=binding["binding_sha256"]
    doctor=["-Action","doctor","-BindingSha256",pin]
    invoke("doctor",doctor)
    def main(src,dst):
        return ["-Action","main","-BindingSha256",pin,"-ProjectRoot",src,"-OutputDirectory",dst]
    result=out/"positive"
    invoke("installed historical comparison",main(project,result))
    expected=Path(__file__).resolve().parents[1]/"release/case/difference.csv"
    with (result/"curve_difference.csv").open(newline="") as f:
        rows=len(list(csv.DictReader(f)))
    assert sha(result/"curve_difference.csv")==sha(expected) and rows==170
    checks.append("170 original reference rows, byte-exact")
    invoke("bad manifest",bind("0"*64),error="PACKAGE_MANIFEST_MISMATCH")
    invoke("binding overwrite",bind(),error="BINDING_ALREADY_EXISTS")
    invoke("bad receipt",["-Action","doctor","-BindingSha256","0"*64],error="BINDING_RECEIPT_MISMATCH")
    invoke("interpreter override",[*doctor,"-PythonExe",sys.executable],error="INTERPRETER_OVERRIDE_DENIED")
    invoke("relative interpreter",["-Action","bind","-PythonExe","python","-ManifestSha256",manifest_pin],
           error="EXPLICIT_ABSOLUTE_LOCAL_PATH_REQUIRED")
    invoke("used output",main(project,result),error="FRESH_EXTERNAL_OUTPUT_REQUIRED")
    config=out/"bad-runtime"
    cf=Path(binding["binding_file"])
    bogus=config/cf.relative_to(out/"local-config")
    bogus.parent.mkdir(parents=True)
    data=read(cf)
    data["runtime"]["runtime_files"][sys.executable]="0"*64
    bogus.write_text(json.dumps(data))
    invoke("runtime changed",["-Action","doctor","-BindingSha256",sha(bogus)],config=config,error="WORKSPACE_RUNTIME_MISMATCH")
    clone=out/"copy"
    shutil.copytree(installed,clone)
    invoke("different install path",doctor,plugin=clone,error="INSTALLATION_IDENTITY_MISMATCH")
    for file in ("references/sanity-model-protocol.md","core/sp_history.py"):
        altered=clone/file
        orig=altered.read_bytes()
        altered.write_bytes(orig+b"\n")
        invoke("modified "+file,bind(),plugin=clone,error="PACKAGE_IDENTITY_MISMATCH")
        altered.write_bytes(orig)
    (clone/"extra.txt").write_text("negative test")
    invoke("extra plugin member",bind(),plugin=clone,error="PACKAGE_FILESET_MISMATCH")
    fixture=out/"wrong-schema-project"
    for name, evidence in read(result/"report.json")["inputs"].items():
        src=project/name
        assert src.resolve().is_relative_to(project) and sha(src)==evidence["sha256"]
        dst=fixture/name
        dst.parent.mkdir(exist_ok=True,parents=True)
        shutil.copyfile(src,dst)
    curve=fixture/"run/run_014/artifacts/odb/punch_force_displacement.csv"
    curve.write_bytes(b"wrong"+curve.read_bytes())
    invoke("altered public file digest",main(fixture,out/"hash-failed"),error="PROVENANCE_HASH_MISMATCH")
    # Exercise the schema gate independently of the preceding provenance gate, in this disposable copy only.
    manifest_path=curve.parent/"manifest.json"
    records=read(manifest_path)
    matches=[r for r in records["files"] if r["path"]==curve.relative_to(fixture).as_posix()]
    assert len(matches)==1
    matches[0].update(sha256=sha(curve),size=curve.stat().st_size)
    manifest_path.write_text(json.dumps(records),encoding="utf-8")
    failure=out/"failed"
    invoke("malformed public csv",main(fixture,failure),error="CSV_SCHEMA_MISMATCH")
    assert read(failure/"failure.json")["metrics"] is None and not (failure/"curve_difference.csv").exists()
    report={"checks":checks,"count":len(checks),"reference_rows":rows,"curve_sha256":sha(expected),
            "solver_calls":0,"host_skill_activation":"NOT_TESTED","independent_acceptance":"PENDING"}
    (out/"checks.json").write_text(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("installed","project","output"):
        p.add_argument("--"+key,required=True,type=Path)
    p.add_argument("--manifest-pin",required=True)
    a=p.parse_args()
    print(json.dumps(verify(a.installed.resolve(),a.manifest_pin,a.project.resolve(),a.output.resolve()),indent=2))
