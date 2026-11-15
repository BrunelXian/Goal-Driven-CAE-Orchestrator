"""Check the two exact Host projections and reject other hook definitions on an extracted RC."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile


def check(archive, out):
    out.mkdir()
    plugin = out / "plugin"
    with zipfile.ZipFile(archive) as z:
        z.extractall(plugin)
    pin = hashlib.sha256((plugin / "package-manifest.json").read_bytes()).hexdigest()
    meta = json.loads((plugin / "plugin.json").read_bytes())
    compat = {k: meta[k] for k in ("name", "description", "version", "license")}
    extension = meta["extensions"]["com.openai"]
    compat.update(skills="./skills/", interface=extension["interface"])
    path = plugin / ".codex-plugin/plugin.json"
    path.parent.mkdir()
    results = {}
    for name, hooks, expected in [("original_projection", None, 0),
                                  ("declared_hooks", extension["hooks"], 0),
                                  ("changed_hooks", "./other.json", 2)]:
        if hooks is not None:
            compat["hooks"] = hooks
        path.write_text(json.dumps(compat), encoding="utf-8")
        env = dict(os.environ, LOCALAPPDATA=str(out / name))
        # Starting Windows PowerShell via Python does not apply pwsh's PSModulePath translation.
        env.pop("PSMODULEPATH", None)
        run = subprocess.run(["powershell.exe", "-NoProfile", "-File", str(plugin / "scripts/launch.ps1"),
                              "-Action", "bind", "-PythonExe", str(Path(sys.executable).resolve()), "-ManifestSha256", pin],
                             env=env, capture_output=True)
        assert run.returncode == expected, (name, run.returncode, run.stdout[:150], run.stderr[:150])
        if expected:
            assert b"HOST_METADATA_MISMATCH" in run.stdout + run.stderr
        results[name] = run.returncode
    (out / "result.json").write_text(json.dumps(results, indent=2))
    print(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    check(args.archive.resolve(), args.out.resolve())
