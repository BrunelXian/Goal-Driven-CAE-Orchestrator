"""Drive only installed local plugin tools using a disposable Desktop-bundled app-server."""
import hashlib
import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path

import psutil

NAME = "cae-agent-scoped-fixture"
ID = NAME + "@gdcae-fixture-lab"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class InstalledHost:
    """A new ephemeral read-only Host thread, with no account copying or model turn."""

    def __init__(self, codex, home, market):
        self.codex, self.home, self.market = map(Path, (codex, home, market))
        self.calls = []
        self.messages = queue.Queue()
        self.seq = 0
        self.host = None
        self.exit_code = None
        self.cleanup = None

    def _drain(self):
        for line in self.host.stdout:
            self.messages.put(json.loads(line))
        self.messages.put(None)

    def send(self, message):
        self.host.stdin.write(json.dumps(message) + "\n")
        self.host.stdin.flush()

    def rpc(self, method, params):
        self.seq += 1
        self.send({"id": self.seq, "method": method, "params": params})
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            obj = self.messages.get(timeout=max(0, deadline - time.monotonic()))
            if obj is None:
                raise RuntimeError("HOST_EXITED")
            if "method" in obj and obj.get("id") is not None:
                raise RuntimeError("HOST_REQUIRES_INTERACTION: " + obj["method"])
            if obj.get("id") == self.seq and "method" not in obj:
                if "error" in obj:
                    raise RuntimeError(obj["error"].get("message", "HOST_RPC_FAILURE"))
                return obj["result"]
        raise TimeoutError(method)

    def __enter__(self):
        env = dict(os.environ, CODEX_HOME=str(self.home))
        if not self.codex.is_absolute() or not self.home.is_dir():
            raise ValueError("EXPLICIT_DISPOSABLE_HOST_REQUIRED")
        self.host = subprocess.Popen([str(self.codex), "app-server", "--stdio"], cwd=self.market,
                                     env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        self.reader = threading.Thread(target=self._drain, daemon=True)
        self.reader.start()
        try:
            init = self.rpc("initialize", {"clientInfo": {"name": "gdcae-local-uat", "version": "1"},
                                            "capabilities": {"experimentalApi": True}})
            self.host_version = init.get("userAgent", "").split(" (")[0]
            self.send({"method": "initialized", "params": {}})
            detail = self.rpc("plugin/read", {"pluginName": NAME, "marketplacePath":
                              str(self.market / ".agents/plugins/marketplace.json")})["plugin"]
            self.plugin = {k: detail["summary"][k] for k in ("installed", "enabled")}
            self.plugin.update(mcpServers=sorted(detail["mcpServers"]), apps=len(detail.get("apps", [])))
            if not self.plugin["installed"] or not self.plugin["enabled"]:
                raise RuntimeError("PLUGIN_NOT_INSTALLED_AND_ENABLED")
            self.thread = self.rpc("thread/start", {"ephemeral": True, "cwd": str(self.market),
                                   "sandbox": "read-only"})["thread"]["id"]
            deadline = time.monotonic() + 45
            while True:
                rows = self.rpc("mcpServerStatus/list", {"threadId": self.thread, "limit": 100})["data"]
                self.servers = {r["name"]: {"tools": sorted(r["tools"]), "status": r["runtimeStatus"],
                                "info": r.get("serverInfo"), "http_origin": r.get("httpOrigin")}
                                for r in rows if r.get("pluginId") == ID}
                if set(self.servers) == {"gdcae-core", "abqjobpilot"} and all(
                        r["status"] == "connected" for r in self.servers.values()):
                    return self
                if time.monotonic() >= deadline:
                    raise RuntimeError("INSTALLED_SERVICES_NOT_CONNECTED: " + str(self.servers))
                time.sleep(0.5)
        except BaseException:
            self.close()
            raise

    def call(self, name, args):
        servers = [server for server, row in self.servers.items() if name in row["tools"]]
        if len(servers) != 1:
            raise ValueError("TOOL_NOT_ADVERTISED")
        raw = self.rpc("mcpServer/tool/call", {"threadId": self.thread, "server": servers[0],
                       "tool": name, "arguments": args})
        body = raw.get("structuredContent")
        if body is None:
            body = json.loads(raw["content"][0]["text"])
        self.calls.append({"server": servers[0], "tool": name, "request_sha256": digest(args),
                           "response_sha256": digest(body), "is_error": raw.get("isError", False)})
        return body

    def close(self):
        if self.host is None:
            return
        children = psutil.Process(self.host.pid).children(recursive=True) if self.host.poll() is None else []
        forced = False
        self.host.stdin.close()
        try:
            self.exit_code = self.host.wait(timeout=20)
        except subprocess.TimeoutExpired:
            forced = True
            self.host.terminate()
            self.exit_code = self.host.wait(timeout=10)
        self.reader.join(timeout=2)
        self.host.stdout.close()
        self.host = None
        _, alive = psutil.wait_procs(children, timeout=5)
        if alive:
            forced = True
            for process in alive:
                try:
                    process.terminate()
                except psutil.NoSuchProcess:
                    pass
            _, alive = psutil.wait_procs(alive, timeout=5)
        self.cleanup = {"observed_descendants": len(children), "surviving_descendants": len(alive),
                        "forced": forced}

    def __exit__(self, *exc):
        self.close()
