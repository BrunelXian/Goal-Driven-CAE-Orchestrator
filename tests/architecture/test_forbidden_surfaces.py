"""Reject deferred product surfaces from the Milestone 0 source tree."""

from __future__ import annotations

import ast
from pathlib import Path

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files, parse_python_file

FORBIDDEN_SURFACE_NAMES = {
    "mcp",
    "skill",
    "skills",
    "gui",
    "ui",
    "llm",
    "agent",
    "agents",
    "queue",
    "worker",
    "workers",
    "database",
    "db",
    "server",
    "client",
    "clients",
    "legacy_compat",
    "abqpilot",
    "abqjobpilot",
}


def module_has_forbidden_surface(module_name: str) -> bool:
    return bool(set(module_name.casefold().split(".")) & FORBIDDEN_SURFACE_NAMES)


def surface_path_violations(src_root: Path) -> tuple[str, ...]:
    """Return forbidden package, directory, and module names."""
    violations: list[str] = []
    for path in src_root.rglob("*"):
        relative = path.relative_to(src_root)
        names = [
            component[:-3] if component.endswith(".py") else component
            for component in relative.parts
        ]
        forbidden = sorted(set(name.casefold() for name in names) & FORBIDDEN_SURFACE_NAMES)
        if forbidden:
            violations.append(
                f"{relative.as_posix()}: forbidden deferred surface {forbidden[0]}"
            )
    return tuple(violations)


def surface_import_violations(tree: ast.AST, display_path: str) -> tuple[str, ...]:
    """Return forbidden static and dynamic module imports."""
    violations: list[str] = []
    import_module_aliases = {"importlib.import_module"}
    importlib_aliases = {"importlib"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    importlib_aliases.add(alias.asname or "importlib")
                if module_has_forbidden_surface(alias.name):
                    violations.append(
                        f"{display_path}:{node.lineno}: forbidden surface import {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        import_module_aliases.add(alias.asname or alias.name)
            if node.module and module_has_forbidden_surface(node.module):
                violations.append(
                    f"{display_path}:{node.lineno}: forbidden surface import {node.module}"
                )
        elif isinstance(node, ast.Call):
            call_name = None
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in importlib_aliases
            ):
                call_name = f"importlib.{node.func.attr}"
            if call_name in import_module_aliases and node.args:
                module = node.args[0]
                if (
                    isinstance(module, ast.Constant)
                    and isinstance(module.value, str)
                    and module_has_forbidden_surface(module.value)
                ):
                    violations.append(
                        f"{display_path}:{node.lineno}: forbidden dynamic import "
                        f"{module.value}"
                    )
    return tuple(violations)


def test_real_repository_has_no_deferred_surface() -> None:
    violations = list(surface_path_violations(SRC_ROOT))
    for path in iter_python_files(SRC_ROOT):
        display_path = path.relative_to(REPO_ROOT).as_posix()
        violations.extend(surface_import_violations(parse_python_file(path), display_path))

    assert not violations, "deferred-surface violations:\n" + "\n".join(
        f"- {item}" for item in violations
    )


def test_surface_path_checker_rejects_simulated_llm_package(tmp_path: Path) -> None:
    simulated_src = tmp_path / "src"
    llm_marker = simulated_src / "aegiscae" / "llm" / "__init__.py"
    llm_marker.parent.mkdir(parents=True)
    llm_marker.write_text('"""Controlled negative LLM package."""\n', encoding="utf-8")

    violations = surface_path_violations(simulated_src)

    assert any("aegiscae/llm" in item for item in violations), (
        "surface checker accepted controlled-negative/aegiscae/llm"
    )


def test_surface_import_checker_rejects_dynamic_import() -> None:
    tree = ast.parse('import importlib\nimportlib.import_module("aegiscae.llm.planner")\n')
    violations = surface_import_violations(tree, "controlled-negative/dynamic_import.py")
    assert violations, "surface checker accepted dynamic import of aegiscae.llm.planner"
