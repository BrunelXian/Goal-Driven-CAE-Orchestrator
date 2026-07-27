"""Reject production process execution entry points in Milestone 0 source."""

from __future__ import annotations

import ast

import pytest

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files, parse_python_file

RAW_LAUNCHER_NAMES = {
    "run_raw_command",
    "execute_raw_command",
    "raw_launcher",
    "execute_controlled_abaqus_command",
    "run_next_job",
}


def dotted_name(node: ast.AST) -> str | None:
    """Return a dotted name for a simple Name/Attribute expression."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return None


def import_aliases(tree: ast.AST) -> dict[str, str]:
    """Map local import names to their fully qualified targets."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".", maxsplit=1)[0]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def resolve_alias(name: str | None, aliases: dict[str, str]) -> str | None:
    """Resolve the leading component of a dotted imported name."""
    if not name:
        return None
    first, separator, rest = name.partition(".")
    resolved = aliases.get(first, first)
    return f"{resolved}.{rest}" if separator else resolved


def is_forbidden_execution_target(name: str) -> bool:
    """Return whether a resolved call target is a process execution primitive."""
    if name.startswith("subprocess."):
        return True
    if name in {"os.system", "os.popen"}:
        return True
    if name.startswith("os.spawn") or name.startswith("os.exec"):
        return True
    if name in {
        "asyncio.create_subprocess_exec",
        "asyncio.create_subprocess_shell",
        "multiprocessing.Process",
    }:
        return True
    return name.rsplit(".", maxsplit=1)[-1] in RAW_LAUNCHER_NAMES


def execution_violations(tree: ast.AST, display_path: str) -> tuple[str, ...]:
    """Return AST-backed execution-policy violations."""
    violations: list[str] = []
    aliases = import_aliases(tree)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess" or alias.name.startswith("subprocess."):
                    violations.append(
                        f"{display_path}:{node.lineno}: subprocess import is forbidden"
                    )
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "subprocess" or node.module.startswith("subprocess."):
                violations.append(
                    f"{display_path}:{node.lineno}: subprocess import is forbidden"
                )
            for alias in node.names:
                target = f"{node.module}.{alias.name}"
                if is_forbidden_execution_target(target):
                    violations.append(
                        f"{display_path}:{node.lineno}: forbidden execution import {target}"
                    )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in RAW_LAUNCHER_NAMES:
                violations.append(
                    f"{display_path}:{node.lineno}: public raw launcher {node.name}"
                )
        elif isinstance(node, ast.Call):
            target = resolve_alias(dotted_name(node.func), aliases)
            if target and is_forbidden_execution_target(target):
                violations.append(
                    f"{display_path}:{node.lineno}: forbidden execution call {target}"
                )
            if any(
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            ):
                violations.append(f"{display_path}:{node.lineno}: shell=True is forbidden")
    return tuple(violations)


def test_real_repository_has_no_process_execution_entry_point() -> None:
    violations: list[str] = []
    for path in iter_python_files(SRC_ROOT):
        display_path = path.relative_to(REPO_ROOT).as_posix()
        violations.extend(execution_violations(parse_python_file(path), display_path))

    assert not violations, "execution policy violations:\n" + "\n".join(
        f"- {item}" for item in violations
    )


@pytest.mark.parametrize(
    "snippet",
    [
        'import subprocess\nsubprocess.run(["solver"])\n',
        'import os\nos.system("solver")\n',
        'from subprocess import Popen\nPopen(["solver"], shell=True)\n',
    ],
)
def test_execution_checker_rejects_controlled_negative_snippets(snippet: str) -> None:
    violations = execution_violations(
        ast.parse(snippet),
        "controlled-negative/execution.py",
    )
    assert violations, (
        "execution checker accepted controlled-negative/execution.py:\n" + snippet
    )
