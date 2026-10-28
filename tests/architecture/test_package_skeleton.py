"""Allow historical markers, the M01-A bridge, and the exact M01-C MCP module."""

from __future__ import annotations

from pathlib import Path

from conftest import SRC_ROOT

PACKAGE_MARKERS = {
    Path("aegiscae/__init__.py"),
    Path("aegiscae/contracts/__init__.py"),
    Path("aegiscae/runtime/__init__.py"),
    Path("aegiscae/validation/__init__.py"),
    Path("aegiscae/interfaces/__init__.py"),
    Path("aegiscae/adapters/__init__.py"),
    Path("aegiscae/adapters/abaqus/__init__.py"),
    Path("aegiscae/research/__init__.py"),
}
M01_MODULES = {
    Path("aegiscae/contracts/af_evidence.py"),
    Path("aegiscae/adapters/abaqus/af_evidence.py"),
    Path("aegiscae/interfaces/mcp_read.py"),
    Path("aegiscae/contracts/research_contracts.py"),
    Path("aegiscae/research/project.py"),
    Path("aegiscae/research/mutation_rules.py"),
    Path("aegiscae/research/mutation.py"),
    Path("aegiscae/research/budget.py"),
    Path("aegiscae/research/budget_rules.py"),
}
EXPECTED_PYTHON_FILES = PACKAGE_MARKERS | M01_MODULES

FORBIDDEN_PACKAGE_PATHS = {
    Path("abqpilot"),
    Path("abqjobpilot"),
    Path("aegiscae/legacy_compat"),
    Path("aegiscae/llm"),
    Path("aegiscae/gui"),
    Path("aegiscae/queue"),
    Path("aegiscae/mcp"),
}

FORBIDDEN_MODULE_NAMES = {
    "context.py",
    "workspace.py",
    "executor.py",
    "authorization.py",
    "policy.py",
    "registry.py",
    "workflow.py",
    "evidence.py",
    "commands.py",
    "jobs.py",
    "diagnostics.py",
    "odb.py",
    "inp.py",
    "cae.py",
    "json_cli.py",
    "mcp.py",
}


def skeleton_violations(src_root: Path) -> tuple[str, ...]:
    """Return package-skeleton violations relative to the supplied source root."""
    python_files = {
        path.relative_to(src_root)
        for path in src_root.rglob("*.py")
        if path.is_file()
    }
    violations = [
        f"unexpected Python module: {path.as_posix()}"
        for path in sorted(python_files - EXPECTED_PYTHON_FILES, key=str)
    ]
    violations.extend(
        f"missing authorized source file: {path.as_posix()}"
        for path in sorted(EXPECTED_PYTHON_FILES - python_files, key=str)
    )
    violations.extend(
        f"Python file is not a package marker: {path.as_posix()}"
        for path in sorted(python_files, key=str)
        if path.name != "__init__.py" and path not in M01_MODULES
    )
    violations.extend(
        f"forbidden package path: {path.as_posix()}"
        for path in sorted(FORBIDDEN_PACKAGE_PATHS, key=str)
        if (src_root / path).exists()
    )
    violations.extend(
        f"forbidden implementation module: {path.relative_to(src_root).as_posix()}"
        for path in sorted(src_root.rglob("*.py"), key=str)
        if path.name in FORBIDDEN_MODULE_NAMES
    )
    return tuple(violations)


def create_allowed_skeleton(src_root: Path) -> None:
    """Create controlled allowed paths below a pytest temporary directory."""
    for relative_path in EXPECTED_PYTHON_FILES:
        target = src_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('"""Temporary package marker."""\n', encoding="utf-8")


def test_real_repository_has_only_authorized_m01_source_files() -> None:
    violations = skeleton_violations(SRC_ROOT)
    assert not violations, (
        "M01 source surface violations:\n"
        + "\n".join(f"- {item}" for item in violations)
    )


def test_skeleton_checker_rejects_functional_module(tmp_path: Path) -> None:
    simulated_src = tmp_path / "src"
    create_allowed_skeleton(simulated_src)
    executor = simulated_src / "aegiscae" / "runtime" / "executor.py"
    executor.write_text('"""Forbidden simulated implementation."""\n', encoding="utf-8")

    violations = skeleton_violations(simulated_src)

    assert any("aegiscae/runtime/executor.py" in item for item in violations), (
        "skeleton checker accepted controlled negative path "
        "aegiscae/runtime/executor.py"
    )


def test_skeleton_checker_accepts_only_exact_bridge_locations(tmp_path: Path) -> None:
    create_allowed_skeleton(tmp_path)
    assert not skeleton_violations(tmp_path)
    misplaced = tmp_path / "aegiscae" / "runtime" / "af_evidence.py"
    misplaced.write_text('"""Misplaced adapter."""\n', encoding="utf-8")
    assert any("runtime/af_evidence.py" in item for item in skeleton_violations(tmp_path))


def test_skeleton_checker_rejects_second_mcp_server(tmp_path: Path) -> None:
    create_allowed_skeleton(tmp_path)
    extra = tmp_path / "aegiscae" / "interfaces" / "mcp_write.py"
    extra.write_text('"""Unauthorized second interface."""\n', encoding="utf-8")
    assert any("interfaces/mcp_write.py" in item for item in skeleton_violations(tmp_path))
