"""Provision one local candidate. Run with the selected absolute interpreter and isolated mode."""
import argparse
import hashlib
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path
from uuid import UUID


def local(path):
    path = Path(path)
    if (not path.is_absolute() or path.drive.startswith("\\\\") or ".." in path.parts or
            any(p.is_symlink() or p.is_junction() for p in (path, *path.parents))):
        raise ValueError("LOCAL_UNREDIRECTED_PATH_REQUIRED")
    return path


def sha(path):
    return hashlib.sha256(local(path).read_bytes()).hexdigest()


def verify_plugin(plugin, pin):
    manifest = local(plugin / "manifest.json")
    if sha(manifest) != pin:
        raise ValueError("MANIFEST_MISMATCH")
    files = json.loads(manifest.read_bytes())["files"]
    actual = {p.relative_to(plugin).as_posix() for p in plugin.rglob("*") if p.is_file()}
    if actual != set(files) | {"manifest.json"} or any(sha(plugin / k) != v for k, v in files.items()):
        raise ValueError("PACKAGE_INVENTORY_MISMATCH")


def configure(args):
    if not sys.flags.isolated or sys.version_info[:3] != (3, 12, 10) or version("mcp") != "2.3.0":
        raise ValueError("BOUND_RUNTIME_MISMATCH")
    for path in (args.plugin, args.binding, args.profile, args.provider, args.backend_root, args.backend_work_root):
        local(path)
    if args.profile.exists():
        raise ValueError("DEPLOYMENT_ALREADY_EXISTS")
    verify_plugin(args.plugin, args.manifest_sha256)
    policy = json.loads((args.plugin / "runtime/abq-readonly.json").read_bytes())
    if sha(args.provider) != policy["source_sha256"]:
        raise ValueError("PROVIDER_MISMATCH")
    sys.path[:0] = [str(args.plugin / "runtime/core"), str(args.provider)]
    from abqjobpilot.project.manager import ProjectManager, load_project_info
    from aegiscae.interfaces.fixture_scope import Scope, authorize
    if args.create_empty_backend:
        if args.backend_root.exists() or args.queue_id:
            raise ValueError("FRESH_EMPTY_BACKEND_REQUIRED")
        recent = local(args.backend_root.with_name(args.backend_root.name + ".recent.json"))
        if recent.exists():
            raise ValueError("FRESH_PROJECT_INDEX_REQUIRED")
        backend_id = ProjectManager(recent_file=recent).create_project(args.backend_root, "Scoped fixture").project_id
    else:
        backend_id = args.backend_id
    if str(UUID(backend_id)) != backend_id or load_project_info(args.backend_root).project_id != backend_id:
        raise ValueError("BACKEND_PROJECT_MISMATCH")
    queue_path = local(args.backend_root / "runtime/queue.json")
    rows = json.loads(queue_path.read_bytes())["jobs"]
    if args.queue_id:
        if len(rows) != 1 or rows[0]["queue_id"] != args.queue_id or rows[0]["status"] != "QUEUED":
            raise ValueError("EXPECTED_SINGLE_INERT_ROW")
        paths = [v for k, v in rows[0].items() if k.endswith("_path") or k == "work_dir"]
        if not paths or any(not local(v).is_relative_to(args.backend_work_root) for v in paths):
            raise ValueError("BACKEND_WORK_PATH_OUTSIDE_SCOPE")
    elif rows:
        raise ValueError("EXPECTED_EMPTY_BACKEND")
    if args.new_fixture_root is not None:
        binding = authorize(args.binding, local(args.new_fixture_root),
                            max_executions=args.max_executions, ttl_seconds=args.ttl_seconds)
        binding_pin = binding["binding_sha256"]
    else:
        binding_pin = args.binding_sha256
    scope = Scope(args.binding, binding_pin).read("gdcae_project_open")
    profile = {"python": sys.executable, "python_sha256": sha(sys.executable),
               "manifest_sha256": args.manifest_sha256, "binding": str(args.binding),
               "binding_sha256": binding_pin, "backend_root": str(args.backend_root),
               "backend_id": backend_id, "provider": str(args.provider)}
    profile.update(queue_sha256=sha(queue_path), backend_work_root=str(args.backend_work_root),
                   queue_id=args.queue_id)
    args.profile.parent.mkdir(parents=True, exist_ok=True)
    with args.profile.open("x", encoding="utf-8") as output:
        json.dump(profile, output)
        output.flush()
        os.fsync(output.fileno())
    return {"configured": True, "project_id": scope["project_id"],
            "backend_kind": "FIXTURE", "max_executions": scope["max_executions"],
            "real_solver_budget": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("profile", "plugin", "provider", "backend-root", "backend-work-root", "binding"):
        parser.add_argument("--" + key, required=True, type=Path)
    backend = parser.add_mutually_exclusive_group(required=True)
    backend.add_argument("--backend-id")
    backend.add_argument("--create-empty-backend", action="store_true")
    parser.add_argument("--queue-id")
    parser.add_argument("--manifest-sha256", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--binding-sha256", help="digest from the operator who issued this scope")
    group.add_argument("--new-fixture-root", type=Path, help="issue a new scope for this new local project")
    parser.add_argument("--max-executions", type=int, default=3)
    parser.add_argument("--ttl-seconds", type=int, default=3600)
    print(json.dumps(configure(parser.parse_args())))
