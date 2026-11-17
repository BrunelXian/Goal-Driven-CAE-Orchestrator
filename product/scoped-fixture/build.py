"""Build the local marketplace from committed allowlisted files, independent of checkout edits."""
import argparse
import ast
import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

BASE = "product/scoped-fixture/"
NAME = "cae-agent-scoped-fixture"
ENTRY = "aegiscae.interfaces.mcp_scoped"


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reachable(files, entry=ENTRY):
    """Resolve imports of committed aegiscae modules, including package initializers."""
    modules = {}
    for path in files:
        if path.startswith("src/aegiscae/") and path.endswith(".py"):
            name = path[4:-3].replace("/", ".").removesuffix(".__init__")
            modules[name] = path
    pending = [entry]
    if entry not in modules:
        raise ValueError("SCOPED_ENTRY_NOT_IN_COMMIT")
    visited = set()
    while pending:
        name = pending.pop()
        if name in visited or name not in modules:
            continue
        visited.add(name)
        package = name if modules[name].endswith("/__init__.py") else name.rpartition(".")[0]
        pending.extend(".".join(name.split(".")[:i]) for i in range(1, len(name.split("."))))
        for node in ast.walk(ast.parse(files[modules[name]])):
            if isinstance(node, ast.Import):
                pending.extend(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                parent = node.module or ""
                if node.level:
                    parts = package.split(".")
                    prefix = parts[:len(parts) - node.level + 1]
                    parent = ".".join(prefix + ([parent] if parent else []))
                pending.append(parent)
                pending.extend(parent + "." + item.name for item in node.names)
    return {modules[n][4:]: files[modules[n]] for n in sorted(visited)}


def build(commit, output):
    if not re.fullmatch("[0-9a-f]{40}", commit):
        raise ValueError("FULL_COMMIT_REQUIRED")
    repo = Path(__file__).resolve().parents[2]
    replay = "examples/scoped_fixture/rehearse.py"
    members = ["LICENSE", "src/aegiscae", BASE, replay,
               "plugins/gdcae-research/runtime/abq-readonly.json"]
    proc = subprocess.run(["git", "--no-replace-objects", "-C", str(repo), "archive",
                           "--format=zip", commit, "--", *members], capture_output=True, check=True)
    with zipfile.ZipFile(io.BytesIO(proc.stdout)) as archive:
        files = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
    payload = {key.removeprefix(BASE + "plugin/"): data for key, data in files.items()
               if key.startswith(BASE + "plugin/")}
    payload["LICENSE"] = files["LICENSE"]
    payload["runtime/abq-readonly.json"] = files[members[-1]]
    payload.update({"runtime/core/" + key: data for key, data in reachable(files).items()})
    version = json.loads(payload["plugin.json"])["version"]
    manifest = {"schema": 1, "source_commit": commit, "name": NAME, "version": version,
                "files": {k: sha(v) for k, v in payload.items()}}
    payload["manifest.json"] = encoded(manifest)
    distribution = {"market/.agents/plugins/marketplace.json": files[BASE + "marketplace.json"],
                    "configure.py": files[BASE + "configure.py"], "INSTALL.md": files[BASE + "README.md"]}
    for entry in (replay, BASE + "host_probe.py", BASE + "installed_case.py"):
        distribution[entry] = files[entry]
    distribution.update({f"market/plugins/{NAME}/{k}": v for k, v in payload.items()})
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"CAE-Agent-Scoped-Fixture-{version}.zip"
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as package:
        for name, data in sorted(distribution.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            package.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
    receipt = {"source_commit": commit, "version": version, "zip": target.name,
               "zip_sha256": sha(target.read_bytes()), "manifest_sha256": sha(payload["manifest.json"]),
               "installed_files": len(payload)}
    with (output / "candidate-inventory.json").open("xb") as stream:
        stream.write(encoded(receipt))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.commit, args.output)))
