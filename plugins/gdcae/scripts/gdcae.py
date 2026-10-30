"""Offline, stdlib-only packaging helper. No install, solver, auth or thread APIs."""

from __future__ import annotations

import argparse
import base64
import hashlib
from importlib import metadata
from importlib.util import find_spec
import json
import os
from pathlib import Path
import re
import sys
import sysconfig

PACKAGE = Path(__file__).resolve().parents[1]
ROLES = ("gdcae-cae", "gdcae-results", "gdcae-inverse", "gdcae-reviewer")
FILES = (
    "plugin.json", "scripts/gdcae.py", "scripts/candidate.py", "skills/setup/SKILL.md",
    "skills/research/SKILL.md", "references/handoff.md",
    *(f"agents/{role}.toml" for role in ROLES),
)


class SetupBlocked(ValueError):
    """Fixed diagnostics only; do not echo caller paths, URLs or credentials."""


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise SetupBlocked("INVALID_ARGUMENTS")


def need(condition: bool, code: str) -> None:
    if not condition:
        raise SetupBlocked(code)


def read_package(root: Path = PACKAGE) -> dict[str, bytes]:
    need(root.is_absolute() and root.is_dir(), "PACKAGE_UNAVAILABLE")
    need(not any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)),
         "PACKAGE_LINK_REJECTED")
    result = {}
    for relative in FILES:
        file = root / relative
        need(not any(p.is_symlink() or p.is_junction()
                     for p in (file, *file.parents)), "PACKAGE_LINK_REJECTED")
        need(file.is_file() and file.stat().st_size <= 65536, "PACKAGE_FILE_INVALID")
        result[relative] = file.read_bytes()
    return result


def content_digest(files: dict[str, bytes]) -> str:
    manifest = {key: hashlib.sha256(value).hexdigest() for key, value in sorted(files.items())}
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()


