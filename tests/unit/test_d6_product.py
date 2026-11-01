"""D6 source/dependency closure and bounded activation; no installer or harness run."""

from importlib import metadata
import json
from pathlib import Path

import pytest

from test_d4_product import setup, builder, package


ROOT = Path(__file__).resolve().parents[2]


def support(tmp_path):
    root = tmp_path / "support"
    root.mkdir()
    for name in package.FAKE_SUPPORT:
        (root / name).write_bytes(b"import pathlib\nimport pytest\n")
    hashes = {name: package.sha((root / name).read_bytes()) for name in package.FAKE_SUPPORT}
    return root, hashes


def test_version_and_one_paste_three_action_handoff_remain_unobserved(tmp_path):
    assert builder.VERSION == setup.validate_package(setup.read_package())["snapshot_version"]
    assert builder.VERSION == "0.0.0+g3d6"
    workspace = tmp_path / "disposable"
    setup.prepare_workspace(workspace, setup.content_digest(setup.read_package()))
    before = {p.relative_to(workspace).as_posix(): p.read_bytes()
              for p in workspace.rglob("*") if p.is_file()}
    request = setup.activation_request(workspace)
    assert len(request["human_steps"]) == 3 and request["paste_count"] == 1
    assert request["reply_options"] == ["已完成", "无法激活"]
    assert request["ui_click_count"] == "NOT_OBSERVED_THREE_ACTION_TARGET"
    assert request["authentication"] == "NOT_OBSERVED_NO_CREDENTIAL_READ"
    assert request["status"] == "BLOCKED_USER_ACTION"
    assert request["desktop_activation"] == request["native_role_loading"] == "NOT_TESTED"
    assert "Main may use only native delegation" in request["prompt"]
    assert "Delegated roles must not use tools" in request["prompt"]
    assert before == {p.relative_to(workspace).as_posix(): p.read_bytes()
                      for p in workspace.rglob("*") if p.is_file()}


def test_exact_support_bytes_packaged_without_importing_or_running(tmp_path):
    root, hashes = support(tmp_path)
    (root / "unselected.py").write_text("raise RuntimeError('must not run')")
    payload = package.fake_support_payload(root, hashes)
    assert set(payload) == {"support/fake_ipc/" + n for n in package.FAKE_SUPPORT}
    assert all(body == b"import pathlib\nimport pytest\n" for body in payload.values())


@pytest.mark.parametrize("damage", ["missing", "changed", "extra_hash", "unknown_import",
                                    "relative_import", "syntax", "private_marker", "oversize"])
def test_support_tamper_and_incomplete_import_closure_rejected(tmp_path, damage):
    root, hashes = support(tmp_path)
    name = package.FAKE_SUPPORT[0]
    path = root / name
    if damage == "missing":
        del hashes[name]
    elif damage == "extra_hash":
        hashes["unknown.py"] = "a" * 64
    else:
        content = {"changed": b"# altered", "unknown_import": b"import unreviewed_dependency\n",
                   "relative_import": b"from . import unreviewed\n", "syntax": b"if\n",
                   "private_marker": b"# codex://threads/REDACTED_SYNTHETIC_MARKER\n",
                   "oversize": b"#" * 65537}[damage]
        path.write_bytes(content)
        if damage != "changed":
            hashes[name] = package.sha(content)
    with pytest.raises(package.PackageBlocked):
        package.fake_support_payload(root, hashes)


def test_dependency_profile_is_exact_observed_metadata_not_wheel_delivery():
    value = package.dependency_manifest()
    assert value["fake_ipc"] == {name: metadata.version(name)
                                 for name in package.FAKE_DEPENDENCIES}
    assert value["dependency_wheels_included"] is False
    assert value["wheelhouse_sha256"] is None
    assert value["installation"] == "NOT_RUN"
    assert value["optional_mcp"]["dependency_closure"] == "NOT_INCLUDED"
    assert value["license_review"] == "INTERNAL_METADATA_ONLY_PUBLIC_REDISTRIBUTION_NOT_APPROVED"


def test_bundle_includes_verified_source_but_not_dependency_or_execution_claim(tmp_path, monkeypatch):
    def snapshot(_root, product, _expected):
        return ("a.whl" if product == "gdcae" else "b.whl", b"SYNTHETIC_WHEEL",
                json.dumps({"selection": {"files": {}}}).encode())
    monkeypatch.setattr(package, "snapshot_payload", snapshot)
    root, support_hashes = support(tmp_path)
    runner_root = ROOT / "external_runner"
    runner_hashes = {n: package.sha((runner_root / n).read_bytes()) for n in package.RUNNER_FILES}
    destination = tmp_path / "bundle"
    result = package.assemble(tmp_path / "gd", tmp_path / "af", destination,
                              runner_root, runner_hashes, gd_manifest_sha256="a" * 64,
                              af_manifest_sha256="b" * 64,
                              fake_ipc_support_hashes=support_hashes, fake_ipc_support_root=root)
    scenario = json.loads((destination / "support/FAKE_IPC_SCENARIO.json").read_bytes())
    manifest = json.loads((destination / "BUNDLE.json").read_bytes())
    assert scenario["support_included"] is True
    assert scenario["harness_imported_or_executed"] is False
    assert scenario["local_import_closure"] == "STATIC_AST_CHECKED"
    assert scenario["qualification"] == "DEPENDENCY_WHEELHOUSE_AND_EXTERNAL_EXECUTION_NOT_QUALIFIED"
    assert scenario["status"] == "NOT_RUN" and result["execution_authorized"] is False
    assert all(manifest["files"]["support/fake_ipc/" + n] == h
               for n, h in support_hashes.items())
