"""D4 file-layout qualification; no pip, venv, process, client or Solver launch."""

from contextlib import contextmanager
import copy
from importlib.util import module_from_spec, spec_from_file_location
import io
import json
from pathlib import Path
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = spec_from_file_location(name, path)
    value = module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


setup = load("d4_product_setup", ROOT / "plugins/gdcae/scripts/gdcae.py")
builder = load("d4_product_builder", ROOT / "plugins/gdcae/scripts/candidate.py")
package = load("d4_product_package", ROOT / "external_runner/package.py")


def test_new_candidate_version_and_portable_manifest_closure():
    files = setup.read_package()
    contract = setup.validate_package(files)
    assert contract["snapshot_version"] == builder.VERSION == "0.0.0+g3d6"
    assert contract["read_only_mcp"]["tools"] == list(setup.READ_TOOLS)
    assert contract["read_only_mcp"]["auto_start"] is False
    assert contract["core_freeze"]["execution_authorized"] is False


@pytest.mark.parametrize("damage", ["version", "onboarding", "hook", "role", "tool", "truthy", "extra"])
def test_declared_resource_or_permission_drift_rejected(damage):
    files = copy.deepcopy(setup.read_package())
    manifest = json.loads(files["plugin.json"])
    runtime = json.loads(files["references/runtime-contract.json"])
    if damage == "version":
        manifest["version"] = "0.1.0-alpha.2"
    elif damage == "onboarding":
        manifest["extensions"]["com.openai"]["onboardingSkill"] = "../../outside/SKILL.md"
    elif damage == "hook":
        manifest["extensions"]["com.openai"]["hooks"] = "./execute.json"
    elif damage == "role":
        path = "agents/gdcae-inverse.toml"
        files[path] = files[path].replace(b"shell_tool = false", b"shell_tool = true")
    elif damage == "tool":
        runtime["read_only_mcp"]["tools"].append("gdcae_execute")
    elif damage == "truthy":
        runtime["solver_authorized"] = 0
    else:
        runtime["private_session"] = "SYNTHETIC_NOT_AN_ID"
    files["plugin.json"] = json.dumps(manifest).encode()
    files["references/runtime-contract.json"] = json.dumps(runtime).encode()
    with pytest.raises(setup.SetupBlocked):
        setup.validate_package(files)


def test_install_plan_has_no_unverified_plugin_install_command():
    value = setup.install_plan("https://github.com/example/source", "a" * 40)
    assert value["commands"] == [["codex", "plugin", "marketplace", "add",
                                   "https://github.com/example/source", "--ref", "a" * 40]]
    assert value["activation"] == "OFFICIAL_DESKTOP_PLUGIN_DIRECTORY_MANUAL_STEP"
    assert value["github_installation"] == "NOT_TESTED"


def test_doctor_declares_missing_optional_dependencies_without_import(monkeypatch):
    def missing(_name):
        raise setup.metadata.PackageNotFoundError
    monkeypatch.setattr(setup.metadata, "version", missing)
    value = setup.doctor()
    assert value["optional_dependencies"] == {"mcp": "MISSING", "pywin32": "MISSING"}
    assert value["read_only_mcp"] == "UNBOUND_REQUIRES_EXPLICIT_TEST_PROJECT"
    assert value["real_execution_authorized"] is False


def test_real_init_requires_installed_core_before_creating_workspace(tmp_path):
    with pytest.raises(setup.SetupBlocked, match="INSTALLED_CORE_REQUIRED"):
        setup.initialize_real_research(tmp_path / "never-created", setup.content_digest(setup.read_package()), "D4")
    assert not (tmp_path / "never-created").exists()


