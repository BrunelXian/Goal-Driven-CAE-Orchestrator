"""In-process D3 pytest wrapper; P1 output projection and no child launch.

The audit hook is a regression guard, not an OS security sandbox. Selection must
still exclude live/native/install tests. No historical report is read.
"""

import contextlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

import m03f1_safe_replay as safe


@contextlib.contextmanager
def private_streams(path):
    """Flush even exceptional exits before restoring the caller's descriptors."""
    saved = (os.dup(1), os.dup(2))
    try:
        with path.open("x", encoding="utf-8") as output:
            sys.stdout.flush()
            sys.stderr.flush()
            os.dup2(output.fileno(), 1)
            os.dup2(output.fileno(), 2)
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                yield
    finally:
        try:
            sys.__stdout__.flush()
            sys.__stderr__.flush()
        except BaseException:
            # Do not restore public FDs while an original stream may hold bytes.
            os.close(saved[0])
            os.close(saved[1])
            raise safe.ProjectionBlocked() from None
        os.dup2(saved[0], 1)
        os.dup2(saved[1], 2)
        os.close(saved[0])
        os.close(saved[1])


def main():
    root = Path(os.environ["LOCALAPPDATA"]) / "GDCAE-G3-D3-OFFLINE-20261030-A01"
    label = sys.argv[1]
    safe.need(label.isascii() and label.replace("-", "").isalnum())
    result_root = root / "gdcae-m03f1p1-g2long-d3"
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
            raise PermissionError("D3_NATIVE_OR_NETWORK_DENIED")

    sys.addaudithook(audit)
    import pytest

    started = time.monotonic()
    targets = sys.argv[2:]
    if targets == ["--reviewed-pure-selection"]:
        targets = json.loads((root / "evidence/pure-selection.json").read_text(encoding="utf-8"))["args"]
    private_output = result_root / (label + ".private.log")
    with private_streams(private_output):
        code = int(pytest.main([*targets, "-q", "-p", "no:cacheprovider",
                               "-p", "m03f1_safe_replay", "--basetemp",
                               str(result_root / (label + "-temp"))]))
    # FD-level capture also contains os.write and sys.__stdout__ output. Enforce
    # a projection size limit without ever reading or displaying an overflow.
    output_size = private_output.stat().st_size
    safe.need(output_size <= safe.MAX_OUTPUT)
    projection = safe.project_counts(safe.decode_record(counters.read_bytes()), code,
                                     safe.source_allowlist())
    result = {"schema": "g3-d3-offline-check-v1", "label": label, "exit_code": code,
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
