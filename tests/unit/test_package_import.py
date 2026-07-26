import sys

import aegiscae


def test_package_import_has_no_legacy_side_effects() -> None:
    assert aegiscae.__version__ == "0.0.0"
    assert "abqpilot" not in sys.modules
    assert "abqjobpilot" not in sys.modules
