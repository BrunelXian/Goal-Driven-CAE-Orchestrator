"""Reviewed Classic 0.2.2 reader for an explicitly bound, inert local Project."""
import asyncio
import hashlib
import json
import sys
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
