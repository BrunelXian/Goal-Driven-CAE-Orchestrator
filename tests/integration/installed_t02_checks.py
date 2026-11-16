"""Exercise the installed T02 operations with a disposable handoff and real vendor stdio.
Supply an installed Research Preview, its independent manifest digest and the reviewed source checkout.
"""
import argparse
import json
import os
from pathlib import Path
import runpy
import shutil
import sys

from engineering_intake import ROOT, backend_fixture, fingerprint, inventory, run_json
from prepare_abq_service import provision


def verify(plugin, pin, source, work):
    work.mkdir()
    env = dict(os.environ, LOCALAPPDATA=str(work/"settings"))
    env.pop("PYTHONPATH", None)
    env.pop("CODEX_THREAD_ID", None)
    shell = shutil.which("pwsh")
    assert shell and fingerprint(plugin/"package-manifest.json") == pin
    configure = runpy.run_path(str(ROOT/"product/research-preview/tools/test_main_fixture.py"))["configure"]
    scope, caller = configure(plugin, pin, env, shell)
    launcher = [shell, "-NoProfile", "-File", plugin/"scripts/launch.ps1"]
    binding = run_json([*launcher, "-Action","bind","-PythonExe",sys.executable,"-ManifestSha256",pin],env)
    common = [*launcher,"-Action","agreement","-ProjectRoot",work/"project","-BindingSha256",binding["binding_sha256"],*scope]

    def op(name, body=None, error=None):
        command = [*common, "-Operation",name]
        if body is not None:
            path = work/"input.json"
            path.write_text(json.dumps(body), encoding="utf8")
            command += ["-InputFile",path]
        return run_json(command,caller,reason=error)

    project = op("new",{"name":"engineering","schema":"research-agreement-project-v3"})["research_project_id"]
    def change(key, rev, data):
        return dict(project=project,host="fixture",desktop_project="fixture-project",key=key,expected_revision=rev,data=data)

    drafts = {tid: dict(goal=tid,deliverable="Evidence",criterion="Independent readback",refs=[]) for tid in ("T01","T02")}
    op("task-init",change("intake",1,dict(summary="Disposable isolated test",drafts=drafts)))
    queue = {"queue_id":"q_fixture"}
    op("t02-plan",queue,"SERVICE_DEPLOYMENT_MISSING")
    op("t02-plan",dict(queue,command="ignored"),"INVALID_T02_REQUEST")
    backend = backend_fixture(source,work,env)
    before = inventory(work/"backend-a")
    provision(source,"fixture","fixture-project",work/"backend-a",backend,Path(env["LOCALAPPDATA"]))
    base = next((Path(env["LOCALAPPDATA"])/"GDCAE/engineering/v1").iterdir())
    archive = base/"server.zip"
    original = archive.read_bytes()
    archive.write_bytes(original+b"!")
    op("t02-plan",queue,"BACKEND_SOURCE_MISMATCH")
    archive.write_bytes(original)
    req = dict(queue,expected_revision=3,key="t02-observe")
    op("t02-read",req,"T02_READ_CONSENT_REQUIRED")

    # Bind an independently expected UUID to the wrong formal project. The real server must refuse it.
    path = base/"deployment.json"
    prior = path.read_bytes()
    profile = json.loads(prior)
    profile["backend_root"] = str(work/"backend-b")
    path.write_text(json.dumps(profile),encoding="utf8")
    other = op("t02-plan",queue)
    path.write_bytes(prior)
    proposal = op("t02-plan",queue)
    assert proposal["service"] == "NOT_QUERIED" and proposal["expected_backend_id"] == backend
    refs = proposal["consent_refs"] + [other["consent_refs"][1]]
    op("task-update", change("read-consent",2,dict(task_id="T02",execution="IN_PROGRESS",evidence=refs)))
    path.write_text(json.dumps(profile),encoding="utf8")
    op("t02-read",req,"BACKEND_PROJECT_MISMATCH")
    path.write_bytes(prior)
    assert not (base/"observations").exists()
    op("t02-read",dict(req,expected_revision=2),"TASK_REVISION_CONFLICT")
    op("t02-read",dict(req,queue_id="another"),"T02_READ_CONSENT_REQUIRED")
    receipt = op("t02-read",req)
    assert receipt["status"] == "REGISTERED_READ_BACK"
    observation, ref = receipt["observation"], receipt["artifact"]
    assert observation["backend_project"] == backend and observation["research_project"] == project
    assert observation["queue_status"]["status"] == "QUEUED" and observation["rows_returned"] == {"queue":1,"history":0}
    assert set(observation["response_sha256"]) == {"history","queue","status"}
    assert not observation["execution_authorized"]
    file, = (base/"observations").rglob("*.json")
    assert fingerprint(file) == ref["sha256"] and file.name == ref["reference"]
    assert op("t02-read",req)["status"] == "REPLAYED"
    restored = op("task-list")
    card, = [row for row in restored["tasks"] if row["task_id"] == "T02"]
    assert restored["revision"] == 4 and card["execution"] == "SUBMITTED"
    assert ref in card["evidence"] and card["authorization"] == "NOT_GRANTED"
    assert card["verification"] == "NOT_VERIFIED" and card["scientific_decision"] == "NOT_ASSESSED"
    assert inventory(work/"backend-a") == before
    file.write_bytes(file.read_bytes()+b" ")
    op("t02-read",req,"EVIDENCE_DIGEST_MISMATCH")
    print(json.dumps({"status":"PASS","backend":"real stdio, isolated formal project","server":observation["version"],
                      "installed_operations":["t02-plan","t02-read","task-list"],"restored_revision":4,
                      "source_project_unchanged":True,"execution_authorized":False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("plugin","backend-source","work"):
        parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--manifest-pin",required=True)
    args=parser.parse_args()
    verify(args.plugin.resolve(),args.manifest_pin,args.backend_source.resolve(),args.work.resolve())
