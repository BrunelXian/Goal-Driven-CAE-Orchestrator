# Install VeriCAE 1.0.0

Use Codex Desktop and a Codex CLI that supports local plugin marketplaces. The research plugin needs no extra language runtime. Obtain `VeriCAE-1.0.0.zip` and `VeriCAE-1.0.0.zip.sha256` from the same approved delivery. Verify the digest against the value supplied by the maintainer. From their directory in PowerShell:

```powershell
$zip = 'VeriCAE-1.0.0.zip'
$expected = ((Get-Content -Raw "$zip.sha256").Trim() -split '\s+')[0]
if ((Get-FileHash $zip -Algorithm SHA256).Hash -ne $expected) { throw 'Archive checksum mismatch' }
$dir = Join-Path (Get-Location) 'VeriCAE-1.0.0'
if (Test-Path -LiteralPath $dir) { throw 'Choose a new extraction directory' }
Expand-Archive -LiteralPath $zip -DestinationPath $dir
foreach ($line in Get-Content -LiteralPath (Join-Path $dir 'FILES.sha256')) {
    $hash, $name = $line -split '  ', 2
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $dir $name)).Hash -ne $hash) { throw "File mismatch: $name" }
}
codex plugin marketplace add "$dir"
codex plugin add vericae-research --marketplace vericae-public --json
codex plugin list --marketplace vericae-public --json
```

Keep the extracted directory in place. The CLI should report `vericae-research@vericae-public`, version `1.0.0`, installed and enabled. For an upgrade, keep the previous archive and original marketplace source until the new version has been checked. To roll back, register the retained prior source, run the same targeted add/list commands and confirm the previous version.

Open the research project in Desktop. In its Main conversation, check the three host-provided skill entries (Initiate, Conduct, Setup), read their version headings and use Setup to check available capabilities. For an external MCP connection verify registration, discovery, an authorized read and the responding service's identity and permissions. If discovery fails, follow `vericae-research/references/mcp-runtime-verification.md` in the archive. Main saves the current state and role bindings before any necessary user-controlled restart. Resume in the original project and Main.
