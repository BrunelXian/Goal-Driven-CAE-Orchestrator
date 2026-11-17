"""Real stdio refusals and persistence checks for an operator-bound research project.

The installed-host rehearsal is the positive execution case. These tests exercise
the public protocol without allocating additional Fixture execution budget.
"""

import asyncio
import sys
from pathlib import Path

from aegiscae.interfaces.fixture_scope import authorize

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples" / "scoped_fixture"))
from rehearse import stdio_connect


def make_scope(root, **limits):
    binding = root / "scope.json"
    grant = authorize(binding, root / "research", **limits)
    return binding, grant


def test_scope_messages_cannot_self_authorize_or_choose_paths(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    binding, grant = make_scope(tmp_path, operations=["gdcae_project_open", "gdcae_diagnostics"])
    project_id = grant["project_id"]
    connect = stdio_connect(binding, grant["binding_sha256"])

    async def scenario():
        async with connect() as call:
            for untrusted in ({"project_root": "../external"}, {"project_root": str(tmp_path.parent)},
                              {"approved": True}, {"role": "Main"}):
                response = await call("gdcae_project_open", untrusted)
                assert response["error"] == "INVALID_ARGUMENTS"
                assert not (tmp_path / "research").exists()
            project = (await call("gdcae_project_open", {}))["data"]
            assert project["project_id"] == project_id
            assert project["host_attestation"] == "UNATTESTED"
            diagnostics = (await call("gdcae_diagnostics", {"project_id": project_id}))["data"]
            assert diagnostics["real_solver_executed"] is False
            assert diagnostics["solver_budget"] == 0
            denied = await call("gdcae_task_list", {"project_id": project_id})
            assert denied["error"] == "OPERATION_DENIED"
            wrong_project = "rp_" + ("1" if project_id[-1] == "0" else "0") * 32
            denied = await call("gdcae_diagnostics", {"project_id": wrong_project})
            assert denied["error"] == "PROJECT_MISMATCH"
            assert (await call("gdcae_project_open", {}))["data"] == project
            binding.write_bytes(binding.read_bytes() + b" ")
            denied = await call("gdcae_project_open", {})
            assert denied["error"] == "BINDING_CHANGED"
        assert not (tmp_path.parent / "external").exists()

    asyncio.run(scenario())


TAMPER_CASES = [
    ("target_mm", "100"), ("tolerance_mm", "2"), ("baseline_digest", "1" * 64),
    ("load_n", -3), ("unit", "kN"), ("evidence", {"goal_met": True}),
]

def test_mcp_frozen_parameters_are_not_client_override_fields(tmp_path):
    binding, grant = make_scope(tmp_path, max_executions=0)
    async def scenario():
        async with stdio_connect(binding, grant["binding_sha256"])() as call:
            project = (await call("gdcae_project_open", {}))["data"]
            for field, value in TAMPER_CASES:
                event = {"project_id": project["project_id"], "key": "advance",
                         "expected_revision": project["revision"], field: value}
                rejected = await call("gdcae_workflow_advance", event)
                assert rejected["error"] == "INVALID_ARGUMENTS"
            actual = (await call("gdcae_project_open", {}))["data"]
            assert actual == project

    asyncio.run(scenario())


def test_reconnect_and_replay_task_after_discarded_response(tmp_path):
    binding, grant = make_scope(tmp_path, max_executions=0)
    connect = stdio_connect(binding, grant["binding_sha256"])
    pid = {"project_id": grant["project_id"]}

    async def scenario():
        async with connect() as call:
            opened = (await call("gdcae_project_open", {}))["data"]
            start = {**pid, "key": "enter-main", "expected_revision": opened["revision"]}
            assert (await call("gdcae_workflow_start", start))["error"] is None
            tasks = (await call("gdcae_task_list", pid))["data"]
            create = {**pid, "key": "create-review", "expected_revision": tasks["revision"],
                      "data": {"task_id": "T90", "kind": "independent-review",
                               "goal": "Review isolated fixture provenance",
                               "criterion": "Recompute evidence digests", "deps": [], "refs": []}}
            # Transport completed, but the coordinating client discards this ACK.
            await call("gdcae_task_create", create)

        async with connect() as call:
            tasks = (await call("gdcae_task_list", pid))["data"]
            assert sum(item["task_id"] == "T90" for item in tasks["tasks"]) == 1
            original = await call("gdcae_task_create", create)
            assert original["error"] is None
            assert await call("gdcae_task_create", create) == original
            assert (await call("gdcae_task_list", pid))["data"] == tasks
            conflict = {**create, "data": {**create["data"], "goal": "Conflicting goal"}}
            assert (await call("gdcae_task_create", conflict))["error"] == "REQUEST_KEY_CONFLICT"
            update = {**pid, "key": "begin-review", "expected_revision": tasks["revision"],
                      "data": {"task_id": "T90", "execution": "IN_PROGRESS", "evidence": []}}
            assert (await call("gdcae_task_update", update))["error"] is None
            updated = (await call("gdcae_task_list", pid))["data"]
            task = next(item for item in updated["tasks"] if item["task_id"] == "T90")
            assert task["execution"] == "IN_PROGRESS" and task["deliverable"]
            assert updated["revision"] == tasks["revision"] + 1

    asyncio.run(scenario())



def test_reject_candidate_fields_before_spending_fixture_budget(tmp_path):
    binding, grant = make_scope(tmp_path)
    pid = {"project_id": grant["project_id"]}

    async def scenario():
        async with stdio_connect(binding, grant["binding_sha256"])() as call:
            opened = (await call("gdcae_project_open", {}))["data"]
            start = {**pid, "key": "start", "expected_revision": opened["revision"]}
            started = (await call("gdcae_workflow_start", start))["data"]
            assert started["next_action"] == "PROPOSE_CANDIDATE" and started["runs_used"] == 0
            proposal = {"force_N": 50, "unit": "N", "baseline_digest": started["baseline_digest"]}
            for bad in ({"force_N": 201}, {"force_N": 0}, {"unit": "kN"},
                        {"baseline_digest": "0" * 64}):
                request = {**pid, "key": "proposal", "expected_revision": started["revision"],
                           "proposal": {**proposal, **bad}}
                rejected = await call("gdcae_workflow_advance", request)
                assert rejected["error"] in {"INVALID_ARGUMENTS", "UNIT_MISMATCH", "BASELINE_MISMATCH",
                                              "LOAD_OUT_OF_BOUNDS"}
                assert (await call("gdcae_workflow_status", pid))["data"] == started
            request = {**pid, "key": "proposal", "expected_revision": started["revision"],
                       "proposal": proposal}
            accepted = (await call("gdcae_workflow_advance", request))["data"]
            assert accepted["state"] == "CANDIDATE" and accepted["runs_used"] == 0

    asyncio.run(scenario())


def test_read_retry_and_original_key_reconciliation_without_execution(tmp_path):
    from rehearse import invoke, recovering_connection

    binding, grant = make_scope(tmp_path, max_executions=0)
    connect = stdio_connect(binding, grant["binding_sha256"])
    pid = {"project_id": grant["project_id"]}

    async def scenario():
        log = []
        counters = {"fresh_service_sessions": 0}
        async with recovering_connection(connect, counters) as call:
            project = await invoke(call, log, "gdcae_project_open", {})
            event = {**pid, "key": "start", "expected_revision": project["revision"]}
            status = await invoke(call, log, "gdcae_workflow_start", event, discard_ack=True)
            assert [entry["tool"] for entry in log] == [
                "gdcae_project_open", "gdcae_workflow_start", "gdcae_workflow_status"]
            assert counters["fresh_service_sessions"] == 2
            assert log[2]["arguments"]["request_key"] == "start"
            assert log[1]["resolution"]["kind"] == "QUERIED_ORIGINAL_KEY"
            assert status["state"] == "BUDGET_EXHAUSTED" and status["runs_used"] == 0
            request = {**pid, "key": "next", "expected_revision": status["revision"]}
            denied = await call("gdcae_workflow_advance", request)
            assert denied["error"] == "ILLEGAL_STEP"
            # A transient read failure carries no authorization significance.
            calls = 0

            async def read_with_one_fault(name, args):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise TimeoutError()
                return await call(name, args)

            recovered = await invoke(read_with_one_fault, log, "gdcae_workflow_status", pid)
            assert recovered["state"] == "BUDGET_EXHAUSTED"
            assert calls == 2 and log[-2]["backoff_seconds"] > 0 and log[-1]["attempt"] == 2

    asyncio.run(scenario())
