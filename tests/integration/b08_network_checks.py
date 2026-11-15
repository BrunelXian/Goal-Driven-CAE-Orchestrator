"""Run Windows PowerShell network classification on real loopback HTTP and typed .NET faults."""
import argparse
import http.server
import json
from pathlib import Path
import subprocess
import threading


class Responses(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        case = self.path.lstrip("/")
        self.send_response(int(case) if case.isdigit() else 200)
        if case == "403":
            self.send_header("X-RateLimit-Remaining", "0")
        self.end_headers()
        body = {"ok": b'{"schema":1}', "bad-json": b"{", "bad-utf8": b'{"x":"\xff"}',
                "oversize": b" " * 65537}.get(case, b"")
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("driver", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Responses) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        fixture = Path(__file__).with_name("b08_network_fixture.ps1")
        result = subprocess.run(["powershell.exe", "-NoProfile", "-File", str(fixture),
                                 str(args.driver.resolve()), f"http://127.0.0.1:{server.server_port}"],
                                capture_output=True, check=False, timeout=45)
        server.shutdown()
    if result.returncode:
        raise SystemExit(result.stderr.decode(errors="replace"))
    report = json.loads(result.stdout)
    args.out.write_text(json.dumps(report, indent=2))
    print(f"{len(report)} classified failures, plus valid JSON")
