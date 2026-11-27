# Install VeriCAE 1.0.0 in Codex Desktop

1. From the formal release, download the plugin ZIP and its checksum into one directory. Use the named plugin asset; GitHub's automatically generated source archives contain the repository tree. [Plugin ZIP](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/v1.0.0/VeriCAE-1.0.0.zip) · [ZIP checksum](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/v1.0.0/VeriCAE-1.0.0.zip.sha256) · [Per-file checksums](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/v1.0.0/FILES.sha256)
2. Open PowerShell in the download directory. Verify the ZIP SHA-256 against `273172ba70763269571f872703e3ba30924e9459d804212f4a132c1c536e4d0b`. Follow the frozen guide to extract it into a new permanent folder and verify the individual files. [Exact PowerShell steps](product/vericae/release/INSTALL.md)
3. From the directory containing the extracted `VeriCAE-1.0.0` folder, register that folder as a local marketplace and install the plugin.

```powershell
codex plugin marketplace add ./VeriCAE-1.0.0
codex plugin add vericae-research --marketplace vericae-public --json
codex plugin list --marketplace vericae-public --json
```

Look for `vericae-research@vericae-public`, version `1.0.0`, installed and enabled. In the research project's Main conversation, open the host-provided Initiate, Conduct and Setup entries and confirm their version headings. For an external connection, use Setup and the original Main to verify all four MCP layers. Keep the extracted directory available as the marketplace source. For an upgrade, retain the former archive and source until the new version is checked. [Runtime verification and recovery](product/vericae/vericae-research/references/mcp-runtime-verification.md) · [Companion platform](COMPATIBILITY.md)
