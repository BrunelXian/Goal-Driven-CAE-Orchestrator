"""Reject implicit CWD authority and hard-coded machine paths."""

from __future__ import annotations

import ast
import re

import pytest

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files, parse_python_file

ENVIRONMENT_PATH_KEYS = {"HOME", "USERPROFILE"}
WINDOWS_ABSOLUTE_PATH = re.compile(r"(?i)[a-z]:[\\/]")
USER_HOME_PATH = re.compile(r"(?i)^/(?:home|users)/[^/\s]+")


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return None


def import_aliases(tree: ast.AST) -> dict[str, str]:
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
    if not name:
        return None
    first, separator, rest = name.partition(".")
    resolved = aliases.get(first, first)
    return f"{resolved}.{rest}" if separator else resolved


def string_literal(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def path_and_cwd_violations(tree: ast.AST, display_path: str) -> tuple[str, ...]:
    """Return implicit-path and hard-coded-path AST violations."""
    aliases = import_aliases(tree)
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if WINDOWS_ABSOLUTE_PATH.search(node.value) or USER_HOME_PATH.search(node.value):
                violations.append(
                    f"{display_path}:{getattr(node, 'lineno', 1)}: "
                    f"hard-coded machine path {node.value!r}"
                )
        elif isinstance(node, ast.Call):
            target = resolve_alias(dotted_name(node.func), aliases)
            if target in {"pathlib.Path.cwd", "os.getcwd"}:
                violations.append(
                    f"{display_path}:{node.lineno}: implicit CWD call {target}"
                )
            if target == "pathlib.Path" and not node.args and not node.keywords:
                violations.append(
                    f"{display_path}:{node.lineno}: zero-argument Path() is implicit CWD"
                )
            if target in {"os.getenv", "os.environ.get"} and node.args:
                key = string_literal(node.args[0])
                if key in ENVIRONMENT_PATH_KEYS:
                    violations.append(
                        f"{display_path}:{node.lineno}: environment path authority {key}"
                    )
        elif isinstance(node, ast.Subscript):
            target = resolve_alias(dotted_name(node.value), aliases)
            key = string_literal(node.slice)
            if target == "os.environ" and key in ENVIRONMENT_PATH_KEYS:
                violations.append(
                    f"{display_path}:{node.lineno}: environment path authority {key}"
                )
    return tuple(violations)


def test_real_repository_has_no_implicit_or_machine_path_authority() -> None:
    violations: list[str] = []
    for path in iter_python_files(SRC_ROOT):
        display_path = path.relative_to(REPO_ROOT).as_posix()
        violations.extend(path_and_cwd_violations(parse_python_file(path), display_path))

    assert not violations, "path/CWD policy violations:\n" + "\n".join(
        f"- {item}" for item in violations
    )


@pytest.mark.parametrize(
    "snippet",
    [
        "from pathlib import Path\nroot = Path.cwd()\n",
        'root = r"D:\\Projects\\AbqPilot-v2"\n',
    ],
)
def test_path_checker_rejects_controlled_negative_snippets(snippet: str) -> None:
    violations = path_and_cwd_violations(
        ast.parse(snippet),
        "controlled-negative/path_authority.py",
    )
    assert violations, (
        "path checker accepted controlled-negative/path_authority.py:\n" + snippet
    )
