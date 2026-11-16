"""Protocol refusal tests. The live stdio acceptance is engineering_intake.py."""
import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace as NS

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[2] / "product/research-preview/tools"
sys.path.insert(0, str(TOOLS_DIR))
import abqjobpilot_readonly as adapter


class Peer:
    def __init__(self):
        self.protocol_version = "2025-11-25"
        self.server_info = NS(name="AbqJobPilot", version="0.2.2")
        self.listing = NS(next_cursor=None, tools=[
            NS(name=n, annotations=NS(read_only_hint=True, destructive_hint=False),
               input_schema={"type":"object","properties":{"scope":{}, "identifier":{}, "limit":{}}})
            for n in sorted(adapter.TOOLS)])
        self.calls = []
        self.status = "RUNNING"
        self.bound_id = "expected"
        self.status_id = "q"

    async def list_tools(self):
        return self.listing

    async def call_tool(self, name, args):
        self.calls.append(name)
        scope = args["scope"]
        if name == "abq_list_jobs":
            status, data = "OK", {"scope":scope, "limit":50, "jobs":[]}
        else:
            status = "STATUS_UNCONFIRMED" if self.status == "RUNNING" else self.status
            data = {"scope":scope,"queue_id":self.status_id,"active_execution_confirmed":False,
                    "observed_status":self.status,"last_log_lines":["example-private-content"]}
        return NS(is_error=False, structured_content={"schema_version":"1.0","project_id":self.bound_id,
                  "errors":[],"error_details":[],"status":status,"data":data})


@pytest.mark.parametrize("case,code", [
    ("server","MCP_SERVER_INCOMPATIBLE"), ("version","MCP_SERVER_INCOMPATIBLE"),
    ("protocol","MCP_SERVER_INCOMPATIBLE"), ("extra-tool","MCP_TOOLSET_INCOMPATIBLE"),
    ("destructive","MCP_TOOLSET_INCOMPATIBLE"), ("schema","MCP_INPUT_SCHEMA_INCOMPATIBLE"),
    ("project","BACKEND_PROJECT_MISMATCH"), ("identifier","INVALID_JOB_STATUS"),
    ("absent","JOB_STATUS_UNVERIFIED"), ("running",None),
])
def test_refusal_or_unconfirmed(case, code, monkeypatch):
    # Main and dual-Project gates are separately tested over the live transport.
    monkeypatch.setattr(adapter, "check_task", lambda *args: None)
    peer = Peer()
    if case == "server": peer.server_info.name = "other"
    if case == "version": peer.server_info.version = "9.0"
    if case == "protocol": peer.protocol_version = "unknown"
    if case == "extra-tool": peer.listing.tools.append(NS(name="write"))
    if case == "destructive": peer.listing.tools[0].annotations.destructive_hint = True
    if case == "schema":
        next(t for t in peer.listing.tools if t.name == "abq_job_status").input_schema["required"] = ["other"]
    if case == "project": peer.bound_id = "different"
    if case == "identifier": peer.status_id = "different"
    if case == "absent": peer.status = "UNKNOWN"
    call = adapter.observe(peer, NS(research_project_id="research"), "host", "desktop", "expected", queue_id="q")
    if code:
        with pytest.raises(ValueError, match=code):
            asyncio.run(call)
    else:
        result = asyncio.run(call)
        assert result["queue_status"]["status"] == "STATUS_UNCONFIRMED"
        assert not result["queue_status"]["active_execution_confirmed"]
        assert "example-private-content" not in str(result)
    assert set(peer.calls) <= {"abq_list_jobs", "abq_job_status"}
    if code and code.startswith("MCP_"):
        assert not peer.calls
