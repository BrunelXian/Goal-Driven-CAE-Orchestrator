"""F1-P1 local test boundary. Never reads private history or starts Codex/AF.

Test output is untrusted data. A pytest hook writes only counters and approved
source locations; stdout/stderr are drained privately and never rendered.
"""

import ast
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time


REPO = Path(__file__).resolve().parents[2]
PYTHON = Path("D:/XianLab/envs/LangChainEnv/Scripts/python.exe")
RUFF = Path("D:/ProgramData/anaconda3/Scripts/ruff.exe")
HEAD = "538bfae9a3a5fcea97970b9effc4f1f168490650"
PRIVACY_TEST = "tests/unit/test_main_runtime_privacy.py"
COUNTS = ("passed", "failed", "skipped", "error", "deselected")
MODES = {"gate", "focused", "full", "ruff", "diff"}
MAX_OUTPUT = 2 * 1024 * 1024


class ProjectionBlocked(ValueError):
    def __init__(self):
        super().__init__("BLOCKED_PRIVACY_PROJECTION")


def need(condition):
    if not condition:
        raise ProjectionBlocked()


def decode_record(body):
    need(type(body) is bytes and len(body) <= 65536)
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result)
            result[key] = value
        return result
    def invalid_constant(_value):
        raise ProjectionBlocked()
    try:
        return json.loads(body.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise ProjectionBlocked() from None


def project_fixture(value):
    """Pure allowlist projection; raw_private is opaque and never returned/hashed."""
    keys = {"schema", "milestone", "status", "passed", "skipped", "test_type", "head",
            "source_ref", "source_read_policy", "raw_private"}
    need(type(value) is dict and set(value) == keys)
    expected = {"schema": "synthetic-evidence-input-v1", "milestone": "M03-F1-R1-P1",
        "test_type": "SYNTHETIC_PRIVACY", "head": HEAD, "source_ref": "NEW_SYNTHETIC_FIXTURE",
        "source_read_policy": "SYNTHETIC_ONLY_NO_HISTORY"}
    need(all(type(value[k]) is str and value[k] == v for k, v in expected.items()))
    need(type(value["status"]) is str and value["status"] in {"PASS", "FAIL", "UNKNOWN", "NOT_TESTED"})
    need(all(type(value[k]) is int and 0 <= value[k] <= 10000 for k in ("passed", "skipped")))
    need(type(value["raw_private"]) is bytes and len(value["raw_private"]) <= 65536)
    return {"schema": "gdcae-safe-projection-v1", **{k: value[k] for k in expected if k != "schema"},
            "status": value["status"], "passed": value["passed"], "skipped": value["skipped"]}


def source_allowlist():
    """Current test source only. No Markdown, manifests, session or historical log reads."""
    allowed = {}
    for file in (REPO / "tests").rglob("test_*.py"):
        need(not file.is_symlink() and file.resolve().is_relative_to(REPO / "tests"))
        relative = file.relative_to(REPO).as_posix()
        tree = ast.parse(file.read_text(encoding="utf-8-sig"))
        allowed[relative] = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                             and re.fullmatch(r"test_[a-zA-Z0-9_]+", n.name)}
    return allowed


def _safe_diagnostic(nodeid, line, allowed):
    # Never expose parametrization, assertion values, exception text or absolute paths.
    base = nodeid.split("[", 1)[0] if type(nodeid) is str else ""
    parts = base.replace("\\", "/").split("::")
    if len(parts) != 2 or parts[0] not in allowed or parts[1] not in allowed[parts[0]]:
        return {"code": "UNCLASSIFIED_TEST_FAILURE"}
    need(type(line) is int and 0 <= line <= 100000)
    return {"code": "TEST_FAILURE", "source_ref": parts[0], "test": parts[1], "line": line}


