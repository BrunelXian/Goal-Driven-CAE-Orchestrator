"""Offline failure injection for TEST harness cleanup; never start an AF owner."""

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def live_helpers(monkeypatch):
    integration = Path(__file__).resolve().parents[1] / "integration"
    monkeypatch.syspath_prepend(str(integration))
    return importlib.import_module("test_mcp_read_live")


def cleanup_fixture(tmp_path, failures):
    """Create tiny synthetic lifecycle metadata, not an AF Project or credential."""
    calls = []
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    (fixture / "lifecycle.json").write_text(json.dumps([{
        "exited": True, "actual_process_handle_signaled": True,
        "terminated_by_owned_handle": False,
    }]), encoding="utf-8")
    (fixture / "inventory.json").write_text(json.dumps({
        "credential_absent_from_remaining_files": "connection" not in failures,
    }), encoding="utf-8")

    def unlink():
        calls.append("unlink")
        if "connection" in failures:
            raise PermissionError("synthetic-private-error-must-not-appear")

    def close_harness():
        calls.append("harness.close")
        if "harness" in failures:
            raise RuntimeError("synthetic-private-error-must-not-appear")

    def reference(index):
        def exit_evidence():
            calls.append(f"ref{index}.exit")
            if "unconfirmed" in failures and index == 0:
                return None
            return {
                "pid": index + 1, "creation_time_100ns": 100 + index,
                "exit_code": 0, "exit_source": "synthetic-owned-handle",
                "exit_observed_at": 200 + index,
                "private": "synthetic-private-extra-must-not-appear",
            }

        def close():
            calls.append(f"ref{index}.close")
            if "handle" in failures and index == 0:
                raise OSError("synthetic-private-error-must-not-appear")

        return SimpleNamespace(exit_evidence=exit_evidence, close=close)

    return (SimpleNamespace(root=fixture, close=close_harness),
            SimpleNamespace(exists=lambda: True, unlink=unlink),
            [reference(0), reference(1)], calls)


@pytest.mark.parametrize("failures,expected_errors", [
    ({"connection"}, ["CONNECTION_CLEANUP_FAILED"]),
    ({"harness"}, ["HARNESS_CLEANUP_FAILED"]),
    ({"connection", "harness"}, ["CONNECTION_CLEANUP_FAILED", "HARNESS_CLEANUP_FAILED"]),
])
def test_cleanup_failures_do_not_skip_owned_stop_handles_or_evidence(
    tmp_path, live_helpers, failures, expected_errors,
):
    harness, connection, refs, calls = cleanup_fixture(tmp_path, failures)
    evidence = {"status": "READS_COMPLETE_REVIEW_TRANSCRIPT_PENDING_AUDIT"}

    live_helpers.cleanup(harness, connection, refs, tmp_path, evidence)

    assert calls == ["unlink", "harness.close", "ref0.exit", "ref0.close",
                     "ref1.exit", "ref1.close"]
    stored = (tmp_path / "evidence.json").read_text(encoding="utf-8")
    assert json.loads(stored) == evidence
    assert "synthetic-private" not in stored
    assert evidence["status"] == "PARTIAL"
    assert evidence["cleanup_verified"] is False
    assert evidence["cleanup_errors"] == expected_errors
    assert len(evidence["exit_evidence"]) == 2
    assert all(row["exit_code"] == 0 for row in evidence["exit_evidence"])


def test_unknown_exit_does_not_claim_cleanup_or_skip_remaining_handle(tmp_path, live_helpers):
    harness, connection, refs, calls = cleanup_fixture(tmp_path, {"unconfirmed"})
    evidence = {"status": "READS_COMPLETE_REVIEW_TRANSCRIPT_PENDING_AUDIT"}

    live_helpers.cleanup(harness, connection, refs, tmp_path, evidence)

    assert calls[-4:] == ["ref0.exit", "ref0.close", "ref1.exit", "ref1.close"]
    assert evidence["cleanup_verified"] is False
    assert evidence["cleanup_errors"] == ["EXIT_UNCONFIRMED"]
    assert evidence["status"] == "PARTIAL"
    assert [row["pid"] for row in evidence["exit_evidence"]] == [2]
    assert json.loads((tmp_path / "evidence.json").read_text()) == evidence


def test_handle_close_failure_continues_remaining_handles_and_saves_partial(tmp_path, live_helpers):
    harness, connection, refs, calls = cleanup_fixture(tmp_path, {"handle"})
    evidence = {"status": "READS_COMPLETE_REVIEW_TRANSCRIPT_PENDING_AUDIT"}

    live_helpers.cleanup(harness, connection, refs, tmp_path, evidence)

    assert calls == ["unlink", "harness.close", "ref0.exit", "ref0.close",
                     "ref1.exit", "ref1.close"]
    assert evidence["cleanup_verified"] is False
    assert evidence["cleanup_errors"] == ["HANDLE_CLOSE_FAILED"]
    assert evidence["status"] == "PARTIAL"
    assert len(evidence["exit_evidence"]) == 2
    stored = (tmp_path / "evidence.json").read_text(encoding="utf-8")
    assert json.loads(stored) == evidence
    assert "synthetic-private" not in stored
