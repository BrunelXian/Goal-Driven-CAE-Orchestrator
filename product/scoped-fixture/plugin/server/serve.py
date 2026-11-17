"""Launch the committed scoped Core or the reviewed Classic read-only service on stdio."""
import asyncio
import hashlib
import json
import os
import sys
import time
from importlib.metadata import version
from pathlib import Path


def require(value, code):
    if not value:
        raise ValueError(code)


def local(path):
    path = Path(path)
    require(path.is_absolute() and not path.drive.startswith("\\\\") and ".." not in path.parts and
            not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)),
            "LOCAL_UNREDIRECTED_PATH_REQUIRED")
    return path


def digest(path):
    return hashlib.sha256(local(path).read_bytes()).hexdigest()


def main(service, profile):
    require(sys.flags.isolated and sys.version_info[:3] == (3, 12, 10) and version("mcp") == "2.3.0",
            "RUNTIME_MISMATCH")
    root = local(Path(__file__).absolute().parents[1])
    profile = local(profile)
    original = profile.read_bytes()
    cfg = json.loads(original)
    manifest_file = root / "manifest.json"
    manifest = json.loads(manifest_file.read_bytes())

    def check_profile():
        require(profile.read_bytes() == original and digest(manifest_file) == cfg["manifest_sha256"],
                "DEPLOYMENT_CHANGED")
        binding = local(cfg["binding"]).read_bytes()
        require(hashlib.sha256(binding).hexdigest() == cfg["binding_sha256"], "BINDING_CHANGED")
        require(time.time() < json.loads(binding)["expires"], "SCOPE_EXPIRED")

    files = manifest["files"]
    def verify_deployment():
        check_profile()
        actual = {local(p).relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
        require(actual == set(files) | {"manifest.json"} and all(digest(root / n) == h for n, h in files.items()),
                "PACKAGE_INVENTORY_MISMATCH")

    verify_deployment()
    if service == "abqjobpilot":
        sys.path.insert(0, str(root / "server"))
        from classic_readonly import classic
        classic(cfg, json.loads((root / "runtime/abq-readonly.json").read_bytes()), verify_deployment)
    elif service == "gdcae-core":
        os.environ["GDCAE_FIXTURE_BINDING_SHA256"] = cfg["binding_sha256"]
        sys.path.insert(0, str(root / "runtime/core"))
        from aegiscae.interfaces.fixture_scope import Scope
        from aegiscae.interfaces.mcp_scoped import create_server, serve
        server = create_server(Scope(cfg["binding"], cfg["binding_sha256"]), verify_deployment=verify_deployment)
        asyncio.run(serve(server))
    else:
        raise ValueError("UNKNOWN_SERVICE")


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]))
