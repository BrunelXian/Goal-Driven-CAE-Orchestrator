"""Permit one lazy public AF seam; reject private imports and vendoring."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files, parse_python_file, read_pyproject

LEGACY_PACKAGES = {"abqpilot", "abqjobpilot"}
ADAPTER_PATH = "src/aegiscae/adapters/abaqus/af_evidence.py"
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
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from flatten_strings(nested)


def permitted_discovery_import(tree: ast.AST, node: ast.AST, display_path: str) -> bool:
    """Recognize only the reviewed lazy import, never an entire package exception."""
    if display_path == "src/aegiscae/research/rod_local_port.py":
        if not (isinstance(node, ast.ImportFrom) and node.level == 0
                and node.module == "abqjobpilot.product_rod" and len(node.names) == 1
                and node.names[0].name in {"RodProduct", "validate_local_reader"}
                and node.names[0].asname is None):
            return False
        expected = "__init__" if node.names[0].name == "RodProduct" else "validate"
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LocalReadPort"]
        return len(classes) == 1 and any(isinstance(n, ast.FunctionDef) and n.name == expected
            and node in n.body for n in classes[0].body)
    if display_path != ADAPTER_PATH or not isinstance(tree, ast.Module):
        return False
    if not (
        isinstance(node, ast.ImportFrom)
        and node.module == "abqjobpilot.service_discovery"
        and node.level == 0
        and len(node.names) == 1
        and node.names[0].name == "discover"
        and node.names[0].asname is None
    ):
        return False
    seams = [
        item for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == "_discover"
    ]
    if len(seams) != 1:
        return False
    seam = seams[0]
    args = seam.args
    if (
        seam.decorator_list or args.posonlyargs or args.kwonlyargs or args.defaults
        or args.vararg or args.kwarg
        or [arg.arg for arg in args.args] != ["explicit_project_root"]
    ):
        return False
    body = seam.body[1:] if ast.get_docstring(seam) is not None else seam.body
    if len(body) != 2 or body[0] is not node:
        return False
    expected_return = ast.parse("return discover(explicit_project_root)").body[0]
    return ast.dump(body[1], include_attributes=False) == ast.dump(
        expected_return, include_attributes=False
    )


def legacy_import_violations(tree: ast.AST, display_path: str) -> tuple[str, ...]:
    """Return forbidden legacy imports found through Python AST nodes."""
    violations: list[str] = []
    for node in ast.walk(tree):
        imported_roots: set[str] = set()
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        if permitted_discovery_import(tree, node, display_path):
            continue
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


LAZY_SEAM = (
    "def _discover(explicit_project_root):\n"
    "    from abqjobpilot.service_discovery import discover\n"
    "    return discover(explicit_project_root)\n"
)


def test_legacy_checker_accepts_only_exact_lazy_public_seam() -> None:
    assert not legacy_import_violations(ast.parse(LAZY_SEAM), ADAPTER_PATH)
    assert legacy_import_violations(ast.parse(LAZY_SEAM), "src/aegiscae/runtime/bridge.py")


@pytest.mark.parametrize("snippet", [
    "from abqjobpilot.service_discovery import discover\n",
    "from abqjobpilot.service_discovery import discover as connect\n",
    "from abqjobpilot.service import Service\n",
    "from abqjobpilot.store import Store\n",
    "from abqjobpilot.backend import Backend\n",
    "from abqjobpilot.operator import Operator\n",
    LAZY_SEAM.replace("discover(explicit_project_root)", "discover()"),
    LAZY_SEAM.replace("_discover(explicit_project_root)", "_discover(explicit_project_root=None)"),
    LAZY_SEAM.replace("import discover", "import discover, Service"),
])
def test_legacy_checker_rejects_private_eager_and_implicit_seams(snippet: str) -> None:
    assert legacy_import_violations(ast.parse(snippet), ADAPTER_PATH)


@pytest.mark.parametrize("dependency", ["abqjobpilot>=1", "abqpilot", "git+https://host/abq-pilot"])
def test_legacy_dependency_guard_traverses_dependency_section_tuple(dependency: str) -> None:
    assert pyproject_legacy_violations({"project": {"dependencies": [dependency]}})


@pytest.mark.parametrize("name,module,function,path", [
    ("StandardOperator", "abqjobpilot.product_standard", "validate", "src/aegiscae/research/rod_local_port.py"),
    ("ExperimentStore", "abqjobpilot.execution.store", "validate", "src/aegiscae/research/rod_local_port.py"),
    ("RodProduct", "abqjobpilot.product_rod", "execute", "src/aegiscae/research/rod_local_port.py"),
    ("RodProduct", "abqjobpilot.product_rod", "__init__", "src/aegiscae/research/rod_local_project.py"),
])
def test_d7_local_import_exception_does_not_grant_authority(name, module, function, path):
    tree = ast.parse(f"class LocalReadPort:\n    def {function}(self):\n        from {module} import {name}\n")
    assert legacy_import_violations(tree, path)
