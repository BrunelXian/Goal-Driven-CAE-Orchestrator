"""Replay the scoped displacement fixture through an actual MCP client.

Operator provisioning is intentionally a separate entry point. This driver accepts
an existing scope and never issues, extends or repairs one. A checkpoint compares
the reopened project, task hub and workflow with the observations before shutdown.
"""

import argparse
import asyncio
import hashlib
import json
import os
import sys
from decimal import Decimal
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import MCPError
from mcp_types import CONNECTION_CLOSED, REQUEST_TIMEOUT

REPO = Path(__file__).resolve().parents[2]
SERVICE = "aegiscae.interfaces.mcp_scoped"


def checked(condition, code):
    if not condition:
        raise RuntimeError(code)


def write_new(path, value):
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, ensure_ascii=False, allow_nan=False)
        output.write("\n")


def fingerprint(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("ascii")).hexdigest()


def stdio_connect(binding, pin):
    @asynccontextmanager
    async def connect():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-B", "-m", SERVICE, "--binding-file", str(binding)],
            env={"GDCAE_FIXTURE_BINDING_SHA256": pin, "PYTHONPATH": str(REPO / "src")},
            cwd=str(REPO),
        )
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=30) as session:
                await session.initialize()

                async def call(name, arguments):
                    try:
                        response = await session.call_tool(name, arguments)
                    except MCPError as exc:
                        if exc.code in {CONNECTION_CLOSED, REQUEST_TIMEOUT}:
                            raise ConnectionError("MCP channel interrupted") from exc
                        raise
                    if response.structured_content is None:
                        raise RuntimeError("MCP_STRUCTURED_RESPONSE_REQUIRED")
                    return response.structured_content

                yield call
    return connect


READ_ONLY = {"gdcae_diagnostics", "gdcae_workflow_status", "gdcae_task_list"}
BACKOFF_SECONDS = (0.05, 0.15)


class MutationResponseUnknown(RuntimeError):
    def __init__(self, tool, arguments):
        super().__init__(f"{tool}: RESPONSE_UNKNOWN")
        self.tool = tool
        self.arguments = arguments


@asynccontextmanager
async def recovering_connection(connect, counters):
    """Own fresh transports for query-first recovery without changing any request key."""
    async with AsyncExitStack() as stack:
        raw = None

        async def reopen():
            nonlocal raw
            await stack.aclose()
            raw = await stack.enter_async_context(connect())
            counters["fresh_service_sessions"] += 1

        async def call(name, args):
            return await raw(name, args)

        call.reopen = reopen
        await reopen()
        yield call


async def reconcile(call, log, entry):
    args = entry["arguments"]
    operations = {"gdcae_workflow_advance": "advance", "gdcae_workflow_start": "start"}
    if not hasattr(call, "reopen") or entry["tool"] not in operations:
        raise MutationResponseUnknown(entry["tool"], args)
    await call.reopen()
    status = await invoke(call, log, "gdcae_workflow_status",
                          {"project_id": args["project_id"], "request_key": args["key"]})
    receipt = status.get("request_receipt")
    expected = {"key": args["key"], "operation": operations[entry["tool"]],
                "expected_revision": args["expected_revision"], "proposal": args.get("proposal")}
    if not isinstance(receipt, dict) or any(receipt.get(k) != v for k, v in expected.items()):
        raise MutationResponseUnknown(entry["tool"], args)
    if receipt.get("proposal_digest") != fingerprint(args.get("proposal")):
        raise MutationResponseUnknown(entry["tool"], args)
    entry["resolution"] = {"kind": "QUERIED_ORIGINAL_KEY", "revision": receipt["revision"]}
    return status



