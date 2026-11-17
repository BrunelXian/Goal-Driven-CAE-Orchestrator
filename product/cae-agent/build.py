"""Build host-neutral CAE Agent services and the optional local Codex adapter from one commit."""
import argparse
import hashlib
import io
import json
import re
import runpy
import subprocess
import zipfile
from pathlib import Path

BASE = "product/cae-agent/"
LEGACY = "product/scoped-fixture/"
VENDOR_POLICY = "plugins/gdcae-research/runtime/abq-readonly.json"
CLASSIC = LEGACY + "plugin/server/classic_readonly.py"
EXAMPLES = "examples/cae_agent/"
VERSION = "0.3.1"
ROOT = Path(__file__).resolve().parents[2]
# The historical builder's static import walk is independent of its adapter and test harness.
reachable = runpy.run_path(str(ROOT / LEGACY / "build.py"))["reachable"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def manifest(kind, commit, assets):
    return encode({"schema": 1, "product": "CAE Agent", "version": VERSION, "kind": kind,
                   "source_commit": commit, "files": {name: digest(data) for name, data in assets.items()}})


def build(commit, output):
    if not re.fullmatch("[0-9a-f]{40}", commit):
        raise ValueError("FULL_COMMIT_REQUIRED")
    samples = [EXAMPLES + name for name in ("contract.json", "test-proposals.json", "scenario.py", "call.py", "README.md")]
    guides = ["docs/architecture/CAE_AGENT_031_AUTHORITY.md", "docs/architecture/SCOPED_FIXTURE_REAL_MODEL_HANDOFF.md"]
    allow = ["LICENSE", "src/aegiscae", BASE, VENDOR_POLICY, CLASSIC, LEGACY + "host_probe.py", *samples, *guides]
    archive = subprocess.run(["git", "--no-replace-objects", "-C", str(ROOT), "archive", "--format=zip",
                              commit, "--", *allow], capture_output=True, check=True)
    with zipfile.ZipFile(io.BytesIO(archive.stdout)) as source:
        files = {n: source.read(n) for n in source.namelist() if not n.endswith("/")}
    core = reachable(files, "aegiscae.interfaces.mcp_research")
    service = {"core/" + n: data for n, data in core.items()}
    service.update({n.removeprefix(BASE + "service/"): d for n, d in files.items() if n.startswith(BASE + "service/")})
    service.update({"LICENSE": files["LICENSE"], "classic_readonly.py": files[CLASSIC],
                    "abq-readonly.json": files[VENDOR_POLICY]})
    adapter = {n.removeprefix(BASE + "plugin/"): d for n, d in files.items() if n.startswith(BASE + "plugin/")}
    descriptor = json.loads(adapter["plugin.json"])
    if descriptor["name"] != "cae-agent" or descriptor["version"] != VERSION:
        raise ValueError("PRODUCT_VERSION_MISMATCH")
    adapter["LICENSE"] = files["LICENSE"]
    service["manifest.json"] = manifest("service", commit, service)
    adapter["manifest.json"] = manifest("codex-adapter", commit, adapter)
    dist = {"market/.agents/plugins/marketplace.json": files[BASE + "marketplace.json"],
            "configure.py": files[BASE + "configure.py"], "INSTALL.md": files[BASE + "README.md"],
            "qa/host_probe.py": files[LEGACY + "host_probe.py"], "qa/installed_check.py": files[BASE + "installed_check.py"],
            "qa/neutral_check.py": files[BASE + "neutral_check.py"]}
    dist.update({"service/" + k: v for k, v in service.items()})
    dist.update({"market/plugins/cae-agent/" + k: v for k, v in adapter.items()})
    dist.update({p: files[p] for p in samples + guides})
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"CAE-Agent-{VERSION}.zip"
    with zipfile.ZipFile(target, "x") as package:
        for name, data in sorted(dist.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            package.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
    report = {"product": "CAE Agent", "version": VERSION, "source_commit": commit, "zip": target.name,
              "zip_sha256": digest(target.read_bytes()), "service_manifest_sha256": digest(service["manifest.json"]),
              "adapter_manifest_sha256": digest(adapter["manifest.json"]), "service_files": len(service),
              "adapter_files": len(adapter)}
    with (output / "candidate-inventory.json").open("xb") as sink:
        sink.write(encode(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.commit, args.output)))
