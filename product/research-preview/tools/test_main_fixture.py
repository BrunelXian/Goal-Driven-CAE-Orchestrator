"""Create synthetic caller evidence ONLY under a disposable acceptance-test directory."""
import json
from pathlib import Path
import subprocess


def configure(plugin, pin, env, shell):
    if "DesktopProjectId" not in (plugin / "scripts/launch.ps1").read_text(encoding="utf8"):
        return [], env
    base = Path(env["LOCALAPPDATA"])
    receipt_dir = base / "GDCAE/project-main-handoffs/v1"
    if receipt_dir.exists():
        raise ValueError("synthetic Main requires fresh test settings")
    def handoff(action, *args):
        proc = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-File",
            str(plugin / "scripts/main-handoff.ps1"), "-Action", action,
            "-HostId", "fixture", "-ProjectId", "fixture-project", "-ManifestSha256", pin,
            *args], env=dict(env, CODEX_THREAD_ID="fixture-setup"), capture_output=True, check=True)
        return json.loads(proc.stdout)
    claim = handoff("claim", "-Title", "Fixture Main")
    assert claim["may_create"]
    ref = ["-RequestId", claim["request_id"], "-ThreadId", "fixture-main"]
    handoff("record", *ref)
    assert handoff("verify", *ref, "-ObservedTitle", "Fixture Main",
                   "-ObservedProjectId", "fixture-project")["state"] == "VERIFIED"
    return ["-HostId", "fixture", "-DesktopProjectId", "fixture-project"], dict(env, CODEX_THREAD_ID="fixture-main")
