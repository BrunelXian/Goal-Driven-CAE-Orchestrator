"""Synthetic-only privacy gate. No historical evidence or actual thread identifiers."""

import ast
import copy
import inspect
import json
import os
from pathlib import Path
import secrets
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "integration"))
import m03f1_safe_replay as safe  # noqa: E402


def fixture():
    # Runtime-created opaque marker. Never a real Codex identifier and never printed.
    marker = ("PRIVATE_SYNTHETIC_" + secrets.token_hex(24)).encode()
    value = {"schema": "synthetic-evidence-input-v1", "milestone": "M03-F1-R1-P1", "status": "PASS",
        "passed": 1, "skipped": 0, "test_type": "SYNTHETIC_PRIVACY", "head": safe.HEAD,
        "source_ref": "NEW_SYNTHETIC_FIXTURE", "source_read_policy": "SYNTHETIC_ONLY_NO_HISTORY",
        "raw_private": marker}
    return value, marker


def test_projection_drops_opaque_marker_before_output(capsys):
    value, marker = fixture()
    output = safe.project_fixture(value)
    print(json.dumps(output))
    captured = capsys.readouterr()
    assert marker not in captured.out.encode() + captured.err.encode()
    assert "raw_private" not in output
    assert output["source_read_policy"] == "SYNTHETIC_ONLY_NO_HISTORY"


@pytest.mark.parametrize("field", ["schema", "milestone", "status", "test_type", "head",
                                   "source_ref", "source_read_policy", "passed", "skipped"])
def test_marker_in_allowlisted_field_fails_closed(field):
    value, marker = fixture()
    value[field] = marker.decode()
    with pytest.raises(safe.ProjectionBlocked) as error:
        safe.project_fixture(value)
    assert str(error.value) == "BLOCKED_PRIVACY_PROJECTION"


@pytest.mark.parametrize("fault", ["missing", "extra", "nested", "bool", "large", "private_type"])
def test_unknown_shape_never_falls_back(fault):
    value, marker = fixture()
    if fault == "missing":
        del value["source_ref"]
    elif fault == "extra":
        value["unrecognized_secret"] = marker
    elif fault == "nested":
        value["status"] = {"message": marker}
    elif fault == "bool":
        value["passed"] = True
    elif fault == "large":
        value["raw_private"] = b"x" * 65537
    else:
        value["raw_private"] = {"unknown": marker}
    with pytest.raises(safe.ProjectionBlocked):
        safe.project_fixture(value)


def test_capture_suppresses_stdout_stderr_and_exception(tmp_path, capsys):
    _value, marker = fixture()
    code = "import sys; v=sys.argv[1]; print(v); print(v,file=sys.stderr); raise ValueError(v)"
    result = safe._capture([sys.executable, "-B", "-c", code, marker.decode()],
                          cwd=tmp_path, env=os.environ.copy(), timeout=15)
    assert result["exit_code"] != 0 and marker in result["raw"]
    # Only predefined counters/labels are released, never result['raw'].
    print(json.dumps({"status": "EXPECTED_FAILURE", "exit_code": result["exit_code"]}))
    captured = capsys.readouterr()
    assert marker not in captured.out.encode() + captured.err.encode()
    assert not list(tmp_path.iterdir())  # No raw log artifact.


def test_false_pass_stdout_cannot_override_hook_exit():
    value = {"schema": "pytest-counters-v1", "exit_code": 0,
             "counts": {k: int(k == "passed") for k in safe.COUNTS}, "diagnostics": []}
    with pytest.raises(safe.ProjectionBlocked):
        safe.project_counts(value, 1, {})
    value["exit_code"] = 1
    assert safe.project_counts(value, 1, {})["counts"]["passed"] == 1
    value["counts"]["failed"] = 1
    value["exit_code"] = 0
    with pytest.raises(safe.ProjectionBlocked):
        safe.project_counts(value, 0, {})


def test_diagnostics_discard_parameters_and_unknown_names():
    _, marker = fixture()
    allowed = {"tests/unit/test_example.py": {"test_example"}}
    node = "tests/unit/test_example.py::test_example[" + marker.decode() + "]"
    result = safe._safe_diagnostic(node, 10, allowed)
    assert marker not in json.dumps(result).encode()
    assert result["test"] == "test_example"
    assert safe._safe_diagnostic(marker.decode(), 0, allowed) == {"code": "UNCLASSIFIED_TEST_FAILURE"}


def test_counter_unknown_secret_rejected():
    _, marker = fixture()
    value = {"schema": "pytest-counters-v1", "exit_code": 0,
             "counts": {k: int(k == "passed") for k in safe.COUNTS}, "diagnostics": []}
    value["raw_message"] = marker.decode()
    with pytest.raises(safe.ProjectionBlocked):
        safe.project_counts(value, 0, {})


