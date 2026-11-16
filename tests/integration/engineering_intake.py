"""Repeat the management baseline and run the real AbqJobPilot stdio service on disposable data.

Run from the development source environment with PYTHONPATH=src. For the optional live
native-return leg, supply the preselected artifact and the SHA/size returned by the Host child.
No Desktop thread is created by this harness.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace

from aegiscae.contracts.research_contracts import require

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "product/research-preview/tools"
sys.path.insert(0, str(TOOLS))
from abqjobpilot_probe import server_parameters
from abqjobpilot_readonly import binding_reference


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_ref(path, size, pin):
    require(path.is_file() and not path.is_symlink() and size == path.stat().st_size
            and fingerprint(path) == pin, "SUBAGENT_ARTIFACT_MISMATCH")
    return {"reference": "native-readonly-artifact", "sha256": pin}


def inventory(root):
    return {p.relative_to(root).as_posix(): fingerprint(p) for p in root.rglob("*") if p.is_file()}


def run_json(cmd, env, *, reason=None):
    run = subprocess.run(list(map(str, cmd)), env=env, capture_output=True, timeout=100)
    if not run.stdout:
        raise AssertionError(f"No JSON from child (exit {run.returncode}): {run.stderr[-500:]!r}")
    value = json.loads(run.stdout)
    if reason:
        assert run.returncode == 2 and (value.get("reason") or value.get("error")) == reason, value
    else:
        assert run.returncode == 0, value
    return value


def backend_fixture(source, work, env):
    # Only seed a synthetic stored row under the temporary directory. No enqueue API or runner.
    fixture = """
