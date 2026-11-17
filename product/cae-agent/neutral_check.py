"""Open the provisioned local service from a standard MCP client without a host adapter."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def probe(profile):
    cfg = json.loads(profile.read_bytes())
    command = StdioServerParameters(command=cfg["python"], args=[
        "-I", "-B", str(Path(cfg["service_root"]) / "serve.py"), "gdcae-core", "--profile", str(profile)])
    async with stdio_client(command) as streams:
        async with ClientSession(*streams, read_timeout_seconds=30) as client:
            handshake = await client.initialize()
            tools = sorted(tool.name for tool in (await client.list_tools()).tools)
            binding = json.loads(Path(cfg["binding"]).read_bytes())
            args = {"project_id": binding["project_id"]}
            outputs = {}
            for tool in ("gdcae_project_open", "gdcae_diagnostics", "gdcae_workflow_status"):
                result = await client.call_tool(tool, {} if tool == "gdcae_project_open" else args)
                if result.is_error or result.structured_content["error"]:
                    raise ValueError("CORE_READBACK_FAILED")
                outputs[tool] = result.structured_content["data"]
            status = outputs["gdcae_workflow_status"]
            encoded = json.dumps(status, sort_keys=True, separators=(",", ":")).encode()
            return {"client": "MCP SDK stdio", "protocol": handshake.protocol_version, "version": handshake.server_info.version,
                    "tools": tools, "completed_tool_calls": 3, "state": status["state"],
                    "revision": status["revision"], "runs_used": status["runs_used"],
                    "workflow_sha256": hashlib.sha256(encoded).hexdigest(), "adapter_loaded": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh receipt path")
    report = asyncio.run(probe(args.profile))
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    print(json.dumps(report))
