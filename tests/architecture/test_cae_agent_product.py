"""Public product metadata and the dependency boundary of the distribution entry point."""
import json
import runpy
import tomllib

from conftest import REPO_ROOT


def test_product_versions_and_registered_surfaces():
    product = REPO_ROOT / "product/cae-agent"
    version = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    descriptor = json.loads((product / "plugin/plugin.json").read_bytes())
    core = runpy.run_path(str(REPO_ROOT / "src/aegiscae/__init__.py"))
    builder = runpy.run_path(str(product / "build.py"))
    assert version == core["__version__"] == descriptor["version"] == builder["VERSION"] == "0.3.1"
    servers = json.loads((product / "plugin/mcp.json").read_bytes())["mcpServers"]
    assert set(servers) == {"gdcae-core", "abqjobpilot"}


def test_neutral_service_import_closure_excludes_legacy_host_gates():
    builder = runpy.run_path(str(REPO_ROOT / "product/cae-agent/build.py"))
    files = {p.relative_to(REPO_ROOT).as_posix(): p.read_bytes()
             for p in (REPO_ROOT / "src/aegiscae").rglob("*.py")}
    payload = builder["reachable"](files, "aegiscae.interfaces.mcp_research")
    assert "aegiscae/research/project_tasks.py" in payload
    assert "aegiscae/research/scoped_coordinator.py" in payload
    for name in ("interfaces/mcp_scoped", "research/task_cards", "research/scoped_fixture"):
        assert f"aegiscae/{name}.py" not in payload
    for data in payload.values():
        assert b"CODEX_THREAD_ID" not in data and b"main-handoffs/v1" not in data
