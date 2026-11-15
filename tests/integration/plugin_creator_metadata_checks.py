"""Exercise the released verifier against an actual Creator layout and edited copies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import zipfile


def check(archive, stored, work, pin, project_previous):
    work.mkdir()
    plugin = work / "plugin"
    overlay = ".codex-plugin/plugin.json"
    with zipfile.ZipFile(archive) as source:
        originals = {name: source.read(name) for name in source.namelist()}
        manifest = json.loads(originals["package-manifest.json"])
        assert hashlib.sha256(originals["package-manifest.json"]).hexdigest() == pin
        assert set(originals) == set(manifest["files"]) | {"package-manifest.json"}
        assert all(hashlib.sha256(originals[n]).hexdigest() == h for n, h in manifest["files"].items())
        if project_previous:
            source.extractall(plugin)
            previous_version = json.loads((stored / "package-manifest.json").read_bytes())["version"]
            assert previous_version != manifest["version"]
            for name in ("plugin.json", overlay):
                observed = json.loads((stored / name).read_bytes())
                assert observed["version"] == previous_version
                observed["version"] = manifest["version"]
                path = plugin / name
                path.parent.mkdir(exist_ok=True)
                path.write_text(json.dumps(observed, indent=2), encoding="utf8")
        else:
            shutil.copytree(stored, plugin)
    assert {p.relative_to(plugin).as_posix() for p in plugin.rglob("*") if p.is_file()} == set(originals) | {overlay}
    for name, data in originals.items():
        if name != "plugin.json":
            assert (plugin / name).read_bytes() == data, name
    docs = {n: json.loads((plugin / n).read_bytes()) for n in ("plugin.json", overlay)}
    assert docs["plugin.json"] == json.loads(originals["plugin.json"])
    # Load only the release-pinned verifier; never execute a modified test member.
    verify = runpy.run_path(str(plugin / "scripts/main.py"))["core_bytes"]
    verify(plugin, pin)
    env = dict(os.environ, LOCALAPPDATA=str(work / "settings"))
    env = {k: v for k, v in env.items() if k.upper() != "PSMODULEPATH"}
    shell = ["powershell.exe", "-NoProfile", "-NonInteractive", "-File", str(plugin / "scripts/launch.ps1")]

    def launch(*args):
        proc = subprocess.run(shell + list(args), env=env, capture_output=True, timeout=60)
        assert proc.returncode == 0, (args[1], proc.stderr[:250], proc.stdout[:250])
        return json.loads(proc.stdout)

    bound = launch("-Action", "bind", "-PythonExe", sys.executable, "-ManifestSha256", pin)
    doctor = launch("-Action", "doctor", "-BindingSha256", bound["binding_sha256"])
    assert bound["status"] == "BOUND" and doctor["status"] == "PACKAGE_AND_CORE_VERIFIED"
    project = str(work / "synthetic-project")
    req = work / "new.json"
    req.write_text(json.dumps({"name": "Metadata smoke", "schema": "research-agreement-project-v3"}))
    core_args = ["-Action", "agreement", "-BindingSha256", bound["binding_sha256"], "-ProjectRoot", project]
    caller_args, env = runpy.run_path(str(Path(__file__).resolve().parents[2] / "product/research-preview/tools/test_main_fixture.py"))["configure"](plugin, pin, env, shell[0])
    core_args += caller_args
    new = launch(*core_args, "-Operation", "new", "-InputFile", str(req))
    overview = launch(*core_args, "-Operation", "overview")
    assert new["research_project_id"] == overview["project"]
    assert overview["status"] == "NO_CONFIRMED_AGREEMENT" and overview["execution_authorized"] is False
    denied = {}

    def refuse(label, name, changed, reason):
        path = plugin / name
        original = path.read_bytes() if path.exists() else None
        path.write_bytes(changed)
        try:
            try:
                verify(plugin, pin)
            except ValueError as exc:
                assert str(exc) == reason, (label, str(exc))
                denied[label] = reason
            else:
                raise AssertionError(label + " unexpectedly passed")
        finally:
            if original is None:
                path.unlink()
            else:
                path.write_bytes(original)

    for name, keys, value in (
        ("plugin.json", ("name",), "other"), ("plugin.json", ("version",), "9.9.9"),
        ("plugin.json", ("author", "email"), "other@example.invalid"),
        ("plugin.json", ("extensions", "com.openai", "hooks"), "./scripts/main.py"),
        ("plugin.json", ("extensions", "com.openai", "onboardingSkill"), "./skills/research/SKILL.md"),
        (overlay, ("hooks",), "./scripts/main.py"), (overlay, ("skills",), "./scripts"),
        (overlay, ("extensions", "com.openai", "onboardingSkill"), "./scripts/update.ps1"),
        (overlay, ("requires_local_executor",), False), (overlay, ("interface", "defaultPrompt"), "run"),
        (overlay, ("version",), "0.2.0-preview.13"), (overlay, ("mcpServers",), "./other.json"),
    ):
        document = json.loads((plugin / name).read_bytes())
        node = document
        for field in keys[:-1]:
            node = node[field]
        node[keys[-1]] = value
        refuse(name + ":" + ".".join(keys), name, json.dumps(document).encode(), "HOST_METADATA_MISMATCH")
    refuse("duplicate JSON key", overlay, b'{"name":"a","name":"b"}', "DUPLICATE_METADATA_KEY")
    for name in ("hooks/hooks.json", "scripts/main.py", "scripts/launch.ps1", "skills/research/SKILL.md",
                 "scripts/update.ps1", "runtime/agreement-core.zip"):
        refuse(name, name, originals[name] + b" ", "PACKAGE_IDENTITY_MISMATCH:" + name)
    if "scripts/intake.ps1" in originals:
        for name in ("scripts/intake.ps1", "skills/setup/SKILL.md"):
            refuse(name, name, originals[name] + b" ", "PACKAGE_IDENTITY_MISMATCH:" + name)
    refuse("extra executable", "extra.ps1", b"# fixture", "PACKAGE_FILESET_MISMATCH")
    refuse("manifest edit", "package-manifest.json", originals["package-manifest.json"] + b" ", "PACKAGE_MANIFEST_MISMATCH")
    verify(plugin, pin)
    report = {"layout": "projected from prior release" if project_previous else "retrieved from Plugin Creator",
              "version": manifest["version"], "manifest_sha256": pin, "bind": bound["status"],
              "doctor": doctor["status"], "agreement_new_overview": "PASS", "refusals": denied}
    (work / "result.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    print(json.dumps({k: v for k, v in report.items() if k != "refusals"}), len(denied))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("archive", "stored", "work"):
        parser.add_argument(name, type=Path)
    parser.add_argument("pin")
    parser.add_argument("--project-previous", action="store_true")
    args = parser.parse_args()
    check(args.archive.resolve(), args.stored.resolve(), args.work.resolve(), args.pin, args.project_previous)
