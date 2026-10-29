"""Separate fixed-project proposal-only STDIO MCP. No admission or execution API."""

import asyncio
import json
import logging
import sys
from typing import Annotated

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from aegiscae.research.proposal_ingress import ProposalIngress


class _Empty(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class _Record(_Empty):
    proposal_key: Annotated[str, Field(pattern=r"^proposalkey_[0-9a-f]{32}$", max_length=44)]
    proposal_json: Annotated[str, Field(min_length=1, max_length=8192)]


_SCHEMAS = {
    "gdcae_record_candidate_proposal": (_Record, "Record one untrusted proposal for the bound challenge. "
        "Never admits, approves, reserves budget, changes Candidate files or starts execution."),
    "gdcae_get_proposal_status": (_Empty, "Read bound challenge, sanitized Brief, original receipt and historical "
        "gate decisions. No side effects. Positive review is not an execution grant."),
}
_SAFE_ERRORS = {"STORE_BUSY", "REVISION_CONFLICT", "CHALLENGE_EXPIRED", "CHALLENGE_REVOKED",
                "PROPOSAL_KEY_MISMATCH", "PROPOSAL_CONTENT_CONFLICT", "PROPOSAL_BINDING_MISMATCH"}


class ProposalTools:
    def __init__(self, ingress):
        if type(ingress) is not ProposalIngress:
            raise ValueError("BOUND_INGRESS_REQUIRED")
        self._ingress = ingress

    async def list_tools(self, context, params):
        return ListToolsResult(tools=[Tool(name=name, description=description,
            inputSchema=model.model_json_schema(), annotations=ToolAnnotations(
                readOnlyHint=name == "gdcae_get_proposal_status", destructiveHint=False,
                idempotentHint=True, openWorldHint=False))
            for name, (model, description) in _SCHEMAS.items()])

    async def call_tool(self, context, params):
        try:
            if params.name not in _SCHEMAS:
                return _response({"error": "UNKNOWN_TOOL", "execution_authorized": False})
            args = _SCHEMAS[params.name][0].model_validate(params.arguments or {})
            if params.name == "gdcae_record_candidate_proposal":
                data = self._ingress.record(args.proposal_key, args.proposal_json)
            else:
                data = self._ingress.status()
            return _response({"error": None, "data": data, "execution_authorized": False})
        except Exception as exc:
            # Never echo raw model strings, paths, SQL, exception messages or logs.
            code = vars(exc).get("code")
            return _response({"error": code if code in _SAFE_ERRORS else "REQUEST_UNAVAILABLE",
                              "execution_authorized": False})


def _response(payload):
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > 24576:
        payload = {"error": "RESPONSE_LIMIT", "execution_authorized": False}
        encoded = json.dumps(payload)
    return CallToolResult(content=[TextContent(type="text", text=encoded)],
                          structuredContent=payload, isError=payload["error"] is not None)


def create_server(ingress):
    handlers = ProposalTools(ingress)
    server = Server("gdcae-proposal-only", version="m03d-v1", on_list_tools=handlers.list_tools,
        on_call_tool=handlers.call_tool, instructions="Untrusted TEST_SYNTHETIC proposals only. "
        "A ProposalReceipt is not admission, human approval, AF Grant or execution. No auto continuation.")
    server.middleware = []
    return server


async def serve(server):
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


def main():
    logging.disable(logging.CRITICAL)
    try:
        if len(sys.argv) != 3 or sys.argv[1] != "--binding-file":
            raise ValueError("EXPLICIT_BINDING_REQUIRED")
        server = create_server(ProposalIngress.from_startup_file(sys.argv[2]))
        asyncio.run(serve(server))
        return 0
    except Exception:
        print("GDCAE_PROPOSAL_MCP_UNAVAILABLE", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
