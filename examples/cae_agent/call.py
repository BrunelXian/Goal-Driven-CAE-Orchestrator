"""One MCP tools/call for an operator-bound service. Arguments come from a UTF-8 file or stdin."""

import argparse
import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVICE = "aegiscae.interfaces.mcp_research"


def stdio_connect(binding, pin, *, source=None):
    """The operator chooses the executable environment and binding outside MCP."""
    @asynccontextmanager
    async def connect():
        env = {"GDCAE_BINDING_SHA256": pin}
        if source is not None:
            env["PYTHONPATH"] = str(source)
        server = StdioServerParameters(command=sys.executable,
            args=["-B", "-m", SERVICE, "--binding-file", str(binding)], env=env)
        async with stdio_client(server) as streams:
            async with ClientSession(*streams, read_timeout_seconds=30) as session:
                initialized = await session.initialize()
                available = {item.name for item in (await session.list_tools()).tools}

                async def call(tool, args):
                    if tool not in available:
                        raise ValueError("Tool is unavailable in the connected server")
                    result = await session.call_tool(tool, args)
                    if not isinstance(result.structured_content, dict):
                        raise ValueError("Structured response required")
                    return result.structured_content

                call.discovery = {"protocol": initialized.protocol_version, "service": initialized.server_info.name,
                                  "version": initialized.server_info.version, "tools": sorted(available)}
                yield call
    return connect


async def one_call(connect, name, arguments):
    async with connect() as call:
        return await call(name, arguments)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--args-file", help="UTF-8 JSON object; default is stdin", type=Path)
    parser.add_argument("--binding-file", required=True, type=Path)
    parser.add_argument("--source", type=Path, help="Source root in a development deployment")
    options = parser.parse_args()
    pin = os.environ.get("GDCAE_BINDING_SHA256")
    if not pin:
        parser.error("set GDCAE_BINDING_SHA256 to the independently provided operator pin")
    data = options.args_file.read_text(encoding="utf-8-sig") if options.args_file else sys.stdin.read()
    args = json.loads(data)
    if not isinstance(args, dict):
        parser.error("arguments must be one JSON object")
    connect = stdio_connect(options.binding_file.resolve(), pin,
                            source=options.source.resolve() if options.source else None)
    result = asyncio.run(one_call(connect, options.tool, args))
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 1 if result.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())
