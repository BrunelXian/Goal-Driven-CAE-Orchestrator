"""Build the local Codex marketplace archive from an immutable Git revision."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import zipfile


def git(*args):
    return subprocess.check_output(["git", *args], cwd=Path(__file__).resolve().parents[3])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    commit = git("rev-parse", "--verify", "--end-of-options", args.ref + "^{commit}").decode().strip()
    base = "product/vericae/"
    catalog = ".agents/plugins/marketplace.json"
    release_docs = ("INSTALL.md", "RELEASE_NOTES.md")
    listing = git("ls-tree", "-rz", commit, "--", base + "vericae-research/",
                  base + catalog, *(base + "release/" + name for name in release_docs))
    files = {}
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        header, path = entry.decode().split("\t", 1)
        mode, kind, oid = header.split()
        if kind != "blob" or mode != "100644":
            raise ValueError(f"Unexpected release entry: {path}")
        member = path.removeprefix(base).removeprefix("release/")
        files[member] = git("cat-file", "blob", oid)

    version = json.loads(files["vericae-research/release.json"])["product_version"]
    if version != "1.0.0" or not {catalog, *release_docs} <= files.keys():
        raise ValueError("Expected the complete 1.0.0 release tree")
    files["SOURCE_COMMIT"] = (commit + "\n").encode()
    files["FILES.sha256"] = "".join(
        f"{sha256(content).hexdigest()}  {name}\n" for name, content in sorted(files.items())
    ).encode()

    args.output.mkdir(parents=True, exist_ok=False)
    archive = args.output / f"VeriCAE-{version}.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED) as bundle:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, content)
    (args.output / "FILES.sha256").write_bytes(files["FILES.sha256"])
    checksum = f"{sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n"
    archive.with_suffix(".zip.sha256").write_bytes(checksum.encode())
    print(checksum.rstrip())


if __name__ == "__main__":
    main()
