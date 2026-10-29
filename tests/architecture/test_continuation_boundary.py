"""Exact fixed continuation store exception; no production process authority."""

import ast

import pytest

from conftest import REPO_ROOT
from test_proposal_boundary import exact, function


STORE = "src/aegiscae/research/continuation_store.py"


def continuation_creation(tree, node, path):
    return path == STORE and function(tree, node) == "create_file" and exact(
        node, "os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)")


def continuation_sql(tree, node, path):
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
            '"SELECT sequence,body,digest FROM events ORDER BY sequence LIMIT 10"'),
        "append": ('"INSERT INTO events VALUES (?,?,?)"',),
    }
    return any(exact(node.args[0], query) for query in allowed.get(function(tree, node), ()))


@pytest.mark.parametrize("snippet", ["connection.execute(sql)", "connection.execute('DELETE FROM events')",
    "os.open(path, flags)", "connection.executescript(sql)"])
def test_continuation_cannot_expand_sql_or_creation(snippet):
    from test_research_boundary import research_violations
    assert research_violations(ast.parse("def append():\n    " + snippet), STORE)


def test_continuation_core_has_no_research_write_or_process_calls():
    forbidden = {"advance", "admit_proposal", "reserve_for_candidate", "record_submission_intent",
                 "propose_mutation", "freeze_contract_bundle", "Popen", "run", "_rpc", "_send"}
    for name in ("continuation.py", "continuation_rules.py", "continuation_store.py"):
        tree = ast.parse((REPO_ROOT / "src/aegiscae/research" / name).read_text())
        assert not any(isinstance(n, ast.Attribute) and n.attr in forbidden for n in ast.walk(tree))
        assert not any(isinstance(n, ast.keyword) and n.arg == "write" and isinstance(n.value, ast.Constant)
                       and n.value.value is True for call in ast.walk(tree)
                       if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                       and call.func.attr == "_snapshot" for n in call.keywords)


def test_test_adapter_is_not_collected_as_live_test_and_no_network_listener():
    path = REPO_ROOT / "tests/integration/m03e1_protocol.py"
    tree = ast.parse(path.read_text())
    assert not any(isinstance(n, ast.FunctionDef) and n.name.startswith("test_") for n in ast.walk(tree))
    text = path.read_text()
    assert '"stdio://"' in text and '"tcp://' not in text and '"websocket' not in text
