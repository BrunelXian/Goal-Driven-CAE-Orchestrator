"""Build or independently inspect the two public ZIPs with the standard library."""
import argparse
import hashlib
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path

PRODUCT = Path(__file__).resolve().parents[1]
REPO = PRODUCT.parents[1]
ID = "gdcae-research"
PLUGIN = REPO / "plugins" / ID
VERSION = "0.2.0-preview.16"
PREFIX = f"GDCAE-Research-Preview-{VERSION}/"
INNER = f"GDCAE-Install-{VERSION}.zip"
PLUGIN_DIR = f"INSTALL-MEDIA/plugins/{ID}/"
PAYLOAD = ("plugin.json", "scripts/launch.ps1", "scripts/main.py", "skills/research/SKILL.md",
           "core/sp_history.py", "references/sanity-model-protocol.md", "scripts/main-handoff.ps1", "references/project-main.md",
           "scripts/agreement_main.py", "references/research-agreement.md",
           "assets/mesh.png", "skills/setup/SKILL.md", "scripts/runtime.ps1",
           "scripts/runtime-checks.ps1", "runtime/cpython-windows.json", "references/runtime-options.md",
           "scripts/update.ps1", "hooks/hooks.json", "references/update.md")
CORE_FILES = ("__init__.py", "contracts/__init__.py", "contracts/research_contracts.py",
              "research/__init__.py", "research/project.py", "research/research_agreement.py", "research/sanity.py",
              "research/task_cards.py", "research/task_roles.py", "research/capability_discovery.py")
CASE = ("CASE.md", "Sanity.csv", "run_014.csv", "difference.csv", "force-displacement.png",
        "rc3-evidence.json", "recompute.py")
CORE_SHA = "df8e330150d4959eb55f6add60b92eba41395d68c4794f68dd558834b67ef535"
START, END = "<!-- research-qa:start -->", "<!-- research-qa:end -->"

def require(ok, message):
    if not ok:
        raise ValueError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()

def public_bytes(root, name):
    path = root / name
    for entry in (path, *path.parents):
        require(not entry.is_symlink() and not entry.is_junction(), f"reparse point: {entry.name}")
    return path.read_bytes()

def qa(text):
    require(text.count(START) == text.count(END) == 1, "README Q&A markers")
    block = text.split(START, 1)[1].split(END, 1)[0]
    numbers = [line.partition(". **")[0] for line in block.splitlines() if ". **" in line]
    require(numbers == list(map(str, range(1, 11))), "expected 10 numbered questions")
    return START + block + END

def render(template, token, value):
    require(template.count(token) == 1, f"expected one {token}")
    return template.replace(token, value).encode()

