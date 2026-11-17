"""Verify a pinned local deployment against its full file inventory."""
import hashlib
import json
import sys
from importlib.metadata import version
from pathlib import Path


def local(value):
    path = Path(value)
    if (not path.is_absolute() or path.drive.startswith("\\\\") or ".." in path.parts or
            any(p.is_symlink() or p.is_junction() for p in (path, *path.parents))):
        raise ValueError("LOCAL_UNREDIRECTED_PATH_REQUIRED")
    return path


def sha(path):
    return hashlib.sha256(local(path).read_bytes()).hexdigest()


def verify(root, pin, kind):
    root = local(root)
    path = root / "manifest.json"
    if sha(path) != pin:
        raise ValueError("MANIFEST_MISMATCH")
    manifest = json.loads(path.read_bytes())
    if manifest["kind"] != kind or manifest["version"] != "0.3.1":
        raise ValueError("WRONG_DISTRIBUTION")
    files = manifest["files"]
    actual = {local(p).relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != set(files) | {"manifest.json"} or any(sha(root / key) != digest for key, digest in files.items()):
        raise ValueError("PACKAGE_INVENTORY_MISMATCH")
    return manifest


def runtime():
    if not (sys.flags.isolated and sys.dont_write_bytecode and sys.version_info[:3] == (3, 12, 10)
            and version("mcp") == "2.3.0"):
        raise ValueError("BOUND_RUNTIME_MISMATCH")
