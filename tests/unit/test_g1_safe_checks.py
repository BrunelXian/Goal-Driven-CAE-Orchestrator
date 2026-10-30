"""Synthetic regression for the G1 evidence baseline precondition."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "integration"))
import g1_safe_checks as runner  # noqa: E402


@pytest.mark.parametrize("head,branch", [
    ("0" * 40, "main"), (runner.HEAD, "other"),
    (runner.HEAD, ""), ("untrusted-private-marker", "main"),
])
def test_baseline_drift_is_rejected_without_projecting_raw_output(monkeypatch, head, branch):
    responses = iter([head.encode(), branch.encode()])
    monkeypatch.setattr(runner.safe, "_capture", lambda *args, **kwargs: {
        "exit_code": 0, "raw": next(responses), "overflow": False,
        "timeout": False, "drain_failed": False, "cleanup_unknown": False})
    with pytest.raises(runner.safe.ProjectionBlocked) as failure:
        runner.check_baseline(Path("."), "main", runner.HEAD, {})
    assert str(failure.value) == "BLOCKED_PRIVACY_PROJECTION"


def test_matching_metadata_returns_measured_head(monkeypatch):
    responses = iter([runner.HEAD.encode() + b"\r\n", b"main\n"])
    monkeypatch.setattr(runner.safe, "_capture", lambda *args, **kwargs: {
        "exit_code": 0, "raw": next(responses), "overflow": False,
        "timeout": False, "drain_failed": False, "cleanup_unknown": False})
    assert runner.check_baseline(Path("."), "main", runner.HEAD, {}) == runner.HEAD
