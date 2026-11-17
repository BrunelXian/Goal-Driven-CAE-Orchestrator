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


def classic(cfg, policy, check_profile):
    provider = local(cfg["provider"])
    root = local(cfg["backend_root"])
    require(digest(provider) == policy["source_sha256"], "BACKEND_PIN_MISMATCH")
    sys.path.insert(0, str(provider))
    from abqjobpilot.mcp.server import build_server
    from abqjobpilot.project.manager import load_project_info

    def check_backend():
        check_profile()
        require(digest(provider) == policy["source_sha256"], "BACKEND_PIN_MISMATCH")
        local(root / "project.json")
        for name in ("project.db", "project.db-wal", "project.db-shm", "runtime/live_status.json"):
            local(root / name)
        queue = local(root / "runtime/queue.json")
        require(digest(queue) == cfg["queue_sha256"], "FIXTURE_QUEUE_CHANGED")
        for row in json.loads(queue.read_bytes())["jobs"]:
            for key, value in row.items():
                if key.endswith("_path") or key == "work_dir":
                    require(local(value).is_relative_to(local(cfg["backend_work_root"])), "BACKEND_PATH_MISMATCH")
        require(load_project_info(root).project_id == cfg["backend_id"], "BACKEND_PROJECT_MISMATCH")

    check_backend()
    server = build_server(str(root))
    expected = {"abq_list_jobs", "abq_job_status", "abq_preflight", "abq_prepare_enqueue", "abq_locate_outputs"}
    require({tool.name for tool in asyncio.run(server.list_tools())} == expected, "BACKEND_TOOLSET_CHANGED")
    for name in expected - {"abq_list_jobs", "abq_job_status"}:
        server.remove_tool(name)

    async def guard(ctx, call_next):
        if ctx.method == "tools/call":
            check_backend()
            args = ctx.params.get("arguments") or {}
            if ctx.params["name"] == "abq_list_jobs":
                limit = args.get("limit", 50)
                require(set(args) <= {"scope", "limit"} and args.get("scope") in {"queue", "history"}
                        and type(limit) is int and 1 <= limit <= 50, "LIST_SELECTOR_OUTSIDE_SCOPE")
            elif ctx.params["name"] == "abq_job_status":
                require(bool(cfg["queue_id"]) and args == {"scope": "queue", "identifier": cfg["queue_id"]},
                        "STATUS_SELECTOR_OUTSIDE_SCOPE")
            else:
                raise ValueError("TOOL_NOT_IN_SCOPE")
        return await call_next(ctx)

    server.middleware.append(guard)
    server.run(transport="stdio")


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
