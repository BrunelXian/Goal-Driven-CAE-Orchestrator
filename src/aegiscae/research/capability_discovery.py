"""Read explicit local distribution metadata without importing or contacting the backend."""
import ast
import hashlib
from pathlib import Path

from aegiscae.contracts.research_contracts import require


def local(path):
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts and not str(path).startswith("\\\\")
            and not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)), "LOCAL_PATH_REQUIRED")
    return path


def source(path):
    local(path)
    if not path.is_file():
        return None, None
    require(path.stat().st_size <= 131072, "METADATA_LIMIT")
    content = path.read_bytes()
    return ast.parse(content), hashlib.sha256(content).hexdigest()


def discover(spec):
    require(isinstance(spec, dict) and set(spec) == {"abaqus_launcher", "abqjobpilot_root"},
            "EXPLICIT_DISCOVERY_SCOPE_REQUIRED")
    result = dict(abaqus="UNKNOWN", abqjobpilot="UNKNOWN", version=None, public_tools=[],
                  metadata_sha256={}, service="BLOCKED_INTERFACE_UNVERIFIED", project="UNVERIFIED",
                  authorization="NOT_GRANTED", execution_authorized=False)
    try:
        if spec["abaqus_launcher"] is not None:
            launcher = local(spec["abaqus_launcher"])
            result["abaqus"] = "LAUNCHER_FILE_PRESENT" if launcher.is_file() else "MISSING_AT_SUPPLIED_PATH"
        if spec["abqjobpilot_root"] is not None:
            root = local(spec["abqjobpilot_root"]) / "abqjobpilot"
            tree, pin = source(root / "__init__.py")
            if tree is None:
                result["abqjobpilot"] = "MISSING_AT_SUPPLIED_PATH"
                return result
            result["abqjobpilot"] = "SOURCE_METADATA_PRESENT"
            result["metadata_sha256"]["package"] = pin
            for node in tree.body:
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    if any(isinstance(x, ast.Name) and x.id == "__version__" for x in node.targets):
                        result["version"] = node.value.value
            server, pin = source(root / "mcp/server.py")
            if server:
                result["metadata_sha256"]["server"] = pin
                result["public_tools"] = sorted(n.name for n in ast.walk(server) if isinstance(n, ast.FunctionDef)
                    and n.name.startswith("abq_") and any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                    and isinstance(d.func.value, ast.Name) and d.func.value.id == "server" and d.func.attr == "tool"
                    for d in n.decorator_list))
    except (OSError, SyntaxError, ValueError):
        result["diagnostic"] = "METADATA_UNREADABLE"
    return result
