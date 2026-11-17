"""Keep the narrow, project-bound MCP exception independent of legacy violations."""
import ast

import pytest

from conftest import REPO_ROOT, SRC_ROOT, parse_python_file
from test_af_read_boundary import boundary_violations
from test_dependency_direction import import_direction_violations, permitted_fixture_import
from test_forbidden_direct_writes import write_violations
from test_forbidden_execution_calls import execution_violations
from test_forbidden_surfaces import surface_import_violations
from test_research_boundary import research_violations


@pytest.mark.parametrize("module", [
    "interfaces/fixture_scope.py", "interfaces/mcp_scoped.py",
    "research/scoped_fixture.py", "research/scoped_fixture_port.py", "research/scoped_fixture_rules.py",
])
def test_fixture_modules_remain_inside_named_boundaries(module):
    path = SRC_ROOT / "aegiscae" / module
    tree = parse_python_file(path)
    rel = path.relative_to(REPO_ROOT).as_posix()
    assert not import_direction_violations(path, tree, SRC_ROOT)
    for checker in (boundary_violations, write_violations, execution_violations,
                    surface_import_violations, research_violations):
        assert not checker(tree, rel)


def test_new_tool_does_not_broaden_original_reader_or_allow_arbitrary_calls():
    snippet = ast.parse("from aegiscae.research.project import open_agreement_project").body[0]
    assert permitted_fixture_import(snippet, "aegiscae/interfaces/fixture_scope.py")
    assert not permitted_fixture_import(snippet, "aegiscae/interfaces/mcp_read.py")
    assert not permitted_fixture_import(snippet, "aegiscae/interfaces/mcp_scoped.py")
    for expression in ('path.open("wb")', "path.unlink()"):
        tree = ast.parse("def authorize():\n    " + expression)
        assert write_violations(tree, "src/aegiscae/interfaces/fixture_scope.py")
    tree = ast.parse('def dispatch():\n    path.open("xb")')
    assert write_violations(tree, "src/aegiscae/interfaces/mcp_scoped.py")
    for call in ("client.apply(event)", "rules.submit(event)"):
        tree = ast.parse("def _record():\n    " + call)
        assert boundary_violations(tree, "src/aegiscae/research/scoped_fixture.py")
