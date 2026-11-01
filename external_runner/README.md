# Independently initiated Windows qualification — NOT_RUN_EXTERNALLY

This is an inert internal candidate, not build_05 approval or a public release.
Do not run it in the present Codex execution host or a terminal it launches.
After separate operator approval, a human must launch a fresh disposable Windows
VM/Sandbox independently. Confirm no shared private folders, credentials, model
files, licensed Solver, or existing Projects are attached. Transfer only the
reviewed bundle. Compare its BUNDLE.json SHA-256 to the separately supplied receipt.

Use an existing external CPython **3.12.10** interpreter. No third-party wheelhouse
is needed for this deliberately narrow standard-library smoke. The interpreter's
bundled ensurepip creates the fresh venv; the two exact internal wheels install
with `--no-index --no-deps`, and there is no network or build backend invocation.
Broader AF, MCP, pywin32 or Solver dependencies are **not qualified** by this smoke.
The Python distribution itself must be trusted/provisioned separately; this bundle
does not redistribute or automatically obtain it.

Treat the following reviewed PowerShell block as the trusted launcher. Obtain it
from the separately approved source snapshot, not from an untrusted bundle's
README. Use a bundle volume that other users/processes cannot write during the
whole run (read-only mount preferred). The launcher checks reparse points and
authenticates `qualify.py` **before** invoking Python. Bundle hash checks inside
`qualify.py` cannot authenticate that script before it executes. This arrangement
assumes no concurrent writer; checks do not prove protection against a privileged
attacker swapping files between verification and execution. Do not proceed when
exclusive/read-only custody cannot be established. No ACL change is automatic.

Single compound command, in that independent VM only (substitute the four final
arguments: approved interpreter, bundle, fresh destination, supplied manifest hash):

```powershell
& {
  param($Python, $Bundle, $Destination, $Expected)
  $ErrorActionPreference = 'Stop'
  function Assert-PlainPath([string] $Path) {
    if (-not [IO.Path]::IsPathRooted($Path)) { throw 'ABSOLUTE_PATH_REQUIRED' }
    $cursor = [IO.Path]::GetFullPath($Path)
    while ($cursor) {
      $item = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
      if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'REPARSE_POINT_REJECTED' }
      $cursor = Split-Path -LiteralPath $cursor
    }
  }
  if ($Expected -cnotmatch '^[a-f0-9]{64}$') { throw 'INVALID_BUNDLE_DIGEST' }
  Assert-PlainPath $Python
  $manifest = Join-Path $Bundle 'BUNDLE.json'
  Assert-PlainPath $manifest
  if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) { throw 'MANIFEST_NOT_FILE' }
  if ((Get-Item -LiteralPath $manifest).Length -gt 262144) { throw 'MANIFEST_TOO_LARGE' }
  $actual = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actual -cne $Expected) { throw 'BUNDLE_DIGEST_MISMATCH' }
  $record = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
  $entryDigest = $record.files.'qualify.py'
  if ($record.schema -cne 'gdcae-external-bundle-v1' -or $entryDigest -cnotmatch '^[a-f0-9]{64}$') { throw 'INVALID_ENTRY_RECORD' }
  $entry = Join-Path $Bundle 'qualify.py'
  Assert-PlainPath $entry
  if (-not (Test-Path -LiteralPath $entry -PathType Leaf)) { throw 'ENTRY_NOT_FILE' }
  $entryActual = (Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($entryActual -cne $entryDigest) { throw 'ENTRY_DIGEST_MISMATCH' }
  & $Python -I $entry --bundle-sha256 $Expected --destination $Destination --approved-independent-vm
  if ($LASTEXITCODE -ne 0) { throw 'EXTERNAL_QUALIFICATION_NOT_PASS' }
} 'C:\ApprovedPython312\python.exe' 'C:\GDCAE\bundle' 'C:\GDCAE\fresh-qualification' '<approved SHA-256>'
```

The flag records human attestation, not technical proof that a child terminal is
independent. The script verifies exact bounded inputs, refuses existing output,
creates one venv, installs two wheels, verifies installed RECORDs and package role
resources, runs read-only doctor, and initializes one offline synthetic Project and a separate real-intent frozen
Project with no Plan, Grant, or execution authority. Installed-copy metadata and
RECORDs must match snapshot version `0.0.0+g3d6`; copied source alone is rejected.
No process-family fixture, native Job manager, Solver/ODB/AF Owner, Codex call,
Grant, installation into a shared environment or global configuration is invoked.
Each stage is bounded to 180 seconds. A timeout yields UNKNOWN_STOP; stop without
retry and have the external VM owner inspect/dispose the VM. No cleanup is automatic.

