"""Real STDIO SDK lifecycle; not labeled a Codex model call."""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from aegiscae.contracts.research_contracts import canonical_json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
from test_candidate_proposal import proposal  # noqa: E402
from m03d_support import prepare_ingress  # noqa: E402


def test_dp03_real_stdio_record_status_close(tmp_path):
    root = tmp_path / "stdio"
    case = prepare_ingress(root)
    async def scenario():
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src"),
               "PYTHONDONTWRITEBYTECODE": "1"}
        params = StdioServerParameters(command=sys.executable, args=["-B", "-m",
            "aegiscae.interfaces.mcp_proposal", "--binding-file", str(root / "proposal-startup.json")], env=env)
        with (root / "mcp-stderr.txt").open("w") as errors:
            async with stdio_client(params, errlog=errors) as (reader, writer):
                async with ClientSession(reader, writer, read_timeout_seconds=15) as session:
                    await session.initialize()
                    listing = await session.list_tools()
                    assert len(listing.tools) == 2
                    initial = (await session.call_tool("gdcae_get_proposal_status", {})).structured_content
                    key = initial["data"]["proposal_key"]
                    assert initial["data"]["receipt"] is None
                    args = {"proposal_key": key, "proposal_json": canonical_json(proposal(case)).decode()}
                    first = (await session.call_tool("gdcae_record_candidate_proposal", args)).structured_content
                    second = (await session.call_tool("gdcae_record_candidate_proposal", args)).structured_content
                    assert first == second and first["data"]["status"] == "RECORDED_PENDING_GATE"
                    status = (await session.call_tool("gdcae_get_proposal_status", {})).structured_content
                    assert status["data"]["receipt"] == first["data"] and status["data"]["decisions"] is None
        assert (root / "mcp-stderr.txt").read_text() == ""
    asyncio.run(scenario())
    assert case.port.oracle()["effects"] == 1


def test_dp15_raw_stdio_stdout_is_protocol_and_process_exits(tmp_path):
    root = tmp_path / "wire"
    prepare_ingress(root)
    wire = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "dp-test", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")}
    result = subprocess.run([sys.executable, "-B", "-m", "aegiscae.interfaces.mcp_proposal",
        "--binding-file", str(root / "proposal-startup.json")], input="\n".join(map(json.dumps, wire)) + "\n",
        capture_output=True, text=True, timeout=20, env=env)
    assert result.returncode == 0 and result.stderr == ""
    assert result.stdout.strip()
    assert all(json.loads(line)["jsonrpc"] == "2.0" for line in result.stdout.splitlines())
