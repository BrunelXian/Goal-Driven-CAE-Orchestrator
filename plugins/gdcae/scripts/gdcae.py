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
import tomllib

PACKAGE = Path(__file__).resolve().parents[1]
ROLES = ("gdcae-cae", "gdcae-results", "gdcae-inverse", "gdcae-reviewer")
READ_TOOLS = ("gdcae_capabilities", "gdcae_list_runs", "gdcae_get_run", "gdcae_get_receipt",
              "gdcae_list_events", "gdcae_get_validations", "gdcae_get_diagnostic")
FILES = (
    "plugin.json", "scripts/gdcae.py", "scripts/candidate.py", "skills/setup/SKILL.md",
    "skills/research/SKILL.md", "references/handoff.md", "references/runtime-contract.json",
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
    validate_package(result)
    return result


def validate_package(files: dict[str, bytes]) -> dict:
    """Validate packaged declarations; presence never proves client activation."""
    need(set(files) == set(FILES), "PACKAGE_CLOSURE_MISMATCH")
    try:
        manifest = json.loads(files["plugin.json"])
        runtime = json.loads(files["references/runtime-contract.json"])
        need(set(manifest) == {"$schema", "name", "version", "description", "extensions"}
             and manifest["name"] == "gdcae"
             and manifest["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
             and manifest["version"] == runtime["plugin_version"] == "0.1.0-alpha.5",
             "PACKAGE_MANIFEST_MISMATCH")
        extension = manifest["extensions"]["com.openai"]
        need(extension["onboardingSkill"] == "./skills/setup/SKILL.md"
             and set(extension) == {"onboardingSkill", "interface"},
             "UNREVIEWED_PLUGIN_SURFACE")
        expected = {
            "schema": "gdcae-product-runtime-v1", "plugin_version": "0.1.0-alpha.5",
            "snapshot_version": "0.0.0+g3d6", "python": "3.12.10",
            "core_freeze": {"module": "aegiscae.research.rod_real_project",
                            "factory": "create_real_research", "execution_authorized": False},
            "qualified_optional_versions": {"mcp": "2.3.0", "pywin32": "312"},
            "read_only_mcp": {"module": "aegiscae.interfaces.mcp_read", "auto_start": False,
                              "binding": "UNBOUND_REQUIRES_EXPLICIT_TEST_PROJECT",
                              "tools": list(READ_TOOLS)},
            "desktop_activation": "NOT_TESTED", "github_installation": "PENDING_REVIEWED_PUSHED_REF",
            "operator_enforcement": "BLOCKED", "solver_authorized": False}
        need(json.dumps(runtime, sort_keys=True) == json.dumps(expected, sort_keys=True),
             "UNREVIEWED_RUNTIME_SURFACE")
        for role in ROLES:
            config = tomllib.loads(files[f"agents/{role}.toml"].decode("utf-8"))
            need(set(config) == {"name", "description", "developer_instructions", "features"}
                 and config["name"] == role
                 and type(config["developer_instructions"]) is str
                 and bool(config["developer_instructions"])
                 and config["features"] == {
                     "shell_tool": False, "apps": False, "plugins": False,
                     "memories": False, "request_permissions_tool": False},
                 "ROLE_POLICY_MISMATCH")
            need(all(value is False for value in config["features"].values()),
                 "ROLE_POLICY_MISMATCH")
        return runtime
    except SetupBlocked:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError):
        raise SetupBlocked("PACKAGE_DECLARATION_INVALID") from None


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
            "commands": [["codex", "plugin", "marketplace", "add", repository, "--ref", ref]],
            "activation": "OFFICIAL_DESKTOP_PLUGIN_DIRECTORY_MANUAL_STEP",
            "github_installation": "NOT_TESTED"}