@contextmanager
def isolated_wheel_layout(tmp_path, monkeypatch):
    """Explicit layout fixture, not an interpreter installation or native role run."""
    site = tmp_path / "wheel-layout"
    site.mkdir()
    files = {p.relative_to(ROOT).as_posix(): p.read_bytes()
             for p in (ROOT / "src/aegiscae").rglob("*.py")}
    files.update({"plugins/gdcae/" + k: v for k, v in setup.read_package().items()})
    for product, bodies in (("gdcae", files), ("af_develop", {"abqjobpilot/__init__.py": b"# layout fixture\n"})):
        _, wheel = builder.wheel_bytes(product, bodies)
        with zipfile.ZipFile(io.BytesIO(wheel)) as archive:
            for name in archive.namelist():
                target = site / name
                assert target.resolve().is_relative_to(site)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
    original = {k: v for k, v in sys.modules.items() if k == "aegiscae" or k.startswith("aegiscae.")
                or k == "abqjobpilot" or k.startswith("abqjobpilot.")}
    for key in original:
        del sys.modules[key]
    try:
        with monkeypatch.context() as patch:
            patch.setattr(sys, "path", [str(site)] + [p for p in sys.path
                if p and not Path(p).resolve().is_relative_to(ROOT)])
            installed = load("d4_layout_setup", site / "aegiscae/_gdcae_plugin/scripts/gdcae.py")
            get_path = installed.sysconfig.get_path
            distribution = installed.metadata.distribution
            patch.setattr(installed.sysconfig, "get_path", lambda key, *a, **kw:
                          str(site) if key in {"purelib", "platlib"} else get_path(key, *a, **kw))
            def fixture_distribution(name):
                if name in {"aegiscae", "abqjobpilot_gdcae_internal"}:
                    return installed.metadata.Distribution.at(site / (name + "-" + builder.VERSION + ".dist-info"))
                return distribution(name)
            patch.setattr(installed.metadata, "distribution", fixture_distribution)
            yield installed, site
    finally:
        for key in tuple(sys.modules):
            if key == "aegiscae" or key.startswith("aegiscae.") or key == "abqjobpilot" or key.startswith("abqjobpilot."):
                del sys.modules[key]
        sys.modules.update(original)


def test_wheel_layout_loads_real_factory_and_new_project_without_source_checkout(tmp_path, monkeypatch):
    with isolated_wheel_layout(tmp_path, monkeypatch) as (installed, site):
        workspace = tmp_path / "new-research-workspace"
        receipt = installed.initialize_real_research(workspace,
            installed.content_digest(installed.read_package()), "D4Layout")
        assert receipt["mode"] == "REAL_CONTRACT_FROZEN_NO_EXECUTION"
        assert receipt["execution_authorized"] is False
        assert receipt["real_a"] == "NOT_READY"
        assert receipt["plan_created"] is receipt["grant_issued"] is False
        assert receipt["maximum_solver_calls"] == 2
        assert "research_project_id" not in receipt
        assert (workspace / "gdcae-real-init.json").is_file()
        assert (workspace / "research/research.sqlite3").is_file()
        assert installed.doctor(workspace)["workspace"]["status"] == "PACKAGE_AND_FOUR_ROLE_BYTES_VERIFIED"
        loaded = [Path(m.__file__) for n, m in sys.modules.items()
                  if n == "aegiscae" or n.startswith("aegiscae.")]
        assert loaded and all(p.resolve().is_relative_to(site) for p in loaded)


def test_wheel_layout_tamper_is_rejected_before_freeze(tmp_path, monkeypatch):
    with isolated_wheel_layout(tmp_path, monkeypatch) as (installed, site):
        source = site / "aegiscae/research/rod_real_project.py"
        source.write_bytes(source.read_bytes() + b"\n# synthetic changed bytes\n")
        with pytest.raises(installed.SetupBlocked, match="CORE_RECORD_DIGEST_MISMATCH"):
            installed.initialize_real_research(tmp_path / "never", installed.content_digest(installed.read_package()), "D4")
        assert not (tmp_path / "never").exists()


def test_operator_preview_files_are_explicit_non_autoload_wheel_resources():
    files = {"src/aegiscae/__init__.py": b"# fixture\n",
             "operator_deployment/preview.py": b"# reviewed preview fixture\n",
             "operator_deployment/audit.py": b"# reviewed readonly audit fixture\n"}
    for name in files:
        builder.allowed_path("gdcae", name)
    with pytest.raises(builder.CandidateBlocked):
        builder.allowed_path("gdcae", "operator_deployment/deploy.py")
    _, body = builder.wheel_bytes("gdcae", files)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        assert archive.read("aegiscae/_gdcae_operator/preview.py") == files["operator_deployment/preview.py"]
        assert not any(name.endswith((".pth", "entry_points.txt")) for name in archive.namelist())
