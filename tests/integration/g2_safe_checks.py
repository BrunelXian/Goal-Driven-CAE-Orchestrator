"""G2 node inventory and regression capture using the unchanged P1 boundary."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import time

import g1_safe_checks as baseline
import m03f1_safe_replay as safe

SENSITIVE = re.compile(
    r"(?i)(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    r"|codex:\/\/threads/|\bsk-[a-z0-9_-]{24,}|\bBearer\s+[a-z0-9._-]{24,})"
)
SKIP_REASONS = {
    "Explicit M01-B approval, fresh TEMP root and isolated invocation required": "M01B_LIVE_OPTIN_DISABLED",
    "M01-C fresh TEST root and explicit live opt-in required": "M01C_LIVE_OPTIN_DISABLED",
    "M03-B fresh TEST root and explicit live opt-in required": "M03B_LIVE_OPTIN_DISABLED",
    "G2 public AF source not explicitly selected; no live process requested": "G2_AF_SOURCE_UNSET",
    "Explicit offline AF source not selected": "G1_AF_SOURCE_UNSET",
}
_SKIPS = []


def project_skip(node, reason, allowed):
    identity = validate_nodes([node], allowed)[0].split("[", 1)[0]
    code = SKIP_REASONS.get(reason.removeprefix("Skipped: "), "UNCLASSIFIED_SKIP")
    return {"test_ref": identity, "reason_code": code}


def pytest_runtest_logreport(report):
    if os.environ.get("GDCAE_G2_NODE_RECORD") and report.skipped:
        reason = report.longrepr[2] if isinstance(report.longrepr, tuple) else ""
        _SKIPS.append(project_skip(report.nodeid, reason, safe.source_allowlist()))


def pytest_sessionfinish(session, exitstatus):
    configured = os.environ.get("GDCAE_G2_NODE_RECORD")
    if configured:
        path = Path(configured).with_suffix(".skips.json")
        safe.need(path.is_absolute() and path.parent.name.startswith("gdcae-m03f1p1-g2long-")
                  and not path.parent.is_symlink() and not path.parent.is_junction()
                  and not path.exists())
        with path.open("x", encoding="utf-8") as stream:
            json.dump({"schema": "g2-skips-v1", "skips": _SKIPS}, stream)


def validate_nodes(nodes, allowed):
    """Project collection identities without ever retaining parametrization text.

    Ordinals preserve distinct cases within each AST-allowlisted test function.
    This is a safe collection inventory, not reusable pytest selection syntax.
    """
    safe.need(isinstance(nodes, list) and 0 < len(nodes) < 20000)
    safe.need(all(isinstance(node, str) for node in nodes))
    safe.need(len(nodes) == len(set(nodes)))
    projected = []
    ordinals = {}
    for node in nodes:
        safe.need(len(node) <= 16384)
        safe.need(all(ord(c) >= 32 for c in node) and not SENSITIVE.search(node))
        parts = node.split("[", 1)[0].split("::")
        safe.need(len(parts) == 2 and parts[0] in allowed
                  and parts[1] in allowed[parts[0]])
        base = "::".join(parts)
        safe.need(re.fullmatch(r"tests/[a-zA-Z0-9_/]+\.py::test_[a-zA-Z0-9_]+", base))
        ordinal = ordinals.get(base, 0) + 1
        ordinals[base] = ordinal
        projected.append(f"{base}[case_{ordinal:05d}]")
    return projected


def encode_inventory(nodes, allowed):
    projected = validate_nodes(nodes, allowed)
    records = [{"schema": "g2-node-inventory-v2"}, *({"node": node} for node in projected)]
    return b"\n".join(json.dumps(record).encode("utf-8") for record in records) + b"\n"


def decode_inventory(body, allowed):
    # Each JSONL record uses the unchanged P1 decoder's 64 KiB ceiling.
    safe.need(type(body) is bytes and len(body) <= 12 * 1024 * 1024)
    lines = body.splitlines()
    safe.need(1 < len(lines) <= 20000)
    safe.need(safe.decode_record(lines[0]) == {"schema": "g2-node-inventory-v2"})
    nodes = []
    for line in lines[1:]:
        record = safe.decode_record(line)
        safe.need(type(record) is dict and set(record) == {"node"})
        nodes.append(record["node"])
    safe.need(validate_nodes(nodes, allowed) == nodes)
    return nodes


def pytest_collection_finish(session):
    """Explicit opt-in writes only validated node identities, never test output."""
    configured = os.environ.get("GDCAE_G2_NODE_RECORD")
    if configured is None:
        return
    path = Path(configured)
    safe.need(path.is_absolute() and path.parent.name.startswith("gdcae-m03f1p1-g2long-"))
    safe.need(not path.exists() and not path.parent.is_symlink()
              and not path.parent.is_junction())
    nodes = validate_nodes([item.nodeid for item in session.items], safe.source_allowlist())
    with path.open("xb") as output:
        output.write(encode_inventory(nodes, safe.source_allowlist()))


def run(root, label, targets, *, collect_only=False, af_source=None):
    safe.need(root.is_absolute() and root.is_dir()
              and root.name.startswith("gdcae-m03f1p1-g2long-"))
    safe.need(not root.is_symlink() and not root.is_junction())
    safe.need(re.fullmatch(r"[a-z0-9-]{1,50}", label) is not None)
    allowed = safe.source_allowlist()
    safe.need(all(target in allowed for target in targets))
    counters = root / (label + ".counters.json")
    nodes_file = root / (label + ".nodes.jsonl")
    result_file = root / (label + ".safe.json")
    safe.need(not any(path.exists() for path in (counters, nodes_file, result_file)))
    gate = safe.decode_record((root / "privacy.safe.json").read_bytes())
    safe.need(gate["status"] == "PASS" and gate["head"] == baseline.HEAD
              and gate["boundary_digest"] == safe.boundary_digest())
    environment = safe._environment(counters)
    environment["GDCAE_G2_NODE_RECORD"] = str(nodes_file)
    head = baseline.check_baseline(safe.REPO, "main", baseline.HEAD, environment)
    if af_source is not None:
        safe.need(af_source.is_absolute() and af_source.is_dir()
                  and not af_source.is_symlink() and not af_source.is_junction())
        baseline.check_baseline(af_source, "Develop",
            "7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88", environment)
        environment["GDCAE_G1_AF_SOURCE"] = str(af_source)
        environment["GDCAE_G2_AF_SOURCE"] = str(af_source)
    command = [str(safe.PYTHON), "-B", "-m", "pytest", *targets, "-q",
               "-p", "no:cacheprovider", "-p", "m03f1_safe_replay",
               "-p", "g2_safe_checks", "--basetemp", str(root / (label + "-temp"))]
    if collect_only:
        command.append("--collect-only")
    started = time.monotonic()
    capture = safe._capture(command, cwd=safe.REPO, env=environment, timeout=5400)
    safe.need(not any(capture[k] for k in
                     ("overflow", "timeout", "drain_failed", "cleanup_unknown")))
    safe.need(baseline.check_baseline(safe.REPO, "main", baseline.HEAD, environment) == head)
    if af_source is not None:
        baseline.check_baseline(af_source, "Develop",
            "7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88", environment)
    nodes = decode_inventory(nodes_file.read_bytes(), allowed)
    skipped = safe.decode_record(nodes_file.with_suffix(".skips.json").read_bytes())
    safe.need(set(skipped) == {"schema", "skips"} and skipped["schema"] == "g2-skips-v1")
    safe.need(isinstance(skipped["skips"], list) and len(skipped["skips"]) < 20000)
    for item in skipped["skips"]:
        safe.need(set(item) == {"test_ref", "reason_code"})
        validate_nodes([item["test_ref"]], allowed)
        safe.need(item["reason_code"] in {*SKIP_REASONS.values(), "UNCLASSIFIED_SKIP"})
    projection = {"counts": None, "diagnostics": []}
    if not collect_only:
        projection = safe.project_counts(safe.decode_record(counters.read_bytes()),
                                         capture["exit_code"], allowed)
        safe.need(projection["counts"]["skipped"] == len(skipped["skips"]))
    result = {"schema": "g2-safe-check-v1", "head": head,
              "boundary_digest": safe.boundary_digest(),
              "mode": "collect" if collect_only else "pytest",
              "status": "PASS" if capture["exit_code"] == 0 else "FAIL",
              "exit_code": capture["exit_code"], "node_count": len(nodes),
              "node_digest": hashlib.sha256(nodes_file.read_bytes()).hexdigest(),
              "elapsed_seconds": round(time.monotonic() - started, 2),
              "skips": skipped["skips"], **projection}
    with result_file.open("x", encoding="utf-8") as stream:
        json.dump(result, stream)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("collect", "pytest"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--af-source", type=Path)
    args = parser.parse_args()
    try:
        result = run(args.root, args.label, args.target,
                     collect_only=args.mode == "collect", af_source=args.af_source)
        print(json.dumps(result))
        raise SystemExit(result["exit_code"])
    except (ValueError, OSError, KeyError):
        print('{"status":"BLOCKED","code":"G2_SAFE_PROJECTION_BLOCKED"}')
        raise SystemExit(2)