def pytest_sessionfinish(session, exitstatus):
    """Trusted hook, independent of child stdout text. This is not a security sandbox."""
    target = os.environ.get("GDCAE_SAFE_RESULT_PATH")
    if not target:
        return
    allowed = source_allowlist()
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    stats = reporter.stats if reporter else {}
    counts = {key: len(stats.get(key, [])) for key in COUNTS}
    diagnostics = []
    for key in ("failed", "error"):
        for report in stats.get(key, [])[:32]:
            location = getattr(report, "location", None)
            line = location[1] + 1 if location and type(location[1]) is int else 0
            diagnostics.append(_safe_diagnostic(getattr(report, "nodeid", ""), line, allowed))
    value = {"schema": "pytest-counters-v1", "exit_code": int(exitstatus),
             "counts": counts, "diagnostics": diagnostics}
    path = Path(target)
    need(path.is_absolute() and path.parent.name.startswith("gdcae-m03f1p1-"))
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream)


def _capture(argv, *, cwd, env, timeout, limit=MAX_OUTPUT):
    """Private bounded drain. Caller may only project it, never return raw bytes."""
    child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    chunks, total, overflow = [], 0, threading.Event()
    drain_failed = threading.Event()
    def drain():
        nonlocal total
        try:
            while True:
                data = child.stdout.read(8192)
                if not data:
                    break
                total += len(data)
                if total <= limit:
                    chunks.append(data)
                else:
                    overflow.set()
                    child.kill()  # Retained handle only; not proof of tree cleanup.
        except BaseException:
            # Never let threading.excepthook render untrusted exception text.
            drain_failed.set()
    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    timed_out = False
    try:
        child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        child.kill()
        child.wait(timeout=15)
    reader.join(timeout=15)
    need(not reader.is_alive())
    child.stdout.close()
    return {"exit_code": child.returncode, "total_bytes": total, "overflow": overflow.is_set(),
            "timeout": timed_out, "drain_failed": drain_failed.is_set(),
            "cleanup_unknown": timed_out or overflow.is_set() or drain_failed.is_set(),
            "raw": b"".join(chunks)}


def project_counts(value, exit_code, allowed):
    need(type(value) is dict and set(value) == {"schema", "exit_code", "counts", "diagnostics"}
         and value["schema"] == "pytest-counters-v1" and type(value["exit_code"]) is int
         and value["exit_code"] == exit_code and 0 <= exit_code <= 5)
    counts = value["counts"]
    need(type(counts) is dict and set(counts) == set(COUNTS)
         and all(type(v) is int and 0 <= v <= 100000 for v in counts.values()))
    if exit_code == 0:
        need(counts["passed"] > 0 and counts["failed"] == counts["error"] == 0)
    need(type(value["diagnostics"]) is list and len(value["diagnostics"]) <= 64)
    for item in value["diagnostics"]:
        need(type(item) is dict)
        if item == {"code": "UNCLASSIFIED_TEST_FAILURE"}:
            continue
        need(set(item) == {"code", "source_ref", "test", "line"}
             and item["code"] == "TEST_FAILURE" and item["source_ref"] in allowed
             and item["test"] in allowed[item["source_ref"]]
             and type(item["line"]) is int and 0 <= item["line"] <= 100000)
    return {"counts": counts, "diagnostics": value["diagnostics"]}


def boundary_digest():
    return hashlib.sha256(Path(__file__).read_bytes() + (REPO / PRIVACY_TEST).read_bytes()).hexdigest()


def validate_result(value, allowed):
    need(type(value) is dict and set(value) == {"schema", "milestone", "source_read_policy", "mode",
        "status", "exit_code", "elapsed_seconds", "suppressed_output_bytes", "counts", "diagnostics",
        "head", "boundary_digest"})
    need(value["schema"] == "gdcae-bounded-run-result-v1" and value["milestone"] == "M03-F1-R1-P1"
         and value["source_read_policy"] == "CURRENT_RUN_ONLY_NO_HISTORY" and value["head"] == HEAD
         and value["mode"] in MODES and value["status"] in {"PASS", "FAIL"}
         and type(value["exit_code"]) is int and value["status"] == ("PASS" if value["exit_code"] == 0 else "FAIL")
         and type(value["elapsed_seconds"]) in (int, float) and math.isfinite(value["elapsed_seconds"])
         and 0 <= value["elapsed_seconds"] <= 2800
         and type(value["suppressed_output_bytes"]) is int and 0 <= value["suppressed_output_bytes"] <= MAX_OUTPUT
         and type(value["boundary_digest"]) is str and re.fullmatch(r"[0-9a-f]{64}", value["boundary_digest"]))
    if value["mode"] in {"gate", "focused", "full"}:
        project_counts({"schema": "pytest-counters-v1", "exit_code": value["exit_code"],
            "counts": value["counts"], "diagnostics": value["diagnostics"]}, value["exit_code"], allowed)
    else:
        need(value["counts"] is None and value["diagnostics"] == [])


