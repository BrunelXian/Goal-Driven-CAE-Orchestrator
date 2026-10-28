"""Opt-in M01-C: fresh Fake owner, official STDIO client and actual Codex CLI.

Trusted fixture preparation is deliberately outside the read-only production
module. Never reuses M01-B runtime artifacts. Run this module alone.
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import tomllib
from dataclasses import asdict

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from test_af_read_live import binding, check, fake_health, safe_exit, save, snapshot


pytestmark = pytest.mark.skipif(
    os.environ.get("GDCAE_M01C_LIVE") != "APPROVED_TEST_ONLY",
    reason="M01-C fresh TEST root and explicit live opt-in required",
)
REPO = Path(__file__).resolve().parents[2]
NAMES = {"gdcae_" + name for name in (
    "capabilities", "list_runs", "get_run", "get_receipt", "list_events",
    "get_validations", "get_diagnostic",
)}


def fresh_root():
    root, temp = Path(os.environ["GDCAE_M01C_ROOT"]), Path(os.environ["TEMP"])
    check(root.is_absolute() and root.parent == temp and root.name.startswith("gdcae-m01c-"),
          "EXPLICIT_TEMP_CHILD_REQUIRED")
    check(not root.exists(), "EXISTING_ROOT_REJECTED")
    for parent in (temp, *temp.parents):
        info = parent.lstat()
        check(not stat.S_ISLNK(info.st_mode) and not (info.st_file_attributes & 0x400),
              "REPARSE_PARENT_REJECTED")
        for marker in (".git", "agent_project.json", "experiment.json", "project.json"):
            check(not (parent / marker).exists(), "PROJECT_ANCESTOR_REJECTED")
    check(root.resolve().parent == temp.resolve(), "ROOT_ESCAPE")
    root.mkdir(exist_ok=False)
    return root


def environment(source):
    return {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(REPO / "src") + os.pathsep + str(source)}


async def mcp_reads(root, source, binding_file, selected, empty, secret):
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-B", "-m", "aegiscae.interfaces.mcp_read", "--binding-file", str(binding_file)],
        env=environment(source), cwd=str(REPO),
    )
    values = []
    with (root / ("empty.stderr" if empty else "seeded.stderr")).open("w", encoding="utf-8") as log:
        async with stdio_client(parameters, errlog=log) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=20) as session:
                initialized = await session.initialize()
                tools = await session.list_tools()
                check({tool.name for tool in tools.tools} == NAMES, "TOOL_SET_MISMATCH")

                async def read(name, arguments=None):
                    result = await session.call_tool(name, arguments or {})
                    value = result.structured_content
                    check(value == json.loads(result.content[0].text), "MCP_CONTENT_MISMATCH")
                    encoded = json.dumps(value)
                    check(secret not in encoded and str(root) not in encoded
                          and json.dumps(str(root))[1:-1] not in encoded
                          and "credential" not in encoded, "MCP_DISCLOSURE")
                    values.append({"name": name, "value": value})
                    return value

                caps = await read("gdcae_capabilities")
                check(caps["data"]["simulation"] is True, "NOT_TEST")
                runs = await read("gdcae_list_runs", {"limit": 2})
                check(len(runs["data"]) == (0 if empty else 2), "RUN_COUNT")
                if not empty:
                    second = await read("gdcae_list_runs", {"cursor": runs["next_cursor"]})
                    check(len(second["data"]) == 1 and second["next_cursor"] is None, "RUN_PAGING")
                events = await read("gdcae_list_events", {"limit": 2, "run_id": selected})
                if not empty:
                    check(not events["data"] and events["more_possible"] is True
                          and events["next_cursor"]["position"] == 2, "FILTERED_EMPTY")
                    page = await read("gdcae_list_events", {"cursor": events["next_cursor"]})
                    check(len(page["data"]) == 10 and page["data"][-1]["project_sequence"] == 12,
                          "EVENT_PAGING")
                for name, args in (
                    ("gdcae_get_run", {"run_id": selected}),
                    ("gdcae_get_receipt", {"key": "key-0"}),
                    ("gdcae_get_validations", {"run_id": selected}),
                    ("gdcae_get_diagnostic", {"run_id": selected}),
                ):
                    value = await read(name, args)
                    check(value["error"]["code"] == "NOT_FOUND" if empty else value["error"] is None,
                          "MISSING_OR_VALID_READ")
                bad = await read("gdcae_get_run", {"run_id": selected, "root": "private-canary"})
                check(bad["error"]["code"] == "INVALID_REQUEST", "BINDING_SWITCH_ACCEPTED")
    return {"protocol": initialized.protocol_version, "tools": sorted(NAMES), "reads": values}


def codex_review(root, source, bound, binding_file):
    config = REPO / ".codex" / "config.toml"
    check_owned_config(config)
    text = (
        "[mcp_servers.gdcae_read]\n"
        f"command = {json.dumps(sys.executable)}\n"
        'args = ["-B", "-m", "aegiscae.interfaces.mcp_read", "--binding-file", '
        + json.dumps(str(binding_file)) + "]\n"
        f"cwd = {json.dumps(str(REPO))}\n"
        "startup_timeout_sec = 30\ntool_timeout_sec = 30\nrequired = true\n"
        "[mcp_servers.gdcae_read.env]\nPYTHONDONTWRITEBYTECODE = '1'\n"
        + "PYTHONPATH = " + json.dumps(str(REPO / "src") + os.pathsep + str(source)) + "\n"
    )
    tomllib.loads(text)
    config.write_text(text, encoding="utf-8")
    # All overrides are invocation-local. Global config/auth are never rewritten.
    command = [os.environ["GDCAE_CODEX_EXE"], "exec", "--json",
               "-C", str(REPO), "-s", "read-only",
               "-c", 'approval_policy="never"',
               "-c", 'mcp_servers.node_repl.enabled=false',
               "-"]
    prompt = f"""M01-C authorized TEST_ONLY evidence review. You are this test's Codex Main.
