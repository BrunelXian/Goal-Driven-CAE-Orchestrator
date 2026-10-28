"""Exact SQLite/write exceptions for M02-A; M01 remains read-only."""

import ast

import pytest

from conftest import REPO_ROOT, SRC_ROOT, iter_python_files, parse_python_file


STORE = "src/aegiscae/research/project.py"
MUTATION = "src/aegiscae/research/mutation.py"
SQL = {
    "_connection": {
        "PRAGMA trusted_schema=OFF", "PRAGMA busy_timeout=2000", "PRAGMA query_only=ON",
    },
    "_read_state": {
        "SELECT name,sql FROM sqlite_master WHERE type IN ('table','view','trigger')",
        "SELECT body,digest FROM project",
        "SELECT bundle_id,version,digest,body,revision,idempotency_key,created_at_utc,"
        "transaction_id,metadata_digest "
        "FROM bundles ORDER BY revision LIMIT 130",
        "SELECT kind,contract_id,version,digest,body FROM parts LIMIT 385",
        "SELECT sequence,body,digest FROM audit ORDER BY sequence LIMIT 1025",
    },
    "_append_audit": {
        "SELECT sequence,digest FROM audit ORDER BY sequence DESC LIMIT 1",
        "INSERT INTO audit VALUES (?,?,?)",
    },
    "create_research_project": {"INSERT INTO project VALUES (1,?,?)"},
    "_commit_budget_event": {"UPDATE project SET body=?,digest=? WHERE singleton=1"},
    "freeze_contract_bundle": {
        "INSERT INTO bundles VALUES (?,?,?,?,?,?,?,?,?)",
        "SELECT version,digest FROM parts WHERE kind=? AND contract_id=? ORDER BY version DESC",
        "INSERT INTO parts VALUES (?,?,?,?,?)",
        "UPDATE project SET body=?,digest=? WHERE singleton=1",
    },
}


def enclosing_function(tree, node):
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
    return None


def same(node, expression):
    return ast.dump(node, include_attributes=False) == ast.dump(
        ast.parse(expression, mode="eval").body, include_attributes=False)


def permitted_store_creation(tree, node, display_path):
    return (
        display_path == STORE and isinstance(node, ast.Call)
        and enclosing_function(tree, node) == "create_research_project"
        and (same(node, "root.mkdir()") or same(
            node, "os.open(root / _DATABASE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)"))
    )


def permitted_mutation_write(tree, node, display_path):
    if display_path != MUTATION or not isinstance(node, ast.Call):
        return False
    expressions = {
        "create_synthetic_workspace": ("root.mkdir()", "staging.mkdir()"),
        "propose_mutation": ("output.mkdir()",),
        "_exclusive_file": ('path.open("xb")', "stream.write(body)", "stream.flush()",
                            "os.fsync(stream.fileno())"),
    }
    return any(same(node, expression) for expression in expressions.get(
        enclosing_function(tree, node), ()))


@pytest.mark.parametrize("function,expression", [
    ("inspect_candidate", "output.mkdir()"),
    ("propose_mutation", "output.mkdir(exist_ok=True)"),
    ("propose_mutation", "output.mkdir(parents=True)"),
    ("_exclusive_file", 'path.open("wb")'),
    ("_exclusive_file", 'path.open("ab")'),
    ("_exclusive_file", "path.open(mode)"),
    ("inspect_candidate", 'path.open("xb")'),
])
def test_mutation_write_exception_is_exact(function, expression):
    tree = ast.parse(f"def {function}():\n    {expression}")
    assert not permitted_mutation_write(tree, tree.body[0].body[0].value, MUTATION)


def test_mutation_file_open_cannot_escape_to_readers_or_sibling():
    from test_forbidden_direct_writes import write_violations

    tree = ast.parse('def _exclusive_file():\n    path.open("xb")')
    assert not write_violations(tree, MUTATION)
    assert write_violations(tree, "src/aegiscae/research/other.py")
    assert write_violations(ast.parse('def inspect_candidate():\n    path.open("wb")'), MUTATION)


def permitted_store_sql(tree, node, display_path):
    if not (display_path == STORE and isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and same(node.func, "connection.execute")
            and node.args and not node.keywords):
        return False
    function = enclosing_function(tree, node)
    query = node.args[0]
    if isinstance(query, ast.Constant) and type(query.value) is str:
        return query.value in SQL.get(function, set())
    if function == "_connection":
        return same(query, '"BEGIN IMMEDIATE" if write else "BEGIN"')
    if function == "create_research_project" and same(query, "statement"):
        return any(isinstance(parent, ast.For) and isinstance(parent.target, ast.Name)
                   and parent.target.id == "statement"
                   and same(parent.iter, "_SCHEMA.values()") and node in ast.walk(parent)
                   for parent in ast.walk(tree))
    return False


