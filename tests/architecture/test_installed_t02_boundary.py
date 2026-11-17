"""Bound the deployed plugin separately from the historical development source tree."""
import ast
import runpy

from conftest import REPO_ROOT
from test_research_boundary import research_violations


def test_deployed_research_core_uses_audited_sql_and_excludes_executors():
    release = runpy.run_path(str(REPO_ROOT/"product/research-preview/tools/release.py"))
    files = set(release["CORE_FILES"])
    assert files == {
        "__init__.py", "contracts/__init__.py", "contracts/research_contracts.py",
        "research/__init__.py", "research/project.py", "research/research_agreement.py",
        "research/sanity.py", "research/task_cards.py", "research/task_roles.py",
        "research/capability_discovery.py", "research/project_tasks.py",
    }
    for name in files:
        path = REPO_ROOT/"src/aegiscae"/name
        tree = ast.parse(path.read_text(encoding="utf8"))
        assert not research_violations(tree,path.relative_to(REPO_ROOT).as_posix())
        for node in ast.walk(tree):
            modules = ([a.name for a in node.names] if isinstance(node,ast.Import) else
                       [node.module or ""] if isinstance(node,ast.ImportFrom) else [])
            assert not any(m.startswith(("abqjobpilot","aegiscae.adapters","aegiscae.interfaces")) for m in modules)


def test_broker_dispatches_only_fixed_read_operations():
    adapter = REPO_ROOT/"product/research-preview/tools/abqjobpilot_readonly.py"
    tree = ast.parse(adapter.read_text(encoding="utf8"))
    calls = [n for n in ast.walk(tree) if isinstance(n,ast.Call)]
    reads = [n for n in calls if isinstance(n.func,ast.Name) and n.func.id == "_read"]
    assert [ast.literal_eval(n.args[1]) for n in reads] == ["abq_list_jobs","abq_job_status"]
    methods = [n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr == "call_tool"]
    assert len(methods) == 1 and methods[0].args[0].id == "name"
    for name in ("t02_service.py","t02_worker.py"):
        source = (REPO_ROOT/"plugins/gdcae-research/scripts"/name).read_text(encoding="utf8")
        tree = ast.parse(source)
        assert not any(isinstance(n,ast.Import) and any(a.name in {"sqlite3","abqjobpilot"} for a in n.names)
                       for n in ast.walk(tree))
        assert not any(isinstance(n,ast.keyword) and n.arg == "shell" for n in ast.walk(tree))
