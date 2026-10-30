"""G1 runner reusing the accepted P1 output boundary, with current baseline metadata."""

import argparse
import json
from pathlib import Path
import re
import tempfile
import time

import m03f1_safe_replay as safe

HEAD = "184245cc8a67859484406d70fb1e2d1cf2e347c7"


def check_baseline(repo, branch, expected, environment):
    """Project only exact approved metadata, never raw unexpected Git output."""
    observed = []
    for arguments in (["rev-parse", "HEAD"], ["branch", "--show-current"]):
        capture = safe._capture(["git", *arguments], cwd=repo, env=environment, timeout=10)
        safe.need(capture["exit_code"] == 0 and not any(capture[key] for key in
                  ("overflow", "timeout", "drain_failed", "cleanup_unknown")))
        observed.append(capture["raw"].strip())
    safe.need(observed == [expected.encode("ascii"), branch.encode("ascii")])
    return observed[0].decode("ascii")


def run(root, mode, label, targets, af_source=None):
    root = Path(root)
    safe.need(root.is_absolute() and root.is_dir()
              and root.name.startswith("gdcae-m03f1p1-") and not root.is_symlink())
    safe.need(re.fullmatch(r"[a-z0-9-]{1,50}", label) is not None)
    environment = safe._environment(root / (label + ".counters.json"))
    actual_head = check_baseline(safe.REPO, "main", HEAD, environment)
    allowed = safe.source_allowlist()
    safe.need(all(t in allowed for t in targets))
    gate = root / "privacy.safe.json"
    if mode != "privacy":
        previous = safe.decode_record(gate.read_bytes())
        safe.need(previous.get("status") == "PASS" and previous.get("head") == HEAD
                  and previous.get("boundary_digest") == safe.boundary_digest())
    counters = root / (label + ".counters.json")
    safe.need(not counters.exists() and not (root / (label + ".safe.json")).exists())
    if mode in {"privacy", "pytest"}:
        if mode == "privacy":
            targets = [safe.PRIVACY_TEST]
        command = [str(safe.PYTHON), "-B", "-m", "pytest", *targets, "-q",
                   "-p", "no:cacheprovider", "-p", "m03f1_safe_replay",
                   "--basetemp", str(root / (label + "-temp"))]
    elif mode == "ruff":
        command = [str(safe.RUFF), "check", "--no-cache", "."]
    else:
        command = ["git", "diff", "--check"]
    start = time.monotonic()
    if af_source is not None:
        safe.need(af_source.is_absolute() and af_source.is_dir()
                  and not af_source.is_symlink() and not af_source.is_junction())
        check_baseline(af_source, "Develop", "7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88",
                       environment)
        environment["GDCAE_G1_AF_SOURCE"] = str(af_source)
    capture = safe._capture(command, cwd=safe.REPO, env=environment,
                            timeout=5400)
    safe.need(not any(capture[key] for key in
                      ("overflow", "timeout", "drain_failed", "cleanup_unknown")))
    safe.need(check_baseline(safe.REPO, "main", HEAD, environment) == actual_head)
    if af_source is not None:
        check_baseline(af_source, "Develop", "7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88",
                       environment)
    projection = {"counts": None, "diagnostics": []}
    if mode in {"privacy", "pytest"}:
        projection = safe.project_counts(safe.decode_record(counters.read_bytes()),
                                         capture["exit_code"], allowed)
    result = {"schema": "gdcae-g1-safe-check-v1", "mode": mode,
              "head": actual_head, "boundary_digest": safe.boundary_digest(),
              "status": "PASS" if capture["exit_code"] == 0 else "FAIL",
              "exit_code": capture["exit_code"],
              "elapsed_seconds": round(time.monotonic() - start, 2), **projection}
    with (root / (label + ".safe.json")).open("x", encoding="utf-8") as stream:
        json.dump(result, stream)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("privacy", "pytest", "ruff", "diff"))
    parser.add_argument("--root", type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--af-source", type=Path)
    args = parser.parse_args()
    root = args.root or Path(tempfile.mkdtemp(prefix="gdcae-m03f1p1-g1-"))
    try:
        result = run(root, args.mode, args.label, args.target, args.af_source)
        print(json.dumps(result, sort_keys=True))
        return result["exit_code"]
    except (ValueError, OSError, KeyError):
        print('{"status":"BLOCKED","code":"G1_SAFE_PROJECTION_BLOCKED"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
