"""Read-only proposed runtime inventory; never a copier, loader, or deployment.

Absolute source paths belong in a private task artifact. This module prints
nothing, imports no inventoried package and never executes inventoried bytes.
The caller must explicitly supply the four reviewed roots. Synthetic roots are
available solely for tests and are permanently labelled TEST_SYNTHETIC.
"""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat


REVIEWED_ROOTS = {
    "gd": "D:/Projects/Goal-Driven-CAE-Orchestrator/src/aegiscae",
    "af": "D:/Projects/abqjobpilot_dev/abqjobpilot",
    "python": "D:/Program Files/Python312",
    "pywin32": "D:/XianLab/envs/LangChainEnv/Lib/site-packages",
}
CODE_ROOT = "C:/Program Files/GDCAE Operator"
FIXED_INTERPRETER = "D:/XianLab/envs/LangChainEnv/Scripts/python.exe"
PYTHON_FILES = ("python.exe", "python312.dll", "python3.dll",
                "vcruntime140.dll", "vcruntime140_1.dll")
PYWIN32_FILES = ("win32/win32api.pyd", "win32/win32security.pyd",
                 "win32/_win32sysloader.pyd", "win32/lib/win32con.py",
                 "win32/lib/pywintypes.py", "win32/lib/pywin32_bootstrap.py",
                 "pywin32_system32/pywintypes312.dll")
EXCLUDED_DIRECTORIES = frozenset({"__pycache__", "site-packages", "test", "tests",
    "idle_test", "docs", "doc", "data", "credentials", "secrets", ".git", ".pytest_cache"})
MAX_ENTRIES = 20000
MAX_FILES = 10000
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024


class InventoryBlocked(ValueError):
    """Only a bounded fixed code is exposed; no paths or source bytes."""


def _need(condition, code):
    if not condition:
        raise InventoryBlocked(code)


def _safe_path(path):
    _need(type(path) in (str, Path) or isinstance(path, Path), "INVENTORY_ROOT_INVALID")
    raw = os.fspath(path)
    _need(type(raw) is str and len(raw) <= 512 and "\x00" not in raw
          and ".." not in raw.replace("\\", "/").split("/"), "INVENTORY_PATH_ESCAPE")
    path = Path(raw)
    _need(path.is_absolute(), "INVENTORY_ROOT_INVALID")
    for item in (*reversed(path.parents), path):
        value = item.stat(follow_symlinks=False)
        _need(not stat.S_ISLNK(value.st_mode)
              and not getattr(value, "st_file_attributes", 0) & 0x400, "INVENTORY_REPARSE_REJECTED")
    return path


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _signature(value):
    # Windows path stat synthesizes executable mode bits from the extension;
    # descriptor fstat does not. File type is comparable, DOS mode is not ACL.
    return (value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode), value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def _destination(value):
    path = PurePosixPath(value)
    _need(not path.is_absolute() and path.parts and ".." not in path.parts
          and "\\" not in value and ":" not in value, "INVENTORY_DESTINATION_INVALID")
    return path.as_posix()


