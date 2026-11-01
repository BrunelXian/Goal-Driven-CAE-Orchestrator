"""G3 checks bound to the audited local checkpoint; reuse P1 capture and G2 nodes."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import time

import g1_safe_checks as baseline
import g2_safe_checks as inventory
import m03f1_safe_replay as safe

GD_PARENT = "184245cc8a67859484406d70fb1e2d1cf2e347c7"
AF_PARENT = "7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88"


def checkpoint_identity(record):
    """Local audit correlation only, never authentication or execution authority."""
    safe.need(type(record) is dict and record.get("schema") == "g3-checkpoint-receipt-v1"
              and record.get("status") == "CROSS_REPO_CHECKPOINT_PARTIAL"
              and record.get("push") is False and record.get("real_abaqus") is False)
    gd, af = record.get("gdcae"), record.get("af")
    safe.need(type(gd) is dict and type(af) is dict)
    safe.need(gd.get("status") == "PASS_LOCAL_OFFLINE_CHECKPOINT"
              and type(gd.get("commit_count")) is int and gd["commit_count"] == 1
              and gd.get("parent") == GD_PARENT and type(gd.get("head")) is str
              and re.fullmatch(r"[0-9a-f]{40}", gd["head"]) is not None
              and gd["head"] != GD_PARENT)
    safe.need(af.get("status") == "BLOCKED_LINT" and af.get("head") == AF_PARENT
              and type(af.get("commit_count")) is int and af["commit_count"] == 0)
    return gd["head"], af["head"]


def run(root, label, targets, *, mode="pytest", af_source=None):
    safe.need(mode in {"privacy", "collect", "pytest"})
    safe.need(root.is_absolute() and root.is_dir()
              and root.name.startswith("gdcae-m03f1p1-g2long-g3-"))
    safe.need(all(not (p.is_symlink() or p.is_junction()) for p in (root, *root.parents)))
    safe.need(re.fullmatch(r"[a-z0-9-]{1,50}", label) is not None)
    head, af_head = checkpoint_identity(safe.decode_record(
        (root / "checkpoint-receipt.safe.json").read_bytes()))
    allowed = safe.source_allowlist()
    if mode == "privacy":
        safe.need(label == "privacy-g3")
        targets = [safe.PRIVACY_TEST]
    else:
        gate = safe.decode_record((root / "privacy-g3.safe.json").read_bytes())
        safe.need(gate["status"] == "PASS" and gate["head"] == head
                  and gate["boundary_digest"] == safe.boundary_digest())
    safe.need(all(target in allowed for target in targets))
    counters = root / (label + ".counters.json")
    nodes_file = root / (label + ".nodes.jsonl")
    result_file = root / (label + ".safe.json")
    safe.need(not any(p.exists() for p in (counters, nodes_file, result_file)))
    environment = safe._environment(counters)
    environment["GDCAE_G2_NODE_RECORD"] = str(nodes_file)
    baseline.check_baseline(safe.REPO, "main", head, environment)
    if af_source is not None:
        safe.need(af_source.resolve() == Path("D:/Projects/abqjobpilot_dev").resolve())
        baseline.check_baseline(af_source, "Develop", af_head, environment)
        environment.update(GDCAE_G1_AF_SOURCE=str(af_source), GDCAE_G2_AF_SOURCE=str(af_source),
                           GDCAE_G3_AF_SOURCE=str(af_source))
    command = [str(safe.PYTHON), "-B", "-m", "pytest", *targets, "-q",
               "-p", "no:cacheprovider", "-p", "m03f1_safe_replay", "-p", "g2_safe_checks",
               "--basetemp", str(root / (label + "-temp"))]
    if mode == "collect":
        command.append("--collect-only")
    started = time.monotonic()
    capture = safe._capture(command, cwd=safe.REPO, env=environment, timeout=5400)
    safe.need(not any(capture[k] for k in ("overflow", "timeout", "drain_failed", "cleanup_unknown")))
    baseline.check_baseline(safe.REPO, "main", head, environment)
    if af_source is not None:
        baseline.check_baseline(af_source, "Develop", af_head, environment)
    nodes = inventory.decode_inventory(nodes_file.read_bytes(), allowed)
    skips = safe.decode_record(nodes_file.with_suffix(".skips.json").read_bytes())
    safe.need(set(skips) == {"schema", "skips"} and skips["schema"] == "g2-skips-v1"
              and type(skips["skips"]) is list and len(skips["skips"]) < 20000)
    for item in skips["skips"]:
        safe.need(set(item) == {"test_ref", "reason_code"})
        inventory.validate_nodes([item["test_ref"]], allowed)
        safe.need(item["reason_code"] in {*inventory.SKIP_REASONS.values(), "UNCLASSIFIED_SKIP"})
    projection = {"counts": None, "diagnostics": []}
    if mode != "collect":
        projection = safe.project_counts(safe.decode_record(counters.read_bytes()),
                                         capture["exit_code"], allowed)
        safe.need(projection["counts"]["skipped"] == len(skips["skips"]))
    result = {"schema": "g3-safe-check-v1", "head": head, "af_head": af_head,
              "boundary_digest": safe.boundary_digest(), "mode": mode,
              "status": "PASS" if capture["exit_code"] == 0 else "FAIL",
              "exit_code": capture["exit_code"], "node_count": len(nodes),
              "node_digest": hashlib.sha256(nodes_file.read_bytes()).hexdigest(),
              "elapsed_seconds": round(time.monotonic() - started, 2),
              "skips": skips["skips"], **projection}
    with result_file.open("x", encoding="utf-8") as stream:
        json.dump(result, stream)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("privacy", "collect", "pytest"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--af-source", type=Path)
    args = parser.parse_args()
    try:
        outcome = run(args.root, args.label, args.target, mode=args.mode, af_source=args.af_source)
        print(json.dumps(outcome))
        raise SystemExit(outcome["exit_code"])
    except (ValueError, OSError, KeyError, TypeError):
        print('{"status":"BLOCKED","code":"G3_SAFE_PROJECTION_BLOCKED"}')
        raise SystemExit(2)
