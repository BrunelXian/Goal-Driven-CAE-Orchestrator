"""M03-B exposes only test composition, no new product or MCP execution seam."""

import ast

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files


def forbidden_port_calls(source):
    tree = ast.parse(source)
    forbidden = {"call", "owner", "spawn", "prepare", "issue_exact", "grant", "validate_run",
                 "resume_dispatch", "apply_reconciliation", "ExperimentStore", "ExecutionService"}
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)
            and (getattr(node.func, "attr", None) or getattr(node.func, "id", None)) in forbidden]


def test_real_test_port_cannot_prepare_grant_start_owner_or_call_generic_rpc():
    source = (REPO_ROOT / "tests/integration/m03b_support.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for name in ("AFTestPort", "CaptureReads"):
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
        assert not forbidden_port_calls(ast.unparse(node))
    assert "def submit(" not in source


def test_guard_rejects_each_privilege_in_a_port():
    for expression in ("client.call('submit', {})", "owner.spawn()", "owner.owner()",
                       "service.prepare()", "fixture.issue_exact()", "client.validate_run({})",
                       "ExperimentStore(context)", "ExecutionService(context, store)",
                       "client.resume_dispatch({})"):
        assert forbidden_port_calls(expression)


def test_fixture_modules_never_imported_by_product():
    for path in iter_python_files(SRC_ROOT):
        source = path.read_text(encoding="utf-8")
        assert "m03b_support" not in source and "m03b_child" not in source
    source = (REPO_ROOT / "tests/integration/m03b_support.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    port = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AFTestPort")
    submits = [n for n in ast.walk(port) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == "submit"]
    assert len(submits) == 1


def test_seven_read_capture_methods_have_no_write_surface():
    source = (REPO_ROOT / "tests/integration/m03b_support.py").read_text(encoding="utf-8")
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "CaptureReads")
    public = {n.name for n in node.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")}
    assert public == {"health", "project_view", "receipt", "run", "events", "validations", "diagnose"}