def doctor(workspace: Path | None = None) -> dict:
    package_files = read_package()
    digest = content_digest(package_files)
    runtime = validate_package(package_files)
    dependencies = {}
    for name, expected in runtime["qualified_optional_versions"].items():
        try:
            current = metadata.version(name)
            dependencies[name] = "QUALIFIED_VERSION_PRESENT" if current == expected else "UNQUALIFIED_VERSION"
        except metadata.PackageNotFoundError:
            dependencies[name] = "MISSING"
    # Discover only a top-level module; do not import its code or any AF module.
    try:
        core = "DISCOVERABLE_NOT_IMPORTED" if find_spec("aegiscae") else "MISSING"
    except (ImportError, ValueError):
        core = "UNKNOWN"
    qualifications = {}
    for name, distribution in (("aegiscae", "aegiscae"),
                               ("abqjobpilot", "abqjobpilot_gdcae_internal")):
        try:
            record = installed_package(name, distribution)
            qualifications[name] = {"status": "RECORD_VERIFIED", **record["receipt"]}
        except (SetupBlocked, ImportError, ValueError):
            qualifications[name] = {"status": "NOT_INSTALLED_OR_INVALID"}
    workspace_check = {"status": "NOT_REQUESTED", "native_role_loading": "NOT_TESTED"}
    if workspace is not None:
        try:
            workspace_check = inspect_workspace(workspace)
        except (SetupBlocked, OSError, ValueError):
            workspace_check = {"status": "INVALID_WORKSPACE_CLOSURE",
                               "native_role_loading": "NOT_TESTED"}
    try:
        plugin_copy = installed_plugin_copy()
    except (SetupBlocked, ImportError, ValueError):
        plugin_copy = {"status": "SOURCE_OR_UNQUALIFIED_COPY", "desktop_activation": "NOT_TESTED"}
    return {"schema": "gdcae-doctor-v1", "windows": os.name == "nt",
            "python_supported": (3, 12) <= sys.version_info[:2] < (4, 0),
            "python": ".".join(map(str, sys.version_info[:3])),
            "package_sha256": digest, "plugin_activation": "NOT_TESTED",
            "research_core": core,
            "installed_packages": qualifications, "workspace": workspace_check,
            "plugin_copy": plugin_copy,
            "native_role_loading": "NOT_TESTED", "repository_access": "UNKNOWN",
            "runtime_contract": "PACKAGE_DECLARATIONS_VERIFIED",
            "optional_dependencies": dependencies,
            "read_only_mcp": "UNBOUND_REQUIRES_EXPLICIT_TEST_PROJECT",
            "github_installation": "PENDING_REVIEWED_PUSHED_REF",
            "abaqus_license": "NOT_TESTED", "af_dynamic_dispatch": "NOT_QUALIFIED",
            "operator_isolation": "BLOCKED_HIL_STRONG_ISOLATION",
            "real_execution_authorized": False}