async def invoke(call, log, name, args, *, discard_ack=False):
    """Retry only a read. Each attempt records its response or transport failure."""
    delays = BACKOFF_SECONDS if name in READ_ONLY else ()
    for attempt in range(1, len(delays) + 2):
        entry = {"tool": name, "arguments": args, "attempt": attempt, "result": None}
        log.append(entry)
        try:
            reply = await call(name, args)
            if discard_ack and reply.get("error") is None:
                entry["discarded_ack_sha256"] = fingerprint(reply)
                entry["fault_injection"] = "DISCARD_ACCEPTED_REPLY_AT_CLIENT"
                raise TimeoutError("ACK discarded by the rehearsal")
            entry["result"] = reply
        except (OSError, EOFError) as exc:
            entry["transport_failure"] = type(exc).__name__
            if name not in READ_ONLY:
                return await reconcile(call, log, entry)
            if attempt > len(delays):
                raise
            if hasattr(call, "reopen"):
                await call.reopen()
        else:
            if reply.get("error") is None and isinstance(reply.get("data"), dict):
                return reply["data"]
            checked(reply.get("error") == "STORE_BUSY" and attempt <= len(delays),
                    f"{name}: {reply.get('error', 'MALFORMED_REPLY')}")
        entry["backoff_seconds"] = delays[attempt - 1]
        await asyncio.sleep(delays[attempt - 1])



async def snapshot(call, log):
    project = await invoke(call, log, "gdcae_project_open", {})
    args = {"project_id": project["project_id"]}
    tasks = await invoke(call, log, "gdcae_task_list", args)
    state = await invoke(call, log, "gdcae_workflow_status", args)
    return {"project": project, "tasks": tasks, "workflow": state}


def export_receipt(receipt, project_id, storage_id):
    """Remove local project identities; retain SHA-256 of the original JSON values."""
    encoded = json.dumps(receipt, ensure_ascii=True)
    for private, label in ((project_id, "<project>"), (storage_id, "<storage>")):
        if isinstance(private, str) and private:
            encoded = encoded.replace(private, label)
    public = json.loads(encoded)
    public["request_sha256"] = fingerprint(receipt["arguments"])
    public["response_sha256"] = fingerprint(receipt["result"]) if receipt["result"] is not None else None
    return public


async def advance(call, log, project_id, state):
    request = {"project_id": project_id, "key": f"main-r{state['revision']}",
               "expected_revision": state["revision"]}
    if state["next_action"] == "PROPOSE_CANDIDATE" and state["candidates"]:
        prior = state["candidates"][-1]
        displacement = Decimal(str(prior["observed_mm"]))
        checked(displacement.is_finite() and displacement > 0, "UNUSABLE_FIXTURE_FEEDBACK")
        new_load = round(Decimal(str(prior["force_N"])) * Decimal("1.0") / displacement)
        request["proposal"] = {"force_N": new_load, "unit": "N",
                               "baseline_digest": state["baseline_digest"]}
    lose_first_ack = state["state"] == "CANDIDATE" and state["runs_used"] == 0
    return await invoke(call, log, "gdcae_workflow_advance", request, discard_ack=lose_first_ack)


def revision_of(snapshot):
    revisions = [snapshot["project"]["revision"], snapshot["tasks"]["revision"],
                 snapshot["workflow"]["revision"]]
    checked(len(set(revisions)) == 1, "INCONSISTENT_PROJECT_SNAPSHOT")
    return revisions[0]


def main():
    parser = argparse.ArgumentParser(description="Rehearse the frozen 1.0 ± 0.1 mm displacement fixture")
    parser.add_argument("--binding-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Fresh JSON receipt file")
    options = parser.parse_args()
    if options.output.exists():
        parser.error("output must be a new file")
    pin = os.environ.get("GDCAE_FIXTURE_BINDING_SHA256")
    if not pin:
        parser.error("set GDCAE_FIXTURE_BINDING_SHA256 to the operator's binding receipt")
    report = asyncio.run(rehearse(stdio_connect(options.binding_file.resolve(), pin)))
    report["surface"] = "MCP SDK stdio child processes"
    write_new(options.output, report)
    print(json.dumps(report["counts"], indent=2))


