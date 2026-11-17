"""Bind CAE Agent services on this computer. The MCP tool surface cannot invoke this entry."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from uuid import UUID


def bind_classic(args, local, sha):
    options = (args.provider, args.classic_root, args.backend_work_root)
    if not any((*options, args.classic_id, args.create_empty_classic, args.queue_id)):
        return None
    if not all(options) or not (args.classic_id or args.create_empty_classic):
        raise ValueError("INCOMPLETE_CLASSIC_BINDING")
    provider, root, work = map(local, options)
    policy = json.loads((args.service_root / "abq-readonly.json").read_bytes())
    if sha(provider) != policy["source_sha256"]:
        raise ValueError("PROVIDER_IDENTITY_CHANGED")
    sys.path.insert(0, str(provider))
    from abqjobpilot.project.manager import ProjectManager, load_project_info
    if args.create_empty_classic:
        index = local(root.with_name(root.name + ".recent.json"))
        if root.exists() or index.exists() or args.queue_id:
            raise ValueError("FRESH_EMPTY_CLASSIC_REQUIRED")
        expected = ProjectManager(recent_file=index).create_project(root, "CAE Agent isolated QA").project_id
    else:
        expected = args.classic_id
    if str(UUID(expected)) != expected or load_project_info(root).project_id != expected:
        raise ValueError("CLASSIC_PROJECT_MISMATCH")
    queue = local(root / "runtime/queue.json")
    rows = json.loads(queue.read_bytes())["jobs"]
    if args.queue_id:
        if len(rows) != 1 or rows[0]["queue_id"] != args.queue_id or rows[0]["status"] != "QUEUED":
            raise ValueError("EXPECTED_SINGLE_INERT_RECORD")
        paths = [v for k, v in rows[0].items() if k.endswith("_path") or k == "work_dir"]
        if not paths or any(not local(v).is_relative_to(work) for v in paths):
            raise ValueError("CLASSIC_WORK_PATH_OUTSIDE_SCOPE")
    elif rows:
        raise ValueError("EXPECTED_EMPTY_CLASSIC_PROJECT")
    return dict(provider=str(provider), backend_root=str(root), backend_id=expected, backend_work_root=str(work),
                queue_id=args.queue_id, queue_sha256=sha(queue))


def configure(args):
    root = args.service_root
    raw = (root / "manifest.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.service_sha256:
        raise ValueError("SERVICE_MANIFEST_MISMATCH")
    if hashlib.sha256((root / "integrity.py").read_bytes()).hexdigest() != json.loads(raw)["files"]["integrity.py"]:
        raise ValueError("CHECKER_IDENTITY_CHANGED")
    sys.path.insert(0, str(root))
    from integrity import local, runtime, sha, verify
    runtime()
    verify(root, args.service_sha256, "service")
    profile = local(args.profile)
    binding = local(args.binding)
    if profile.exists():
        raise ValueError("PROFILE_ALREADY_EXISTS")
    if bool(args.adapter_root) != bool(args.adapter_sha256):
        raise ValueError("INCOMPLETE_ADAPTER_BINDING")
    if args.adapter_root:
        verify(args.adapter_root, args.adapter_sha256, "codex-adapter")
    if bool(args.contract_file) != bool(args.new_project):
        raise ValueError("EXPLICIT_CONTRACT_AND_PROJECT_REQUIRED")
    if args.new_project and args.max_executions is None:
        raise ValueError("EXPLICIT_EXECUTION_LIMIT_REQUIRED")
    sys.path.insert(0, str(root / "core"))
    from aegiscae.interfaces.research_scope import Scope, authorize
    from aegiscae.contracts.research_contracts import strict_json
    contract = None
    if args.contract_file:
        contract_path = local(args.contract_file)
        if contract_path.stat().st_size > 8192:
            raise ValueError("CONTRACT_SIZE_LIMIT")
        contract = strict_json(contract_path.read_bytes())
    classic = bind_classic(args, local, sha)
    if args.new_project:
        pin = authorize(binding, local(args.new_project), contract=contract, max_executions=args.max_executions,
                        ttl_seconds=args.ttl_seconds, operations=args.allow_operation)["binding_sha256"]
    else:
        pin = args.binding_sha256
    if binding.stat().st_size > 8192:
        raise ValueError("SCOPE_SIZE_LIMIT")
    record = strict_json(binding.read_bytes())
    Scope.validate(record)
    scope = Scope(binding, pin).read(record["operations"][0])
    data = {"service_root": str(root), "service_sha256": args.service_sha256,
            "adapter_root": str(args.adapter_root) if args.adapter_root else None,
            "adapter_sha256": args.adapter_sha256,
            "python": sys.executable, "python_sha256": sha(sys.executable), "classic": classic,
            "binding": str(binding), "binding_sha256": pin}
    profile.parent.mkdir(parents=True, exist_ok=True)
    with profile.open("x", encoding="utf-8") as stream:
        json.dump(data, stream)
        stream.flush()
        os.fsync(stream.fileno())
    return {"configured": True, "project_id": scope["project_id"], "binding_sha256": pin,
            "max_executions": scope["max_executions"], "operations": scope["operations"],
            "classic_deployed": bool(classic)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("service-root", "profile", "binding"):
        parser.add_argument("--" + key, required=True, type=Path)
    for key in ("adapter-root", "provider", "classic-root", "backend-work-root", "contract-file"):
        parser.add_argument("--" + key, type=Path)
    parser.add_argument("--service-sha256", required=True)
    parser.add_argument("--adapter-sha256")
    parser.add_argument("--queue-id")
    backend = parser.add_mutually_exclusive_group()
    backend.add_argument("--classic-id")
    backend.add_argument("--create-empty-classic", action="store_true")
    bind = parser.add_mutually_exclusive_group(required=True)
    bind.add_argument("--new-project", type=Path)
    bind.add_argument("--binding-sha256")
    parser.add_argument("--max-executions", type=int, choices=range(4))
    parser.add_argument("--allow-operation", action="append", help="repeat to narrow the new binding's MCP operations")
    parser.add_argument("--ttl-seconds", type=int, default=3600)
    print(json.dumps(configure(parser.parse_args())))
