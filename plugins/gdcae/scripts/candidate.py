"""Build inert, allowlisted internal source snapshots and pure-Python wheels.

No source hooks, subprocesses, network, installation or Git mutations are used.
The caller supplies an independently reviewed selection and base-commit record.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

STATUS = "INTERNAL_CANDIDATE_NOT_FOR_RELEASE"
VERSION = "0.0.0+g3d6"
PRODUCTS = {
    "gdcae": ("aegiscae", "src/aegiscae/", "aegiscae"),
    "af_develop": ("abqjobpilot_gdcae_internal", "abqjobpilot/", "abqjobpilot"),
}
HEX = re.compile(r"[0-9a-f]{64}")
PRIVATE = re.compile(
    rb"(?i)(?:codex:\/\/threads\/|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}|"
    rb"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    rb"\bsk-[a-z0-9_-]{24,}|\bBearer\s+[a-z0-9._-]{24,})"
)
TOP_FILES = {"README.md", "pyproject.toml", "LICENSE", "LICENSE.md", "LICENSE.txt",
             "NOTICE", "NOTICE.md", "NOTICE.txt"}


class CandidateBlocked(ValueError):
    """Bounded public codes, never caller-controlled text."""


def need(condition, code):
    if not condition:
        raise CandidateBlocked(code)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def no_links(path):
    need(path.is_absolute() and not any(p.is_symlink() or p.is_junction()
         for p in (path, *path.parents)), "UNSAFE_PATH")


def allowed_path(product, value):
    need(type(value) is str and len(value) <= 240 and
         re.fullmatch(r"[A-Za-z0-9_./ -]+", value) is not None, "INVALID_SELECTION_PATH")
    p = PurePosixPath(value)
    need(not p.is_absolute() and p.as_posix() == value and
         not {".", "..", ".git", "Kickoff_Docs", "CAE models", "__pycache__"} & set(p.parts),
         "INVALID_SELECTION_PATH")
    need(all(part == part.rstrip(". ") and part.split(".")[0].upper() not in
             {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
              *(f"LPT{i}" for i in range(1, 10))} for part in p.parts),
         "INVALID_SELECTION_PATH")
    package = PRODUCTS[product][1]
    runtime = value.startswith(package) and p.suffix in {".py", ".json", ".toml", ".txt"}
    plugin = product == "gdcae" and (
        value.startswith("plugins/gdcae/") or value.startswith(".codex/agents/")
        or value == ".agents/plugins/marketplace.json"
    ) and p.suffix in {".py", ".json", ".toml", ".md"}
    documentation = value.startswith("docs/architecture/7D_G2_") and p.suffix == ".md"
    fixture = value.startswith("tests/") and p.suffix == ".py"
    operator = product == "gdcae" and value in {
        "operator_deployment/preview.py", "operator_deployment/audit.py"}
    need(value in TOP_FILES or runtime or plugin or documentation or fixture or operator,
         "SELECTION_OUT_OF_SCOPE")
    # This reviewed runtime module implements credential handling; it is not a
    # credential record. Its exact bytes still pass every read_stable check.
    credential_source = (product, value) == (
        "af_develop", "abqjobpilot/local_credentials.py")
    need(credential_source or not any(word in p.name.lower()
         for word in ("auth.json", "credential", "secret")),
         "PRIVATE_MATERIAL_REJECTED")
    return value


def read_stable(path, expected):
    no_links(path)
    need(path.is_file() and path.stat().st_size <= 1048576, "SOURCE_FILE_INVALID")
    before = path.stat()
    body = path.read_bytes()
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "SOURCE_CHANGED")
    need(digest(body) == expected, "SOURCE_DIGEST_MISMATCH")
    need(not PRIVATE.search(body), "PRIVATE_MATERIAL_REJECTED")
    return body


def validate_selection(selection):
    need(type(selection) is dict and set(selection) == {
        "schema", "product", "base_commit", "files", "dirty_files", "license_status"
    }, "INVALID_SELECTION")
    need(selection["schema"] == "gdcae-source-selection-v1" and
         type(selection["product"]) is str and
         selection["product"] in PRODUCTS, "INVALID_SELECTION")
    need(type(selection["base_commit"]) is str and
         re.fullmatch(r"[0-9a-f]{40}", selection["base_commit"]), "INVALID_BASE_COMMIT")
    need(type(selection["license_status"]) is str and selection["license_status"] in
         {"REVIEWED_INTERNAL_ONLY", "UNRESOLVED_INTERNAL_ONLY"},
         "PUBLIC_RELEASE_NOT_AUTHORIZED")
    files = selection["files"]
    need(type(files) is dict and 1 <= len(files) <= 512, "INVALID_SELECTION")
    for name, sha in files.items():
        allowed_path(selection["product"], name)
        need(type(sha) is str and HEX.fullmatch(sha), "INVALID_SOURCE_DIGEST")
    need(len({name.casefold() for name in files}) == len(files), "CASE_COLLISION")
    dirty = selection["dirty_files"]
    need(type(dirty) is dict and set(dirty) <= set(files) and
         all(files[k] == v for k, v in dirty.items()), "DIRTY_RECORD_MISMATCH")
    need(PRODUCTS[selection["product"]][1] + "__init__.py" in files,
         "PACKAGE_MARKER_MISSING")


def zip_bytes(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, body in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, body)
    return stream.getvalue()


def wheel_bytes(product, files):
    distribution, prefix, package = PRODUCTS[product]
    payload = {package + "/" + name[len(prefix):]: body
               for name, body in files.items() if name.startswith(prefix)}
    if product == "gdcae":
        # Keep the exact reviewed plugin/roles inside the installed distribution,
        # covered by RECORD. Presence is not native role or Desktop activation.
        payload.update({"aegiscae/_gdcae_plugin/" + name[len("plugins/gdcae/"):]: body
                        for name, body in files.items()
                        if name.startswith("plugins/gdcae/")})
        # Reviewed deployment preview/audit resources, never auto-imported.
        payload.update({"aegiscae/_gdcae_operator/" + name.split("/")[-1]: body
                        for name, body in files.items() if name in {
                            "operator_deployment/preview.py", "operator_deployment/audit.py"}})
    need(package + "/__init__.py" in payload, "PACKAGE_MARKER_MISSING")
    dist_info = f"{distribution}-{VERSION}.dist-info"
    payload[dist_info + "/METADATA"] = (
        "Metadata-Version: 2.1\n"
        f"Name: {distribution}\nVersion: {VERSION}\nRequires-Python: >=3.12,<4\n"
        "Summary: Internal reviewed source snapshot; not a public release\n\n"
        "No third-party dependencies are bundled. Qualification covers only the\n"
        "reviewed offline runtime paths; optional product dependencies remain unqualified.\n"
    ).encode()
    payload[dist_info + "/WHEEL"] = (
        "Wheel-Version: 1.0\nGenerator: gdcae-reviewed-stdlib-snapshot\n"
        "Root-Is-Purelib: true\nTag: py3-none-any\n"
    ).encode()
    rows = []
    for name, body in sorted(payload.items()):
        sha = base64.urlsafe_b64encode(hashlib.sha256(body).digest()).rstrip(b"=").decode()
        rows.append((name, "sha256=" + sha, str(len(body))))
    rows.append((dist_info + "/RECORD", "", ""))
    csv_stream = io.StringIO(newline="")
    csv.writer(csv_stream, lineterminator="\n").writerows(rows)
    payload[dist_info + "/RECORD"] = csv_stream.getvalue().encode()
    return f"{distribution}-{VERSION}-py3-none-any.whl", zip_bytes(payload)


def export_snapshot(source_root, selection, destination):
    """Exclusive write, exact bytes. Partial output is retained after an interruption."""
    source_root, destination = Path(source_root), Path(destination)
    validate_selection(selection)
    no_links(source_root)
    no_links(destination)
    need(source_root.is_dir() and destination.parent.is_dir() and not destination.exists(),
         "FRESH_DESTINATION_REQUIRED")
    need(not destination.resolve().is_relative_to(source_root.resolve()),
         "SOURCE_DESTINATION_REJECTED")
    files = {}
    total = 0
    for name, sha in selection["files"].items():
        body = read_stable(source_root / name, sha)
        total += len(body)
        need(total <= 33554432, "SELECTION_TOO_LARGE")
        files[name] = body
    wheel_name, wheel = wheel_bytes(selection["product"], files)
    manifest = {"schema": "gdcae-internal-candidate-v1", "status": STATUS,
                "release_ref": "PENDING_RELEASE_REF", "selection": selection,
                "selection_sha256": digest(canonical(selection)),
                "dependency_qualification": "OFFLINE_RUNTIME_SUBSET_ONLY",
                "installation": "NOT_PERFORMED", "real_execution_authorized": False}
    manifest_bytes = canonical(manifest)
    notice = (
        "INTERNAL_CANDIDATE_NOT_FOR_RELEASE\n"
        "No publication or third-party relicensing authorization. License review remains\n"
        "as recorded in the manifest. No real Solver, Grant or Operator isolation claim.\n"
    ).encode()
    source_zip = zip_bytes({**{"source/" + k: v for k, v in files.items()},
                            "CANDIDATE_MANIFEST.json": manifest_bytes,
                            "NOTICE_INTERNAL.txt": notice})
    artifacts = {"CANDIDATE_MANIFEST.json": manifest_bytes,
                 "NOTICE_INTERNAL.txt": notice, "source.zip": source_zip, wheel_name: wheel}
    destination.mkdir()
    for name, body in files.items():
        target = destination / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(body)
    for name, body in artifacts.items():
        with (destination / name).open("xb") as stream:
            stream.write(body)
    artifact_hashes = {name: digest(body) for name, body in artifacts.items()}
    with (destination / "SHA256SUMS.json").open("x", encoding="utf-8") as stream:
        json.dump(artifact_hashes, stream, sort_keys=True, indent=2)
    return {"status": STATUS, "product": selection["product"], "files": len(files),
            "selection_sha256": manifest["selection_sha256"], "artifacts": artifact_hashes,
            "real_execution_authorized": False, "release_ref": "PENDING_RELEASE_REF"}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise CandidateBlocked("INVALID_ARGUMENTS")


def main():
    parser = SafeParser(prog="gdcae-candidate")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    try:
        args = parser.parse_args()
        no_links(args.selection)
        need(args.selection.is_file() and args.selection.stat().st_size <= 262144,
             "INVALID_SELECTION")
        selection = json.loads(args.selection.read_text(encoding="utf-8"))
        print(json.dumps(export_snapshot(args.source_root, selection, args.destination),
                         sort_keys=True))
        return 0
    except CandidateBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "code": str(exc)}))
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
        print('{"status":"BLOCKED","code":"CANDIDATE_IO_OR_SCHEMA_FAILED"}')
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
