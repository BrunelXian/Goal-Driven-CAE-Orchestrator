"""Protect the distinction between test fixtures and physical evidence."""

from __future__ import annotations

import re
from pathlib import Path

from conftest import REPO_ROOT, TESTS_ROOT

FIXTURES_ROOT = TESTS_ROOT / "fixtures"
POLICY_PATH = FIXTURES_ROOT / "README.md"
TRUTHY_EVIDENCE_METADATA = re.compile(
    r"(?im)^\s*"
    r"(?:physical_evidence_eligible|physical evidence eligible|"
    r"real_physical_evidence|production_evidence)"
    r"\s*:\s*(?:true|yes)\s*(?:#.*)?$"
)

NEGATION_MARKERS = {"不是", "not", "no", "不能", "不得"}


def line_has_terms_and_negation(text: str, terms: tuple[str, ...]) -> bool:
    """Check semantic token co-occurrence with an explicit negation marker."""
    for line in text.casefold().splitlines():
        if all(term.casefold() in line for term in terms) and any(
            marker in line for marker in NEGATION_MARKERS
        ):
            return True
    return False


def metadata_claims_physical_evidence(text: str) -> bool:
    """Return whether fixture metadata claims production or physical evidence."""
    return TRUTHY_EVIDENCE_METADATA.search(text) is not None


def fixture_policy_violations(fixtures_root: Path) -> tuple[str, ...]:
    """Return fixture directory and policy violations."""
    violations: list[str] = []
    files = sorted(path for path in fixtures_root.iterdir() if path.is_file())
    allowed = {"README.md", "synthetic_workflow_port.py"}
    unexpected = [path for path in files if path.name not in allowed]
    violations.extend(
        f"tests/fixtures/{path.name}: fixture is outside the exact synthetic helper allowlist"
        for path in unexpected
    )

    policy = fixtures_root / "README.md"
    if not policy.is_file():
        return tuple(violations + ["tests/fixtures/README.md: policy is missing"])

    text = policy.read_text(encoding="utf-8")
    lowered = text.casefold()
    if "synthetic" not in lowered and "test-only" not in lowered:
        violations.append(
            "tests/fixtures/README.md: fixtures are not identified as synthetic/test-only"
        )
    semantic_requirements = {
        ("abaqus", "execution", "evidence"): "Abaqus execution evidence",
        ("odb", "validity", "evidence"): "ODB validity evidence",
        ("physical", "evidence"): "physical evidence",
        ("mock", "pass", "runtime", "production", "pass"): "mock versus production PASS",
    }
    for terms, label in semantic_requirements.items():
        if not line_has_terms_and_negation(text, terms):
            violations.append(
                f"tests/fixtures/README.md: missing negative policy for {label}"
            )
    eligible_line = next(
        (
            line.casefold()
            for line in text.splitlines()
            if "physical evidence eligible" in line.casefold()
        ),
        "",
    )
    if "no" not in eligible_line:
        violations.append(
            "tests/fixtures/README.md: physical evidence eligible must default to NO"
        )
    if metadata_claims_physical_evidence(text):
        violations.append(
            "tests/fixtures/README.md: policy contains truthy physical-evidence metadata"
        )
    return tuple(violations)


def test_workflow_fixture_exception_does_not_allow_other_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(POLICY_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "synthetic_workflow_port.py").write_text('"""TEST_ONLY helper."""', encoding="utf-8")
    assert not fixture_policy_violations(tmp_path)
    (tmp_path / "real_receipt.json").write_text("{}", encoding="utf-8")
    assert fixture_policy_violations(tmp_path)


def test_real_repository_fixture_policy_denies_evidence_authority() -> None:
    violations = fixture_policy_violations(FIXTURES_ROOT)
    assert not violations, "fixture evidence policy violations:\n" + "\n".join(
        f"- {item}" for item in violations
    )
    assert POLICY_PATH.relative_to(REPO_ROOT).as_posix() == "tests/fixtures/README.md"


def test_fixture_metadata_checker_rejects_truthy_claim(tmp_path: Path) -> None:
    metadata = tmp_path / "fixture.yaml"
    metadata.write_text("physical_evidence_eligible: true\n", encoding="utf-8")

    assert metadata_claims_physical_evidence(
        metadata.read_text(encoding="utf-8")
    ), "fixture metadata checker accepted controlled-negative/fixture.yaml"