def marketplace() -> dict:
    return {"name": "gdcae-preview", "interface": {"displayName": "GDCAE Research Preview"},
            "plugins": [{"name": "gdcae", "source": {
                "source": "local", "path": "./plugins/gdcae"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity"}]}


def prepare_workspace(workspace: Path, expected: str, root: Path = PACKAGE) -> dict:
    """Exclusive fresh-directory creation. On failure preserve partial files; never overwrite."""
    files = read_package(root)
    digest = content_digest(files)
    need(re.fullmatch(r"[0-9a-f]{64}", expected) is not None and digest == expected,
         "PACKAGE_DIGEST_MISMATCH")
    need(workspace.is_absolute(), "ABSOLUTE_WORKSPACE_REQUIRED")
    need(not any(p.is_symlink() or p.is_junction()
                 for p in (workspace, *workspace.parents)), "WORKSPACE_LINK_REJECTED")
    need(workspace.parent.is_dir() and not workspace.exists(), "FRESH_WORKSPACE_REQUIRED")
    need(not workspace.resolve().is_relative_to(root.resolve()), "PACKAGE_DESTINATION_REJECTED")
    if root.parent.name == "plugins":
        need(not workspace.resolve().is_relative_to(root.parent.parent.resolve()),
             "SOURCE_WORKSPACE_DESTINATION_REJECTED")
    need(not workspace.resolve().is_relative_to(Path.home().resolve() / ".codex"),
         "GLOBAL_CONFIG_DESTINATION_REJECTED")
    configured_home = os.environ.get("CODEX_HOME")
    if configured_home:
        need(not workspace.resolve().is_relative_to(Path(configured_home).resolve()),
             "GLOBAL_CONFIG_DESTINATION_REJECTED")
    # A hard failure deliberately leaves a non-reusable partial destination for diagnosis.
    workspace.mkdir()
    for relative, body in files.items():
        target = workspace / "plugins" / "gdcae" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(body)
    for role in ROLES:
        target = workspace / ".codex" / "agents" / f"{role}.toml"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(files[f"agents/{role}.toml"])
    target = workspace / ".agents" / "plugins" / "marketplace.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        json.dump(marketplace(), stream, indent=2)
    record = {"schema": "gdcae-workspace-package-v1", "package_sha256": digest,
              "roles": list(ROLES), "plugin_activation": "NOT_TESTED",
              "source": "LOCAL_REVIEWED_PACKAGE", "execution_authorized": False}
    with (workspace / "gdcae-package.json").open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
    return record


def install_plan(repository: str, ref: str) -> dict:
    """Return argument vectors only; never execute Git, network or Codex mutations."""
    need(re.fullmatch(r"https://github\.com/[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+", repository)
         is not None, "CREDENTIAL_FREE_GITHUB_URL_REQUIRED")
    need(re.fullmatch(r"[0-9a-f]{40}", ref) is not None, "FULL_COMMIT_REQUIRED")
    return {"schema": "gdcae-install-plan-v1", "executed": False,
            "approval_required": True, "repository_access": "UNKNOWN",
            "core_installation": "REQUIRES_APPROVED_PINNED_SOURCE_INSTALL",
            "af_installation": "SEPARATE_QUALIFICATION_REQUIRED",
            "commands": [["codex", "plugin", "marketplace", "add", repository, "--ref", ref],
                         ["codex", "plugin", "add", "gdcae@gdcae-preview"]]}


def doctor() -> dict:
    digest = content_digest(read_package())
    # Discover only a top-level module; do not import its code or any AF module.
    try:
        core = "DISCOVERABLE_NOT_IMPORTED" if find_spec("aegiscae") else "MISSING"
    except (ImportError, ValueError):
        core = "UNKNOWN"
    return {"schema": "gdcae-doctor-v1", "windows": os.name == "nt",
            "python_supported": (3, 12) <= sys.version_info[:2] < (4, 0),
            "python": ".".join(map(str, sys.version_info[:3])),
            "package_sha256": digest, "plugin_activation": "NOT_TESTED",
            "research_core": core,
            "native_role_loading": "NOT_TESTED", "repository_access": "UNKNOWN",
            "abaqus_license": "NOT_TESTED", "af_dynamic_dispatch": "NOT_QUALIFIED",
            "operator_isolation": "BLOCKED_HIL_STRONG_ISOLATION",
            "real_execution_authorized": False}


def verify_installed_core() -> Path:
    """Check interpreter installation/RECORD consistency, not publisher authenticity."""
    code = "INSTALLED_CORE_REQUIRED"
    core = find_spec("aegiscae")
    need(core is not None and core.origin is not None, code)
    origin = Path(core.origin).resolve()
    roots = {Path(sysconfig.get_path(key)).resolve() for key in ("purelib", "platlib")}
    root = origin.parent.parent
    need(root in roots and origin == root / "aegiscae" / "__init__.py", code)
    try:
        dist = metadata.distribution("aegiscae")
        need(Path(dist.locate_file("")).resolve() == root, code)
        direct = dist.read_text("direct_url.json")
        if direct is not None:
            direct = json.loads(direct)
            need(isinstance(direct, dict) and not direct.get("dir_info", {}).get("editable"),
                 "EDITABLE_CORE_REJECTED")
        files = dist.files
        need(bool(files), "CORE_RECORD_REQUIRED")
        records = {str(item).replace("\\", "/"): item for item in files}
        need(any(name.endswith(".dist-info/RECORD") for name in records),
             "CORE_RECORD_REQUIRED")
        package_files = {name: item for name, item in records.items()
                         if name.startswith("aegiscae/")}
        need("aegiscae/__init__.py" in package_files, "CORE_RECORD_REQUIRED")
        for name, item in package_files.items():
            path = root / name
            need(path.resolve().is_relative_to(root / "aegiscae"), code)
            need(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)), code)
            if path.suffix == ".pyc":
                continue  # Installer-generated cache is not source provenance.
            need(path.is_file() and item.hash is not None and item.hash.mode == "sha256",
                 "CORE_RECORD_REQUIRED")
            body = path.read_bytes()
            actual = base64.urlsafe_b64encode(hashlib.sha256(body).digest()).rstrip(b"=").decode()
            need(actual == item.hash.value and len(body) == item.size,
                 "CORE_RECORD_DIGEST_MISMATCH")
        actual_files = {(p.relative_to(root).as_posix()) for p in (root / "aegiscae").rglob("*")
                        if p.is_file() and p.suffix != ".pyc"}
        need(actual_files == {name for name in package_files if not name.endswith(".pyc")},
             "CORE_UNRECORDED_FILE")
        need(list(core.submodule_search_locations or []) == [str(origin.parent)], code)
        for name, module in tuple(sys.modules.items()):
            if name == "aegiscae" or name.startswith("aegiscae."):
                loaded = getattr(module, "__file__", None)
                need(loaded is not None and Path(loaded).resolve().is_relative_to(origin.parent), code)
    except (metadata.PackageNotFoundError, OSError, ValueError, TypeError, AttributeError) as exc:
        if isinstance(exc, SetupBlocked):
            raise
        raise SetupBlocked(code) from None
    return origin


def initialize_research(workspace: Path, expected: str, name: str,
                        goal_min: str = "0.019", goal_max: str = "0.021") -> dict:
    """Freeze a new offline preview using an installed Core; never prepare B or a Grant."""
    need(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", name) is not None,
         "INVALID_PROJECT_NAME")
    verify_installed_core()
    from aegiscae.research.rod_preview import RodPreviewContract, create_preview
    from dataclasses import asdict

    contract = RodPreviewContract(goal_min_mm=goal_min, goal_max_mm=goal_max)
    # Validate before filesystem setup, and keep incomplete setup on any later failure.
    contract = RodPreviewContract.from_dict(asdict(contract))
    receipt = prepare_workspace(workspace, expected)
    adapter = create_preview(workspace / "research", name, contract)
    state = adapter.inspect()
    result = {"schema": "gdcae-research-init-v1", "project_created": True,
              "package_sha256": receipt["package_sha256"],
              "contract_sha256": contract.digest(), "project_revision": state["project_revision"],
              "evidence_mode": contract.evidence_mode, "maximum_solver_calls": 2,
              "core_origin": "INSTALLED_SITE_PACKAGES", "core_record": "SHA256_VERIFIED",
              "plugin_activation": "NOT_TESTED",
              "real_a": "NOT_RUN", "real_b": "NOT_RUN", "execution_authorized": False}
    with (workspace / "gdcae-research-init.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


def main() -> int:
    if not (3, 12) <= sys.version_info[:2] < (4, 0):
        print('{"status":"BLOCKED","code":"PYTHON_312_OR_NEWER_REQUIRED"}')
        return 2
    parser = SafeArgumentParser(prog="gdcae-preview", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("package-digest")
    setup = sub.add_parser("prepare-workspace")
    setup.add_argument("--workspace", type=Path, required=True)
    setup.add_argument("--expected-package-digest", required=True)
    init = sub.add_parser("init-research")
    init.add_argument("--workspace", type=Path, required=True)
    init.add_argument("--expected-package-digest", required=True)
    init.add_argument("--name", required=True)
    init.add_argument("--goal-min-mm", default="0.019")
    init.add_argument("--goal-max-mm", default="0.021")
    plan = sub.add_parser("install-plan")
    plan.add_argument("--repository", required=True)
    plan.add_argument("--ref", required=True)
    try:
        args = parser.parse_args()
        if args.command == "doctor":
            result = doctor()
        elif args.command == "package-digest":
            result = {"package_sha256": content_digest(read_package())}
        elif args.command == "prepare-workspace":
            result = prepare_workspace(args.workspace, args.expected_package_digest)
        elif args.command == "init-research":
            result = initialize_research(args.workspace, args.expected_package_digest,
                                         args.name, args.goal_min_mm, args.goal_max_mm)
        else:
            result = install_plan(args.repository, args.ref)
        print(json.dumps(result, sort_keys=True))
        return 0
    except SetupBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "code": str(exc)}))
        return 2
    except OSError:
        print(json.dumps({"status": "BLOCKED", "code": "FILESYSTEM_OPERATION_FAILED"}))
        return 2
    except (ValueError, ImportError):
        print(json.dumps({"status": "BLOCKED", "code": "CORE_INITIALIZATION_REJECTED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
