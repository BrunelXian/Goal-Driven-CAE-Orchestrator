"""Operator-only provisioning of the reviewed read-only server for one Desktop Project."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

from abqjobpilot_probe import ABQ_COMMIT
from aegiscae.research.capability_discovery import local


def service_archive(repository):
    result = subprocess.run(["git", "--no-replace-objects", "-C", str(local(repository)), "archive",
                             "--format=zip", ABQ_COMMIT, "--", "abqjobpilot"],
                            check=True, capture_output=True, timeout=30)
    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(result.stdout)) as src, zipfile.ZipFile(buf, "w") as dst:
        for name in sorted(src.namelist()):
            if name.endswith(".py"):
                item = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                item.create_system = 3
                item.external_attr = 0o100644 << 16
                dst.writestr(item, src.read(name))
    return buf.getvalue()


def provision(repository, host, desktop, backend_root, backend_id, directory):
    from uuid import UUID
    if str(UUID(backend_id)) != backend_id or not local(backend_root).is_dir():
        raise ValueError("Invalid deployment binding")
    payload = service_archive(repository)
    policy = json.loads((Path(__file__).resolve().parents[3] /
                         "plugins/gdcae-research/runtime/abq-readonly.json").read_bytes())
    if hashlib.sha256(payload).hexdigest() != policy["source_sha256"]:
        raise ValueError("Source identity mismatch")
    scope = hashlib.sha256((host+"\n"+desktop).encode()).hexdigest()
    dest = local(directory / "GDCAE/engineering/v1" / scope)
    profile = {"schema":1,"host":host,"desktop":desktop,"backend_root":str(local(backend_root)),
               "backend_id":backend_id,"provider":"abqjobpilot-0.2.2-stdio"}
    dest.mkdir(parents=True, exist_ok=True)
    # Publish the complete server before the profile. Never replace an existing deployment.
    with tempfile.TemporaryDirectory(dir=dest) as scratch:
        for name, data in (("server.zip",payload),("deployment.json",json.dumps(profile,sort_keys=True).encode())):
            target = local(dest/name)
            temporary = Path(scratch)/name
            with temporary.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                if local(target).read_bytes() != data:
                    raise ValueError("Existing deployment conflict") from None
    return {"status":"PROVISIONED","source_sha256":policy["source_sha256"]}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("repository","host","desktop","backend-root","backend-id"):
        parser.add_argument("--"+key,required=True)
    args=parser.parse_args()
    print(json.dumps(provision(Path(args.repository),args.host,args.desktop,Path(args.backend_root),
                               args.backend_id,Path(os.environ["LOCALAPPDATA"]))))
