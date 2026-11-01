"""Package/RECORD closure tests use in-memory wheels; no installer or process."""

import base64
import csv
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import io
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = spec_from_file_location(name, ROOT / path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate = load("d3_candidate", "plugins/gdcae/scripts/candidate.py")
setup = load("d3_setup", "plugins/gdcae/scripts/gdcae.py")
package = load("d3_package", "external_runner/package.py")
runner = load("d3_qualify", "external_runner/qualify.py")


def test_wheel_contains_all_exact_plugin_and_role_bytes_in_record():
    files = {"src/aegiscae/__init__.py": b"# fixture\n"}
    files.update({"plugins/gdcae/" + k: v for k, v in setup.read_package().items()})
    _, body = candidate.wheel_bytes("gdcae", files)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        records = next(n for n in archive.namelist() if n.endswith(".dist-info/RECORD"))
        rows = {row[0]: row[1:] for row in csv.reader(io.StringIO(archive.read(records).decode()))}
        for path, expected in setup.read_package().items():
            name = "aegiscae/_gdcae_plugin/" + path
            assert archive.read(name) == expected
            digest = base64.urlsafe_b64encode(hashlib.sha256(expected).digest()).rstrip(b"=")
            assert rows[name] == ["sha256=" + digest.decode(), str(len(expected))]


def snapshot(tmp_path, product):
    source = tmp_path / (product + "-source")
    prefix = candidate.PRODUCTS[product][1]
    files = {prefix + "__init__.py": b"# fixture\n"}
    if product == "gdcae":
        files.update({"plugins/gdcae/" + k: v for k, v in setup.read_package().items()})
    for name, body in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    hashes = {k: candidate.digest(v) for k, v in files.items()}
    selection = {"schema": "gdcae-source-selection-v1", "product": product,
                 "base_commit": "a" * 40, "files": hashes, "dirty_files": hashes,
                 "license_status": "UNRESOLVED_INTERNAL_ONLY"}
    destination = tmp_path / product
    result = candidate.export_snapshot(source, selection, destination)
    return destination, result["artifacts"]["CANDIDATE_MANIFEST.json"]


def test_two_snapshot_bundle_exact_source_provenance_and_not_run(tmp_path):
    gd, gsha = snapshot(tmp_path, "gdcae")
    af, asha = snapshot(tmp_path, "af_develop")
    runner_root = ROOT / "external_runner"
    hashes = {n: candidate.digest((runner_root / n).read_bytes()) for n in package.RUNNER_FILES}
    result = package.assemble(gd, af, tmp_path / "bundle", runner_root, hashes,
                              gd_manifest_sha256=gsha, af_manifest_sha256=asha)
    verified = runner.verify_bundle(tmp_path / "bundle", result["manifest_sha256"])
    assert verified["status"] == "NOT_RUN_EXTERNALLY"
    assert result["source_ref"] == "REVIEWED_DIRTY_SNAPSHOT"
    assert verified["execution_authorized"] is False
    assert len(verified["wheels"]) == 2


@pytest.mark.parametrize("damage", ["source", "wheel", "manifest"])
def test_snapshot_damage_cannot_be_repackaged(tmp_path, damage):
    gd, expected = snapshot(tmp_path, "gdcae")
    target = {"source": gd / "source/src/aegiscae/__init__.py",
              "wheel": next(gd.glob("*.whl")), "manifest": gd / "CANDIDATE_MANIFEST.json"}[damage]
    target.write_bytes(b"changed")
    with pytest.raises(package.PackageBlocked, match="INPUT_CHANGED"):
        package.snapshot_payload(gd, "gdcae", expected)
