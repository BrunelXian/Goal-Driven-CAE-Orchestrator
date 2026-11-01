"""Assemble two previously reviewed snapshots; never build/install/run their code."""

import hashlib
import json
from pathlib import Path
import re
import zipfile
import io
import ast
import sys

RUNNER_FILES = ("qualify.py", "smoke.py", "README.md")
OPERATOR_FILES = ("operator_deployment/preview.py", "operator_deployment/audit.py")
FAKE_SUPPORT = ("g2_fake_rehearsal.py", "supervisor_helpers.py", "execution_helpers.py",
                "run003_process.py", "reconciliation_helpers.py")
FAKE_DEPENDENCIES = {"pytest": "9.1.0", "colorama": "0.4.6", "iniconfig": "2.3.0",
                     "packaging": "26.2", "pluggy": "1.6.0", "pygments": "2.20.0"}
DEPENDENCY_LICENSES = {"pytest": "MIT", "colorama": "BSD_CLASSIFIER_EXACT_TERMS_REVIEW_PENDING",
                      "iniconfig": "MIT", "packaging": "Apache-2.0 OR BSD-2-Clause",
                      "pluggy": "MIT", "pygments": "BSD-2-Clause"}


class PackageBlocked(ValueError):
    pass


def need(condition, code):
    if not condition:
        raise PackageBlocked(code)


def sha(body):
    return hashlib.sha256(body).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def read_exact(path, expected):
    need(path.is_absolute() and not any(p.is_symlink() or p.is_junction()
         for p in (path, *path.parents)), "LINK_REJECTED")
    need(path.is_file() and path.stat().st_size < 33554432, "FILE_INVALID")
    body = path.read_bytes()
    need(sha(body) == expected, "INPUT_CHANGED")
    return body


def fake_support_payload(root, expected_hashes):
    """Copy only exact reviewed source; never import the native test harness."""
    need(type(expected_hashes) is dict and set(expected_hashes) == set(FAKE_SUPPORT),
         "FAKE_SUPPORT_ALLOWLIST_INVALID")
    local_modules = {Path(name).stem for name in FAKE_SUPPORT}
    result = {}
    for name in FAKE_SUPPORT:
        body = read_exact(root / name, expected_hashes[name])
        need(len(body) <= 65536, "FAKE_SUPPORT_TOO_LARGE")
        need(not re.search(rb"(?i)(codex://threads/|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
                           rb"\bsk-[a-z0-9_-]{24,}|\bBearer\s+[a-z0-9._-]{24,})", body),
             "FAKE_SUPPORT_PRIVATE_MATERIAL")
        try:
            tree = ast.parse(body.decode("utf-8-sig"))
        except (SyntaxError, UnicodeError):
            raise PackageBlocked("FAKE_SUPPORT_SYNTAX_INVALID") from None
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                need(node.level == 0 and node.module is not None,
                     "FAKE_SUPPORT_IMPORT_CLOSURE")
                imports.add(node.module.split(".")[0])
        need(imports <= set(sys.stdlib_module_names) | local_modules | {"pytest", "abqjobpilot"},
             "FAKE_SUPPORT_IMPORT_CLOSURE")
        result["support/fake_ipc/" + name] = body
    return result


def dependency_manifest():
    """Pinned preparation record; no wheel download, installation or authenticity claim."""
    return {"schema": "gdcae-external-dependency-profile-v1", "python": "3.12.10",
            "platform": "win32", "fake_ipc": dict(FAKE_DEPENDENCIES),
            "license_metadata": dict(DEPENDENCY_LICENSES),
            "license_review": "INTERNAL_METADATA_ONLY_PUBLIC_REDISTRIBUTION_NOT_APPROVED",
            "profile_basis": "PYTEST_9_1_0_WINDOWS_PYTHON312_METADATA_NO_EXTRAS",
            "optional_operator_audit": {"pywin32": "312", "license_metadata": "PSF"},
            "optional_mcp": {"mcp": "2.3.0", "dependency_closure": "NOT_INCLUDED"},
            "dependency_wheels_included": False, "wheelhouse_sha256": None,
            "delivery": "SEPARATE_APPROVED_HASH_PINNED_WHEELHOUSE_REQUIRED",
            "network": "NO_AUTOMATIC_DOWNLOAD", "installation": "NOT_RUN"}


