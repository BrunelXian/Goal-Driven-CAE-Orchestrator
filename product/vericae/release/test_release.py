"""Exercise the frozen marketplace without a Desktop session or solver."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
import zipfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLUGIN = HERE.parent / "vericae-research"


class ReleaseTests(unittest.TestCase):
    def test_versions_and_roles(self):
        release = json.loads((PLUGIN / "release.json").read_bytes())
        version = release["product_version"]
        self.assertEqual(version, "1.0.0")
        for path in ["plugin.json", ".codex-plugin/plugin.json"]:
            self.assertEqual(json.loads((PLUGIN / path).read_bytes())["version"], version)
        dev = HERE.parent / "developer"
        project = tomllib.loads((dev / "pyproject.toml").read_text())
        self.assertEqual(project["project"]["version"], version)
        self.assertIn(f'__version__ = "{version}"', (dev / "src/vericae/__init__.py").read_text())
        self.assertEqual(release["role_names"], ["Main", "CAE", "Results", "Independent Validation"])
        roles = {tomllib.loads(p.read_text(encoding="utf8"))["name"] for p in (PLUGIN / "native-agents").glob("*.toml")}
        self.assertEqual(roles, {"vericae-cae", "vericae-results", "vericae-validation"})

    def test_skill_entrypoints_and_recovery(self):
        entries = {p.parent.name: p for p in PLUGIN.glob("skills/*/SKILL.md")}
        self.assertEqual(set(entries), {"setup", "conduct", "initiate"})
        for name, entry in entries.items():
            text = entry.read_text(encoding="utf8")
            self.assertIn(f"name: {name}\n", text)
            self.assertIn("VeriCAE 1.0.0", text)
        protocol = PLUGIN / "references/mcp-runtime-verification.md"
        for path in [entries["setup"], entries["conduct"], PLUGIN / "references/three-skills-contract.md"]:
            self.assertIn(protocol.name, path.read_text(encoding="utf8"))
        for marker in ["MCP Registration: PASS", "Runtime Discovery: BLOCKED", "Research State: Preserved", "Resume"]:
            self.assertIn(marker, protocol.read_text(encoding="utf8"))

    def test_committed_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = [Path(tmp) / label for label in ("first", "second")]
            for output in outputs:
                subprocess.run([sys.executable, str(HERE / "build.py"), "--output", str(output)], check=True)
            archive = outputs[0] / "VeriCAE-1.0.0.zip"
            self.assertEqual(archive.read_bytes(), (outputs[1] / archive.name).read_bytes())
            with zipfile.ZipFile(archive) as bundle:
                sums = bundle.read("FILES.sha256")
                self.assertEqual(sums, (outputs[0] / "FILES.sha256").read_bytes())
                expected = {".agents/plugins/marketplace.json", "SOURCE_COMMIT", "INSTALL.md", "RELEASE_NOTES.md"}
                expected.update("vericae-research/" + f.relative_to(PLUGIN).as_posix()
                                for f in PLUGIN.rglob("*") if f.is_file())
                self.assertCountEqual(bundle.namelist(), expected | {"FILES.sha256"})
                lines = []
                for name in sorted(expected):
                    data = bundle.read(name)
                    lines.append(f"{hashlib.sha256(data).hexdigest()}  {name}\n")
                    if name.startswith("vericae-research/") or name.startswith(".agents/"):
                        self.assertEqual(data, subprocess.check_output(
                            ["git", "show", f"HEAD:product/vericae/{name}"], cwd=ROOT))
                self.assertEqual("".join(lines).encode(), sums)
                catalog = json.loads(bundle.read(".agents/plugins/marketplace.json"))
                self.assertEqual(catalog["plugins"][0]["source"]["path"], "./vericae-research")
                self.assertEqual(bundle.read("SOURCE_COMMIT").strip(),
                                 subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).strip())
                self.assertEqual(bundle.read("vericae-research/LICENSE"),
                                 subprocess.check_output(["git", "show", "HEAD:LICENSE"], cwd=ROOT))


if __name__ == "__main__":
    unittest.main()