def _environment(result_file):
    allowed = {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "TEMP", "TMP", "COMSPEC", "USERPROFILE",
               "APPDATA", "LOCALAPPDATA"}
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        PYTHONPATH=os.pathsep.join((str(REPO / "src"), str(Path(__file__).parent))),
        GDCAE_M01B_LIVE="", GDCAE_M01C_LIVE="", GDCAE_M03B_LIVE="",
        GDCAE_SAFE_RESULT_PATH=str(result_file), NO_COLOR="1")
    return env


def run(root, mode, label):
    root = Path(root)
    need(mode in MODES and re.fullmatch(mode + r"-[1-3]", label) is not None)
    need(root.is_absolute() and root.name.startswith("gdcae-m03f1p1-") and root.is_dir()
         and not root.is_symlink() and root.resolve() == root)
    if mode != "gate":
        valid = False
        for name in ("gate-1", "gate-2", "gate-3"):
            path = root / (name + ".safe.json")
            if path.is_file():
                record = decode_record(path.read_bytes())
                validate_result(record, source_allowlist())
                valid |= (record.get("mode") == "gate" and record.get("status") == "PASS" and record.get("exit_code") == 0
                          and record.get("boundary_digest") == boundary_digest()
                          and record.get("head") == HEAD)
        need(valid)
    with (root / (label + ".intent")).open("x", encoding="ascii") as stream:
        stream.write("OFFLINE_ONLY")
    counters = root / (label + ".counters.json")
    temp = root / (label + "-temp")
    need(not counters.exists() and not temp.exists())
    if mode in {"gate", "focused", "full"}:
        targets = {"gate": [PRIVACY_TEST], "focused": ["tests/unit/test_main_runtime.py", "tests/architecture"],
                   "full": []}[mode]
        command = [str(PYTHON), "-B", "-m", "pytest", *targets, "-q", "-p", "no:cacheprovider",
                   "-p", "m03f1_safe_replay", "--basetemp", str(temp)]
    elif mode == "ruff":
        command = [str(RUFF), "check", "--no-cache", "."]
    else:
        command = ["git", "diff", "--check"]
    start = time.monotonic()
    captured = _capture(command, cwd=REPO, env=_environment(counters), timeout=2700)
    need(not captured["overflow"] and not captured["timeout"]
         and not captured["drain_failed"] and not captured["cleanup_unknown"])
    projected = {"counts": None, "diagnostics": []}
    if mode in {"gate", "focused", "full"}:
        need(counters.is_file() and counters.stat().st_size <= 65536)
        projected = project_counts(decode_record(counters.read_bytes()),
                                   captured["exit_code"], source_allowlist())
    result = {"schema": "gdcae-bounded-run-result-v1", "milestone": "M03-F1-R1-P1",
        "source_read_policy": "CURRENT_RUN_ONLY_NO_HISTORY", "mode": mode,
        "status": "PASS" if captured["exit_code"] == 0 else "FAIL",
        "exit_code": captured["exit_code"], "elapsed_seconds": round(time.monotonic() - start, 2),
        "suppressed_output_bytes": captured["total_bytes"], **projected,
        "head": HEAD, "boundary_digest": boundary_digest()}
    validate_result(result, source_allowlist())
    with (root / (label + ".safe.json")).open("x", encoding="utf-8") as stream:
        json.dump(result, stream)
    return result


def main():
    try:
        need(len(sys.argv) == 4)
        result = run(*sys.argv[1:])
    except BaseException:
        # No repr(error), traceback, last-output tail or raw fallback on any failure.
        result = {"schema": "gdcae-safe-block-v1", "status": "BLOCKED_PRIVACY_PROJECTION"}
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
