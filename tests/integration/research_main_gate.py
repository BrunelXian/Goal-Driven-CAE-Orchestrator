"""Exercise the release driver's role gate using fresh synthetic Host identities."""
import argparse
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys


def verify(plugin, pin, work):
    work.mkdir()
    shell = shutil.which("pwsh") or shutil.which("powershell")
    env = dict(os.environ, LOCALAPPDATA=str(work / "settings"))
    env.pop("PYTHONPATH", None)
    env.pop("CODEX_THREAD_ID", None)
    helpers = Path(__file__).resolve().parents[2] / "product/research-preview/tools/test_main_fixture.py"
    scope, main_env = runpy.run_path(str(helpers))["configure"](plugin, pin, env, shell)
    prefix = [shell, "-NoProfile", "-NonInteractive", "-File", str(plugin / "scripts/launch.ps1")]

    def invoke(args, caller, error=None):
        proc = subprocess.run(prefix + list(map(str, args)), env=caller, capture_output=True, timeout=40)
        value = json.loads(proc.stdout)
        assert proc.returncode == (2 if error else 0), (value, error)
        if error:
            assert value["error"] == error, (value, error)
        return value

    bound = invoke(["-Action", "bind", "-PythonExe", sys.executable, "-ManifestSha256", pin], env)
    common = ["-BindingSha256", bound["binding_sha256"], "-ProjectRoot", work / "model"]
    out = work / "result"
    calculate = ["-Action", "main", "-OutputDirectory", out, *common]
    wrong = dict(env, CODEX_THREAD_ID="fixture-setup")
    for caller, args, reason in ((env, scope, "MAIN_THREAD_UNAVAILABLE"), (wrong, scope, "MAIN_IDENTITY_MISMATCH"),
                                (main_env, [], "VERIFIED_RESEARCH_MAIN_REQUIRED")):
        invoke(calculate + args, caller, reason)
    operations = ["new","freeze","propose","confirm","attribute","overview","detail","diff","hint",
                  "sanity-triage","sanity-assess","sanity-reference","task-list","task-init","task-create",
                  "task-update","capability-discovery"]
    for operation in operations:
        invoke(["-Action", "agreement", "-Operation", operation, *common, *scope], wrong, "MAIN_IDENTITY_MISMATCH")
    assert not out.exists() and not (work / "model").exists()
    request = work / "new.json"
    request.write_text(json.dumps({"name":"Gate test", "schema":"research-agreement-project-v3"}))
    ops = ["-Action","agreement",*common,*scope]
    created = invoke([*ops,"-Operation","new","-InputFile",request], main_env)
    assert invoke([*ops,"-Operation","task-list"], main_env)["project"] == created["research_project_id"]
    enrollment = dict(project=created["research_project_id"], host="fixture", desktop_project="fixture-project",
                      expected_revision=1, key="fixture-intake", data=dict(summary="Fixture study",
                      drafts={k: dict(goal=k, criterion="Fixture criterion", deliverable="Fixture report", refs=[])
                              for k in ("T01", "T02")}))
    request.write_text(json.dumps(enrollment))
    invoke([*ops, "-Operation", "task-init", "-InputFile", request], main_env)
    handoff = [shell, "-NoProfile", "-NonInteractive", "-File", str(plugin / "scripts/main-handoff.ps1"),
               "-ManifestSha256", pin, "-HostId", "fixture", "-ProjectId", "other-desktop"]
    def action(*flags, caller=wrong, expected=0):
        proc = subprocess.run([*handoff, *flags], env=caller, capture_output=True, timeout=40)
        assert proc.returncode == expected
        if expected:
            assert b"ONBOARDING_CANNOT_VERIFY_SELF" in proc.stderr
        else:
            return json.loads(proc.stdout)
    claim = action("-Action", "claim", "-Title", "Other Main")
    receipt = ["-RequestId", claim["request_id"], "-ThreadId", "other-main"]
    other = dict(env, CODEX_THREAD_ID="other-main")
    action("-Action", "record", *receipt, caller=other, expected=2)
    action("-Action", "record", *receipt)
    action("-Action", "verify", *receipt, "-ObservedProjectId", "other-desktop", "-ObservedTitle", "Other Main")
    invoke(["-Action", "agreement", "-Operation", "task-list", *common,
            "-HostId", "fixture", "-DesktopProjectId", "other-desktop"], other, "MAIN_PROJECT_MISMATCH")
    print("PASS: all 17 agreement routes and analysis reject Setup before project access; verified synthetic Main accepted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("plugin", type=Path)
    parser.add_argument("pin")
    parser.add_argument("fresh_work", type=Path)
    args = parser.parse_args()
    verify(args.plugin.resolve(), args.pin, args.fresh_work.resolve())
