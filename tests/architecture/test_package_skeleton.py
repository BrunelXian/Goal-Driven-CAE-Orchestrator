"""Freeze the deliberately empty Milestone 0 package surface."""

from __future__ import annotations

from pathlib import Path

from conftest import SRC_ROOT

EXPECTED_PYTHON_FILES = {
    Path("aegiscae/__init__.py"),
    Path("aegiscae/contracts/__init__.py"),
    Path("aegiscae/runtime/__init__.py"),
    Path("aegiscae/validation/__init__.py"),
    Path("aegiscae/interfaces/__init__.py"),
    Path("aegiscae/adapters/__init__.py"),
    Path("aegiscae/adapters/abaqus/__init__.py"),
}

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
        f"missing package marker: {path.as_posix()}"
        for path in sorted(EXPECTED_PYTHON_FILES - python_files, key=str)
    )
    violations.extend(
        f"Python file is not a package marker: {path.as_posix()}"
        for path in sorted(python_files, key=str)
        if path.name != "__init__.py"
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


def create_empty_skeleton(src_root: Path) -> None:
    """Create a controlled package skeleton below a pytest temporary directory."""
    for relative_path in EXPECTED_PYTHON_FILES:
        target = src_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('"""Temporary package marker."""\n', encoding="utf-8")


def test_real_repository_has_exact_empty_package_skeleton() -> None:
    violations = skeleton_violations(SRC_ROOT)
    assert not violations, (
        "Milestone 0 package skeleton violations:\n"
        + "\n".join(f"- {item}" for item in violations)
    )


def test_skeleton_checker_rejects_functional_module(tmp_path: Path) -> None:
    simulated_src = tmp_path / "src"
    create_empty_skeleton(simulated_src)
    executor = simulated_src / "aegiscae" / "runtime" / "executor.py"
    executor.write_text('"""Forbidden simulated implementation."""\n', encoding="utf-8")

    violations = skeleton_violations(simulated_src)

    assert any("aegiscae/runtime/executor.py" in item for item in violations), (
        "skeleton checker accepted controlled negative path "
        "aegiscae/runtime/executor.py"
    )
