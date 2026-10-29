"""Exact M03-D sidecar and interface exceptions, not generic write authority."""

import ast

import pytest

from conftest import REPO_ROOT

STORE = "src/aegiscae/research/ingress_store.py"
INTERFACE = "src/aegiscae/interfaces/mcp_proposal.py"


def function(tree, node):
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name


def exact(node, expression):
    return ast.dump(node, include_attributes=False) == ast.dump(ast.parse(expression, mode="eval").body,
                                                              include_attributes=False)


def proposal_creation(tree, node, path):
    return path == STORE and function(tree, node) == "create_file" and exact(
        node, "os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)")


def proposal_sql(tree, node, path):
    if path != STORE or not isinstance(node, ast.Call) or not exact(node.func, "connection.execute") \
            or not node.args or node.keywords:
        return False
    if exact(node.args[0], "SCHEMA"):
        return function(tree, node) == "connection_for" and any(
            isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id == "SCHEMA"
            and exact(n.value, repr("CREATE TABLE events (sequence INTEGER PRIMARY KEY, body BLOB NOT NULL, digest TEXT NOT NULL)"))
            for n in tree.body)
    allowed = {
        "connection_for": ('"PRAGMA trusted_schema=OFF"', '"PRAGMA busy_timeout=2000"',
            '"PRAGMA query_only=ON"', '"BEGIN IMMEDIATE" if write else "BEGIN"', "SCHEMA"),
        "read_events": ('"SELECT name,sql FROM sqlite_master WHERE type IN (\'table\',\'view\',\'trigger\')"',
            '"SELECT sequence,body,digest FROM events ORDER BY sequence LIMIT 6"'),
        "append": ('"INSERT INTO events VALUES (?,?,?)"',),
    }
    return any(exact(node.args[0], query) for query in allowed.get(function(tree, node), ()))


def proposal_import(node, path):
    return path == "aegiscae/interfaces/mcp_proposal.py" and isinstance(node, ast.ImportFrom) \
        and node.level == 0 and node.module == "aegiscae.research.proposal_ingress" \
        and len(node.names) == 1 and node.names[0].name == "ProposalIngress" and node.names[0].asname is None


@pytest.mark.parametrize("statement", ["connection.execute(sql)", "connection.execute('DELETE FROM events')",
    "other.execute('INSERT INTO events VALUES (?,?,?)')", "os.open(path, flags)",
    "connection.executescript(sql)"])
def test_new_sql_exception_rejects_dynamic_or_destructive_calls(statement):
    from test_research_boundary import research_violations
    tree = ast.parse("def append():\n    " + statement)
    assert research_violations(tree, STORE)


def test_schema_name_is_not_permission_for_other_ddl():
    tree = ast.parse("SCHEMA='DROP TABLE events'\ndef connection_for():\n    connection.execute(SCHEMA)")
    assert not proposal_sql(tree, tree.body[1].body[0].value, STORE)


def test_proposal_interface_has_only_two_operations_and_no_gate_dependency():
    from aegiscae.interfaces.mcp_proposal import _SCHEMAS
    assert set(_SCHEMAS) == {"gdcae_record_candidate_proposal", "gdcae_get_proposal_status"}
    tree = ast.parse((REPO_ROOT / INTERFACE).read_text())
    forbidden = {"evaluate_recorded", "admit_proposal", "advance", "reserve_for_candidate",
                 "_snapshot", "_evaluate_snapshot", "revoke_challenge", "issue_challenge"}
    assert not any(isinstance(n, ast.Attribute) and n.attr in forbidden for n in ast.walk(tree))
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert [n for n in imports if n.startswith("aegiscae.")] == ["aegiscae.research.proposal_ingress"]


@pytest.mark.parametrize("module", ["mcp_read.py", "other.py"])
def test_new_import_exception_does_not_expand_old_interfaces(module):
    assert not proposal_import(ast.parse("from aegiscae.research.proposal_ingress import ProposalIngress").body[0],
                               "aegiscae/interfaces/" + module)


def test_receipt_facade_has_no_execution_or_review_imports():
    tree = ast.parse((REPO_ROOT / "src/aegiscae/research/proposal_ingress.py").read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any(name and any(s in name for s in ("budget", "mutation", "proposal_review", "adapters"))
                   for name in imports)
    workflow_imports = [n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
                        and n.module == "aegiscae.research.workflow"]
    assert len(workflow_imports) == 1
    assert [a.name for a in workflow_imports[0].names] == ["historical_research_brief"]
