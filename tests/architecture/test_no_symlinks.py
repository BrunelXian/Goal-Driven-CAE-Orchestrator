"""Reject symlinks and junction-like paths in critical repository regions."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

from conftest import BASELINE_ROOT, SRC_ROOT, TESTS_ROOT, relative_to_repo

PROTECTED_ROOTS = (
    SRC_ROOT,
    TESTS_ROOT / "fixtures",
    BASELINE_ROOT,
)


def pathlib_detects_link(path: Path) -> bool:
    """Detect symlinks and junctions supported by the running Python version."""
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def find_link_paths(
    root: Path,
    detector: Callable[[Path], bool] = pathlib_detects_link,
) -> tuple[Path, ...]:
    """Find link-like paths without following them."""
    if detector(root):
        return (root,)
    if not root.exists():
        return ()
    links: list[Path] = []
    pending = [root]
    while pending:
        current = pending.pop()
        for child in current.iterdir():
            if detector(child):
                links.append(child)
            elif child.is_dir():
                pending.append(child)
    return tuple(sorted(links, key=str))


def test_real_repository_critical_regions_contain_no_links() -> None:
    violations = [
        relative_to_repo(path)
        for root in PROTECTED_ROOTS
        for path in find_link_paths(root)
    ]
    assert not violations, "critical repository path links:\n" + "\n".join(
        f"- {item}" for item in violations
    )


def test_link_checker_rejects_mocked_symlink_without_platform_privilege(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "simulated-link"
    candidate.write_text("controlled negative\n", encoding="utf-8")
    original_is_symlink = Path.is_symlink

    def mocked_is_symlink(path: Path) -> bool:
        return path == candidate or original_is_symlink(path)

    with patch.object(Path, "is_symlink", autospec=True, side_effect=mocked_is_symlink):
        violations = find_link_paths(tmp_path)

    assert candidate in violations, (
        "symlink checker accepted controlled-negative/simulated-link"
    )