def installed_package(package: str, distribution: str, *,
                      expected_version: str = "0.0.0+g3d6") -> dict:
    """Check interpreter installation/RECORD consistency, not publisher authenticity."""
    need((package, distribution) in {("aegiscae", "aegiscae"),
         ("abqjobpilot", "abqjobpilot_gdcae_internal")}, "UNKNOWN_DISTRIBUTION")
    need(expected_version in {"0.0.0+g3d6", "0.0.0+d7r2f"}, "INSTALLED_VERSION_MISMATCH")
    code = "INSTALLED_CORE_REQUIRED"
    core = find_spec(package)
    need(core is not None and core.origin is not None, code)
    origin = Path(core.origin).resolve()
    roots = {Path(sysconfig.get_path(key)).resolve() for key in ("purelib", "platlib")}
    root = origin.parent.parent
    need(root in roots and origin == root / package / "__init__.py", code)
    try:
        dist = metadata.distribution(distribution)
        need(Path(dist.locate_file("")).resolve() == root, code)
        need(dist.version == expected_version, "INSTALLED_VERSION_MISMATCH")
        direct = dist.read_text("direct_url.json")
        if direct is not None:
            direct = json.loads(direct)
            need(isinstance(direct, dict) and not direct.get("dir_info", {}).get("editable"),
                 "EDITABLE_CORE_REJECTED")
        files = dist.files
        need(bool(files) and len(files) <= 1024, "CORE_RECORD_REQUIRED")
        records = {str(item).replace("\\", "/"): item for item in files}
        need(len(records) == len(files), "CORE_RECORD_DUPLICATE")
        need(any(name.endswith(".dist-info/RECORD") for name in records),
             "CORE_RECORD_REQUIRED")
        package_files = {name: item for name, item in records.items()
                         if name.startswith(package + "/")}
        need(package + "/__init__.py" in package_files, "CORE_RECORD_REQUIRED")
        for name, item in package_files.items():
            path = root / name
            need(path.resolve().is_relative_to(root / package), code)
            need(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)), code)
            if path.suffix == ".pyc":
                continue  # Installer-generated cache is not source provenance.
            need(path.is_file() and item.hash is not None and item.hash.mode == "sha256",
                 "CORE_RECORD_REQUIRED")
            need(path.stat().st_size <= 1048576, "CORE_RECORD_FILE_TOO_LARGE")
            body = path.read_bytes()
            actual = base64.urlsafe_b64encode(hashlib.sha256(body).digest()).rstrip(b"=").decode()
            need(actual == item.hash.value and len(body) == item.size,
                 "CORE_RECORD_DIGEST_MISMATCH")
        actual_files = {(p.relative_to(root).as_posix()) for p in (root / package).rglob("*")
                        if p.is_file() and p.suffix != ".pyc"}
        need(actual_files == {name for name in package_files if not name.endswith(".pyc")},
             "CORE_UNRECORDED_FILE")
        need(list(core.submodule_search_locations or []) == [str(origin.parent)], code)
        for name, module in tuple(sys.modules.items()):
            if name == package or name.startswith(package + "."):
                loaded = getattr(module, "__file__", None)
                need(loaded is not None and Path(loaded).resolve().is_relative_to(origin.parent), code)
        manifest = {name: item.hash.value for name, item in package_files.items()
                    if not name.endswith(".pyc")}
        receipt = {"distribution": distribution, "version": dist.version,
                   "source": "INTERPRETER_INSTALLATION_RECORD",
                   "package_files_sha256": hashlib.sha256(json.dumps(
                       manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                   "record_sha256": hashlib.sha256(dist.read_text("RECORD").encode()).hexdigest()}
    except (metadata.PackageNotFoundError, OSError, ValueError, TypeError, AttributeError) as exc:
        if isinstance(exc, SetupBlocked):
            raise
        raise SetupBlocked(code) from None
    return {"origin": origin, "receipt": receipt}



def activation_request(workspace: Path) -> dict:
    """Bounded UI handoff; no activation, configuration mutation or client launch."""
    closure = inspect_workspace(workspace)
    return {"schema": "gdcae-activation-request-v1", "plugin": "gdcae@gdcae-preview",
            "display_name": "GDCAE", "plugin_version": "0.1.0-alpha.5",
            "package_sha256": content_digest(read_package()),
            "role_sha256": closure["role_sha256"],
            "roles": list(ROLES), "status": "BLOCKED_USER_ACTION",
            "installed_copy": "NOT_OBSERVED", "desktop_activation": "NOT_TESTED",
            "native_role_loading": "NOT_TESTED", "global_configuration_changed": False,
            "execution_authorized": False,
            "action": "OPEN_DISPOSABLE_PROJECT_SELECT_OFFICIAL_PLUGIN_AND_SEND_TEXT",
            "human_steps": ["OPEN_PREPARED_DISPOSABLE_PROJECT",
                            "SELECT_GDCAE_IN_OFFICIAL_PLUGIN_UI",
                            "PASTE_BOUNDED_PROMPT_AND_SEND"],
            "paste_count": 1, "reply_options": ["已完成", "无法激活"],
            "ui_click_count": "NOT_OBSERVED_THREE_ACTION_TARGET",
            "authentication": "NOT_OBSERVED_NO_CREDENTIAL_READ",
            "prompt": "@GDCAE For this disposable text-only TEST_SYNTHETIC task, "
                      "delegate separately to gdcae-cae, gdcae-results, gdcae-inverse "
                      "and gdcae-reviewer. Each role must return its role name and "
                      "one boundary: allowed load, missing evidence, refusal of B "
                      "before A, or independent review limit. Main may use only "
                      "native delegation to these four roles. Delegated roles must "
                      "not use tools. Neither Main nor roles may "
                      "read files, execute code, access other chats, create Plans "
                      "or Grants, or claim numerical/physical validation. Main "
                      "must report actual plugin recognition and actual role "
                      "returns; do not substitute a default agent."}


def installed_plugin_copy() -> dict:
    """Qualification of this helper's installed bytes; not Desktop registration."""
    core = installed_package("aegiscae", "aegiscae")
    need(PACKAGE.resolve() == core["origin"].parent / "_gdcae_plugin",
         "INSTALLED_PLUGIN_COPY_REQUIRED")
    return {"status": "INSTALLED_RECORD_VERIFIED", "package_sha256":
            content_digest(read_package()), "distribution": core["receipt"],
            "desktop_activation": "NOT_TESTED", "native_role_loading": "NOT_TESTED"}


def verify_installed_core() -> Path:
    return installed_package("aegiscae", "aegiscae")["origin"]


def inspect_workspace(workspace: Path) -> dict:
    """Validate copied package/role bytes only; never claim host role activation."""
    need(workspace.is_absolute() and not any(p.is_symlink() or p.is_junction()
         for p in (workspace, *workspace.parents)), "INVALID_WORKSPACE_CLOSURE")
    files = read_package(workspace / "plugins/gdcae")
    need(content_digest(files) == content_digest(read_package()), "PACKAGE_DIGEST_MISMATCH")
    directory = workspace / ".codex/agents"
    need(not any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents)),
         "INVALID_WORKSPACE_CLOSURE")
    need({p.name for p in directory.iterdir()} == {role + ".toml" for role in ROLES},
         "ROLE_CLOSURE_MISMATCH")
    hashes = {}
    for role in ROLES:
        file = directory / (role + ".toml")
        need(file.is_file() and not file.is_symlink() and file.stat().st_size <= 65536,
             "ROLE_CLOSURE_MISMATCH")
        body = file.read_bytes()
        need(body == files[f"agents/{role}.toml"], "ROLE_CLOSURE_MISMATCH")
        hashes[role] = hashlib.sha256(body).hexdigest()
    return {"status": "PACKAGE_AND_FOUR_ROLE_BYTES_VERIFIED", "role_sha256": hashes,
            "native_role_loading": "NOT_TESTED", "plugin_activation": "NOT_TESTED"}


