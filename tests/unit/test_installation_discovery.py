"""Installed product registration, source and operational authority are separate observations."""
import pytest

from aegiscae.contracts.research_contracts import ContractError
from aegiscae.research import capability_discovery as discovery


def test_inventory_is_opt_in(monkeypatch):
    def unexpected():
        raise AssertionError("unexpected OS scan")
    monkeypatch.setattr(discovery, "windows_installation", unexpected)
    spec = dict(abaqus_launcher=None, abqjobpilot_root=None)
    assert discovery.discover(spec)["installed_product"] == {"status": "NOT_CHECKED", "versions": []}
    with pytest.raises(ContractError):
        discovery.discover(dict(spec, check_windows_registration="yes"))


@pytest.mark.parametrize("state,versions", [
    ("REGISTERED", ["0.2.1"]), ("REGISTRY_INCOMPLETE", []), ("NOT_LISTED", [])])
def test_registration_does_not_grant_backend_access(tmp_path, monkeypatch, state, versions):
    package = tmp_path / "abqjobpilot"
    package.mkdir()
    (package / "__init__.py").write_text("__version__='0.2.2'")
    monkeypatch.setattr(discovery, "windows_installation", lambda: {"status": state, "versions": versions})
    result = discovery.discover(dict(abaqus_launcher=None, abqjobpilot_root=str(tmp_path),
                                     check_windows_registration=True))
    assert result["version"] == "0.2.2" and result["abqjobpilot"] == "SOURCE_METADATA_PRESENT"
    assert result["installed_product"] == {"status": state, "versions": versions}
    assert result["service"] == "BLOCKED_INTERFACE_UNVERIFIED"
    assert result["project"] == "UNVERIFIED" and result["authorization"] == "NOT_GRANTED"
