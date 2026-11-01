"""In-process D6 pytest wrapper; P1 output projection and no child launch.

The audit hook is a regression guard, not an OS security sandbox. Selection must
still exclude live/native/install tests. No historical report is read.
"""

import json
import os
from pathlib import Path
import sys
import tempfile
import time

import m03f1_safe_replay as safe


from g3_d3_offline_checks import private_streams


def main():
    root = Path(os.environ["LOCALAPPDATA"]) / "GDCAE-G3-D3-OFFLINE-20261030-A01" / "D6-20261031-A01"
    label = sys.argv[1]
    safe.need(label.isascii() and label.replace("-", "").isalnum())
    result_root = root / "gdcae-m03f1p1-g2long-d6"
    result_root.mkdir(exist_ok=True)
    counters = result_root / (label + ".counters.json")
    safe.need(not counters.exists())
    environment = safe._environment(counters)
    os.environ.clear()
    os.environ.update(environment)
    os.environ["TEMP"] = os.environ["TMP"] = str(result_root)
    tempfile.tempdir = str(result_root)
    for key in ("GDCAE_G1_AF_SOURCE", "GDCAE_G2_AF_SOURCE", "GDCAE_G3_AF_SOURCE"):
        os.environ[key] = "D:/Projects/abqjobpilot_dev"
    sys.path[:0] = [str(safe.REPO / "src"), str(safe.REPO / "tests/unit")]
    if label.startswith("af-"):
        sys.path[:0] = ["D:/Projects/abqjobpilot_dev", "D:/Projects/abqjobpilot_dev/tests"]
    denied = []

    def audit(event, _args):
        if event in {"subprocess.Popen", "os.system", "os.exec", "os.spawn",
                     "os.startfile", "os.startfile/2", "socket.connect", "socket.bind"}:
            denied.append(event)
            raise PermissionError("D6_NATIVE_OR_NETWORK_DENIED")

    sys.addaudithook(audit)
    import pytest

    class Inventory:
        def pytest_collection_finish(self, session):
            # Exact current-run node IDs are private, never tool-output diagnostics.
            path = result_root / (label + ".collection.private.json")
            with path.open("x", encoding="utf-8") as stream:
                json.dump([item.nodeid for item in session.items], stream)

    started = time.monotonic()
    targets = sys.argv[2:]
    if targets == ["--reviewed-pure-selection"]:
        targets = json.loads((root / "evidence/pure-selection.json").read_text(encoding="utf-8"))["args"]
    private_output = result_root / (label + ".private.log")
    with private_streams(private_output):
        code = int(pytest.main([*targets, "-q", "-p", "no:cacheprovider",
                               "-p", "m03f1_safe_replay", "--basetemp",
                               str(result_root / (label + "-temp"))], plugins=[Inventory()]))
    # FD-level capture also contains os.write and sys.__stdout__ output. Enforce
    # a projection size limit without ever reading or displaying an overflow.
    output_size = private_output.stat().st_size
    safe.need(output_size <= safe.MAX_OUTPUT)
    projection = safe.project_counts(safe.decode_record(counters.read_bytes()), code,
                                     safe.source_allowlist())
    result = {"schema": "g3-d6-offline-check-v1", "label": label, "exit_code": code,
              "status": "PASS" if code == 0 and not denied else "FAIL",
              "elapsed_seconds": round(time.monotonic() - started, 2),
              "denied_native_or_network_attempts": len(denied),
              "suppressed_output_bytes": output_size, "boundary_digest": safe.boundary_digest(),
              **projection}
    (result_root / (label + ".safe.json")).write_text(json.dumps(result), encoding="utf-8")
    print(json.dumps(result))
    return code if code else int(bool(denied))


if __name__ == "__main__":
    try:
        result_code = main()
    except BaseException:
        print('{"status":"BLOCKED_PRIVACY_PROJECTION"}')
        result_code = 2
    sys.exit(result_code)