def archive(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as output:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return buf.getvalue()

def entries(data, allowed):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        require(len(z.namelist()) == len(allowed) and set(z.namelist()) == set(allowed), "unexpected ZIP members")
        return {key: z.read(key) for key in allowed}

def sums(files):
    return "".join(f"{digest(data)}  {name}\n" for name, data in sorted(files.items())).encode()

def private_publisher_manifest(public_manifest):
    """Restore the original private Creator metadata only for an identity-checked build."""
    filename = os.environ.get("GDCAE_PREVIEW15_PUBLISHER_MANIFEST")
    require(filename, "Set GDCAE_PREVIEW15_PUBLISHER_MANIFEST to the approved external .15 plugin.json")
    path = Path(filename).resolve()
    require(path.is_file() and not path.is_relative_to(REPO) and path.stat().st_size <= 65536,
            "expected an external publisher manifest")
    original = public_bytes(path.parent, path.name)
    require(digest(original) == "d70ba01dbf56cd270cb6a6a835b5855f467b1065993b86665883337e04eb0f94",
            "private publisher manifest identity mismatch")
    reviewed = json.loads(original)
    require(reviewed["version"] == "0.2.0-preview.15", "publisher source version")
    reviewed["version"] = VERSION
    private_manifest = encoded(reviewed)
    del reviewed["author"]["email"]
    require(reviewed == json.loads(public_manifest), "public plugin source disagrees with the approved identity")
    return private_manifest


def plugin_files():
    payload = {name: public_bytes(PLUGIN, name) for name in PAYLOAD}
    payload["plugin.json"] = private_publisher_manifest(payload["plugin.json"])
    # Plugin Creator may supply the skill body while the Host denies a second
    # file read. Embed the same reviewed onboarding text in both entry points.
    guide = payload["references/project-main.md"]
    begin, end = b"<!-- onboarding:start -->", b"<!-- onboarding:end -->"
    require(guide.count(begin) == guide.count(end) == 1 and guide.index(begin) < guide.index(end),
            "missing shared onboarding definition")
    introduction = guide.split(begin, 1)[1].split(end, 1)[0].strip()
    marker = b"<!-- embed:project-main/onboarding -->"
    for skill in ("skills/setup/SKILL.md", "skills/research/SKILL.md"):
        require(payload[skill].count(marker) == 1, "missing onboarding insertion point: " + skill)
        payload[skill] = payload[skill].replace(marker, introduction)
    payload["LICENSE"] = public_bytes(REPO, "LICENSE").replace(b"\r\n", b"\n")
    payload["runtime/agreement-core.zip"] = archive({"aegiscae/"+name:
        public_bytes(REPO/"src/aegiscae",name).replace(b"\r\n",b"\n") for name in CORE_FILES})
    require(digest(payload["core/sp_history.py"]) == CORE_SHA, "historical analysis component changed")
    meta = json.loads(payload["plugin.json"])
    require((meta["name"], meta["version"]) == (ID, VERSION), "plugin identity")
    # Pin complete semantic documents, including each path and publisher field.
    compatibility = {key: meta[key] for key in ("name", "version", "description", "license")}
    compatibility.update(skills="./skills/", interface=meta["extensions"]["com.openai"]["interface"])
    documents = {"plugin.json": meta, ".codex-plugin/plugin.json": compatibility}
    def semantic_hash(doc):
        return digest(json.dumps(doc, ensure_ascii=True, allow_nan=False, sort_keys=True,
                                 separators=(",", ":")).encode("ascii"))
    metadata_hashes = {name: semantic_hash(doc) for name, doc in documents.items()}
    ext = meta["extensions"]["com.openai"]
    with_hooks = dict(compatibility, hooks=ext["hooks"])
    # Observed Plugin Creator projection. Derive values from reviewed source,
    # never from metadata found beside the installed executable.
    creator = dict(with_hooks, author=meta["author"], keywords=[], skills="./skills",
                   interface={"defaultPrompt": None, **ext["interface"]},
                   requires_local_executor=ext["requires_local_executor"],
                   extensions={"com.openai": {"onboardingSkill": ext["onboardingSkill"]}})
    package = encoded({"version": VERSION, "component": "sp-history-1.0.0",
                       "metadata_sha256": metadata_hashes,
                       "compat_with_hooks_sha256": semantic_hash(with_hooks),
                       "plugin_creator_compat_sha256": semantic_hash(creator),
                       "files": {k: digest(v) for k,v in payload.items()}})
    payload["package-manifest.json"] = package
    return payload

def materials():
    payload = plugin_files()
    package = payload["package-manifest.json"]
    inner = {PLUGIN_DIR + k: v for k,v in payload.items()}
    inner["INSTALL-MEDIA/.agents/plugins/marketplace.json"] = public_bytes(PRODUCT, "marketplace.json")
    inner["INSTALL-MEDIA/INSTALL.md"] = render(public_bytes(PRODUCT, "INSTALL.template.md").decode(),
                                               "{{MANIFEST_SHA256}}", digest(package))
    block = qa(public_bytes(REPO, "README.md").decode().replace("\r\n", "\n"))
    outer = {"README.md": render(public_bytes(PRODUCT, "release/README.template.md").decode(), "{{RESEARCH_QA}}", block),
             "CAPABILITIES.md": public_bytes(PRODUCT, "release/CAPABILITIES.md"),
             "docs/sanity-model-protocol.md": payload["references/sanity-model-protocol.md"]}
    outer["docs/SANITY_MODEL_USER_GUIDE.md"] = render(public_bytes(REPO, "docs/user/SANITY_MODEL_USER_GUIDE.md").decode(),
        "../architecture/AGENT_MODEL_UNDERSTANDING_AND_SANITY_PROTOCOL.md", "sanity-model-protocol.md")
    for name in CASE:
        outer["case/" + name] = public_bytes(PRODUCT, "release/case/" + name)
    expected_case = json.loads(public_bytes(PRODUCT, "historical-case-sha256.json"))
    require(expected_case == {name: digest(outer["case/" + name]) for name in CASE}, "historical case changed")
    return inner, outer

def verify(data):
    inner, outer = materials()
    files = entries(data, [PREFIX + n for n in (*outer, INNER, "SHA256SUMS.txt")])
    actual = {key.removeprefix(PREFIX): val for key,val in files.items()}
    checksum_file = actual.pop("SHA256SUMS.txt")
    require(checksum_file == sums(actual), "outer content sums")
    media = actual.pop(INNER)
    require(actual == outer and entries(media, inner) == inner, "archive differs from public source")
    return {"outer_sha256": digest(data), "inner_sha256": digest(media),
            "manifest_sha256": digest(inner[PLUGIN_DIR + "package-manifest.json"]), "core_sha256": CORE_SHA,
            "agreement_core_sha256":digest(inner[PLUGIN_DIR+"runtime/agreement-core.zip"]),
            "agreement_core_members":sorted("aegiscae/"+name for name in CORE_FILES),
            "inner_members": sorted(inner), "outer_members": sorted(files)}

def build(dest):
    require(not dest.exists() and dest.parent.is_dir() and not dest.is_relative_to(REPO), "fresh external output required")
    inner, outer = materials()
    outer[INNER] = archive(inner)
    outer["SHA256SUMS.txt"] = sums(outer)
    data = archive({PREFIX + k:v for k,v in outer.items()})
    report = verify(data)
    with tempfile.TemporaryDirectory(dir=dest.parent) as temp:
        stage = Path(temp) / "out"
        stage.mkdir()
        (stage / (PREFIX[:-1] + ".zip")).write_bytes(data)
        (stage / "inventory.json").write_bytes(encoded(report))
        os.rename(stage, dest)
    return report

def export_channel(dest):
    """Publishable Git marketplace tree. Preserve exact binary and text identities on Windows."""
    require(not dest.exists() and dest.parent.is_dir() and not dest.is_relative_to(REPO), "fresh external output required")
    payload = plugin_files()
    manifest = digest(payload["package-manifest.json"])
    metadata = {"schema": 1, "product": ID, "version": VERSION, "manifest_sha256": manifest,
                "zip_sha256": digest(archive(payload)), "change": "auto-update", "impact": "restart-rebind-no-migration"}
    files = {"plugins/"+ID+"/"+name: body for name, body in payload.items()}
    files.update({".agents/plugins/marketplace.json": public_bytes(PRODUCT, "preview-marketplace.json"),
                  ".gitattributes": b"* -text\n", "channel.json": encoded(metadata)})
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
        tree = Path(tmp) / "tree"
        for name, data in files.items():
            path = tree / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        os.rename(tree, dest)
    return metadata

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--build", type=Path, metavar="FRESH_DIRECTORY")
    action.add_argument("--verify", type=Path, metavar="OUTER_ZIP")
    action.add_argument("--channel", type=Path, metavar="FRESH_MARKETPLACE_DIRECTORY")
    action.add_argument("--public-zip", type=Path, metavar="FRESH_ZIP",
                        help="Build the standalone graphical-import candidate")
    args = parser.parse_args()
    if args.channel:
        report = export_channel(args.channel.resolve())
    elif args.public_zip:
        dest = args.public_zip.resolve()
        require(dest.suffix.lower() == ".zip" and not dest.is_relative_to(REPO), "external ZIP required")
        payload = plugin_files()
        data = archive(payload)
        require(entries(data, payload) == payload, "standalone verification failed")
        with dest.open("xb") as stream:
            stream.write(data)
        report = {"version": VERSION, "sha256": digest(data),
                  "manifest_sha256": digest(payload["package-manifest.json"])}
    else:
        report = build(args.build.resolve()) if args.build else verify(args.verify.read_bytes())
    print(json.dumps(report, indent=2))
