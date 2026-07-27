"""Protect canonical baseline names, bytes, hashes, and registration."""

from __future__ import annotations

from pathlib import Path

from conftest import BASELINE_ROOT, relative_to_repo, sha256_file

EXPECTED_BASELINES = {
    "AegisCAE Runtime 项目计划书.md": (
        "9a89a5ad661a80a69ec159124066e5b34ed6dc74de9295336f426b17079e7448"
    ),
    "LEGACY_ABQJOBPILOT_SUMMARY.md": (
        "f938b243ff438c6e7587f9337be4c4730e4bddeed78a874a5bd4e0f2a1128dfb"
    ),
    "LEGACY_ABQPILOT_SUMMARY.md": (
        "d1685d26a208f15ad772335fcd927c0c22f31f0fe8901613d9a7b02ac9591a43"
    ),
    "LEGACY_MIGRATION_DECISIONS.md": (
        "d90e35737ee86a3aa77b67afa5d6becf4977a371f35517317615db351e3603c2"
    ),
}

REGISTER_NAME = "BASELINE_REGISTER.md"


def baseline_hash_matches(path: Path, expected_hash: str) -> bool:
    """Compare raw file bytes with a frozen SHA-256 value."""
    return sha256_file(path) == expected_hash


def baseline_violations(baseline_root: Path) -> tuple[str, ...]:
    """Return canonical baseline and register violations."""
    violations: list[str] = []
    markdown_files = {
        path.name: path
        for path in baseline_root.glob("*.md")
        if path.is_file()
    }
    expected_names = set(EXPECTED_BASELINES) | {REGISTER_NAME}
    actual_names = set(markdown_files)

    for name in sorted(expected_names - actual_names):
        violations.append(f"missing baseline file: docs/baseline/{name}")
    for name in sorted(actual_names - expected_names):
        violations.append(f"unexpected baseline file: docs/baseline/{name}")
    if len(actual_names) != 5:
        violations.append(
            f"docs/baseline must contain exactly 5 Markdown files, found {len(actual_names)}"
        )

    for name, expected_hash in EXPECTED_BASELINES.items():
        path = markdown_files.get(name)
        if path is not None and not baseline_hash_matches(path, expected_hash):
            violations.append(f"baseline hash mismatch: docs/baseline/{name}")

    register = markdown_files.get(REGISTER_NAME)
    if register is None:
        return tuple(violations)

    register_text = register.read_text(encoding="utf-8")
    register_lower = register_text.casefold()
    for name, expected_hash in EXPECTED_BASELINES.items():
        if name not in register_text:
            violations.append(f"register omits filename: {name}")
        if expected_hash not in register_lower:
            violations.append(f"register omits SHA-256 for: {name}")
        registered_row = next(
            (
                line.casefold()
                for line in register_text.splitlines()
                if name.casefold() in line.casefold()
                and expected_hash in line.casefold()
            ),
            "",
        )
        if not registered_row.endswith("| no | no |"):
            violations.append(
                f"register row does not declare Content changed/Runtime input = NO: {name}"
            )
    if "runtime input: no" not in register_lower:
        violations.append("register does not declare Runtime input: NO")
    if "1. `legacy_migration_decisions.md`" not in register_lower:
        violations.append(
            "register does not give LEGACY_MIGRATION_DECISIONS.md highest precedence"
        )
    return tuple(violations)


def test_real_repository_baseline_is_byte_preserved_and_registered() -> None:
    violations = baseline_violations(BASELINE_ROOT)
    assert not violations, "baseline integrity violations:\n" + "\n".join(
        f"- {item}" for item in violations
    )


def test_hash_checker_rejects_one_byte_mutation(tmp_path: Path) -> None:
    name, expected_hash = next(iter(EXPECTED_BASELINES.items()))
    source = BASELINE_ROOT / name
    mutated = tmp_path / name
    original_bytes = source.read_bytes()
    mutated.write_bytes(original_bytes + b"\x00")

    assert not baseline_hash_matches(mutated, expected_hash), (
        "raw-byte baseline checker accepted a one-byte mutation in "
        f"{relative_to_repo(source)}"
    )
