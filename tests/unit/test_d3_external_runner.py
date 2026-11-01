"""Pure runner contract tests; injected responses never launch a process."""

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = spec_from_file_location("d3_runner", ROOT / "external_runner/qualify.py")
runner = module_from_spec(spec)
spec.loader.exec_module(runner)


def bundle(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    bodies = {"qualify.py": b"# fixture", "smoke.py": b"# fixture", "README.md": b"fixture",
              "wheels/a.whl": b"fixture-a", "wheels/b.whl": b"fixture-b"}
    for name, body in bodies.items():
        path = root / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(body)
    manifest = {"schema": "gdcae-external-bundle-v1", "status": "NOT_RUN_EXTERNALLY",
                "files": {k: runner.sha(v) for k, v in bodies.items()},
                "wheels": ["wheels/a.whl", "wheels/b.whl"], "python": "3.12.10",
                "provenance": {}, "execution_authorized": False}
    body = json.dumps(manifest).encode()
    (root / "BUNDLE.json").write_bytes(body)
    return root, runner.sha(body)


def run(root, destination, digest, fake, **kwargs):
    return runner.qualify(root, destination, digest, runner=fake, approved=True,
                          independent=True, system="nt", version="3.12.10", **kwargs)


def test_no_permission_no_process_or_output(tmp_path):
    root, digest = bundle(tmp_path)
    with pytest.raises(runner.Blocked, match="EXTERNAL_APPROVAL_REQUIRED"):
        runner.qualify(root, tmp_path / "out", digest,
                       runner=lambda *_: pytest.fail("process called"))
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("damage", ["manifest", "file", "extra", "missing", "path"])
def test_exact_input_negative_before_process(tmp_path, damage):
    root, digest = bundle(tmp_path)
    if damage == "manifest":
        digest = "f" * 64
    elif damage == "file":
        (root / "smoke.py").write_bytes(b"changed")
    elif damage == "extra":
        (root / "private.txt").write_bytes(b"SYNTHETIC_PRIVATE_MARKER")
    elif damage == "missing":
        (root / "smoke.py").unlink()
    else:
        value = json.loads((root / "BUNDLE.json").read_bytes())
        value["files"]["../escape"] = "a" * 64
        body = json.dumps(value).encode()
        (root / "BUNDLE.json").write_bytes(body)
        digest = runner.sha(body)
    with pytest.raises((runner.Blocked, OSError)):
        run(root, tmp_path / "out", digest, lambda *_: pytest.fail("process called"))
    assert not (tmp_path / "out").exists()


def test_success_claims_require_smoke_evidence_and_keep_family_unknown(tmp_path):
    root, digest = bundle(tmp_path)
    commands = []

    def fake(command, cwd):
        commands.append(command)
        if len(commands) == 3:
            (cwd / "smoke.json").write_text(json.dumps(dict.fromkeys(runner.CLAIMS, "PASS")))
        return 0

    result = run(root, tmp_path / "out", digest, fake)
    assert result["status"] == "NO_SOLVER_SMOKE_PASS"
    assert result["family_finalization"] == "NOT_VERIFIED"
    assert result["desktop_activation"] == "NOT_TESTED"
    assert len(commands) == 3
    assert "--no-index" in commands[1] and "--no-deps" in commands[1]
    assert len(list((tmp_path / "out").glob("receipt-*.json"))) == 4
    assert all(str(tmp_path) not in p.read_text() for p in (tmp_path / "out").glob("receipt*"))


@pytest.mark.parametrize("failure", ["timeout", "exception", "exit", "invalid"])
def test_failure_stops_without_retry_or_private_output(tmp_path, failure):
    root, digest = bundle(tmp_path)
    calls = []

    def fake(command, cwd):
        calls.append(command)
        if failure == "timeout":
            raise subprocess.TimeoutExpired("SYNTHETIC_PRIVATE_MARKER", 180)
        if failure == "exception":
            raise OSError("SYNTHETIC_PRIVATE_MARKER")
        return 7 if failure == "exit" else "SYNTHETIC_PRIVATE_MARKER"

    result = run(root, tmp_path / "out", digest, fake)
    assert len(calls) == 1
    assert result["status"] == ("FAILED" if failure == "exit" else "UNKNOWN_STOP")
    assert "SYNTHETIC_PRIVATE_MARKER" not in json.dumps(result)
    assert all(value == "NOT_RUN" for value in result["claims"].values())


def test_exit_zero_without_smoke_is_not_pass(tmp_path):
    root, digest = bundle(tmp_path)
    result = run(root, tmp_path / "out", digest, lambda *_: 0)
    assert result["status"] == "FAILED_SMOKE_EVIDENCE"


def test_existing_destination_never_reused(tmp_path):
    root, digest = bundle(tmp_path)
    destination = tmp_path / "out"
    destination.mkdir()
    with pytest.raises(runner.Blocked, match="FRESH_EXTERNAL_DESTINATION_REQUIRED"):
        run(root, destination, digest, lambda *_: pytest.fail("process called"))


@pytest.mark.parametrize("relative, invocation", [
    ("external_runner/README.md", "& $Python -I $entry"),
    (".github/workflows/gdcae-external-qualification.yml", "& python -I $entry"),
])
def test_trusted_launchers_authenticate_entrypoint_before_execution(relative, invocation):
    # Static qualification only: deliberately never execute PowerShell or Python children.
    text = (ROOT / relative).read_text(encoding="utf-8")
    order = ("Assert-PlainPath $manifest", "BUNDLE_DIGEST_MISMATCH",
             "$entryDigest = $record.files.'qualify.py'", "Assert-PlainPath $entry",
             "Get-FileHash -LiteralPath $entry", "ENTRY_DIGEST_MISMATCH", invocation)
    positions = [text.index(token) for token in order]
    assert positions == sorted(positions)
    assert "ReparsePoint" in text
    assert "concurrent" in text