The receipt contains fixed status fields, numeric Windows version and exit codes,
hashes and no stdout/stderr, absolute paths, credentials or process identifiers.
An exit-zero command proves its direct process returned only. Detailed descendant
finalization remains NOT_VERIFIED until separately observed at the independent VM
boundary; retain the VM/host job completion evidence separately.

| Gate | Before external execution | Permitted successful claim |
|---|---|---|
| install / import RECORD | NOT_RUN | two reviewed wheel installations |
| plugin/four-role bytes | NOT_RUN | resource closure; not role loading |
| doctor / new Project init | NOT_RUN | bounded offline API smoke |
| all AF optional imports / full regression | NOT_RUN | none from this smoke |
| process family / VM finalization | NOT_VERIFIED | separate VM evidence required |
| Desktop @GDCAE / native roles | NOT_TESTED | separate user activation required |
| HIL / real A / real B / ODB | BLOCKED / NOT_RUN | none |

For the disposable Desktop handoff, use the single authoritative bounded prompt
returned by `activation-request` for that prepared workspace. Main may only delegate
to the four named native roles; the delegated roles have no tool authority. Neither
Main nor roles may read files, run Solver/Owner, create Plans/Grants or access other
chats. Its report is text-only role/recognition evidence, not installed-copy proof.
The separate installed-copy inspection remains a read-only qualification gate.

For hosted Actions, the draft workflow is manual-only and requires private-repo
approval, a separately approved sanitized commit, the reviewed bundle at its exact
path, and the manifest hash supplied in the dispatch. No push or run is authorized
in G3-D3. Hosted Windows evidence does not qualify the local Abaqus machine.

## D6 qualification boundary and Fake IPC follow-up

The final D6 bundle includes `support/FAKE_IPC_SCENARIO.json` and the five exact
reviewed AF TEST_ONLY harness sources in `support/fake_ipc/`. Their local imports
are statically checked and their bytes are independently hashed; they are never
imported or executed by the packager. No private bootstrap files or credentials
are copied. A hash-only legacy bundle remains possible and is labelled explicitly
as missing support; it is not the proposed final D6 candidate.

`support/DEPENDENCIES.json` records the exact Python 3.12 / Windows pytest runtime
closure (pytest, colorama, iniconfig, packaging, pluggy, pygments), based on the
selected environment's distribution metadata without extras. It does not deliver
third-party wheel bytes or claim their provenance. The optional Operator pywin32
and MCP profiles are separate; MCP dependency closure is not included. Current
smoke does not launch the Fake Owner or claim Fake IPC PASS. A separately approved,
hash-pinned dependency wheelhouse, exact license review and external setup remain
prerequisites before that scenario can run. There is no automatic network fetch.
Re-use `g2_fake_rehearsal.FakeRehearsal`: fresh Project, one Fake Owner, original
Receipt/Run/Event/Validation read, replay/wrong-Receipt refusals, then normal exit
and retained original process-handle signal evidence. UNKNOWN stops without retry.
This is preparation, not authority to run that scenario or introduce a new controller.
A VM approval alone cannot turn missing dependencies/support into qualification.
The current single entrypoint remains the narrow installation/initialization
smoke; the packaged Fake rehearsal is a separate, dormant qualification scenario.
Do not describe the full independent Windows gate as closed until both are run
under their separately approved scope and original handle/VM evidence is reviewed.

Preferred host: an independent disposable local Windows VM, exact Windows image
and existing Python 3.12.10 identity selected by its operator before approval.
Availability, image hash and licensing/cost are NOT_VERIFIED. Only this reviewed
bundle may leave the workstation; no credentials, private reports, model assets or
Project databases. Local VM resource exposure is limited to the approved host/disk
budget; nothing is uploaded automatically. Keep direct-process receipt separate
from VM-level finalization evidence, and do not automatically delete the VM or
historic material. Hosted Actions remains an unexecuted alternative: manual
`workflow_dispatch` requires the workflow on the default branch and reviewed source
artifacts; current unpushed overlays are not available from an older remote ref.

One Desktop action (separate from VM execution): open the prepared disposable
workspace, select **GDCAE** in the official plugin UI and send its bounded
`activation-request` prompt. This may require explicit UI consent. Do not run a
marketplace-add or activation command automatically; the official plugin browser
can save user-level settings. Record only plugin recognition and four exact role
returns; never request a private thread ID or authentication data. Both installed
copy registration and Desktop activation remain unverified until observed there.

Official references checked for this preparation:
https://developers.openai.com/plugins/build/plugins
https://learn.chatgpt.com/docs/plugins
https://learn.chatgpt.com/docs/developer-commands
https://docs.github.com/actions/managing-workflow-runs/manually-running-a-workflow
