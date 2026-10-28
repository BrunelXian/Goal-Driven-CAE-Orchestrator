"""Enforce the package DAG with the exact M01-C public read-bridge exception."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from conftest import SRC_ROOT, iter_python_files, parse_python_file

ALLOWED_AEGISCAE_TARGETS = {
    "root": set(),
    "contracts": set(),
    "validation": {"contracts"},
    "runtime": {"contracts", "validation"},
    "adapters": {"contracts", "validation"},
    "interfaces": {"contracts", "runtime"},
    "research": {"contracts"},
}


def permitted_mcp_bridge_import(node: ast.AST, display_path: str) -> bool:
    """Only the approved STDIO module can import the public EvidenceBridge class."""
    return (
        display_path == "aegiscae/interfaces/mcp_read.py"
        and isinstance(node, ast.ImportFrom)
        and node.level == 0
        and node.module == "aegiscae.adapters.abaqus.af_evidence"
        and len(node.names) == 1
        and node.names[0].name == "EvidenceBridge"
    )


def source_layer(path: Path, src_root: Path) -> str:
    relative = path.relative_to(src_root)
    return relative.parts[1] if len(relative.parts) > 2 else "root"


def package_parts(path: Path, src_root: Path) -> tuple[str, ...]:
    relative = path.relative_to(src_root).with_suffix("")
    parts = relative.parts
    return parts[:-1] if parts[-1] != "__init__" else parts[:-1]


def import_targets(node: ast.Import | ast.ImportFrom, package: tuple[str, ...]) -> tuple[str, ...]:
    """Resolve absolute and relative AST imports to module-like targets."""
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)

    if node.level:
        climb = node.level - 1
        base = list(package[: len(package) - climb]) if climb <= len(package) else []
        if node.module:
            target = ".".join(base + node.module.split("."))
            targets = [target]
            if target in {"aegiscae", "aegiscae.runtime"}:
                targets.extend(
                    f"{target}.{alias.name}"
                    for alias in node.names
                    if alias.name.islower()
                )
            return tuple(targets)
        return tuple(".".join(base + [alias.name]) for alias in node.names)

    if not node.module:
        return ()
    targets = [node.module]
    if node.module in {"aegiscae", "aegiscae.runtime"}:
        targets.extend(
            f"{node.module}.{alias.name}"
            for alias in node.names
            if alias.name.islower()
        )
    return tuple(targets)


def import_direction_violations(
    path: Path,
    tree: ast.AST,
    src_root: Path,
) -> tuple[str, ...]:
    """Return dependency-direction violations for one source module."""
    layer = source_layer(path, src_root)
    package = package_parts(path, src_root)
    display_path = path.relative_to(src_root).as_posix()
    violations: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        targets = import_targets(node, package)
        if path.name == "__init__.py":
            violations.append(
                f"{display_path}:{node.lineno}: package marker import is forbidden"
            )
        for target in targets:
            top_level = target.split(".", maxsplit=1)[0]
            if layer == "contracts" and top_level not in sys.stdlib_module_names:
                violations.append(
                    f"{display_path}:{node.lineno}: contracts may import standard library only: "
                    f"{target}"
                )
            if top_level != "aegiscae":
                continue
            parts = target.split(".")
            target_layer = parts[1] if len(parts) > 1 else "root"
            if target_layer == layer:
                continue
            if (
                target_layer not in ALLOWED_AEGISCAE_TARGETS[layer]
                and not permitted_mcp_bridge_import(node, display_path)
            ):
                violations.append(
                    f"{display_path}:{node.lineno}: forbidden dependency "
                    f"{layer} -> {target_layer} ({target})"
                )
            if (
                layer == "interfaces"
                and target.startswith("aegiscae.runtime.")
            ):
                violations.append(
                    f"{display_path}:{node.lineno}: interfaces may use only the "
                    f"runtime public facade ({target})"
                )
    return tuple(violations)


def root_package_violations(path: Path, tree: ast.Module) -> tuple[str, ...]:
    """Restrict the root package to a docstring and static version assignment."""
    violations: list[str] = []
    for index, node in enumerate(tree.body):
        if (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__version__"
            and isinstance(node.value, ast.Constant)
            and node.value.value == "0.0.0"
        ):
            continue
        violations.append(
            f"{path.relative_to(SRC_ROOT).as_posix()}:{node.lineno}: "
            "root package may contain only its docstring and static __version__"
        )
    return tuple(violations)


def test_real_repository_respects_frozen_dependency_direction() -> None:
    violations: list[str] = []
    for path in iter_python_files(SRC_ROOT):
        tree = parse_python_file(path)
        violations.extend(import_direction_violations(path, tree, SRC_ROOT))
        if path == SRC_ROOT / "aegiscae" / "__init__.py":
            assert isinstance(tree, ast.Module)
            violations.extend(root_package_violations(path, tree))

    assert not violations, "dependency-direction violations:\n" + "\n".join(
        f"- {item}" for item in violations
    )


def test_runtime_to_adapter_import_is_rejected(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    path = src_root / "aegiscae" / "runtime" / "example.py"
    path.parent.mkdir(parents=True)
    path.write_text(
        "from aegiscae.adapters.abaqus import commands\n",
        encoding="utf-8",
    )
    violations = import_direction_violations(
        path,
        ast.parse(path.read_text(encoding="utf-8")),
        src_root,
    )
    assert violations, (
        "dependency checker accepted controlled-negative/runtime/example.py "
        "importing aegiscae.adapters"
    )


def test_adapter_to_runtime_import_is_rejected(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    path = src_root / "aegiscae" / "adapters" / "abaqus" / "example.py"
    path.parent.mkdir(parents=True)
    path.write_text(
        "from aegiscae.runtime import executor\n",
        encoding="utf-8",
    )
    violations = import_direction_violations(
        path,
        ast.parse(path.read_text(encoding="utf-8")),
        src_root,
    )
    assert violations, (
        "dependency checker accepted controlled-negative/adapters/abaqus/example.py "
        "importing aegiscae.runtime"
    )


def test_exact_mcp_module_may_import_only_public_evidence_bridge(tmp_path: Path) -> None:
    path = tmp_path / "aegiscae" / "interfaces" / "mcp_read.py"
    tree = ast.parse("from aegiscae.adapters.abaqus.af_evidence import EvidenceBridge")
    assert not import_direction_violations(path, tree, tmp_path)


@pytest.mark.parametrize("module, snippet", [
    ("other.py", "from aegiscae.adapters.abaqus.af_evidence import EvidenceBridge"),
    ("mcp_read.py", "from aegiscae.adapters.abaqus.af_evidence import _discover"),
    ("mcp_read.py", "from aegiscae.adapters.abaqus.af_evidence import *"),
    ("mcp_read.py", "from aegiscae.adapters.abaqus.af_evidence import EvidenceBridge, _discover"),
    ("mcp_read.py", "import aegiscae.adapters.abaqus.af_evidence"),
    ("mcp_read.py", "from aegiscae.adapters.abaqus import commands"),
])
def test_mcp_bridge_exception_does_not_open_other_adapter_access(
    tmp_path: Path, module: str, snippet: str,
) -> None:
    path = tmp_path / "aegiscae" / "interfaces" / module
    assert import_direction_violations(path, ast.parse(snippet), tmp_path)
