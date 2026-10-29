"""Static tripwires for the M01-A read facade, not an OS security sandbox."""

from __future__ import annotations

import ast

import pytest

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files, parse_python_file
from test_forbidden_legacy_dependencies import ADAPTER_PATH
from test_research_boundary import permitted_store_sql
from test_proposal_boundary import proposal_sql
from test_continuation_boundary import continuation_sql
from test_main_runtime_boundary import runtime_sql

PUBLIC_READS = {
    "capabilities", "list_runs", "get_run", "get_receipt", "list_events",
    "get_validations", "get_diagnostic",
}
CLIENT_READS = {"health", "project_view", "run", "receipt", "events", "validations", "diagnose"}
WRITE_OR_LIFECYCLE = {
    "submit", "submit_run", "validate_run", "stop_service", "start_service",
    "start_supervisor", "stop_supervisor", "resume_dispatch", "pause_dispatch",
    "export_diagnostic", "get_or_create_project", "cancel", "enqueue", "execute",
    "apply", "set_project", "create_project",
}
IMPLICIT_ROOTS = {
    "recent_project", "get_recent_project", "load_recent_project", "from_cwd",
    "resolve_project_root", "get_default_project",
}
SAFE_EXCEPTION_FIELDS = {"code", "message", "retryable", "details"}


