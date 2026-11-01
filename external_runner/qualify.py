"""Inert on import. Execution requires a separately approved independent Windows VM.

No solver/Owner/Codex calls; no network, source hooks, global setup or custom Job manager.
An explicit human attestation is a prerequisite, not machine proof of independence.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

PYTHON_VERSION = "3.12.10"
STAGES = ("venv", "install", "smoke")
CLAIMS = ("install", "import_record", "plugin_resources", "doctor", "init",
          "offline_project_smoke", "real_contract_freeze", "no_execution_authority")


class Blocked(ValueError):
    pass


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise Blocked("INVALID_ARGUMENTS")


def need(condition, code):
    if not condition:
        raise Blocked(code)


def sha(body):
    return hashlib.sha256(body).hexdigest()


def no_links(path):
    need(path.is_absolute() and not any(p.is_symlink() or p.is_junction()
         for p in (path, *path.parents)), "PATH_REJECTED")


def verify_bundle(root, expected):
    no_links(root)
    need(type(expected) is str and re.fullmatch(r"[a-f0-9]{64}", expected), "DIGEST_REQUIRED")
    manifest_path = root / "BUNDLE.json"
    no_links(manifest_path)
    need(manifest_path.stat().st_size < 262144, "MANIFEST_TOO_LARGE")
    body = manifest_path.read_bytes()
    need(sha(body) == expected, "MANIFEST_CHANGED")
    manifest = json.loads(body)
    need(set(manifest) == {"schema", "status", "files", "wheels", "python",
                          "provenance", "execution_authorized"}, "INVALID_MANIFEST")
    need(manifest["schema"] == "gdcae-external-bundle-v1"
         and manifest["status"] == "NOT_RUN_EXTERNALLY"
         and manifest["execution_authorized"] is False
         and manifest["python"] == PYTHON_VERSION, "INVALID_MANIFEST")
    files = manifest["files"]
    need(type(files) is dict and 5 <= len(files) <= 100, "INVALID_MANIFEST")
    need(len({p.casefold() for p in files}) == len(files), "CASE_COLLISION")
    total = 0
    for name, digest in files.items():
        need(type(name) is str and re.fullmatch(r"[A-Za-z0-9_./+-]+", name)
             and not PurePosixPath(name).is_absolute()
             and ".." not in name.split("/") and PurePosixPath(name).as_posix() == name,
             "PATH_REJECTED")
        need(type(digest) is str and re.fullmatch(r"[a-f0-9]{64}", digest), "INVALID_MANIFEST")
        path = root / name
        no_links(path)
        need(path.is_file() and path.stat().st_size < 33554432, "INPUT_INVALID")
        data = path.read_bytes()
        total += len(data)
        need(total < 67108864 and sha(data) == digest, "INPUT_CHANGED")
    need({p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
         == set(files) | {"BUNDLE.json"}, "UNDECLARED_INPUT")
    wheels = manifest["wheels"]
    need(type(wheels) is list and len(wheels) == 2 and len(set(wheels)) == 2
         and all(w in files and re.fullmatch(r"wheels/[A-Za-z0-9_.+-]+\.whl", w)
                 for w in wheels), "INVALID_WHEELS")
    need({"qualify.py", "smoke.py", "README.md"} <= set(files), "ENTRYPOINT_MISSING")
    return manifest


def run_step(argv, cwd):
    # Timeouts make family completion UNKNOWN; no claim that killing the direct
    # child proves descendant exit. Never retry or proceed to another stage.
    return subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          timeout=180, check=False).returncode


def qualify(root, destination, expected, *, approved=False, independent=False,
            runner=run_step, system=None, version=None):
    need(approved is True and independent is True, "EXTERNAL_APPROVAL_REQUIRED")
    need((os.name if system is None else system) == "nt", "WINDOWS_REQUIRED")
    need((sys.version.split()[0] if version is None else version) == PYTHON_VERSION,
         "PYTHON_VERSION_MISMATCH")
    manifest = verify_bundle(root, expected)
    no_links(destination)
    need(destination.parent.is_dir() and not destination.exists()
         and not destination.is_relative_to(root), "FRESH_EXTERNAL_DESTINATION_REQUIRED")
    destination.mkdir()
    python = destination / "venv/Scripts/python.exe"
    commands = (
        [sys.executable, "-I", "-m", "venv", str(destination / "venv")],
        [str(python), "-I", "-m", "pip", "--isolated", "install", "--no-index",
         "--no-deps", "--disable-pip-version-check", "--no-compile",
         *(str(root / w) for w in manifest["wheels"])],
        [str(python), "-I", str(root / "smoke.py"), str(destination)],
    )
    receipt = {"schema": "gdcae-external-receipt-v1", "status": "IN_PROGRESS",
               "bundle_sha256": expected, "python": PYTHON_VERSION,
               "windows_version": list(sys.getwindowsversion()[:3]) if os.name == "nt" else [],
               "stages": [], "claims": dict.fromkeys(CLAIMS, "NOT_RUN"),
               "family_finalization": "NOT_VERIFIED", "external_root": "HUMAN_ATTESTED",
               "desktop_activation": "NOT_TESTED", "fake_ipc": "NOT_RUN",
               "fake_ipc_qualification": "DEPENDENCIES_AND_SUPPORT_DELIVERY_NOT_QUALIFIED",
               "real_execution_authorized": False}

    def persist():
        # New sequence files preserve crash history; never mutate original receipts.
        target = destination / ("receipt-" + str(len(receipt["stages"])) + ".json")
        with target.open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, sort_keys=True)

    persist()
    for stage, command in zip(STAGES, commands, strict=True):
        try:
            code = runner(command, destination)
            need(type(code) is int, "INVALID_PROCESS_RESPONSE")
            receipt["stages"].append({"stage": stage, "exit_code": code})
            if code != 0:
                receipt["status"] = "FAILED"
                persist()
                return receipt
        except (OSError, subprocess.TimeoutExpired, Blocked):
            receipt["stages"].append({"stage": stage, "exit_code": None})
            receipt["status"] = "UNKNOWN_STOP"
            persist()
            return receipt
        if stage == "smoke":
            try:
                result_path = destination / "smoke.json"
                no_links(result_path)
                need(result_path.stat().st_size < 4096, "INVALID_SMOKE")
                result = json.loads(result_path.read_bytes())
                need(result == dict.fromkeys(CLAIMS, "PASS"), "INVALID_SMOKE")
                receipt["claims"] = result
                receipt["status"] = "NO_SOLVER_SMOKE_PASS"
            except (OSError, ValueError, Blocked):
                receipt["status"] = "FAILED_SMOKE_EVIDENCE"
        persist()
    return receipt


def main():
    parser = SafeParser(description="Separately approved external VM only")
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--approved-independent-vm", action="store_true")
    try:
        args = parser.parse_args()
        result = qualify(Path(__file__).resolve().parent, args.destination,
                         args.bundle_sha256, approved=args.approved_independent_vm,
                         independent=args.approved_independent_vm)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "NO_SOLVER_SMOKE_PASS" else 2
    except (Blocked, OSError, ValueError):
        print('{"status":"BLOCKED","code":"EXTERNAL_PREFLIGHT_FAILED"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