def initialize_research(workspace: Path, expected: str, name: str,
                        goal_min: str = "0.019", goal_max: str = "0.021") -> dict:
    """Freeze a new offline preview using an installed Core; never prepare B or a Grant."""
    need(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", name) is not None,
         "INVALID_PROJECT_NAME")
    core_info = installed_package("aegiscae", "aegiscae")
    from aegiscae.research.rod_preview import RodPreviewContract, create_preview
    from dataclasses import asdict

    contract = RodPreviewContract(goal_min_mm=goal_min, goal_max_mm=goal_max)
    # Validate before filesystem setup, and keep incomplete setup on any later failure.
    contract = RodPreviewContract.from_dict(asdict(contract))
    receipt = prepare_workspace(workspace, expected)
    closure = inspect_workspace(workspace)
    adapter = create_preview(workspace / "research", name, contract)
    state = adapter.inspect()
    source_receipt = {"schema": "gdcae-initialization-source-v1",
                      "plugin_package_sha256": receipt["package_sha256"],
                      "installed_core": core_info["receipt"], "role_sha256": closure["role_sha256"],
                      "source_ref": "CONTENT_ADDRESSED_LOCAL_BYTES",
                      "commit_inclusion": "NOT_ASSERTED", "execution_authorized": False}
    source_body = json.dumps(source_receipt, sort_keys=True, indent=2).encode()
    with (workspace / "gdcae-source-receipt.json").open("xb") as stream:
        stream.write(source_body)
    result = {"schema": "gdcae-research-init-v1", "project_created": True,
              "package_sha256": receipt["package_sha256"],
              "contract_sha256": contract.digest(), "project_revision": state["project_revision"],
              "evidence_mode": contract.evidence_mode, "maximum_solver_calls": 2,
              "core_origin": "INSTALLED_SITE_PACKAGES", "core_record": "SHA256_VERIFIED",
              "source_receipt_sha256": hashlib.sha256(source_body).hexdigest(),
              "role_configuration": closure["status"],
              "plugin_activation": "NOT_TESTED",
              "real_a": "NOT_RUN", "real_b": "NOT_RUN", "execution_authorized": False}
    with (workspace / "gdcae-research-init.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    return result


def initialize_real_research(workspace: Path, expected: str, name: str) -> dict:
    """Explicit new real-contract freeze, never installation, Plan or authorization."""
    need(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", name) is not None,
         "INVALID_PROJECT_NAME")
    core_info = installed_package("aegiscae", "aegiscae")
    from aegiscae.research.rod_real_project import create_real_research

    package = prepare_workspace(workspace, expected)
    closure = inspect_workspace(workspace)
    project = create_real_research(workspace / "research", name)
    state = project.inspect()
    need(state["execution_authorized"] is False, "UNEXPECTED_INITIALIZATION_AUTHORITY")
    receipt = {
        "schema": "gdcae-real-initialization-v1", "mode": "REAL_CONTRACT_FROZEN_NO_EXECUTION",
        "package_sha256": package["package_sha256"], "installed_core": core_info["receipt"],
        "role_sha256": closure["role_sha256"], "contract_sha256": state["contract_digest"],
        "project_revision": state["project_revision"], "research_project_id": state["research_project_id"],
        "maximum_solver_calls": 2, "plan_created": False, "grant_issued": False,
        "real_a": "NOT_READY", "real_b": "NOT_RUN", "plugin_activation": "NOT_TESTED",
        "source_ref": "CONTENT_ADDRESSED_LOCAL_BYTES", "execution_authorized": False}
    with (workspace / "gdcae-real-init.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
    # The Project's local identity is persisted, not emitted in the public CLI receipt.
    return {key: value for key, value in receipt.items() if key != "research_project_id"}


def main() -> int:
    if not (3, 12) <= sys.version_info[:2] < (4, 0):
        print('{"status":"BLOCKED","code":"PYTHON_312_OR_NEWER_REQUIRED"}')
        return 2
    parser = SafeArgumentParser(prog="gdcae-preview", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    diagnose = sub.add_parser("doctor")
    diagnose.add_argument("--workspace", type=Path)
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
    real_init = sub.add_parser("init-real-research")
    real_init.add_argument("--workspace", type=Path, required=True)
    real_init.add_argument("--expected-package-digest", required=True)
    real_init.add_argument("--name", required=True)
    activation = sub.add_parser("activation-request")
    activation.add_argument("--workspace", type=Path, required=True)
    plan = sub.add_parser("install-plan")
    plan.add_argument("--repository", required=True)
    plan.add_argument("--ref", required=True)
    try:
        args = parser.parse_args()
        if args.command == "doctor":
            result = doctor(args.workspace)
        elif args.command == "package-digest":
            result = {"package_sha256": content_digest(read_package())}
        elif args.command == "prepare-workspace":
            result = prepare_workspace(args.workspace, args.expected_package_digest)
        elif args.command == "init-research":
            result = initialize_research(args.workspace, args.expected_package_digest,
                                         args.name, args.goal_min_mm, args.goal_max_mm)
        elif args.command == "activation-request":
            result = activation_request(args.workspace)
        elif args.command == "init-real-research":
            result = initialize_real_research(args.workspace, args.expected_package_digest, args.name)
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
