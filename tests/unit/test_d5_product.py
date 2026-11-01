"""D5 pure packaging/activation checks; fixture layout is not installation or UI."""

import csv
from importlib.util import module_from_spec, spec_from_file_location
import io
import json
from pathlib import Path

import pytest

from test_d4_product import isolated_wheel_layout, setup, builder, package
from test_d3_external_runner import bundle, run, runner

ROOT = Path(__file__).resolve().parents[2]


def test_current_snapshot_matches_runtime_contract():
    contract = setup.validate_package(setup.read_package())
    assert contract["snapshot_version"] == builder.VERSION == "0.0.0+g3d6"
    assert contract["plugin_version"] == "0.1.0-alpha.5"


def test_activation_request_is_bounded_text_and_does_not_enable_plugin(tmp_path):
    workspace = tmp_path / "disposable"
    setup.prepare_workspace(workspace, setup.content_digest(setup.read_package()))
    before = {p.relative_to(workspace).as_posix(): p.read_bytes()
              for p in workspace.rglob("*") if p.is_file()}
    value = setup.activation_request(workspace)
    after = {p.relative_to(workspace).as_posix(): p.read_bytes()
             for p in workspace.rglob("*") if p.is_file()}
    assert before == after
    assert not (workspace / ".codex/config.toml").exists()
    assert value["status"] == "BLOCKED_USER_ACTION"
    assert value["installed_copy"] == "NOT_OBSERVED"
    assert value["desktop_activation"] == value["native_role_loading"] == "NOT_TESTED"
    assert value["execution_authorized"] is False
    assert value["global_configuration_changed"] is False
    assert set(value["role_sha256"]) == set(setup.ROLES)
    assert all(role in value["prompt"] for role in setup.ROLES)
    assert "Main may use only native delegation" in value["prompt"]
    assert "Delegated roles must not use tools" in value["prompt"]
    assert str(workspace) not in json.dumps(value)


def test_activation_request_rejects_changed_role(tmp_path):
    workspace = tmp_path / "disposable"
    setup.prepare_workspace(workspace, setup.content_digest(setup.read_package()))
    (workspace / ".codex/agents/gdcae-reviewer.toml").write_text("name='default'")
    with pytest.raises(setup.SetupBlocked):
        setup.activation_request(workspace)


def test_installed_layout_copy_is_explicitly_not_desktop_registration(tmp_path, monkeypatch):
    with isolated_wheel_layout(tmp_path, monkeypatch) as (installed, _site):
        result = installed.installed_plugin_copy()
        assert result["status"] == "INSTALLED_RECORD_VERIFIED"
        assert result["distribution"]["version"] == builder.VERSION
        assert result["desktop_activation"] == result["native_role_loading"] == "NOT_TESTED"
        assert installed.doctor()["plugin_copy"]["status"] == "INSTALLED_RECORD_VERIFIED"


def test_source_helper_cannot_claim_it_is_installed_copy(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, "installed_package", lambda *_: {
        "origin": tmp_path / "installed/aegiscae/__init__.py", "receipt": {}})
    with pytest.raises(setup.SetupBlocked, match="INSTALLED_PLUGIN_COPY_REQUIRED"):
        setup.installed_plugin_copy()


@pytest.mark.parametrize("damage", ["version", "duplicate_record", "oversize"])
def test_installed_record_negative_before_qualification(tmp_path, monkeypatch, damage):
    with isolated_wheel_layout(tmp_path, monkeypatch) as (installed, site):
        info = site / ("aegiscae-" + builder.VERSION + ".dist-info")
        if damage == "version":
            p = info / "METADATA"
            p.write_bytes(p.read_bytes().replace(builder.VERSION.encode(), b"0.0.0+obsolete"))
            code = "INSTALLED_VERSION_MISMATCH"
        elif damage == "duplicate_record":
            p = info / "RECORD"
            rows = list(csv.reader(io.StringIO(p.read_text())))
            row = next(x for x in rows if x[0] == "aegiscae/__init__.py")
            stream = io.StringIO(newline="")
            csv.writer(stream, lineterminator="\n").writerows(rows + [row])
            p.write_text(stream.getvalue())
            code = "CORE_RECORD_DUPLICATE"
        else:
            (site / "aegiscae/__init__.py").write_bytes(b"#" * 1048577)
            code = "CORE_RECORD_FILE_TOO_LARGE"
        with pytest.raises(installed.SetupBlocked, match=code):
            installed.installed_plugin_copy()


def test_external_new_claims_still_do_not_claim_fake_ipc_or_family_exit(tmp_path):
    root, digest = bundle(tmp_path)
    calls = []
    def fake(command, cwd):
        calls.append(command)
        if len(calls) == 3:
            (cwd / "smoke.json").write_text(json.dumps(dict.fromkeys(runner.CLAIMS, "PASS")))
        return 0
    result = run(root, tmp_path / "out", digest, fake)
    assert result["claims"]["real_contract_freeze"] == "PASS"
    assert result["claims"]["no_execution_authority"] == "PASS"
    assert result["fake_ipc"] == "NOT_RUN"
    assert result["fake_ipc_qualification"] == "DEPENDENCIES_AND_SUPPORT_DELIVERY_NOT_QUALIFIED"
    assert result["family_finalization"] == "NOT_VERIFIED"
    assert result["real_execution_authorized"] is False


def test_external_smoke_uses_real_factory_without_authority_in_fixture(tmp_path, monkeypatch):
    spec = spec_from_file_location("d5_external_smoke", ROOT / "external_runner/smoke.py")
    smoke = module_from_spec(spec)
    spec.loader.exec_module(smoke)
    with isolated_wheel_layout(tmp_path, monkeypatch) as (installed, _site):
        # Existing imported helper gets fixture-only installation metadata; the
        # actual factories and persisted databases execute from extracted bytes.
        monkeypatch.setattr(smoke, "module_from_spec", lambda _spec: installed)
        class Loader:
            def exec_module(self, _module):
                pass
        class Spec:
            loader = Loader()
        monkeypatch.setattr(smoke, "spec_from_file_location", lambda *_: Spec())
        destination = tmp_path / "external-layout"
        destination.mkdir()
        smoke.smoke(destination)
        assert json.loads((destination / "smoke.json").read_text()) == dict.fromkeys(runner.CLAIMS, "PASS")
        assert (destination / "real-contract-project/research/research.sqlite3").is_file()


def test_bundle_fake_scenario_is_metadata_only(tmp_path, monkeypatch):
    def snapshot(_root, product, _expected):
        name = "a.whl" if product == "gdcae" else "b.whl"
        return name, b"SYNTHETIC_WHEEL", json.dumps({"selection": {"files": {}}}).encode()
    monkeypatch.setattr(package, "snapshot_payload", snapshot)
    runner_root = ROOT / "external_runner"
    hashes = {name: package.sha((runner_root / name).read_bytes()) for name in package.RUNNER_FILES}
    support = {name: "a" * 64 for name in package.FAKE_SUPPORT}
    out = tmp_path / "bundle"
    package.assemble(tmp_path / "gd", tmp_path / "af", out, runner_root, hashes,
                     gd_manifest_sha256="b" * 64, af_manifest_sha256="c" * 64,
                     fake_ipc_support_hashes=support)
    plan = json.loads((out / "support/FAKE_IPC_SCENARIO.json").read_bytes())
    assert plan["support_hashes"] == support
    assert plan["support_included"] is False
    assert plan["status"] == "NOT_RUN" and plan["execution_authorized"] is False
    assert plan["real_grant_allowed"] is False
    assert not any((out / name).exists() for name in package.FAKE_SUPPORT)
