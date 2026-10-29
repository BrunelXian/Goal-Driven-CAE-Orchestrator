"""Exact F1 sidecar exception, not a general SQL/owner/process capability."""

import ast

import pytest

from conftest import REPO_ROOT
from test_proposal_boundary import exact, function


STORE = "src/aegiscae/research/main_runtime_store.py"


def runtime_creation(tree, node, path):
    return path == STORE and function(tree, node) == "create_files" and exact(
        node, "os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)")


def runtime_sql(tree, node, path):
    if path != STORE or not isinstance(node, ast.Call) or not exact(node.func, "connection.execute") \
            or not node.args or node.keywords:
        return False
    if exact(node.args[0], "SCHEMA"):
        return function(tree, node) == "connection_for" and any(
            isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id == "SCHEMA" and exact(n.value, repr(
                "CREATE TABLE events (sequence INTEGER PRIMARY KEY, body BLOB NOT NULL, digest TEXT NOT NULL)"))
            for n in tree.body)
    allowed = {
        "connection_for": ('"PRAGMA trusted_schema=OFF"', '"PRAGMA busy_timeout=2000"',
            '"PRAGMA query_only=ON"', '"BEGIN IMMEDIATE" if write else "BEGIN"'),
        "read_events": ('"SELECT name,sql FROM sqlite_master WHERE type IN (\'table\',\'view\',\'trigger\')"',
            '"SELECT sequence,body,digest FROM events ORDER BY sequence LIMIT 66"'),
        "append": ('"INSERT INTO events VALUES (?,?,?)"',),
    }
    return any(exact(node.args[0], query) for query in allowed.get(function(tree, node), ()))


@pytest.mark.parametrize("snippet", ["connection.execute(sql)", "connection.execute('DELETE FROM events')",
    "os.open(path, flags)", "connection.executescript(sql)", "import sqlite3 as db"])
def test_runtime_cannot_expand_database_authority(snippet):
    from test_research_boundary import research_violations
    assert research_violations(ast.parse("def append():\n    " + snippet), STORE)


def test_runtime_has_no_project_write_af_or_process_authority():
    forbidden = {"advance", "admit_proposal", "reserve_for_candidate", "record_submission_intent",
        "propose_mutation", "freeze_contract_bundle", "Popen", "run", "_rpc", "_send", "_block",
        "_commit_budget_event", "_commit_workflow_event"}
    for name in ("main_runtime.py", "main_runtime_rules.py", "main_runtime_store.py"):
        tree = ast.parse((REPO_ROOT / "src/aegiscae/research" / name).read_text())
        assert not any(isinstance(n, ast.Attribute) and n.attr in forbidden for n in ast.walk(tree))
        assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "_snapshot" and n.keywords for n in ast.walk(tree))


def test_runtime_sql_exception_does_not_apply_to_other_readers():
    from test_research_boundary import research_violations
    tree = ast.parse("def append():\n    connection.execute('INSERT INTO events VALUES (?,?,?)', data)")
    assert not research_violations(tree, STORE)
    assert research_violations(tree, "src/aegiscae/interfaces/mcp_read.py")
    assert research_violations(ast.parse("def status():\n    os.open(path, os.O_CREAT)"), STORE)


def test_sender_lock_is_not_a_research_or_session_file():
    tree = ast.parse((REPO_ROOT / STORE).read_text())
    constants = {n.targets[0].id: n.value.value for n in tree.body if isinstance(n, ast.Assign)
        and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.Constant)}
    assert constants["FILENAME"] == "main-runtime-v1.sqlite3"
    assert constants["LOCKFILE"] == "main-runtime-v1.owner"
