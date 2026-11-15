"""Emit an external receipt after a private release has been independently read back."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

PRODUCT = "gdcae-research"
PLUGIN_ID = "plugins_6af978c244ec8191ba521a0eb8bb949d"
REPOSITORY = "BrunelXian/Goal-Driven-CAE-Orchestrator"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def make_receipt(candidate, report, inventory):
    evidence = json.loads(report.read_bytes())
    version = evidence["version"]
    if (evidence["plugin_id"] != PLUGIN_ID or evidence["scope"] != "USER"
            or evidence["visibility"] != "PRIVATE" or evidence["PRIVATE_PLUGIN_UPDATE"] != "PASS"
            or not re.fullmatch(r"0\.2\.0-preview\.[1-9][0-9]{0,5}", version)
            or not re.fullmatch(r"pluginrel_[0-9a-f]{32}", evidence["release_id"])
            or not re.fullmatch(r"[0-9a-f]{40}", evidence["source_commit"])):
        raise ValueError("invalid publisher or release evidence")
    with ZipFile(candidate) as archive:
        files = {name: digest(archive.read(name)) for name in archive.namelist()}
        manifest = json.loads(archive.read("package-manifest.json"))
        meta = json.loads(archive.read("plugin.json"))
        if (len(files) != len(archive.namelist()) or meta["name"] != PRODUCT
                or meta["version"] != version or manifest["version"] != version
                or manifest["files"] != {k: v for k, v in files.items() if k != "package-manifest.json"}):
            raise ValueError("inconsistent release archive")
    rows = json.loads(inventory.read_bytes())
    stored = {row["path"]: row for row in rows}
    extra = ".codex-plugin/plugin.json"
    if (len(stored) != len(rows) or set(stored) != set(files) | {extra}
            or any(stored[k]["candidate_sha256"] != h or stored[k]["platform_sha256"] != h for k, h in files.items())
            or evidence["original_files_byte_exact"] != len(files) or evidence["platform_files"] != len(rows)
            or evidence["metadata_validation"] != "Matched plugin_creator_compat_sha256 in pinned manifest"
            or not re.fullmatch(r"[0-9a-f]{64}", stored[extra]["platform_sha256"])):
        raise ValueError("incomplete or mismatched platform readback")
    zip_sha = digest(candidate.read_bytes())
    pin = files["package-manifest.json"]
    if pin != evidence["manifest_sha256"] or zip_sha != evidence["candidate_zip_sha256"]:
        raise ValueError("package disagrees with release evidence")
    return dict(schema=1, repository=REPOSITORY, product=PRODUCT, channel="plugin-creator-private",
                plugin_id=PLUGIN_ID, release_id=evidence["release_id"], version=version,
                source_commit=evidence["source_commit"], manifest_sha256=pin, zip_sha256=zip_sha)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "readback_report", "readback_inventory", "output_directory"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    record = make_receipt(args.candidate, args.readback_report, args.readback_inventory)
    destination = args.output_directory / (record["version"] + ".json")
    with destination.open("x", encoding="ascii", newline="\n") as out:
        out.write(json.dumps(record, indent=2) + "\n")
