"""The new inventory must not copy private identifiers or ambiguous test nodes."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "integration"))
from g2_safe_checks import decode_inventory, encode_inventory, project_skip, validate_nodes  # noqa: E402

ALLOWED = {"tests/unit/test_example.py": {"test_negative", "test_case"}}


def test_inventory_preserves_distinct_cases_without_parameter_text():
    nodes = ["tests/unit/test_example.py::test_negative[changed_input]"]
    result = validate_nodes(nodes, ALLOWED)
    assert result == ["tests/unit/test_example.py::test_negative[case_00001]"]
    assert validate_nodes(result, ALLOWED) == result


def test_inventory_projects_long_legitimate_parameters_before_storage():
    nodes = ["tests/unit/test_example.py::test_case[" + "fixture_" * 200 + "]",
             "tests/unit/test_example.py::test_case[second]"]
    assert validate_nodes(nodes, ALLOWED) == [
        "tests/unit/test_example.py::test_case[case_00001]",
        "tests/unit/test_example.py::test_case[case_00002]",
    ]


def test_skip_projection_never_repeats_unknown_reason():
    result = project_skip("tests/unit/test_example.py::test_case[private_parameter]",
                          "arbitrary private failure text", ALLOWED)
    assert result == {"test_ref": "tests/unit/test_example.py::test_case",
                      "reason_code": "UNCLASSIFIED_SKIP"}


def test_skip_projection_known_disabled_gate():
    result = project_skip("tests/unit/test_example.py::test_case",
                          "Skipped: M01-C fresh TEST root and explicit live opt-in required", ALLOWED)
    assert result["reason_code"] == "M01C_LIVE_OPTIN_DISABLED"


def test_large_inventory_uses_bounded_individual_records():
    nodes = [f"tests/unit/test_example.py::test_case[case_{i:05d}]" for i in range(1, 2001)]
    body = encode_inventory(nodes, ALLOWED)
    assert len(body) > 65536 and max(map(len, body.splitlines())) < 65536
    assert decode_inventory(body, ALLOWED) == nodes


@pytest.mark.parametrize("body", [
    b'{"schema":"g2-node-inventory-v2"}\n{"node":"unapproved::test_case"}\n',
    b'{"schema":"g2-node-inventory-v2"}\n{"node":"x","node":"y"}\n',
    b'{"schema":"other"}\n{}\n',
    b'x' * (12 * 1024 * 1024 + 1),
], ids=["unknown_source", "duplicate_key", "unknown_schema", "oversized"])
def test_inventory_decode_rejects_untrusted_records(body):
    with pytest.raises(ValueError):
        decode_inventory(body, ALLOWED)


@pytest.mark.parametrize("nodes", [
    [],
    ["tests/unit/test_example.py::test_case"] * 2,
    ["outside.py::test_case"],
    ["tests/unit/test_example.py::test_unknown"],
    ["tests/unit/test_example.py::TestUnknown::test_case"],
    ["tests/unit/test_example.py::test_case[" + "x" * 16384 + "]"],
    ["tests/unit/test_example.py::test_case\nsecret"],
    ["tests/unit/test_example.py::test_case[" + "codex" + "://threads/fixture]"],
    ["tests/unit/test_example.py::test_case[" + "-".join(["0" * 8, "0" * 4,
                                                       "0" * 4, "0" * 4, "0" * 12]) + "]"],
])
def test_inventory_rejects_ambiguous_or_sensitive_nodes(nodes):
    with pytest.raises(ValueError):
        validate_nodes(nodes, ALLOWED)