def snapshot_payload(root, product, expected_manifest):
    manifest_body = read_exact(root / "CANDIDATE_MANIFEST.json", expected_manifest)
    manifest = json.loads(manifest_body)
    selection = manifest["selection"]
    need(manifest["schema"] == "gdcae-internal-candidate-v1"
         and manifest["status"] == "INTERNAL_CANDIDATE_NOT_FOR_RELEASE"
         and manifest["installation"] == "NOT_PERFORMED"
         and manifest["real_execution_authorized"] is False
         and selection["product"] == product
         and manifest["selection_sha256"] == sha(canonical(selection)), "MANIFEST_INVALID")
    for name, digest in selection["files"].items():
        need(re.fullmatch(r"[A-Za-z0-9_./+-]+", name) and ".." not in name.split("/")
             and not name.startswith("/"), "PATH_REJECTED")
        read_exact(root / "source" / name, digest)
    need(set(selection["dirty_files"]) <= set(selection["files"])
         and all(selection["files"][k] == v for k, v in selection["dirty_files"].items()),
         "DIRTY_PROVENANCE_INVALID")
    wheels = list(root.glob("*.whl"))
    need(len(wheels) == 1, "WHEEL_COUNT")
    # Regenerate exact wheel bytes in memory from the reviewed source snapshot.
    # The local audited builder, not candidate-source code, supplies the format.
    from importlib.util import module_from_spec, spec_from_file_location
    script = Path(__file__).resolve().parents[1] / "plugins/gdcae/scripts/candidate.py"
    spec = spec_from_file_location("d3_audited_builder", script)
    builder = module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.validate_selection(selection)
    files = {name: builder.read_stable(root / "source" / name, digest)
             for name, digest in selection["files"].items()}
    wheel_name, expected_body = builder.wheel_bytes(product, files)
    need(wheels[0].name == wheel_name, "WHEEL_IDENTITY")
    wheel_body = read_exact(wheels[0], sha(expected_body))
    if product == "gdcae":
        required = {"plugin.json", "scripts/gdcae.py", "scripts/candidate.py",
                    "skills/setup/SKILL.md", "skills/research/SKILL.md", "references/handoff.md",
                    "references/runtime-contract.json",
                    *("agents/" + role + ".toml" for role in
                      ("gdcae-cae", "gdcae-results", "gdcae-inverse", "gdcae-reviewer"))}
        with zipfile.ZipFile(io.BytesIO(wheel_body)) as archive:
            need({"aegiscae/_gdcae_plugin/" + p for p in required} <= set(archive.namelist()),
                 "PLUGIN_CLOSURE_MISSING")
    return wheel_name, wheel_body, manifest_body


def assemble(gd_snapshot, af_snapshot, destination, runner_root, expected_runner_hashes,
             *, gd_manifest_sha256, af_manifest_sha256, fake_ipc_support_hashes=None,
             fake_ipc_support_root=None):
    """Exact entry digest approval is external to this builder; no source-ref fiction."""
    need(set(expected_runner_hashes) == set(RUNNER_FILES), "RUNNER_ALLOWLIST_INVALID")
    need(destination.is_absolute() and destination.parent.is_dir() and not destination.exists()
         and not any(p.is_symlink() or p.is_junction()
                     for p in (destination, *destination.parents)), "FRESH_DESTINATION_REQUIRED")
    payload = {name: read_exact(runner_root / name, digest)
               for name, digest in expected_runner_hashes.items()}
    provenance = {}
    wheels = []
    for product, source, expected in (("gdcae", gd_snapshot, gd_manifest_sha256),
                                      ("af_develop", af_snapshot, af_manifest_sha256)):
        name, body, manifest = snapshot_payload(source, product, expected)
        payload["wheels/" + name] = body
        wheels.append("wheels/" + name)
        payload["provenance/" + product + ".json"] = manifest
        provenance[product] = sha(manifest)
        if product == "gdcae":
            files = json.loads(manifest)["selection"]["files"]
            selected = set(OPERATOR_FILES) & set(files)
            need(not selected or selected == set(OPERATOR_FILES), "OPERATOR_CLOSURE_INCOMPLETE")
            for name in sorted(selected):
                payload["support/" + name] = read_exact(source / "source" / name, files[name])
    support = {} if fake_ipc_support_hashes is None else fake_ipc_support_hashes
    need(type(support) is dict and (not support or set(support) == set(FAKE_SUPPORT))
         and all(type(v) is str and re.fullmatch(r"[a-f0-9]{64}", v)
                 for v in support.values()), "FAKE_SCENARIO_HASHES_INVALID")
    included = fake_ipc_support_root is not None
    if included:
        payload.update(fake_support_payload(fake_ipc_support_root, support))
    payload["support/DEPENDENCIES.json"] = canonical(dependency_manifest())
    payload["support/FAKE_IPC_SCENARIO.json"] = canonical({
        "schema": "gdcae-external-fake-scenario-v1", "status": "NOT_RUN",
        "qualification": "DEPENDENCY_WHEELHOUSE_AND_EXTERNAL_EXECUTION_NOT_QUALIFIED"
                         if included else "DEPENDENCIES_AND_SUPPORT_DELIVERY_NOT_QUALIFIED",
        "support_hashes": support, "support_included": included,
        "required_dependencies": dict(FAKE_DEPENDENCIES),
        "local_import_closure": "STATIC_AST_CHECKED" if included else "NOT_CHECKED",
        "harness_imported_or_executed": False,
        "existing_entry": "g2_fake_rehearsal.FakeRehearsal",
        "scenario": ["new_isolated_TEST_ONLY_Project", "one_fake_owner",
                     "original_receipt_run_events_validation",
                     "wrong_receipt_and_replay_refusal",
                     "original_process_handles_signaled"],
        "completion_evidence": ["normal_exit", "all_owned_processes_exited",
                                "actual_process_handle_signaled"],
        "failure": "UNKNOWN_STOP_NO_RETRY_NO_UNKNOWN_PROCESS_CLEANUP",
        "execution_authorized": False, "real_grant_allowed": False,
        "synthetic_numeric_source": "SYNTHETIC_DAT_NOT_ABAQUS",
        "real_validation": "NOT_VERIFIED"})
    manifest = {"schema": "gdcae-external-bundle-v1", "status": "NOT_RUN_EXTERNALLY",
                "python": "3.12.10", "files": {k: sha(v) for k, v in payload.items()},
                "wheels": wheels, "provenance": provenance, "execution_authorized": False}
    payload["BUNDLE.json"] = canonical(manifest)
    destination.mkdir()
    for name, body in payload.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(body)
    return {"status": "NOT_RUN_EXTERNALLY", "manifest_sha256": sha(payload["BUNDLE.json"]),
            "files": len(payload), "source_ref": "REVIEWED_DIRTY_SNAPSHOT",
            "execution_authorized": False}
