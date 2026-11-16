"""Main's source/development entry for a project-bound read-only engineering probe."""
import argparse
import asyncio
from contextlib import contextmanager
import io
import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from abqjobpilot_readonly import (
    binding_reference, check_task, observe, save_observation, submit_observation,
)
from aegiscae.contracts.research_contracts import ContractError
from aegiscae.research.capability_discovery import local
from aegiscae.research.project import open_agreement_project

ABQ_COMMIT = "7012133e7cc0176bb3e56fc24d7154ee3b90bb81"


@contextmanager
def server_parameters(args):
    from mcp import StdioServerParameters

    params = ["-I", "-B", "-m", "abqjobpilot.mcp.server", "--project", str(local(args.backend_project))]
    if args.backend_source is None:
        # The operator supplies the separately provisioned interpreter, never a command from a task.
        yield StdioServerParameters(command=str(local(args.backend_python)), args=params)
        return
    # Execute the reviewed upstream Git object, including when the user's checkout is dirty.
    # No local working-tree module, alternate backend entry or recent Project is imported.
    with tempfile.TemporaryDirectory(prefix="gdcae-abq-read-") as tmp:
        data = subprocess.run(["git", "--no-replace-objects", "-C", str(local(args.backend_source)), "archive",
                               "--format=zip", ABQ_COMMIT, "--", "abqjobpilot"],
                              capture_output=True, check=True, timeout=30).stdout
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            archive.extractall(tmp)
        bootstrap = ("import runpy,sys;sys.path.insert(0,sys.argv.pop(1));"
                     "runpy.run_module('abqjobpilot.mcp.server',run_name='__main__')")
        yield StdioServerParameters(command=str(local(args.backend_python)), cwd=tmp,
                                    args=["-I", "-B", "-c", bootstrap, tmp, *params[-2:]])


async def capture(args, project):
    check_task(project, args.host, args.desktop, args.backend_id)
    try:
        if version("mcp").split(".", 1)[0] != "2":
            raise ContractError("MCP_CLIENT_SDK_INCOMPATIBLE")
        from mcp import Client
    except (PackageNotFoundError, ImportError):
        raise ContractError("MCP_CLIENT_SDK_UNAVAILABLE") from None
    with server_parameters(args) as params:
        async with asyncio.timeout(60):
            async with Client(params, mode="legacy", read_timeout_seconds=15) as client:
                report = await observe(client, project, args.host, args.desktop, args.backend_id, queue_id=args.queue_id)
    report["launch_source"] = "reviewed-source" if args.backend_source else "operator-provisioned-interpreter"
    if args.backend_source:
        report["source_commit"] = ABQ_COMMIT
    return {"observation": report, "artifact": save_observation(report, args.evidence_dir)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    bind = commands.add_parser("binding-ref", help="compute the pair for Main to record on T02")
    bind.add_argument("--research-id", required=True)
    bind.add_argument("--backend-id", required=True)
    probe = commands.add_parser("observe")
    submit = commands.add_parser("submit")
    for cmd in (probe, submit):
        cmd.add_argument("--project", required=True, type=Path, help="explicit existing GD-CAE ResearchProject")
        cmd.add_argument("--host", required=True)
        cmd.add_argument("--desktop", required=True)
        cmd.add_argument("--backend-id", required=True, help="previously approved AbqJobPilot Project UUID")
        cmd.add_argument("--evidence-dir", required=True, type=Path)
    probe.add_argument("--backend-project", required=True, type=Path)
    probe.add_argument("--backend-python", required=True, type=Path)
    probe.add_argument("--backend-source", type=Path, help="optional checkout containing the reviewed commit")
    probe.add_argument("--queue-id", help="specific queue identifier to inspect")
    submit.add_argument("--sha256", required=True, help="pin returned by the trusted observe invocation")
    submit.add_argument("--expected-revision", required=True, type=int)
    submit.add_argument("--key", required=True)
    args = parser.parse_args()
    if args.action == "binding-ref":
        result = binding_reference(args.research_id, args.backend_id)
    else:
        from aegiscae.research.task_cards import main_identity
        main_identity(args.host, args.desktop)
        project = open_agreement_project(args.project, write=args.action == "submit")
        if args.action == "observe":
            result = asyncio.run(capture(args, project))
        else:
            result = submit_observation(project, args.host, args.desktop, args.backend_id, args.evidence_dir,
                                        args.sha256, args.expected_revision, args.key)
    print(json.dumps(result, ensure_ascii=True))


def failure_code(exc):
    # AnyIO can wrap application refusals when leaving an SDK stdio task group.
    if isinstance(exc, BaseExceptionGroup):
        reasons = {failure_code(cause) for cause in exc.exceptions}
        return reasons.pop() if len(reasons) == 1 else "MCP_SESSION_FAILED"
    return getattr(exc, "code", type(exc).__name__)


if __name__ == "__main__":
    try:
        main()
    except (ContractError, OSError, RuntimeError, ValueError, subprocess.SubprocessError, ExceptionGroup) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": failure_code(exc),
                          "execution_authorized": False}))
        sys.exit(2)