def research_violations(tree, display_path):
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module]
            if any(name and name.split(".")[0] in {"sqlite3", "sqlalchemy", "peewee"}
                   for name in modules):
                if not (display_path == STORE and isinstance(node, ast.Import)
                        and len(node.names) == 1 and node.names[0].name == "sqlite3"
                        and node.names[0].asname is None):
                    violations.append("database import outside exact store")
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method == "execute" and not permitted_store_sql(tree, node, display_path):
                violations.append("SQL execution outside literal allowlist")
            if method in {"executemany", "executescript"}:
                violations.append("unapproved bulk SQL")
            if same(node.func, "sqlite3.connect") and not (
                display_path == STORE and enclosing_function(tree, node) == "_connection"
            ):
                violations.append("database connection outside store connection")
            if same(node.func, "os.open") and not permitted_store_creation(tree, node, display_path):
                violations.append("raw file open outside exclusive creation")
    return violations


def test_research_store_has_only_explicit_sql_and_creation_paths():
    for path in iter_python_files(SRC_ROOT):
        assert not research_violations(parse_python_file(path), path.relative_to(REPO_ROOT).as_posix())


@pytest.mark.parametrize("snippet", [
    "def inspect():\n    connection.execute('INSERT INTO audit VALUES (?,?,?)', values)",
    "def freeze_contract_bundle():\n    connection.execute(query, values)",
    "def freeze_contract_bundle():\n    connection.execute('DELETE FROM bundles')",
    "def freeze_contract_bundle():\n    other.execute('INSERT INTO bundles VALUES (?,?,?,?,?,?,?)')",
    "def create_research_project():\n    connection.execute(statement)",
    "connection.executescript(sql)",
    "import sqlite3 as db",
    "from sqlite3 import connect",
    "import sqlalchemy",
    "os.open(filename, flags)",
])
def test_sql_exception_rejects_dynamic_wrong_receiver_and_readonly_writes(snippet):
    assert research_violations(ast.parse(snippet), STORE)


def test_same_approved_sql_is_rejected_in_sibling_module():
    tree = ast.parse("def _append_audit():\n    connection.execute('INSERT INTO audit VALUES (?,?,?)')")
    assert not research_violations(tree, STORE)
    assert research_violations(tree, "src/aegiscae/research/other.py")


@pytest.mark.parametrize("function,path,sql", [
    ("inspect_budget", STORE, "UPDATE project SET body=?,digest=? WHERE singleton=1"),
    ("_commit_budget_event", "src/aegiscae/research/budget.py",
     "UPDATE project SET body=?,digest=? WHERE singleton=1"),
    ("_commit_budget_event", STORE, "DELETE FROM audit"),
])
def test_budget_revision_write_exception_cannot_expand(function, path, sql):
    tree = ast.parse(f"def {function}():\n    connection.execute({sql!r}, values)")
    assert research_violations(tree, path)


@pytest.mark.parametrize("function,statement", [
    ("inspect", "root.mkdir()"),
    ("create_research_project", "root.mkdir(exist_ok=True)"),
    ("create_research_project", "root.mkdir(parents=True)"),
    ("create_research_project", "root.write_text('replacement')"),
])
def test_create_exception_is_exact_function_and_call(function, statement):
    tree = ast.parse(f"def {function}():\n    {statement}")
    assert not permitted_store_creation(tree, tree.body[0].body[0].value, STORE)


@pytest.mark.parametrize("relative,snippet", [
    ("aegiscae/interfaces/mcp_read.py", "from aegiscae.research.project import ResearchProject"),
    ("aegiscae/adapters/abaqus/af_evidence.py",
     "from aegiscae.research.project import ResearchProject"),
    ("aegiscae/contracts/research_contracts.py",
     "from aegiscae.research.project import ResearchProject"),
    ("aegiscae/research/project.py", "from aegiscae.adapters.abaqus.af_evidence import EvidenceBridge"),
])
def test_research_layer_does_not_connect_m01_read_surfaces_to_writes(relative, snippet):
    from test_dependency_direction import import_direction_violations

    assert import_direction_violations(SRC_ROOT / relative, ast.parse(snippet), SRC_ROOT)


def test_store_exception_does_not_allow_private_af_or_process_calls():
    from test_forbidden_execution_calls import execution_violations
    from test_forbidden_legacy_dependencies import legacy_import_violations

    assert legacy_import_violations(ast.parse("from abqjobpilot.execution.store import Store"), STORE)
    assert execution_violations(ast.parse("import subprocess\nsubprocess.Popen(command)"), STORE)


def test_exact_creation_exception_is_not_reusable_for_sibling_or_readonly_function():
    from test_forbidden_direct_writes import write_violations

    approved = ast.parse("def create_research_project():\n    root.mkdir()")
    assert not write_violations(approved, STORE)
    assert write_violations(approved, "src/aegiscae/research/other.py")
    assert write_violations(ast.parse("def inspect():\n    root.mkdir()"), STORE)
