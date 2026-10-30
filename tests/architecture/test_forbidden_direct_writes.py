"""Reject direct production write primitives in Milestone 0 source."""

from __future__ import annotations

import ast
import textwrap

import pytest

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files, parse_python_file
from test_research_boundary import permitted_mutation_write, permitted_store_creation
from test_proposal_boundary import proposal_creation
from test_continuation_boundary import continuation_creation
from test_main_runtime_boundary import runtime_creation

PATH_WRITE_METHODS = {
    "write_text",
    "write_bytes",
    "touch",
    "mkdir",
    "unlink",
    "rename",
    "replace",
}

QUALIFIED_WRITE_CALLS = {
    "shutil.copy",
    "shutil.copy2",
    "shutil.copytree",
    "shutil.move",
    "shutil.rmtree",
    "os.replace",
    "os.rename",
    "os.remove",
    "os.unlink",
    "os.mkdir",
    "os.makedirs",
}

# Exact validated string block, not a general .replace or path exemption.
ROD_ORIGIN_BLOCK = r'''
for key in ("package_path", "service_path", "supervisor_path"):
    require(type(origin[key]) is str and 0 < len(origin[key]) <= 1024
            and not any(c in origin[key] for c in "\x00\n\r"), "FAKE_ORIGIN_MISMATCH")
package = origin["package_path"].replace("\\", "/").rstrip("/")
require(origin["service_path"].replace("\\", "/") == package + "/execution/service.py"
        and origin["supervisor_path"].replace("\\", "/") == package + "/execution/supervisor.py",
        "FAKE_ORIGIN_MISMATCH")
'''


def permitted_rod_string_normalization(tree, node, display_path):
    if display_path != "src/aegiscae/research/rod_evidence.py":
        return False
    functions = [item for item in tree.body if isinstance(item, ast.FunctionDef)
                 and item.name == "check_fake_evidence"]
    if len(functions) != 1:
        return False
    expected = ast.dump(ast.parse(ROD_ORIGIN_BLOCK), include_attributes=False)
    body = functions[0].body
    for index in range(len(body) - 2):
        block = ast.Module(body=body[index:index + 3], type_ignores=[])
        if ast.dump(block, include_attributes=False) == expected:
            calls = [item for item in ast.walk(block) if isinstance(item, ast.Call)
                     and isinstance(item.func, ast.Attribute) and item.func.attr == "replace"]
            return len(calls) == 3 and any(item is node for item in calls)
    return False


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


def open_mode(call: ast.Call) -> ast.AST | None:
    if len(call.args) >= 2:
        return call.args[1]
    return next(
        (keyword.value for keyword in call.keywords if keyword.arg == "mode"),
        None,
    )


def write_violations(tree: ast.AST, display_path: str) -> tuple[str, ...]:
    """Return AST-backed direct-write violations."""
    violations: list[str] = []
    aliases = import_aliases(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        unresolved = dotted_name(node.func)
        target = resolve_alias(unresolved, aliases)
        method_name = node.func.attr if isinstance(node.func, ast.Attribute) else None

        if (permitted_store_creation(tree, node, display_path)
                or permitted_mutation_write(tree, node, display_path)
                or proposal_creation(tree, node, display_path)
                or continuation_creation(tree, node, display_path)
                or runtime_creation(tree, node, display_path)
                or permitted_rod_string_normalization(tree, node, display_path)):
            continue

        if target in {"open", "builtins.open"}:
            mode = open_mode(node)
            if mode is not None:
                if not isinstance(mode, ast.Constant) or not isinstance(mode.value, str):
                    violations.append(
                        f"{display_path}:{node.lineno}: open mode must be a read-only literal"
                    )
                elif any(flag in mode.value for flag in "wax+"):
                    violations.append(
                        f"{display_path}:{node.lineno}: write-capable open mode {mode.value!r}"
                    )
        elif method_name == "open":
            mode = node.args[0] if node.args else next(
                (keyword.value for keyword in node.keywords if keyword.arg == "mode"), None)
            if mode is not None and (not isinstance(mode, ast.Constant)
                    or not isinstance(mode.value, str) or any(flag in mode.value for flag in "wax+")):
                violations.append(f"{display_path}:{node.lineno}: unapproved path open mode")
        if method_name in PATH_WRITE_METHODS:
            violations.append(
                f"{display_path}:{node.lineno}: forbidden path write method {method_name}"
            )
        if target in QUALIFIED_WRITE_CALLS:
            violations.append(
                f"{display_path}:{node.lineno}: forbidden direct write call {target}"
            )
    return tuple(violations)


def test_real_repository_has_no_direct_write_primitive() -> None:
    violations: list[str] = []
    for path in iter_python_files(SRC_ROOT):
        display_path = path.relative_to(REPO_ROOT).as_posix()
        violations.extend(write_violations(parse_python_file(path), display_path))

    assert not violations, "direct-write policy violations:\n" + "\n".join(
        f"- {item}" for item in violations
    )


@pytest.mark.parametrize(
    "snippet",
    [
        'from pathlib import Path\nPath("result.json").write_text("{}")\n',
        (
            'with open("result.json", "w") as stream:\n'
            '    stream.write("{}")\n'
        ),
    ],
)
def test_write_checker_rejects_controlled_negative_snippets(snippet: str) -> None:
    violations = write_violations(
        ast.parse(snippet),
        "controlled-negative/direct_write.py",
    )
    assert violations, (
        "direct-write checker accepted controlled-negative/direct_write.py:\n"
        + snippet
    )


def test_write_checker_allows_explicit_read_only_open() -> None:
    tree = ast.parse('with open("input.txt", "r") as stream:\n    stream.read()\n')
    assert not write_violations(tree, "controlled-negative/read_only.py")


def rod_tree(block=ROD_ORIGIN_BLOCK, name="check_fake_evidence"):
    return ast.parse(f"def {name}():\n" + textwrap.indent(block.strip(), "    "))


def test_rod_string_normalization_exact_block_is_not_a_file_write():
    assert not write_violations(rod_tree(), "src/aegiscae/research/rod_evidence.py")


@pytest.mark.parametrize("block", [
    ROD_ORIGIN_BLOCK.replace("type(origin[key]) is str", "True"),
    ROD_ORIGIN_BLOCK.replace("type(origin[key]) is str", "isinstance(origin[key], str)"),
    ROD_ORIGIN_BLOCK.replace('"supervisor_path"):', '"other_path"):'),
    ROD_ORIGIN_BLOCK.replace('package =', 'origin["package_path"] = Path("x")\npackage ='),
    ROD_ORIGIN_BLOCK + '\nPath("x").replace("y")\n',
    ROD_ORIGIN_BLOCK + '\norigin["package_path"].replace("y")\n',
])
def test_rod_string_exception_rejects_changed_guard_or_extra_write(block):
    assert write_violations(rod_tree(block), "src/aegiscae/research/rod_evidence.py")


@pytest.mark.parametrize("path,name", [
    ("src/aegiscae/research/other.py", "check_fake_evidence"),
    ("src/aegiscae/research/rod_evidence.py", "other_function"),
])
def test_rod_string_exception_is_module_and_function_specific(path, name):
    assert write_violations(rod_tree(name=name), path)


def test_rod_string_exception_does_not_accept_nested_function():
    tree = ast.parse("def outer():\n" + textwrap.indent(
        ast.unparse(rod_tree()), "    "))
    assert write_violations(tree, "src/aegiscae/research/rod_evidence.py")