from pathlib import Path
import sys, json
sys.path.insert(0, sys.argv[1])
from abqjobpilot.project.manager import ProjectManager
from abqjobpilot.queue_store import build_queue_record, save_queue
w = Path(sys.argv[2])
manager = ProjectManager(recent_file=w/'recent.json')
a = manager.create_project(w/'backend-a', 'engineering-A')
manager.create_project(w/'backend-b', 'engineering-B')
inp = w/'inert.inp'
inp.write_text('*Heading\\n', encoding='utf8')
row = build_queue_record(inp, 1, 0, '', '', 'synthetic', True, True, '', queue_id='q_fixture')
save_queue([row], runtime_dir=a.runtime_dir)
print(json.dumps({'backend':a.project_id}))
"""
    args = SimpleNamespace(backend_source=source, backend_python=Path(sys.executable), backend_project=work)
    with server_parameters(args) as params:
        return run_json([sys.executable, "-I", "-B", "-c", fixture, params.cwd, work], env)["backend"]


def exercise(args, work):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    assert shell and fingerprint(args.plugin / "package-manifest.json") == args.manifest_pin
    env = dict(os.environ, LOCALAPPDATA=str(work/"settings"), PYTHONDONTWRITEBYTECODE="1")
    env.pop("CODEX_THREAD_ID", None)
    clean_env = env.copy()
    clean_env.pop("PYTHONPATH", None)
    configure = runpy.run_path(str(ROOT/"product/research-preview/tools/test_main_fixture.py"))["configure"]
    scope, caller = configure(args.plugin, args.manifest_pin, clean_env, shell)
    assert scope, "This baseline requires the release's verified Main gate"
    launched = [shell, "-NoProfile", "-NonInteractive", "-File", args.plugin/"scripts/launch.ps1"]
    bound = run_json([*launched, "-Action", "bind", "-PythonExe", sys.executable,
                      "-ManifestSha256", args.manifest_pin], clean_env)
    root = work/"research"
    common = [*launched, "-Action", "agreement", "-ProjectRoot", root, "-BindingSha256", bound["binding_sha256"], *scope]
    request = work/"input.json"

    def operation(op, body=None, who=None, error=None):
        flags = [*common, "-Operation", op]
        if body is not None:
            request.write_text(json.dumps(body), encoding="utf8")
            flags += ["-InputFile", request]
        return run_json(flags, who or caller, reason=error)

    wrong = dict(caller, CODEX_THREAD_ID="fixture-setup")
    operation("new", {"name":"engineering", "schema":"research-agreement-project-v3"}, wrong, "MAIN_IDENTITY_MISMATCH")
    assert not root.exists()
    project = operation("new", {"name":"engineering", "schema":"research-agreement-project-v3"})["research_project_id"]
    assert operation("task-list")["revision"] == 1
    backend = backend_fixture(args.backend_source, work, env)
    def change(key, rev, data):
        return dict(project=project, host="fixture", desktop_project="fixture-project", key=key,
                    expected_revision=rev, data=data)
    drafts = {tid: dict(goal=tid, deliverable="Evidence", criterion="Independent readback", refs=[])
              for tid in ("T01", "T02")}
    init = change("intake", 1, {"summary":"Disposable engineering baseline", "drafts":drafts})
    registered = operation("task-init", init)
    assert operation("task-init", init) == registered and registered["revision"] == 2
    operation("task-init", dict(init, project="wrong-project"), error="INVALID_TASK_REQUEST")

    def transition(task, stage, rev, refs):
        return operation("task-update", change(task+stage, rev, {"task_id":task, "execution":stage, "evidence":refs}))
    transition("T01","IN_PROGRESS",2,[])
    t01 = native_ref(args.native_artifact, args.native_size, args.native_sha256)
    try:
        native_ref(args.native_artifact, args.native_size, "0"*64)
    except ValueError as exc:
        assert str(exc) == "SUBAGENT_ARTIFACT_MISMATCH"
    else:
        raise AssertionError("Accepted a bad subagent digest")
    transition("T01","SUBMITTED",3,[t01])
    pair = binding_reference(project, backend)
    transition("T02","IN_PROGRESS",4,[pair])

    evidence_dir = work/"observations"
    evidence_dir.mkdir()
    source_env = dict(caller, PYTHONPATH=str(ROOT/"src"))
    module = [sys.executable, "-B", TOOLS / "abqjobpilot_probe.py"]
    context = ["--project", root, "--host","fixture","--desktop","fixture-project",
               "--backend-id",backend,"--evidence-dir", evidence_dir]
    probe = [*module, "observe", *context, "--backend-python", sys.executable, "--backend-source",
             args.backend_source, "--queue-id", "q_fixture", "--backend-project"]
    before = {n:inventory(work/n) for n in ("backend-a","backend-b")}
    run_json([*probe, work/"backend-a"], dict(source_env, CODEX_THREAD_ID="fixture-setup"), reason="MAIN_IDENTITY_MISMATCH")
    missing_sdk = [sys.executable, "-S", *probe[1:], work/"backend-a"]
    run_json(missing_sdk, source_env, reason="MCP_CLIENT_SDK_UNAVAILABLE")
    run_json([*probe, work/"backend-b"], source_env, reason="BACKEND_PROJECT_MISMATCH")
    assert not list(evidence_dir.iterdir())
    capture = run_json([*probe, work/"backend-a"], source_env)
    obs, ref = capture["observation"], capture["artifact"]
    assert obs["research_project"] == project and obs["backend_project"] == backend
    assert obs["rows_returned"] == {"queue":1,"history":0}
    assert obs["queue_status"]["status"] == "QUEUED" and not obs["queue_status"]["active_execution_confirmed"]
    assert not obs["execution_authorized"] and obs["source_commit"] and set(obs["response_sha256"]) == {"queue","history","status"}
    path = evidence_dir/ref["reference"]
    assert fingerprint(path) == ref["sha256"]
    submit = [*module,"submit",*context,"--sha256",ref["sha256"],"--key","T02-observation","--expected-revision","5"]
    original = path.read_bytes()
    path.write_bytes(original+b" ")
    run_json(submit,source_env,reason="EVIDENCE_DIGEST_MISMATCH")
    path.write_bytes(original)
    assert operation("task-list")["revision"] == 5
    first = run_json(submit,source_env)
    assert run_json(submit,source_env) == first and first["revision"] == 6
    reopened = operation("task-list")
    assert reopened["project"] == project and reopened["revision"] == 6 and not reopened["execution_authorized"]
    one,two = reopened["tasks"]
    assert [one["task_id"],two["task_id"]] == ["T01","T02"] and one["evidence"] == [t01] and two["evidence"] == [pair,ref]
    assert all(t["execution"] == "SUBMITTED" and t["verification"] == "NOT_VERIFIED"
               and t["scientific_decision"] == "NOT_ASSESSED" and t["authorization"] == "NOT_GRANTED" for t in (one,two))
    assert before == {n:inventory(work/n) for n in before}
    print(json.dumps({"status":"PASS","release_gate":"synthetic Host receipts, actual installed launcher",
                      "service":obs["server"], "version":obs["version"], "protocol":obs["protocol"],
                      "backend":"real stdio, disposable formal Projects", "job_status":"QUEUED", "native_digest":"independent byte match; dispatch established by Host",
                      "source_commit":obs["source_commit"],"revision_after_restart":6,"tasks":["T01","T02"],
                      "execution_authorized":False,"private_runtime_data_exported":False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plugin","backend-source","native-artifact"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--manifest-pin", required=True)
    parser.add_argument("--native-size", required=True, type=int)
    parser.add_argument("--native-sha256", required=True)
    with tempfile.TemporaryDirectory(prefix="gdcae-engineering-") as tmp:
        exercise(parser.parse_args(), Path(tmp))