async def rehearse(connect):
    """Enter Main once, resume a pending claim in a new service process, check the terminal replay."""
    log = []
    counters = {"fresh_service_sessions": 0}
    async with recovering_connection(connect, counters) as call:
        opened = await invoke(call, log, "gdcae_project_open", {})
        project_id = opened["project_id"]
        pid = {"project_id": project_id}
        diag = await invoke(call, log, "gdcae_diagnostics", pid)
        checked(diag["backend_kind"] == "FIXTURE" and diag["real_solver_executed"] is False
                and diag["solver_budget"] == 0 and diag["host_attestation"] == "UNATTESTED",
                "WRONG_BACKEND_OR_SCOPE")
        initial = await invoke(call, log, "gdcae_workflow_status", pid)
        checked(initial["state"] == "NEW", "FRESH_SCOPED_WORKFLOW_REQUIRED")
        await invoke(call, log, "gdcae_workflow_start",
                     {**pid, "key": "enter-main", "expected_revision": opened["revision"]})
        state = await invoke(call, log, "gdcae_workflow_status", pid)
        # Stop after the first accepted claim. The checkpoint is only comparison evidence.
        for _ in range(12):
            if state["state"] == "CLAIMED":
                break
            await advance(call, log, project_id, state)
            state = await invoke(call, log, "gdcae_workflow_status", pid)
        checked(state["state"] == "CLAIMED", "CLAIM_CHECKPOINT_NOT_REACHED")
        checkpoint = await snapshot(call, log)
        revision_of(checkpoint)

    async with recovering_connection(connect, counters) as call:
        # Query the original workflow before introducing any further mutation.
        recovered = await invoke(call, log, "gdcae_workflow_status", pid)
        checked(recovered == checkpoint["workflow"]
                and recovered["next_action"] == "QUERY_ORIGINAL_KEY_ONLY", "CLAIM_RECOVERY_FAILED")
        checked(await snapshot(call, log) == checkpoint, "REOPEN_PROJECT_OR_TASK_MISMATCH")
        state = recovered
        for _ in range(24):
            if state["state"] in {"GOAL_MET", "BUDGET_EXHAUSTED"}:
                break
            await advance(call, log, project_id, state)
            state = await invoke(call, log, "gdcae_workflow_status", pid)
        checked(state["state"] == "GOAL_MET" and state["runs_used"] == 2, "GOAL_NOT_REACHED_IN_TWO")
        terminal = await snapshot(call, log)
        revision_of(terminal)

    async with recovering_connection(connect, counters) as call:
        checked(await snapshot(call, log) == terminal, "TERMINAL_REOPEN_MISMATCH")

    candidates = state["candidates"]
    checked(len(candidates) == 2, "TWO_CANDIDATES_REQUIRED")
    first, second = candidates
    low, high = Decimal("0.9"), Decimal("1.1")
    observed = [Decimal(str(c["observed_mm"])) for c in candidates]
    checked(all(x.is_finite() for x in observed) and not low <= observed[0] <= high
            and low <= observed[1] <= high, "NUMERICAL_REPLAY_MISMATCH")
    checked(first["input_digest"] != second["input_digest"]
            and first["evidence_digest"] != second["evidence_digest"]
            and first["decision"] != second["decision"], "CANDIDATE_PROVENANCE_COLLISION")
    checked(state["backend_kind"] == "FIXTURE" and not state["real_solver_executed"],
            "BACKEND_MISMATCH")
    return {"goal": state["goal"], "state": state["state"],
            "backend_kind": state["backend_kind"], "host_attestation": state["host_attestation"],
            "counts": {"mcp_tool_calls": len(log), **counters,
                       "read_retries": sum(x["attempt"] > 1 for x in log),
                       "fixture_executions": state["runs_used"], "real_solver_calls": 0,
                       "in_scope_human_interventions": 0},
            "recovery": {"claim_snapshot_sha256": fingerprint(checkpoint),
                         "terminal_snapshot_sha256": fingerprint(terminal),
                         "claim_revision": revision_of(checkpoint), "terminal_revision": revision_of(terminal),
                         "project_tasks_workflow_equal_after_each_restart": True,
                         "recovered_next_action": recovered["next_action"]},
            "receipts": [export_receipt(x, project_id, opened["storage_generation"]) for x in log]}


if __name__ == "__main__":
    main()
