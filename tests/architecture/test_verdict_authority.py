"""Prevent presentation and client layers from creating machine truth."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files, parse_python_file

MACHINE_VERDICTS = {
    "AUTHORIZED",
    "EXECUTION_STARTED",
    "EXECUTION_COMPLETED",
    "SOLVER_FAILED",
    "ARTIFACT_STALE",
    "ODB_READABLE",
    "ODB_VALID",
    "REQUIRED_FIELDS_PRESENT",
    "PHYSICS_WARNING",
    "PHYSICS_REJECTED",
    "EVIDENCE_FROZEN",
}

PROTECTED_LAYERS = {
    "interfaces",
    "reports",
    "reporting",
    "clients",
    "llm",
    "gui",
    "mcp",
    "skills",
}


def string_verdicts(node: ast.AST) -> set[str]:
    """Collect protected verdict string literals below an AST node."""
    return {
        nested.value
        for nested in ast.walk(node)
        if isinstance(nested, ast.Constant)
        and isinstance(nested.value, str)
        and nested.value in MACHINE_VERDICTS
    }


def target_names(node: ast.AST) -> set[str]:
    """Collect simple assignment target names."""
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for element in node.elts:
            names.update(target_names(element))
        return names
    if isinstance(node, ast.Attribute):
        return {node.attr}
    return set()


def verdict_violations(tree: ast.AST, display_path: str) -> tuple[str, ...]:
    """Return forbidden machine-verdict construction sites."""
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names = set().union(*(target_names(target) for target in node.targets))
            verdicts = string_verdicts(node.value)
            protected_names = names & MACHINE_VERDICTS
            if protected_names or verdicts:
                detail = sorted(protected_names | verdicts)
                violations.append(
                    f"{display_path}:{node.lineno}: machine verdict assignment {detail}"
                )
        elif isinstance(node, ast.AnnAssign):
            names = target_names(node.target) & MACHINE_VERDICTS
            verdicts = string_verdicts(node.value) if node.value else set()
            if names or verdicts:
                violations.append(
                    f"{display_path}:{node.lineno}: machine verdict assignment "
                    f"{sorted(names | verdicts)}"
                )
        elif isinstance(node, ast.Return):
            verdicts = string_verdicts(node.value) if node.value else set()
            if verdicts:
                violations.append(
                    f"{display_path}:{node.lineno}: machine verdict return "
                    f"{sorted(verdicts)}"
                )
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=True):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and key.value.casefold() in {"status", "verdict"}
                ):
                    verdicts = string_verdicts(value)
                    if verdicts:
                        violations.append(
                            f"{display_path}:{node.lineno}: machine verdict dictionary "
                            f"{sorted(verdicts)}"
                        )
        elif isinstance(node, ast.Call):
            verdicts = set().union(
                *(string_verdicts(value) for value in (*node.args, *[item.value for item in node.keywords]))
            )
            if verdicts:
                violations.append(
                    f"{display_path}:{node.lineno}: machine verdict construction "
                    f"{sorted(verdicts)}"
                )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in MACHINE_VERDICTS:
                violations.append(
                    f"{display_path}:{node.lineno}: machine verdict definition {node.name}"
                )
    return tuple(violations)


def is_protected_layer(path: Path, src_root: Path) -> bool:
    relative_parts = {part.casefold() for part in path.relative_to(src_root).parts}
    return bool(relative_parts & PROTECTED_LAYERS)


def test_real_repository_protected_layers_do_not_create_verdicts() -> None:
    violations: list[str] = []
    for path in iter_python_files(SRC_ROOT):
        if not is_protected_layer(path, SRC_ROOT):
            continue
        display_path = path.relative_to(REPO_ROOT).as_posix()
        violations.extend(verdict_violations(parse_python_file(path), display_path))

    assert not violations, "machine-verdict authority violations:\n" + "\n".join(
        f"- {item}" for item in violations
    )


@pytest.mark.parametrize(
    "snippet",
    [
        'RESULT = "ODB_VALID"\n',
        (
            "def approve():\n"
            '    return {"verdict": "AUTHORIZED"}\n'
        ),
    ],
)
def test_verdict_checker_rejects_controlled_interface_snippets(snippet: str) -> None:
    violations = verdict_violations(
        ast.parse(snippet),
        "aegiscae/interfaces/controlled_negative.py",
    )
    assert violations, (
        "verdict checker accepted controlled interface machine truth:\n" + snippet
    )
