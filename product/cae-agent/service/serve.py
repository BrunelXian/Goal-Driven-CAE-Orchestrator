"""Start one host-neutral, local stdio service from an operator-pinned deployment."""
import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
from pathlib import Path


def launch(service, profile_path, adapter=None):
    original = profile_path.read_bytes()
    cfg = json.loads(original)
    root = Path(__file__).absolute().parent
    if root != Path(cfg["service_root"]) or Path(sys.executable) != Path(cfg["python"]):
        raise ValueError("RUNTIME_BINDING_CHANGED")
    raw = (root / "manifest.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != cfg["service_sha256"]:
        raise ValueError("SERVICE_MANIFEST_CHANGED")
    for file in ("integrity.py", "serve.py"):
        if hashlib.sha256((root / file).read_bytes()).hexdigest() != json.loads(raw)["files"][file]:
            raise ValueError("LAUNCHER_IDENTITY_CHANGED")
    sys.path.insert(0, str(root))
    from integrity import local, runtime, sha, verify

    runtime()
    profile = local(profile_path)
    if adapter is not None and local(adapter) != local(cfg["adapter_root"]):
        raise ValueError("ADAPTER_BINDING_CHANGED")

    def check():
        if profile.read_bytes() != original or sha(sys.executable) != cfg["python_sha256"]:
            raise ValueError("DEPLOYMENT_CHANGED")
        verify(root, cfg["service_sha256"], "service")
        if adapter is not None:
            verify(adapter, cfg["adapter_sha256"], "codex-adapter")
        binding = local(cfg["binding"]).read_bytes()
        if hashlib.sha256(binding).hexdigest() != cfg["binding_sha256"]:
            raise ValueError("BINDING_CHANGED")
        if time.time() >= json.loads(binding)["expires"]:
            raise ValueError("SCOPE_EXPIRED")

    check()
    if service == "gdcae-core":
        os.environ["GDCAE_BINDING_SHA256"] = cfg["binding_sha256"]
        sys.path.insert(0, str(root / "core"))
        from aegiscae.interfaces.mcp_research import create_server, serve
        from aegiscae.interfaces.research_scope import Scope
        server = create_server(Scope(cfg["binding"], cfg["binding_sha256"]), verify_deployment=check)
        asyncio.run(serve(server))
    elif service == "abqjobpilot":
        if cfg["classic"] is None:
            raise ValueError("CLASSIC_NOT_DEPLOYED")
        from classic_readonly import classic
        classic(cfg["classic"], json.loads((root / "abq-readonly.json").read_bytes()), check)
    else:
        raise ValueError("UNKNOWN_SERVICE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("service", choices=("gdcae-core", "abqjobpilot"))
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, help="optional installed adapter integrity check")
    args = parser.parse_args()
    launch(args.service, args.profile, args.adapter)