def _inventory(roots, synthetic):
    _need(type(roots) is dict and set(roots) == set(REVIEWED_ROOTS)
          and type(synthetic) is bool, "INVENTORY_ROOT_SET_INVALID")
    if not synthetic:
        _need(all(isinstance(roots[k], (str, Path))
                  and str(Path(roots[k])).replace("\\", "/").casefold() == expected.casefold()
                  for k, expected in REVIEWED_ROOTS.items()), "INVENTORY_ROOT_NOT_REVIEWED")
    paths = {key: _safe_path(value) for key, value in roots.items()}
    _need(all(path.is_dir() for path in paths.values()), "INVENTORY_ROOT_INVALID")
    _need(len({str(p).casefold() for p in paths.values()}) == len(paths)
          and not any(a != b and (a.is_relative_to(b) or b.is_relative_to(a))
                      for a in paths.values() for b in paths.values()), "INVENTORY_ROOT_OVERLAP")
    records, destinations, count, total = [], set(), 0, 0
    signatures = {}

    def add(source, destination, component):
        nonlocal total
        _need(len(records) < MAX_FILES, "INVENTORY_FILE_LIMIT")
        source = _safe_path(source)
        _need(source.is_relative_to(paths[component]), "INVENTORY_PATH_ESCAPE")
        destination = _destination(destination)
        _need(destination.casefold() not in destinations, "INVENTORY_DESTINATION_COLLISION")
        before = source.stat(follow_symlinks=False)
        _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, "INVENTORY_REGULAR_FILE_REQUIRED")
        _need(0 <= before.st_size <= MAX_FILE_BYTES
              and (before.st_size > 0 or source.suffix.lower() == ".py")
              and total + before.st_size <= MAX_TOTAL_BYTES, "INVENTORY_SIZE_LIMIT")
        digest, observed = hashlib.sha256(), 0
        with source.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            # On Windows stat ctime may be creation time while fstat ctime is
            # metadata-change time. Compare each API's own stable ctime, and
            # all shared identity/content attributes across the two APIs.
            _need(_signature(opened)[:-1] == _signature(before)[:-1], "INVENTORY_SOURCE_CHANGED")
            while chunk := stream.read(1024 * 1024):
                observed += len(chunk)
                _need(observed <= before.st_size, "INVENTORY_SOURCE_CHANGED")
                digest.update(chunk)
            after = os.fstat(stream.fileno())
        _safe_path(source)
        current = source.stat(follow_symlinks=False)
        _need(observed == before.st_size and _signature(opened) == _signature(after)
              and _signature(before) == _signature(current), "INVENTORY_SOURCE_CHANGED")
        total += observed
        destinations.add(destination.casefold())
        signatures[source] = _signature(current)
        records.append({"component": component, "source_absolute": str(source),
                        "destination_relative": destination, "size": observed,
                        "sha256": digest.hexdigest()})

    def walk(directory, component, destination, suffixes, recursive):
        nonlocal count
        directory = _safe_path(directory)
        _need(directory.is_relative_to(paths[component]), "INVENTORY_PATH_ESCAPE")
        before = _signature(directory.stat(follow_symlinks=False))
        with os.scandir(directory) as entries:
            children = []
            for entry in entries:
                count += 1
                _need(count <= MAX_ENTRIES, "INVENTORY_ENTRY_LIMIT")
                children.append(entry.name)
        for name in sorted(children):
            child = directory / name
            value = child.stat(follow_symlinks=False)
            _need(not stat.S_ISLNK(value.st_mode)
                  and not getattr(value, "st_file_attributes", 0) & 0x400, "INVENTORY_REPARSE_REJECTED")
            if stat.S_ISDIR(value.st_mode):
                if name.casefold() in EXCLUDED_DIRECTORIES:
                    continue
                _need(recursive, "INVENTORY_UNEXPECTED_DIRECTORY")
                walk(child, component, destination + "/" + name, suffixes, recursive)
            elif child.suffix.lower() in suffixes:
                if name.casefold().startswith(("test_", "_test")) or name == "_ctypes_test.pyd":
                    continue
                add(child, destination + "/" + name, component)
        _need(before == _signature(directory.stat(follow_symlinks=False)), "INVENTORY_SOURCE_CHANGED")
        signatures[directory] = before

    for key, destination in (("gd", "code/aegiscae"), ("af", "code/abqjobpilot")):
        _need((paths[key] / "__init__.py").is_file(), "INVENTORY_PACKAGE_ROOT_REQUIRED")
        walk(paths[key], key, destination, {".py"}, True)
    for name in PYTHON_FILES:
        add(paths["python"] / name, "runtime/" + name, "python")
    walk(paths["python"] / "DLLs", "python", "runtime/DLLs", {".pyd", ".dll"}, False)
    walk(paths["python"] / "Lib", "python", "runtime/Lib", {".py"}, True)
    for name in PYWIN32_FILES:
        add(paths["pywin32"] / name, "runtime/Lib/site-packages/" + name, "pywin32")
    for path, signature in signatures.items():
        _safe_path(path)
        _need(signature == _signature(path.stat(follow_symlinks=False)), "INVENTORY_SOURCE_CHANGED")
    records.sort(key=lambda row: row["destination_relative"].casefold())
    result = {
        "schema": "gdcae-operator-frozen-inventory-v1",
        "source_kind": "TEST_SYNTHETIC" if synthetic else "EXPLICIT_REVIEWED_SOURCE_ROOTS",
        "status": "INVENTORIED_NOT_DEPLOYED", "runtime_qualification": "RUNTIME_NOT_LOAD_QUALIFIED",
        "roots": {key: str(path) for key, path in paths.items()}, "files": records,
        "file_count": len(records), "total_bytes": total,
        "inventory_sha256": hashlib.sha256(_canonical(records)).hexdigest(),
        "proposed_code_root": CODE_ROOT, "current_af_fixed_interpreter": FIXED_INTERPRETER,
        "fixed_interpreter_gate": "BLOCKED_FIXED_INTERPRETER_OUTSIDE_CODE_ROOT",
        "runtime_version": "CPYTHON_312_LAYOUT_DECLARATION_NOT_EXECUTED",
        "pywin32_loading": "BOOTSTRAP_AND_SYSLOADER_INVENTORIED_NOT_LOADED",
        "excluded": sorted(EXCLUDED_DIRECTORIES) + ["NON_PY_SOURCE", "TEST_NAMED_FILES", "PTH_FILES"],
        "limitations": ["INVENTORY_IS_NOT_SIGNATURE_OR_OS_CUSTODY_PROOF",
                        "DLL_IMPORT_GRAPH_AND_ABI_NOT_QUALIFIED",
                        "RESOURCE_AND_DYNAMIC_IMPORT_CLOSURE_NOT_QUALIFIED",
                        "AF_FIXED_INTERPRETER_AND_PROTECTED_CODE_ROOT_REQUIRE_RECONCILIATION",
                        "NO_SITE_PTH_BOOTSTRAP_EXECUTED"],
        "copied": False, "installed": False, "runtime_executed": False,
        "deployment_authorized": False, "execution_authorized": False,
    }
    return result


def freeze_inventory(roots, *, synthetic=False):
    """Return a bounded inventory for explicit roots; caller may save privately.

    No implicit discovery, user-directory enumeration, binaries loaded or files
    written. The production mode accepts only the four exact reviewed roots.
    """
    try:
        return _inventory(roots, synthetic)
    except OSError:
        raise InventoryBlocked("INVENTORY_SOURCE_UNAVAILABLE") from None