def boundary_violations(tree: ast.AST, display_path: str) -> tuple[str, ...]:
    """Reject known bypass patterns without granting general client execution."""
    violations: list[str] = []
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}

    def reject(node: ast.AST, reason: str) -> None:
        violations.append(f"{display_path}:{getattr(node, 'lineno', 1)}: {reason}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name in {"importlib", "builtins"} for alias in node.names):
                reject(node, "dynamic import/dispatch module")
        elif isinstance(node, ast.ImportFrom):
            if node.module in {"importlib", "builtins"}:
                reject(node, "dynamic import/dispatch module")
        elif isinstance(node, ast.Attribute):
            if node.attr == "call":
                reject(node, "raw .call forwarding")
            if (node.attr in WRITE_OR_LIFECYCLE or node.attr.startswith("apply_")) and not (
                node.attr == "execute" and (permitted_store_sql(tree, parents.get(node), display_path)
                                          or proposal_sql(tree, parents.get(node), display_path)
                                          or continuation_sql(tree, parents.get(node), display_path)
                                          or runtime_sql(tree, parents.get(node), display_path))
            ):
                reject(node, "write or lifecycle surface")
            if node.attr in IMPLICIT_ROOTS:
                reject(node, "implicit Project selection")
            if isinstance(node.value, ast.Name) and node.value.id == "client":
                parent = parents.get(node)
                endpoint_read = (
                    node.attr == "endpoint" and isinstance(node.ctx, ast.Load)
                    and not (isinstance(parent, ast.Call) and parent.func is node)
                )
                if display_path != ADAPTER_PATH or (
                    node.attr not in CLIENT_READS and not endpoint_read
                ):
                    reject(node, "client method outside exact read allowlist")
            if (
                isinstance(node.value, ast.Name) and node.value.id == "self"
                and node.attr in {"client", "service", "backend", "store", "operator"}
            ):
                reject(node, "raw AF object exposed on facade")
        elif isinstance(node, ast.Name) and node.id in IMPLICIT_ROOTS:
            reject(node, "implicit Project selection")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, (ast.Subscript, ast.Call)):
                reject(node, "dynamic callable dispatch")
            if isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec", "__import__", "globals", "locals"}:
                    reject(node, "dynamic import/dispatch builtin")
                if node.func.id == "getattr" and not (
                    len(node.args) >= 2 and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value in SAFE_EXCEPTION_FIELDS
                ):
                    reject(node, "dynamic attribute dispatch")
        elif isinstance(node, ast.ClassDef) and node.name == "EvidenceBridge":
            methods = [
                item for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            public = {item.name for item in methods if not item.name.startswith("_")}
            if public != PUBLIC_READS:
                reject(node, "public facade must contain exactly seven read operations")
            for method in methods:
                if method.name in PUBLIC_READS:
                    args = method.args.posonlyargs + method.args.args
                    required = args[:len(args) - len(method.args.defaults)]
                    required_names = {arg.arg for arg in required}
                    required_names.update(
                        arg.arg for arg, default in zip(
                            method.args.kwonlyargs, method.args.kw_defaults, strict=True
                        ) if default is None
                    )
                    if "binding" not in required_names:
                        reject(method, "explicit required binding missing")
                    if method.args.vararg or method.args.kwarg:
                        reject(method, "generic operation forwarding")
                if method.name == "__init__":
                    for part in ast.walk(method):
                        if isinstance(part, ast.Call):
                            target = part.func
                            name = target.id if isinstance(target, ast.Name) else (
                                target.attr if isinstance(target, ast.Attribute) else ""
                            )
                            if name in {"discover", "_discover", "discovery", "_discovery"}:
                                reject(part, "constructor performs discovery")
    return tuple(violations)


def test_real_repository_retains_read_only_af_boundary() -> None:
    violations = []
    for path in iter_python_files(SRC_ROOT):
        violations.extend(boundary_violations(
            parse_python_file(path), path.relative_to(REPO_ROOT).as_posix()
        ))
    assert not violations, "AF read boundary violations:\n" + "\n".join(violations)


@pytest.mark.parametrize("snippet", [
    "client.call(command, params)",
    "forward = client.call",
    "client.submit_run(run_id)",
    "client.validate_run(run_id)",
    "client.stop_service()",
    "client.export_diagnostic(run_id)",
    "client.apply_patch(patch)",
    "getattr(client, operation)(run_id)",
    "methods[operation](run_id)",
    "import importlib as loader\nloader.import_module(package)",
    "__import__(package)",
    "self.client = client",
    "client.endpoint()",
    "client.endpoint = replacement",
    "root = recent_project()",
    "root = project.get_recent_project()",
])
def test_boundary_guard_rejects_controlled_bypasses(snippet: str) -> None:
    assert boundary_violations(ast.parse(snippet), ADAPTER_PATH)


@pytest.mark.parametrize("method", sorted(CLIENT_READS))
def test_client_reads_are_allowed_only_inside_exact_adapter(method: str) -> None:
    tree = ast.parse(f"client.{method}()")
    assert not boundary_violations(tree, ADAPTER_PATH)
    assert boundary_violations(tree, "src/aegiscae/runtime/bridge.py")


def facade_snippet(binding: str = "binding", constructor: str = "pass") -> str:
    methods = "\n".join(
        f"    def {name}(self, {binding}):\n        pass" for name in sorted(PUBLIC_READS)
    )
    return f"class EvidenceBridge:\n    def __init__(self):\n        {constructor}\n{methods}\n"


def test_facade_guard_accepts_exact_reads_with_required_binding() -> None:
    assert not boundary_violations(ast.parse(facade_snippet()), ADAPTER_PATH)


@pytest.mark.parametrize("snippet", [
    facade_snippet("binding=None"),
    facade_snippet("project=None"),
    facade_snippet() + "    def submit(self, binding):\n        pass\n",
    facade_snippet(constructor="self._discovery(root)"),
    facade_snippet(constructor="discover(root)"),
])
def test_facade_guard_rejects_optional_binding_extra_method_and_eager_discovery(
    snippet: str,
) -> None:
    assert boundary_violations(ast.parse(snippet), ADAPTER_PATH)


def test_safe_exception_metadata_lookup_is_not_command_dispatch() -> None:
    assert not boundary_violations(ast.parse("getattr(exc, 'code', None)"), ADAPTER_PATH)


def test_endpoint_identity_metadata_is_only_read_in_adapter() -> None:
    tree = ast.parse("endpoint = client.endpoint")
    assert not boundary_violations(tree, ADAPTER_PATH)
    assert boundary_violations(tree, "src/aegiscae/contracts/af_evidence.py")
