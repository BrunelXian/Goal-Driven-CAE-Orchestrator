"""Original isolated paths; link refusals are simulated without OS changes."""

import ast
from pathlib import Path

import pytest

from g3_rehearsal import confined_existing


def tree(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    workspace = root / "workspace"
    workspace.mkdir()
    packet = workspace / "packet.json"
    packet.write_text("{}", encoding="utf-8")
    return root, workspace, packet


def test_exact_existing_project_and_packet_are_confined(tmp_path):
    root, workspace, packet = tree(tmp_path)
    assert confined_existing(workspace, root, kind="directory") == workspace.resolve()
    assert confined_existing(packet, root, kind="file") == packet.resolve()


@pytest.mark.parametrize("case", ["dotdot", "sibling_prefix", "outside", "relative_path",
                                 "relative_root", "missing", "file_as_dir", "dir_as_file"])
def test_nonconfined_or_wrong_kind_paths_rejected(tmp_path, case):
    root, workspace, packet = tree(tmp_path)
    outside = tmp_path / "root_other"
    outside.mkdir()
    path, owner, kind = {
        "dotdot": (root / ".." / "root_other", root, "directory"),
        "sibling_prefix": (outside, root, "directory"),
        "outside": (tmp_path, root, "directory"),
        "relative_path": (Path("workspace"), root, "directory"),
        "relative_root": (workspace, Path("root"), "directory"),
        "missing": (root / "absent", root, "file"),
        "file_as_dir": (packet, root, "directory"),
        "dir_as_file": (workspace, root, "file"),
    }[case]
    with pytest.raises((ValueError, OSError)):
        confined_existing(path, owner, kind=kind)


@pytest.mark.parametrize("target,method", [
    ("root", "is_junction"), ("workspace", "is_junction"),
    ("packet", "is_symlink"), ("workspace", "is_symlink"),
])
def test_leaf_and_ancestor_links_refused_without_creating_links(tmp_path, monkeypatch, target, method):
    root, workspace, packet = tree(tmp_path)
    chosen = {"root": root, "workspace": workspace, "packet": packet}[target]
    original = getattr(Path, method)
    monkeypatch.setattr(Path, method, lambda path: path == chosen or original(path))
    with pytest.raises(ValueError):
        confined_existing(packet, root, kind="file")


def test_all_import_and_workspace_roots_are_checked_before_configure():
    import g3_rehearsal

    tree_ast = ast.parse(Path(g3_rehearsal.__file__).read_text(encoding="utf-8"))
    main = tree_ast.body[-1]
    guarded = next(node for node in main.body if isinstance(node, ast.Try))
    calls = {}
    configure_index = None
    for index, node in enumerate(guarded.body):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if isinstance(node.value.func, ast.Name) and node.value.func.id == "configure":
            configure_index = index
        target = node.targets[0]
        if isinstance(target, ast.Attribute) and target.attr in {"workspace", "site_packages", "af_fixtures"}:
            assert ast.unparse(node.value) == (
                f"confined_existing(args.{target.attr}, args.task_root, kind='directory')")
            calls[target.attr] = index
    assert set(calls) == {"workspace", "site_packages", "af_fixtures"}
    assert configure_index is not None and all(index < configure_index for index in calls.values())
