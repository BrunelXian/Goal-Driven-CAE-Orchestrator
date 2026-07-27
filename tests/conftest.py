"""Read-only helpers shared by the architecture policy tests."""

from __future__ import annotations

import ast
import hashlib
import tomllib
from pathlib import Path
from typing import Any

TESTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TESTS_ROOT.parent
SRC_ROOT = REPO_ROOT / "src"
BASELINE_ROOT = REPO_ROOT / "docs" / "baseline"


def iter_python_files(root: Path) -> tuple[Path, ...]:
    """Return Python files below *root* without mutating the repository."""
    return tuple(sorted((path for path in root.rglob("*.py") if path.is_file()), key=str))


def parse_python_file(path: Path) -> ast.AST:
    """Parse a UTF-8 Python source file."""
    return ast.parse(path.read_text(encoding="utf-8"), filename=relative_to_repo(path))


def relative_to_repo(path: Path) -> str:
    """Return a stable repository-relative display path when possible."""
    candidate = path if path.is_absolute() else REPO_ROOT / path
    try:
        return candidate.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_pyproject() -> dict[str, Any]:
    """Read project metadata with the Python standard-library TOML parser."""
    with (REPO_ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def sha256_file(path: Path) -> str:
    """Hash the original file bytes without normalization."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
