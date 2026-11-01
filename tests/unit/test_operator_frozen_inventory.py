"""Synthetic files only; never imports inventoried code or executes binaries."""

import hashlib
import importlib.util
from pathlib import Path

import pytest


PATH = Path(__file__).resolve().parents[2] / "operator_deployment/frozen_inventory.py"
SPEC = importlib.util.spec_from_file_location("frozen_inventory_test_subject", PATH)
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


@pytest.fixture
def roots(tmp_path):
    result = {key: tmp_path / key for key in inventory.REVIEWED_ROOTS}
    for root in result.values():
        root.mkdir()
    for component in ("gd", "af"):
        (result[component] / "__init__.py").write_bytes(b"")
        (result[component] / "module.py").write_bytes(b"raise RuntimeError('MUST_NOT_IMPORT')\n")
    for name in inventory.PYTHON_FILES:
        (result["python"] / name).write_bytes(b"SYNTHETIC_NOT_EXECUTABLE_" + name.encode())
    (result["python"] / "DLLs").mkdir()
    (result["python"] / "DLLs" / "synthetic.pyd").write_bytes(b"SYNTHETIC_NOT_LOADABLE")
    (result["python"] / "Lib").mkdir()
    (result["python"] / "Lib" / "synthetic.py").write_bytes(b"SYNTHETIC_ONLY\n")
    for name in inventory.PYWIN32_FILES:
        path = result["pywin32"] / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"SYNTHETIC_" + name.encode())
    return result


def test_inventory_is_deterministic_declarative_and_does_not_copy_or_execute(roots):
    before = {p: p.read_bytes() for root in roots.values() for p in root.rglob("*") if p.is_file()}
    first = inventory.freeze_inventory(roots, synthetic=True)
    assert inventory.freeze_inventory(roots, synthetic=True) == first
    assert first["source_kind"] == "TEST_SYNTHETIC"
    assert first["runtime_qualification"] == "RUNTIME_NOT_LOAD_QUALIFIED"
    assert first["fixed_interpreter_gate"] == "BLOCKED_FIXED_INTERPRETER_OUTSIDE_CODE_ROOT"
    assert all(first[key] is False for key in ("copied", "installed", "runtime_executed",
                                              "deployment_authorized", "execution_authorized"))
    assert first["file_count"] == len(before)
    assert first["total_bytes"] == sum(map(len, before.values()))
    assert len({r["destination_relative"] for r in first["files"]}) == len(before)
    assert all(r["sha256"] == hashlib.sha256(before[Path(r["source_absolute"])]).hexdigest()
               for r in first["files"])
    assert before == {p: p.read_bytes() for root in roots.values() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("directory", sorted(inventory.EXCLUDED_DIRECTORIES))
def test_excluded_directory_not_read_or_included(roots, directory, monkeypatch):
    excluded = roots["python"] / "Lib" / directory
    excluded.mkdir()
    private = excluded / "do_not_read.py"
    private.write_bytes(b"synthetic-private-placeholder")
    opened = []
    original = Path.open

    def checked(self, *args, **kwargs):
        opened.append(self)
        assert self != private
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", checked)
    result = inventory.freeze_inventory(roots, synthetic=True)
    assert private not in opened
    assert all(r["source_absolute"] != str(private) for r in result["files"])


def test_explicit_pywin32_subset_does_not_absorb_other_packages_pth_or_dlls(roots):
    for name in ("private.json", "extra.py", "pywin32.pth", "win32/extra.pyd",
                 "pywin32_system32/pythoncom312.dll"):
        (roots["pywin32"] / name).write_bytes(b"EXCLUDED_SYNTHETIC")
    result = inventory.freeze_inventory(roots, synthetic=True)
    selected = [Path(r["source_absolute"]).relative_to(roots["pywin32"]).as_posix()
                for r in result["files"] if r["component"] == "pywin32"]
    assert sorted(selected) == sorted(inventory.PYWIN32_FILES)


def test_source_data_test_named_files_and_binary_assets_excluded(roots):
    for name in ("private.json", "unknown.dll", "fixture.dat", "test_secret.py"):
        (roots["af"] / name).write_bytes(b"EXCLUDED_SYNTHETIC")
    result = inventory.freeze_inventory(roots, synthetic=True)
    assert {Path(r["source_absolute"]).name for r in result["files"] if r["component"] == "af"} == {
        "__init__.py", "module.py"}


def test_extra_root_cannot_expand_inventory(roots):
    roots["extra"] = roots["gd"]
    with pytest.raises(inventory.InventoryBlocked, match="INVENTORY_ROOT_SET_INVALID"):
        inventory.freeze_inventory(roots, synthetic=True)


def test_production_refuses_unreviewed_root_before_any_stat(roots, monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("Unreviewed source must not be examined")
    monkeypatch.setattr(Path, "stat", forbidden)
    with pytest.raises(inventory.InventoryBlocked, match="INVENTORY_ROOT_NOT_REVIEWED"):
        inventory.freeze_inventory(roots)


@pytest.mark.parametrize("change", ["relative", "parent", "overlap", "missing"])
def test_invalid_or_missing_roots_fail_closed(roots, change):
    if change == "relative":
        roots["gd"] = "relative"
    elif change == "parent":
        roots["gd"] = roots["gd"] / ".." / "gd"
    elif change == "overlap":
        roots["gd"] = roots["af"]
    else:
        roots["gd"] = roots["gd"] / "missing"
    with pytest.raises(inventory.InventoryBlocked):
        inventory.freeze_inventory(roots, synthetic=True)


@pytest.mark.parametrize("name", ["MAX_FILES", "MAX_ENTRIES", "MAX_FILE_BYTES", "MAX_TOTAL_BYTES"])
def test_limits_fail_closed(roots, monkeypatch, name):
    monkeypatch.setattr(inventory, name, 1)
    with pytest.raises(inventory.InventoryBlocked):
        inventory.freeze_inventory(roots, synthetic=True)


def test_dll_inventory_rejects_extra_directory_expansion(roots):
    (roots["python"] / "DLLs" / "unreviewed").mkdir()
    with pytest.raises(inventory.InventoryBlocked, match="INVENTORY_UNEXPECTED_DIRECTORY"):
        inventory.freeze_inventory(roots, synthetic=True)


def test_missing_required_pywin32_dependency_blocks(roots):
    (roots["pywin32"] / "win32/_win32sysloader.pyd").unlink()
    with pytest.raises(inventory.InventoryBlocked, match="INVENTORY_SOURCE_UNAVAILABLE"):
        inventory.freeze_inventory(roots, synthetic=True)


def test_reparse_attribute_injection_blocks_without_real_link_or_process(roots, monkeypatch):
    original = Path.stat

    class Reparse:
        st_mode = 0o100644
        st_file_attributes = 0x400

    def replaced(self, *args, **kwargs):
        if self == roots["gd"] / "module.py":
            return Reparse()
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", replaced)
    with pytest.raises(inventory.InventoryBlocked, match="INVENTORY_REPARSE_REJECTED"):
        inventory.freeze_inventory(roots, synthetic=True)


def test_mutation_during_open_rejected(roots, monkeypatch):
    original = Path.open
    target = roots["gd"] / "module.py"
    once = False

    def changed(self, *args, **kwargs):
        nonlocal once
        if self == target and args and args[0] == "rb" and not once:
            once = True
            with original(self, "ab") as stream:
                stream.write(b"MUTATED")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", changed)
    with pytest.raises(inventory.InventoryBlocked, match="INVENTORY_SOURCE_CHANGED"):
        inventory.freeze_inventory(roots, synthetic=True)
