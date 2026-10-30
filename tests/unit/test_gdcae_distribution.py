"""Source-only distribution tests; never install Codex plugins or start a service."""

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import tomllib

import pytest

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "plugins" / "gdcae"
spec = spec_from_file_location("gdcae_setup", PACKAGE / "scripts" / "gdcae.py")
setup = module_from_spec(spec)
spec.loader.exec_module(setup)


def test_fresh_workspace_contains_exact_allowlist_without_installing(tmp_path):
    target = tmp_path / "new-research"
    package = setup.read_package()
    result = setup.prepare_workspace(target, setup.content_digest(package))
    expected = {f"plugins/gdcae/{name}" for name in setup.FILES}
    expected |= {f".codex/agents/{name}.toml" for name in setup.ROLES}
    expected |= {".agents/plugins/marketplace.json", "gdcae-package.json"}
    assert {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()} == expected
    assert not (target / ".codex/config.toml").exists()
    assert result["plugin_activation"] == "NOT_TESTED"
    assert result["execution_authorized"] is False
    for name, body in package.items():
        assert (target / "plugins/gdcae" / name).read_bytes() == body
    for role in setup.ROLES:
        assert (target / ".codex/agents" / f"{role}.toml").read_bytes() == (
            REPO / ".codex/agents" / f"{role}.toml").read_bytes()


def test_existing_workspace_and_digest_conflict_are_not_overwritten(tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    digest = setup.content_digest(setup.read_package())
    with pytest.raises(setup.SetupBlocked, match="FRESH_WORKSPACE_REQUIRED"):
        setup.prepare_workspace(target, digest)
    with pytest.raises(setup.SetupBlocked, match="PACKAGE_DIGEST_MISMATCH"):
        setup.prepare_workspace(tmp_path / "new", "0" * 64)
    assert sentinel.read_text() == "preserve"
    assert not (tmp_path / "new").exists()


def test_source_and_global_destinations_rejected(tmp_path, monkeypatch):
    digest = setup.content_digest(setup.read_package())
    with pytest.raises(setup.SetupBlocked, match="SOURCE_WORKSPACE_DESTINATION_REJECTED"):
        setup.prepare_workspace(REPO / "not-created-g1-test", digest)
    home = tmp_path / "codex-home"
    home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    with pytest.raises(setup.SetupBlocked, match="GLOBAL_CONFIG_DESTINATION_REJECTED"):
        setup.prepare_workspace(home / "not-created", digest)


@pytest.mark.parametrize("ref", ["main", "v1.0", "f" * 39, "f" * 41, "-x", "A" * 40])
def test_install_plan_ref_must_be_immutable(ref):
    with pytest.raises(setup.SetupBlocked, match="FULL_COMMIT_REQUIRED"):
        setup.install_plan("https://github.com/example/source", ref)


@pytest.mark.parametrize("url", [
    "https://credential@github.com/example/source", "https://github.com/example/source?secret=x",
    "https://github.com/example/source#fragment", "https://untrusted.invalid/example/source",
    "https://github.com/example/source;command", "file:///local/path",
])
def test_install_plan_rejects_credentials_or_shell_content(url):
    with pytest.raises(setup.SetupBlocked, match="CREDENTIAL_FREE_GITHUB_URL_REQUIRED"):
        setup.install_plan(url, "a" * 40)


def test_install_plan_only_returns_arguments():
    plan = setup.install_plan("https://github.com/example/source", "a" * 40)
    assert plan["executed"] is False
    assert plan["approval_required"] is True
    assert plan["repository_access"] == "UNKNOWN"
    assert plan["core_installation"] == "REQUIRES_APPROVED_PINNED_SOURCE_INSTALL"
    assert plan["commands"][0][-2:] == ["--ref", "a" * 40]


def test_packaged_native_agents_and_discovery_contract():
    manifest = json.loads((PACKAGE / "plugin.json").read_text())
    assert manifest["name"] == "gdcae"
    onboarding = manifest["extensions"]["com.openai"]["onboardingSkill"]
    assert (PACKAGE / onboarding).is_file()
    catalog = json.loads((REPO / ".agents/plugins/marketplace.json").read_text())
    assert catalog == setup.marketplace()
    for role in setup.ROLES:
        config = tomllib.loads((PACKAGE / "agents" / f"{role}.toml").read_text())
        assert config["name"] == role
        assert config["developer_instructions"]
        assert config["features"]["shell_tool"] is False
        assert not {"mcp_servers", "sandbox_mode", "approval_policy", "model"} & config.keys()
    assert not (PACKAGE / "mcp.json").exists()  # No unbound execution/credential endpoint.


def test_doctor_never_upgrades_unknown_capabilities_to_pass():
    result = setup.doctor()
    assert result["real_execution_authorized"] is False
    assert result["operator_isolation"] == "BLOCKED_HIL_STRONG_ISOLATION"
    assert result["plugin_activation"] == "NOT_TESTED"


def test_doctor_reports_missing_core_without_importing_it(monkeypatch):
    monkeypatch.setattr(setup, "find_spec", lambda name: None)
    assert setup.doctor()["research_core"] == "MISSING"


def test_unknown_cli_arguments_do_not_echo_private_input(monkeypatch, capsys):
    marker = "NEW_SYNTHETIC_PRIVATE_MARKER"
    monkeypatch.setattr(setup.sys, "argv", ["gdcae.py", "doctor", "--unknown=" + marker])
    assert setup.main() == 2
    output = capsys.readouterr()
    assert marker not in output.out + output.err
    assert json.loads(output.out) == {"status": "BLOCKED", "code": "INVALID_ARGUMENTS"}


def test_unsupported_python_stops_before_package_or_environment_access(monkeypatch, capsys):
    monkeypatch.setattr(setup.sys, "version_info", (3, 11, 0))
    monkeypatch.setattr(setup, "read_package", lambda: pytest.fail("must not inspect package"))
    assert setup.main() == 2
    assert json.loads(capsys.readouterr().out)["code"] == "PYTHON_312_OR_NEWER_REQUIRED"
