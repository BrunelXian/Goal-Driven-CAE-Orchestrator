"""Reject legacy package dependencies, imports, submodules, and vendoring."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files, parse_python_file, read_pyproject

LEGACY_PACKAGES = {"abqpilot", "abqjobpilot"}
FORBIDDEN_PATHS = {
    Path(".gitmodules"),
    Path("src/abqpilot"),
    Path("src/abqjobpilot"),
    Path("vendor/abqpilot"),
    Path("vendor/abqjobpilot"),
}


def flatten_strings(value: Any) -> Iterable[str]:
    """Yield string values from nested TOML structures."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from flatten_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from flatten_strings(nested)


def legacy_import_violations(tree: ast.AST, display_path: str) -> tuple[str, ...]:
    """Return forbidden legacy imports found through Python AST nodes."""
    violations: list[str] = []
    for node in ast.walk(tree):
        imported_roots: set[str] = set()
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        for imported_root in sorted(imported_roots & LEGACY_PACKAGES):
            violations.append(
                f"{display_path}:{node.lineno}: forbidden legacy import {imported_root}"
            )
    return tuple(violations)


def pyproject_legacy_violations(project_data: dict[str, Any]) -> tuple[str, ...]:
    """Inspect only dependency-bearing pyproject sections."""
    dependency_sections = (
        project_data.get("project", {}).get("dependencies", []),
        project_data.get("project", {}).get("optional-dependencies", {}),
        project_data.get("build-system", {}).get("requires", []),
    )
    violations = []
    for dependency in flatten_strings(dependency_sections):
        normalized = dependency.casefold().replace("\\", "/")
        if any(package in normalized for package in LEGACY_PACKAGES):
            violations.append(f"pyproject.toml: forbidden legacy dependency {dependency!r}")
        elif (
            "brunelxian/abq_job_pilot" in normalized
            or "git+" in normalized
            and ("abq" in normalized and "pilot" in normalized)
        ):
            violations.append(f"pyproject.toml: forbidden legacy Git dependency {dependency!r}")
    return tuple(violations)


def test_real_repository_has_no_legacy_dependency_or_import() -> None:
    violations = list(pyproject_legacy_violations(read_pyproject()))
    for path in iter_python_files(SRC_ROOT):
        violations.extend(legacy_import_violations(parse_python_file(path), path.relative_to(REPO_ROOT).as_posix()))
    violations.extend(
        f"forbidden legacy repository path exists: {path.as_posix()}"
        for path in sorted(FORBIDDEN_PATHS, key=str)
        if (REPO_ROOT / path).exists()
    )

    assert not violations, "legacy dependency violations:\n" + "\n".join(
        f"- {item}" for item in violations
    )


def test_legacy_import_checker_rejects_controlled_ast_snippet() -> None:
    tree = ast.parse("from abqpilot.solver import run\n")
    violations = legacy_import_violations(tree, "controlled-negative/legacy_import.py")

    assert violations, (
        "legacy import checker accepted controlled-negative/legacy_import.py: "
        "from abqpilot.solver import run"
    )
