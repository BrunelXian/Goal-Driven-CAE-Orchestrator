"""Reject deferred surfaces except the exact public AF seam and M01-C SDK imports."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files, parse_python_file
from test_forbidden_legacy_dependencies import permitted_discovery_import

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

MCP_INTERFACE_PATH = "src/aegiscae/interfaces/mcp_read.py"
MCP_SDK_IMPORTS = {
    "mcp.server.lowlevel": {"Server"},
    "mcp.server.stdio": {"stdio_server"},
    "mcp.types": {"Tool", "ToolAnnotations", "ListToolsResult", "CallToolResult", "TextContent"},
}


def permitted_mcp_sdk_import(node: ast.AST, display_path: str) -> bool:
    """SDK use is a named import allowlist, never a generic client permission."""
    return (
        display_path == MCP_INTERFACE_PATH
        and isinstance(node, ast.ImportFrom)
        and node.level == 0
        and node.module in MCP_SDK_IMPORTS
        and bool(node.names)
        and all(alias.name in MCP_SDK_IMPORTS[node.module] for alias in node.names)
    )


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
            if (
                permitted_discovery_import(tree, node, display_path)
                or permitted_mcp_sdk_import(node, display_path)
            ):
                continue
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


@pytest.mark.parametrize("snippet", [
    "from mcp.server.lowlevel import Server",
    "from mcp.server.stdio import stdio_server",
    "from mcp.types import ToolAnnotations",
    "from mcp.types import Tool, ListToolsResult, CallToolResult, TextContent",
])
def test_exact_mcp_sdk_imports_are_allowed_only_at_the_read_interface(snippet: str) -> None:
    tree = ast.parse(snippet)
    assert not surface_import_violations(tree, MCP_INTERFACE_PATH)
    assert surface_import_violations(tree, "src/aegiscae/runtime/mcp_read.py")


@pytest.mark.parametrize("snippet", [
    "import mcp",
    "from mcp import ClientSession",
    "from mcp.client.stdio import stdio_client",
    "from mcp.server.lowlevel import *",
    "from mcp.server.lowlevel import Server, unexpected",
    "from mcp.server.mcpserver import MCPServer",
    "from mcp.server.fastmcp import FastMCP",
    "import importlib\nimportlib.import_module('mcp.server.lowlevel')",
    "from agents import Agent",
    "from aegiscae.agent import Planner",
])
def test_mcp_sdk_exception_rejects_unapproved_imports(snippet: str) -> None:
    assert surface_import_violations(ast.parse(snippet), MCP_INTERFACE_PATH)
