"""Isolated internal-candidate packaging and actual local wheel installation tests."""

import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "plugins/gdcae/scripts"


def load(name):
    spec = spec_from_file_location("g2_" + name, SCRIPTS / (name + ".py"))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate = load("candidate")
setup = load("gdcae")


def selection(source, bodies=None):
    bodies = bodies or {"src/aegiscae/__init__.py": b'VALUE = "ORIGINAL_FIXTURE"\n',
                        "src/aegiscae/resource.txt": b"original bounded package resource\n"}
    for name, body in bodies.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    hashes = {name: hashlib.sha256(body).hexdigest() for name, body in bodies.items()}
    return {"schema": "gdcae-source-selection-v1", "product": "gdcae",
            "base_commit": "a" * 40, "files": hashes, "dirty_files": dict(hashes),
            "license_status": "UNRESOLVED_INTERNAL_ONLY"}


def test_snapshot_exact_allowlist_hashes_resources_and_determinism(tmp_path):
    source = tmp_path / "source"
    manifest = selection(source)
    (source / "do-not-copy.txt").write_text("unselected")
    first = candidate.export_snapshot(source, manifest, tmp_path / "first snapshot")
    second = candidate.export_snapshot(source, manifest, tmp_path / "second snapshot")
    assert first == second
    assert first["status"] == "INTERNAL_CANDIDATE_NOT_FOR_RELEASE"
    assert first["release_ref"] == "PENDING_RELEASE_REF"
    copied = tmp_path / "first snapshot/source"
    assert {p.relative_to(copied).as_posix() for p in copied.rglob("*") if p.is_file()} == (
        set(manifest["files"]))
    for name, sha in first["artifacts"].items():
        assert hashlib.sha256((tmp_path / "first snapshot" / name).read_bytes()).hexdigest() == sha
    wheel = next((tmp_path / "first snapshot").glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        assert archive.read("aegiscae/resource.txt") == b"original bounded package resource\n"
        assert not any("do-not-copy" in name for name in archive.namelist())


def test_actual_plugin_source_closure_includes_candidate_helper_without_rule_false_positive(tmp_path):
    bodies = {"src/aegiscae/__init__.py": b"# Original isolated package fixture\n"}
    bodies.update({"plugins/gdcae/" + name: body for name, body in setup.read_package().items()})
    source = tmp_path / "source"
    manifest = selection(source, bodies)
    exported = tmp_path / "snapshot"
    candidate.export_snapshot(source, manifest, exported)
    plugin = exported / "source/plugins/gdcae"
    assert setup.read_package(plugin) == setup.read_package()
    assert (plugin / "scripts/candidate.py").is_file()
    url_fixture = b"codex:" + b"//threads/" + b"SYNTHETIC_PRIVATE_MARKER"
    assert candidate.PRIVATE.search(url_fixture) is not None


@pytest.mark.parametrize("path", [
    "../private.txt", "src/aegiscae/../escape.py", "src/aegiscae/CON.py",
    "src/aegiscae/trailing./x.py", "src/aegiscae/x.py ", "src/aegiscae/x.db",
    "Kickoff_Docs/private.md", "CAE models/model.inp", ".codex/auth.json",
    "docs/milestones/private.md", "src/aegiscae/credentials.txt", "src/aegiscae/x.pth",
])
def test_selection_rejects_private_traversal_executable_overlay_and_unknown_files(tmp_path, path):
    manifest = selection(tmp_path / "source")
    manifest["files"][path] = "b" * 64
    with pytest.raises(candidate.CandidateBlocked):
        candidate.export_snapshot(tmp_path / "source", manifest, tmp_path / "never-created")
    assert not (tmp_path / "never-created").exists()


def test_source_tamper_and_missing_resource_fail_before_destination(tmp_path):
    source = tmp_path / "source"
    manifest = selection(source)
    (source / "src/aegiscae/resource.txt").write_bytes(b"changed")
    with pytest.raises(candidate.CandidateBlocked, match="SOURCE_DIGEST_MISMATCH"):
        candidate.export_snapshot(source, manifest, tmp_path / "tampered")
    (source / "src/aegiscae/resource.txt").unlink()
    with pytest.raises(candidate.CandidateBlocked, match="SOURCE_FILE_INVALID"):
        candidate.export_snapshot(source, manifest, tmp_path / "missing")
    assert not (tmp_path / "tampered").exists() and not (tmp_path / "missing").exists()


def test_fresh_destination_and_case_collision_rejected(tmp_path):
    source = tmp_path / "source"
    manifest = selection(source)
    target = tmp_path / "existing"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep")
    with pytest.raises(candidate.CandidateBlocked, match="FRESH_DESTINATION_REQUIRED"):
        candidate.export_snapshot(source, manifest, target)
    manifest["files"]["src/aegiscae/RESOURCE.txt"] = "b" * 64
    with pytest.raises(candidate.CandidateBlocked, match="CASE_COLLISION"):
        candidate.export_snapshot(source, manifest, tmp_path / "collision")
    assert sentinel.read_text() == "keep"


def test_dirty_record_and_license_claim_rejected(tmp_path):
    manifest = selection(tmp_path / "source")
    manifest["dirty_files"]["src/aegiscae/resource.txt"] = "f" * 64
    with pytest.raises(candidate.CandidateBlocked, match="DIRTY_RECORD_MISMATCH"):
        candidate.validate_selection(manifest)
    manifest["dirty_files"] = {}
    manifest["license_status"] = "PUBLICLY_APPROVED"
    with pytest.raises(candidate.CandidateBlocked, match="PUBLIC_RELEASE_NOT_AUTHORIZED"):
        candidate.validate_selection(manifest)


def test_sensitive_fixture_rejected_without_echo(tmp_path, monkeypatch, capsys):
    source = tmp_path / "source"
    marker = b"sk-" + b"SYNTHETIC_CANARY_ONLY_" * 3
    manifest = selection(source, {"src/aegiscae/__init__.py": marker})
    selection_file = tmp_path / "selection.json"
    selection_file.write_text(json.dumps(manifest))
    monkeypatch.setattr(sys, "argv", ["candidate.py", "--source-root", str(source),
                        "--selection", str(selection_file), "--destination", str(tmp_path / "out")])
    assert candidate.main() == 2
    output = capsys.readouterr()
    assert marker.decode() not in output.out + output.err
    assert json.loads(output.out)["code"] == "PRIVATE_MATERIAL_REJECTED"
    assert not (tmp_path / "out").exists()


def test_exact_af_credential_source_exception_retains_all_content_guards(tmp_path):
    source = tmp_path / "af_source"
    name = "abqjobpilot/local_credentials.py"
    body = b"# Original synthetic credential-handling source, no credential data\n"
    manifest = selection(source, {"abqjobpilot/__init__.py": b"# synthetic package\n",
                                  name: body})
    manifest["product"] = "af_develop"
    candidate.export_snapshot(source, manifest, tmp_path / "accepted")
    assert (tmp_path / "accepted/source" / name).read_bytes() == body
    # Exact product AND exact case-sensitive path; no broader basename exemption.
    for product, path in [
        ("gdcae", "src/aegiscae/local_credentials.py"),
        ("af_develop", "abqjobpilot/other_credentials.py"),
        ("af_develop", "abqjobpilot/local_credentials.json"),
        ("af_develop", "abqjobpilot/local_credentials.py.txt"),
        ("af_develop", "abqjobpilot/nested/local_credentials.py"),
        ("af_develop", "abqjobpilot/LOCAL_CREDENTIALS.py"),
        ("af_develop", "abqjobpilot/auth.json"),
        ("af_develop", "abqjobpilot/secrets.txt"),
    ]:
        with pytest.raises(candidate.CandidateBlocked, match="PRIVATE_MATERIAL_REJECTED"):
            candidate.allowed_path(product, path)
    with pytest.raises(candidate.CandidateBlocked, match="SELECTION_OUT_OF_SCOPE"):
        candidate.allowed_path("gdcae", name)
    path = source / name
    path.write_bytes(body + b"# changed\n")
    with pytest.raises(candidate.CandidateBlocked, match="SOURCE_DIGEST_MISMATCH"):
        candidate.export_snapshot(source, manifest, tmp_path / "tampered")
    canary = b"sk-" + b"SYNTHETIC_CANARY_ONLY_" * 3
    path.write_bytes(canary)
    manifest["files"][name] = hashlib.sha256(canary).hexdigest()
    manifest["dirty_files"][name] = manifest["files"][name]
    with pytest.raises(candidate.CandidateBlocked, match="PRIVATE_MATERIAL_REJECTED"):
        candidate.export_snapshot(source, manifest, tmp_path / "secret-rejected")
    assert not (tmp_path / "tampered").exists()
    assert not (tmp_path / "secret-rejected").exists()


def test_initialization_refuses_source_checkout_import_without_writing(tmp_path):
    with pytest.raises(setup.SetupBlocked, match="INSTALLED_CORE_REQUIRED"):
        setup.initialize_research(tmp_path / "fresh", setup.content_digest(setup.read_package()),
                                  "G2Preview")
    assert not (tmp_path / "fresh").exists()


def test_arbitrary_site_packages_name_cannot_claim_installed_core(tmp_path, monkeypatch):
    fake = tmp_path / "source/site-packages/aegiscae/__init__.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("raise AssertionError('must never import')")
    monkeypatch.setattr(setup, "find_spec", lambda _: SimpleNamespace(origin=str(fake)))
    with pytest.raises(setup.SetupBlocked, match="INSTALLED_CORE_REQUIRED"):
        setup.initialize_research(tmp_path / "fresh", setup.content_digest(setup.read_package()),
                                  "G2Preview")
    assert not (tmp_path / "fresh").exists()


def test_real_offline_wheel_install_has_no_development_import_fallback(tmp_path):
    source = tmp_path / "fixture source"
    manifest = selection(source)
    destination = tmp_path / "internal candidate"
    candidate.export_snapshot(source, manifest, destination)
    wheel = next(destination.glob("*.whl"))
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment.update(PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1",
                       PIP_CONFIG_FILE=os.devnull, PYTHONDONTWRITEBYTECODE="1")
    venv = tmp_path / "isolated venv"
    created = subprocess.run([sys.executable, "-I", "-m", "venv", str(venv)],
                             capture_output=True, env=environment, timeout=60)
    assert created.returncode == 0
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    installed = subprocess.run([str(python), "-I", "-m", "pip", "--isolated", "install",
                                "--no-index", "--no-deps", "--no-cache-dir", "--no-compile",
                                str(wheel)], capture_output=True, env=environment, timeout=60)
    assert installed.returncode == 0
    probe = subprocess.run([str(python), "-I", "-c",
        "import aegiscae,json,importlib.resources as r;"
        "print(json.dumps({'origin':aegiscae.__file__,'value':aegiscae.VALUE,"
        "'resource':r.files('aegiscae').joinpath('resource.txt').read_text()}))"],
        cwd=tmp_path, env=environment, capture_output=True, timeout=20)
    assert probe.returncode == 0
    result = json.loads(probe.stdout)
    assert Path(result["origin"]).is_relative_to(venv)
    assert not Path(result["origin"]).is_relative_to(source)
    assert result["value"] == "ORIGINAL_FIXTURE"
    assert result["resource"] == "original bounded package resource\n"
    # Load only our reviewed helper; the Core discovery remains the real installed wheel.
    verifier = '''
import importlib.util, importlib.metadata, json, pathlib, sys
spec = importlib.util.spec_from_file_location("setup", sys.argv[1])
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)
origin = setup.verify_installed_core()
assert origin.is_relative_to(pathlib.Path(sys.prefix))
dist = importlib.metadata.distribution("aegiscae")
direct = pathlib.Path(dist.locate_file(next(p for p in dist.files
                        if str(p).endswith(".dist-info/direct_url.json"))))
original_direct = direct.read_bytes()
direct.write_text(json.dumps({"url":"file:///SYNTHETIC", "dir_info":{"editable":True}}))
def rejected(code):
    try:
        setup.verify_installed_core()
    except setup.SetupBlocked as error:
        assert str(error) == code
    else:
        raise AssertionError("expected rejection")
rejected("EDITABLE_CORE_REJECTED")
direct.write_bytes(original_direct)
original_source = origin.read_bytes()
origin.write_bytes(original_source + b"# synthetic tamper\\n")
rejected("CORE_RECORD_DIGEST_MISMATCH")
origin.write_bytes(original_source)
extra = origin.parent / "unrecorded.py"
extra.write_text("# synthetic unrecorded source")
rejected("CORE_UNRECORDED_FILE")
print(json.dumps({"installed_record":True,"editable_rejected":True,
                  "tamper_rejected":True,"unrecorded_rejected":True}))
'''
    verified = subprocess.run([str(python), "-I", "-c", verifier, str(SCRIPTS / "gdcae.py")],
                              cwd=tmp_path, env=environment, capture_output=True, timeout=20)
    assert verified.returncode == 0
    assert json.loads(verified.stdout) == {"installed_record": True, "editable_rejected": True,
                                          "tamper_rejected": True, "unrecorded_rejected": True}
