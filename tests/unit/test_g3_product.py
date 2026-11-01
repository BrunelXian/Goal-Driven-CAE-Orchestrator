"""G3 product consistency checks; no Codex Turn, AF Owner or solver."""

import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]


def load(name):
    spec = spec_from_file_location("g3_" + name, REPO / "plugins/gdcae/scripts" / (name + ".py"))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = load("gdcae")
candidate = load("candidate")


def test_doctor_reports_records_without_importing_uninstalled_code(monkeypatch):
    monkeypatch.setattr(setup, "find_spec", lambda _: None)
    result = setup.doctor()
    assert result["installed_packages"] == {
        "aegiscae": {"status": "NOT_INSTALLED_OR_INVALID"},
        "abqjobpilot": {"status": "NOT_INSTALLED_OR_INVALID"}}
    assert result["workspace"]["status"] == "NOT_REQUESTED"
    assert result["native_role_loading"] == "NOT_TESTED"


def test_unknown_distribution_is_not_inspected():
    with pytest.raises(setup.SetupBlocked, match="UNKNOWN_DISTRIBUTION"):
        setup.installed_package("unapproved", "unapproved")


def test_workspace_four_role_closure_is_not_activation(tmp_path):
    workspace = tmp_path / "research"
    setup.prepare_workspace(workspace, setup.content_digest(setup.read_package()))
    result = setup.doctor(workspace)["workspace"]
    assert result["status"] == "PACKAGE_AND_FOUR_ROLE_BYTES_VERIFIED"
    assert set(result["role_sha256"]) == set(setup.ROLES)
    assert result["native_role_loading"] == result["plugin_activation"] == "NOT_TESTED"


@pytest.mark.parametrize("mutation", ["missing", "changed", "extra", "plugin_changed"])
def test_workspace_damaged_or_unexpected_roles_fail_closed(tmp_path, mutation):
    workspace = tmp_path / "research"
    setup.prepare_workspace(workspace, setup.content_digest(setup.read_package()))
    role = workspace / ".codex/agents/gdcae-inverse.toml"
    if mutation == "missing":
        role.unlink()
    elif mutation == "changed":
        role.write_text('name = "default"')
    elif mutation == "extra":
        (role.parent / "default.toml").write_text('name = "default"')
    else:
        (workspace / "plugins/gdcae/plugin.json").write_text("{}")
    result = setup.doctor(workspace)
    assert result["workspace"]["status"] == "INVALID_WORKSPACE_CLOSURE"
    assert result["real_execution_authorized"] is False


def test_invalid_workspace_does_not_echo_path(tmp_path, capsys, monkeypatch):
    private = tmp_path / "SYNTHETIC_CANARY_NOT_FOR_OUTPUT"
    monkeypatch.setattr(sys, "argv", ["gdcae", "doctor", "--workspace", str(private)])
    assert setup.main() == 0
    output = capsys.readouterr().out
    assert str(private) not in output
    assert json.loads(output)["workspace"]["status"] == "INVALID_WORKSPACE_CLOSURE"


def test_real_project_api_source_receipt_with_explicit_fixture_installation(monkeypatch, tmp_path):
    # Installation qualification is separately tested using actual wheels below.
    # This test exercises the real offline Project API and receipt handoff only.
    install = {"distribution": "aegiscae", "source": "INTERPRETER_INSTALLATION_RECORD",
               "package_files_sha256": "a" * 64, "record_sha256": "b" * 64}
    monkeypatch.setattr(setup, "installed_package", lambda *_: {
        "origin": tmp_path / "fixture-installed-source", "receipt": install})
    workspace = tmp_path / "research"
    expected = setup.content_digest(setup.read_package())
    result = setup.initialize_research(workspace, expected, "G3ReceiptFixture")
    body = (workspace / "gdcae-source-receipt.json").read_bytes()
    receipt = json.loads(body)
    assert hashlib.sha256(body).hexdigest() == result["source_receipt_sha256"]
    assert receipt["installed_core"] == install
    assert receipt["plugin_package_sha256"] == expected
    assert receipt["commit_inclusion"] == "NOT_ASSERTED"
    assert receipt["source_ref"] == "CONTENT_ADDRESSED_LOCAL_BYTES"
    assert set(receipt["role_sha256"]) == set(setup.ROLES)
    assert result["real_a"] == result["real_b"] == "NOT_RUN"
    assert result["execution_authorized"] is False


def test_two_installed_fixture_distributions_have_distinct_record_identity(tmp_path):
    wheels = []
    for product, package, prefix in (("gdcae", "aegiscae", "src/aegiscae"),
                                      ("af_develop", "abqjobpilot", "abqjobpilot")):
        source = tmp_path / (product + "_source")
        marker = source / prefix / "__init__.py"
        marker.parent.mkdir(parents=True)
        marker.write_bytes(b"# Pure original synthetic package; must not be imported.\n")
        names = {prefix + "/__init__.py": hashlib.sha256(marker.read_bytes()).hexdigest()}
        selection = {"schema": "gdcae-source-selection-v1", "product": product,
                     "base_commit": "a" * 40, "files": names, "dirty_files": {},
                     "license_status": "UNRESOLVED_INTERNAL_ONLY"}
        out = tmp_path / product
        candidate.export_snapshot(source, selection, out)
        wheels.extend(out.glob("*.whl"))
    env = {k: v for k, v in os.environ.items() if k.upper() not in {"PYTHONPATH", "PYTHONHOME"}}
    env.update(PIP_NO_INDEX="1", PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK="1")
    venv = tmp_path / "venv"
    assert subprocess.run([sys.executable, "-I", "-m", "venv", str(venv)],
                          capture_output=True, env=env, timeout=60).returncode == 0
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    assert subprocess.run([str(python), "-I", "-m", "pip", "--isolated", "install",
        "--no-index", "--no-deps", "--no-cache-dir", "--no-compile", *map(str, wheels)],
        capture_output=True, env=env, timeout=60).returncode == 0
    script = '''
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("helper", sys.argv[1])
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
result = helper.doctor()
assert "aegiscae" not in sys.modules and "abqjobpilot" not in sys.modules
for name in ("aegiscae", "abqjobpilot"):
    assert result["installed_packages"][name]["status"] == "RECORD_VERIFIED"
print(json.dumps(result["installed_packages"]))
'''
    checked = subprocess.run([str(python), "-I", "-B", "-c", script,
                              str(REPO / "plugins/gdcae/scripts/gdcae.py")],
                             capture_output=True, env=env, cwd=tmp_path, timeout=20)
    assert checked.returncode == 0
    receipt = json.loads(checked.stdout)
    assert receipt["aegiscae"]["record_sha256"] != receipt["abqjobpilot"]["record_sha256"]
