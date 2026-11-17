"""Rehearse the scoped fixture through an installed candidate, including new Host processes."""
import argparse
import asyncio
import hashlib
import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from host_probe import InstalledHost

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples/scoped_fixture"))
from rehearse import rehearse


def inventory(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob("*") if p.is_file()}


async def run(args):
    profile = json.loads((args.home / "gdcae-scoped-fixture/deployment.json").read_bytes())
    root = Path(profile["backend_root"])
    if args.queue_id != profile["queue_id"]:
        raise ValueError("BOUND_QUEUE_SELECTOR_REQUIRED")
    before = inventory(root)
    reports = []
    classic = {}

    @asynccontextmanager
    async def connect():
        instance = InstalledHost(args.codex, args.home, args.market)
        try:
            with instance as host:
                if not reports:
                    if host.servers["abqjobpilot"]["tools"] != ["abq_job_status", "abq_list_jobs"]:
                        raise RuntimeError("CLASSIC_TOOLSET_CHANGED")
                    jobs = host.call("abq_list_jobs", {"scope": "queue"})
                    history = host.call("abq_list_jobs", {"scope": "history"})
                    if (any(x["project_id"] != profile["backend_id"] or x["errors"] for x in (jobs, history))
                            or history["data"]["jobs"] or [r["queue_id"] for r in jobs["data"]["jobs"]] !=
                            ([args.queue_id] if args.queue_id else [])):
                        raise RuntimeError("CLASSIC_FIXTURE_MISMATCH")
                    classic.update(queue_rows=len(jobs["data"]["jobs"]), history_rows=0, expected_backend_id_matched=True)
                    if args.queue_id:
                        status = host.call("abq_job_status", {"scope": "queue", "identifier": args.queue_id})
                        if (status["project_id"] != profile["backend_id"] or status["errors"] or
                                status["status"] != "QUEUED" or status["data"]["active_execution_confirmed"]):
                            raise RuntimeError("CLASSIC_STATUS_MISMATCH")
                        classic.update(status=status["status"], active_execution_confirmed=False)

                async def call(name, arguments):
                    return host.call(name, arguments)

                yield call
        finally:
            reports.append({"host": getattr(instance, "host_version", None),
                            "plugin": getattr(instance, "plugin", None),
                            "servers": getattr(instance, "servers", None),
                            "tool_calls": instance.calls, "host_exit": instance.exit_code, "cleanup": instance.cleanup})

    result = None
    failure = None
    try:
        result = await rehearse(connect)
        if any(r["host_exit"] != 0 or r["cleanup"]["forced"] or r["cleanup"]["surviving_descendants"]
               for r in reports) or before != inventory(root):
            raise RuntimeError("HOST_EXIT_OR_CLASSIC_DATA_CHANGED")
    except Exception as exc:
        failure = str(exc)[:400]
    return {"surface": "Desktop-bundled app-server; installed local marketplace; ephemeral host, no GUI/model turn",
            "status": "PARTIAL" if failure else "PASS", "failure": failure,
            "host_processes": reports, "classic": classic, "classic_data_unchanged": before == inventory(root),
            "total_completed_host_tool_calls": sum(len(r["tool_calls"]) for r in reports),
            "fixture": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("codex", "home", "market", "output"):
        parser.add_argument("--" + key, required=True, type=Path)
    parser.add_argument("--queue-id", help="the preselected inert QUEUED fixture row, omit for empty project")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output receipt must be a new file")
    result = asyncio.run(run(args))
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({"host_processes": len(result["host_processes"]),
                      "completed_host_tool_calls": result["total_completed_host_tool_calls"],
                      "status": result["status"], "failure": result["failure"]}))
    sys.exit(0 if result["status"] == "PASS" else 2)