def test_projection_is_pure_read_and_does_not_bootstrap(tmp_path):
    value, _ = fixture()
    before = copy.deepcopy(value)
    original = tuple(tmp_path.iterdir())
    for _ in range(3):
        safe.project_fixture(value)
    assert value == before and tuple(tmp_path.iterdir()) == original
    tree = ast.parse(inspect.getsource(safe.project_fixture))
    forbidden = {"open", "connect", "Popen", "run", "write_text", "write_bytes", "mkdir", "initialize_runtime"}
    assert not any(isinstance(n, ast.Call) and (
        isinstance(n.func, ast.Name) and n.func.id in forbidden or
        isinstance(n.func, ast.Attribute) and n.func.attr in forbidden) for n in ast.walk(tree))


def test_oversized_capture_is_blocked_not_raw_fallback(tmp_path):
    result = safe._capture([sys.executable, "-B", "-c", "print('x'*100000)"],
                          cwd=tmp_path, env=os.environ.copy(), timeout=15, limit=1000)
    assert result["overflow"] and len(result["raw"]) <= 1000


def test_counter_source_allowlist_is_exact():
    value = {"schema": "pytest-counters-v1", "exit_code": 1,
             "counts": {k: int(k == "failed") for k in safe.COUNTS},
             "diagnostics": [{"code": "TEST_FAILURE", "source_ref": "private-file", "test": "test_x", "line": 1}]}
    with pytest.raises(safe.ProjectionBlocked):
        safe.project_counts(value, 1, {})


@pytest.mark.parametrize("body", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}',
                                  b'\xff', b'{', b'x' * 65537],
                         ids=["duplicate", "nan", "infinity", "encoding", "syntax", "size"])
def test_parse_failure_never_returns_partial_record(body):
    with pytest.raises(safe.ProjectionBlocked):
        safe.decode_record(body)


def test_gate_record_missing_or_injected_fields_is_not_authority():
    with pytest.raises(safe.ProjectionBlocked):
        safe.validate_result({"status": "PASS", "head": safe.HEAD}, {})


@pytest.mark.parametrize("fault", ["read", "kill", "timeout"])
def test_drain_exceptions_never_reach_thread_hook(monkeypatch, capsys, fault):
    _, marker = fixture()
    hooks = []
    monkeypatch.setattr(safe.threading, "excepthook", lambda value: hooks.append(True))

    class Pipe:
        def read(self, size):
            if fault == "read":
                raise ValueError(marker.decode())
            if fault == "kill":
                return b"x" * 2
            return b""

        def close(self):
            pass

    class Child:
        stdout = Pipe()
        returncode = 0
        waits = 0

        def wait(self, timeout):
            self.waits += 1
            if fault == "timeout" and self.waits == 1:
                raise safe.subprocess.TimeoutExpired(marker.decode(), timeout)

        def kill(self):
            if fault == "kill":
                raise ValueError(marker.decode())

    monkeypatch.setattr(safe.subprocess, "Popen", lambda *args, **kwargs: Child())
    result = safe._capture([], cwd=None, env={}, timeout=1, limit=1)
    assert result["cleanup_unknown"]
    assert result["timeout"] if fault == "timeout" else result["drain_failed"]
    assert not hooks
    captured = capsys.readouterr()
    assert not captured.out and not captured.err


def test_changed_boundary_invalidates_gate(monkeypatch, tmp_path):
    root = tmp_path / "gdcae-m03f1p1-synthetic"
    root.mkdir()
    record = {"schema": "gdcae-bounded-run-result-v1", "milestone": "M03-F1-R1-P1",
              "source_read_policy": "CURRENT_RUN_ONLY_NO_HISTORY", "mode": "gate", "status": "PASS",
              "exit_code": 0, "elapsed_seconds": 1, "suppressed_output_bytes": 0,
              "counts": {k: int(k == "passed") for k in safe.COUNTS}, "diagnostics": [],
              "head": safe.HEAD, "boundary_digest": "0" * 64}
    (root / "gate-1.safe.json").write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(safe, "source_allowlist", lambda: {})
    monkeypatch.setattr(safe, "boundary_digest", lambda: "1" * 64)
    calls = []
    monkeypatch.setattr(safe, "_capture", lambda *args, **kwargs: calls.append(True))
    with pytest.raises(safe.ProjectionBlocked):
        safe.run(root, "full", "full-1")
    assert not calls and not (root / "full-1.intent").exists()