Use the project skill gdcae-evidence-review (read its SKILL.md). Scope is read-only.
Explicit expected source: project {bound.project_id}, instance {bound.project_instance_id},
owner {bound.owner_id}. Use ONLY gdcae_read MCP for evidence; no direct files/database,
shell discovery, AF tools, solver or lifecycle. Shell may only read the Skill text.
Call all seven gdcae tools yourself at least once. Receipt key key-0 is authorized.
List Runs with limit=2 and continue its cursor, read events and validations/diagnostic.
Find unresolved or inconclusive evidence. Challenge the deliberately unsupported claim:
'These FINISHED Fake Runs prove the physical model and research goal are verified.'
Then actually delegate to configured native custom agent gdcae_independent_reviewer,
with evidence IDs and that claim; require independent MCP reads and structured return.
Wait for its completion and summarize the challenge back here. Do not simulate a reviewer.
Do not change files, invoke shell commands except reading the Skill, run Python or
start any owner. Use no other MCP server. If tools/custom agent unavailable say PARTIAL.
Final: brief facts, safe citations, unknowns and reviewer result. Explicitly state
SCIENTIFIC_VERIFICATION_AVAILABLE=false and AUTO_CONTINUE_ORIGINAL_DESKTOP_MAIN=NOT_TESTED.
"""
    try:
        with (root / "codex-main.jsonl").open("wb") as out, (root / "codex-main.stderr").open("wb") as err:
            process = subprocess.Popen(command, cwd=REPO, env=environment(source),
                                       stdin=subprocess.PIPE, stdout=out, stderr=err,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                process.communicate(prompt.encode("utf-8"), timeout=600)
            except subprocess.TimeoutExpired:
                # Exact Popen-owned CLI process only. This is never an AF lifecycle path.
                process.terminate()
                process.wait(timeout=15)
                raise RuntimeError("CODEX_REVIEW_TIMEOUT") from None
        items = []
        for line in (root / "codex-main.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                items.append(json.loads(line))
            except ValueError:
                raise RuntimeError("CODEX_STDOUT_NOT_JSONL") from None
        return {"exit_code": process.returncode, "events": items}
    finally:
        # Retain this ignored binding, disabled after the test; never auto-rebind.
        check(config.read_text(encoding="utf-8") == text, "LOCAL_CONFIG_CHANGED_EXTERNALLY")
        config.write_text(text.replace("[mcp_servers.gdcae_read]\n",
                                       "[mcp_servers.gdcae_read]\nenabled = false\n", 1),
                          encoding="utf-8")


def check_owned_config(config):
    if config.exists():
        # Only a deliberately selected, byte-identical prior M01-C local config
        # may be replaced. Never accept an arbitrary existing user's config.
        expected = os.environ.get("GDCAE_M01C_OWN_CONFIG_SHA256")
        check(expected is not None and hashlib.sha256(config.read_bytes()).hexdigest() == expected,
              "EXISTING_USER_PROJECT_CONFIG")


def cleanup(harness, connection, refs, root, evidence):
    errors = []
    try:
        if connection is not None and connection.exists():
            connection.unlink()
    except Exception:
        errors.append("CONNECTION_CLEANUP_FAILED")
    try:
        # Stop the exact owned process even if handoff removal failed.
        harness.close()
    except Exception:
        errors.append("HARNESS_CLEANUP_FAILED")
    exits = []
    for ref in refs:
        try:
            value = ref.exit_evidence()
            if value is None:
                errors.append("EXIT_UNCONFIRMED")
            else:
                exits.append(safe_exit(value))
        except Exception:
            errors.append("EXIT_OBSERVATION_FAILED")
        finally:
            try:
                ref.close()
            except Exception:
                errors.append("HANDLE_CLOSE_FAILED")
    try:
        lifecycle = json.loads((harness.root / "lifecycle.json").read_text())
        inventory = json.loads((harness.root / "inventory.json").read_text())
        evidence["forced_termination"] = any(row["terminated_by_owned_handle"] for row in lifecycle)
        evidence["credential_removed"] = inventory["credential_absent_from_remaining_files"]
        evidence["cleanup_verified"] = not errors and len(lifecycle) == 1 and all(
            row["exited"] and row["actual_process_handle_signaled"] for row in lifecycle)
    except Exception:
        errors.append("CLEANUP_RECORD_UNAVAILABLE")
        evidence["cleanup_verified"] = False
    evidence.update(exit_evidence=exits, cleanup_errors=errors)
    if errors:
        evidence["status"] = "PARTIAL"
    save(root / "evidence.json", evidence)


def test_real_stdio_codex_native_review():
    check(sys.platform == "win32" and sys.version_info[:2] == (3, 12), "HOST_UNSUPPORTED")
    source = Path(os.environ["GDCAE_AF_SOURCE"])
    check(source.is_absolute() and (source / "tests" / "supervisor_helpers.py").is_file(),
          "AUDITED_SOURCE_REQUIRED")
    check_owned_config(REPO / ".codex" / "config.toml")
    sys.path[:0] = [str(source), str(source / "tests")]
    from abqjobpilot.application_runtime import validate_runtime
    from abqjobpilot.execution.process_handles import ProcessReference
    from supervisor_helpers import ProcessHarness, read_json

    check(validate_runtime() == Path(sys.executable).resolve(), "INTERPRETER_MISMATCH")
    root = fresh_root()
    save(root / "prestart-manifest.json", {
        "stage": "M01-C", "mode": "TEST_ONLY fake-v1", "owner_start_budget": 1,
        "solver_budget": 0, "fake_submissions": 3, "wall_seconds": 720,
        "cleanup": "Exact ProcessHarness close; no PID/name kill; no unknown restart",
        "reads": "Official STDIO MCP, then real Codex CLI Main/custom reviewer",
        "prior_M01B_artifacts": "NOT_ACCESSED",
    })
    directory = root / "fixture"
    directory.mkdir()
    harness = ProcessHarness(directory, fake_jobs=3)
    check(harness.process_config is None, "PROCESS_BACKEND_FORBIDDEN")
    evidence = {"status": "RUNNING", "root_name": root.name, "fixture_submissions": 0}
    connection, refs = None, []
    started = time.monotonic()
    try:
        owner = harness.owner()  # Exactly once. Unknown startup is never retried.
        refs.append(ProcessReference(owner.identity["pid"], owner.identity))
        if owner.process.pid != owner.identity["pid"]:
            check(owner.identity["parent_pid"] == owner.process.pid, "PROCESS_CHAIN_MISMATCH")
            refs.append(ProcessReference(owner.process.pid))
        client = harness.client()
        health = client.health()
        fake_health(health)
        evidence.update(owner_pid=owner.identity["pid"], transport_pid=owner.process.pid,
                        owner_id=client.endpoint["owner_id"], backend=health["backend"],
                        execution_scope=health["execution_scope"])
        (directory / "private").mkdir()
        connection = directory / "private" / "connection.json"
        save(connection, {"endpoint": read_json(harness.endpoint_file), "credential": harness.credential})
        bound = binding(harness.context, client.endpoint["owner_id"])
        binding_file = root / "binding.json"
        save(binding_file, {"test_only": True, "binding": asdict(bound)})
        before = snapshot(harness.context)
        evidence["empty"] = asyncio.run(mcp_reads(root, source, binding_file,
                                                 "r_" + "f" * 32, True, harness.credential))
        evidence["empty_unchanged"] = before == snapshot(harness.context)
        check(evidence["empty_unchanged"], "EMPTY_BUSINESS_MUTATION")
        # This is the controlled fixture WRITE phase, never MCP/bridge behavior.
        receipts = []
        for request in harness.requests:
            receipt = client.submit(request)["receipt"]
            harness.finished(receipt["run_id"])
            receipts.append(receipt)
            evidence["fixture_submissions"] += 1
        before = snapshot(harness.context)
        check(before["slot"] is None and before["highest_event_sequence"] == 12, "NOT_QUIESCENT")
        evidence["seeded"] = asyncio.run(mcp_reads(root, source, binding_file,
                                                  receipts[-1]["run_id"], False, harness.credential))
        evidence["codex"] = codex_review(root, source, bound, binding_file)
        log_paths = [root / name for name in (
            "codex-main.jsonl", "codex-main.stderr", "empty.stderr", "seeded.stderr",
        )]
        evidence["logs_secret_free"] = all(
            harness.credential.encode() not in path.read_bytes() for path in log_paths)
        check(evidence["logs_secret_free"], "LOG_CREDENTIAL_DISCLOSURE")
        after = snapshot(harness.context)
        evidence.update(before=before, after=after, seeded_unchanged=before == after)
        check(before == after, "SEEDED_BUSINESS_MUTATION")
        check(evidence["codex"]["exit_code"] == 0, "CODEX_PROCESS_FAILED")
        evidence["status"] = "READS_COMPLETE_REVIEW_TRANSCRIPT_PENDING_AUDIT"
    except Exception as exc:
        evidence.update(status="PARTIAL", failure_type=type(exc).__name__)
        if isinstance(exc, RuntimeError) and str(exc).replace("_", "").isalnum():
            evidence["failure_label"] = str(exc)
        raise RuntimeError("M01C_LIVE_FAILURE_SEE_SANITIZED_EVIDENCE") from None
    finally:
        evidence["elapsed_seconds"] = round(time.monotonic() - started, 3)
        cleanup(harness, connection, refs, root, evidence)
        print(json.dumps({key: evidence.get(key) for key in (
            "status", "root_name", "cleanup_verified", "forced_termination", "elapsed_seconds",
        )}))
    check(evidence["cleanup_verified"] and all(row["exit_code"] == 0 for row in
                                               evidence["exit_evidence"]), "EXIT_UNCONFIRMED")
