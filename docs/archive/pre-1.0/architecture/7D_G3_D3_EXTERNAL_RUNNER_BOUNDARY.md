# G3-D3 independent Windows qualification boundary

Status: **prepared, NOT_RUN_EXTERNALLY**. G3-D3 does not authorize installation,
external dispatch, push, native process-family experiments or real execution.
The accepted historical B1 UNKNOWN, build_04 BLOCKED and D2 Gate A6 refusal stand.

The primary route is a human-started fresh disposable Windows VM/Sandbox, with no
shared private directories, credentials or models. A terminal spawned by Codex is
not independent. The secondary route is a private GitHub-hosted `windows-2025`
VM after explicit sanitized-ref/push and manual-run approval. The draft workflow
has only `workflow_dispatch`, `contents: read`, immutable action commit pins,
Python 3.12.10, no declared secrets, no persisted checkout credential and a bounded
job. Its candidate directory is intentionally absent until separately approved.
Hosted interpreter provisioning may use network; candidate wheel installation
uses only exact local wheels and `--no-index --no-deps`. No third-party dependency
wheelhouse is claimed; broader AF optional dependencies remain unqualified.

`candidate.py` still builds two inert reviewed snapshots. It now includes GDCAE
plugin resources and four exact role definitions in `aegiscae/_gdcae_plugin`,
covered by installed wheel RECORD. `external_runner/package.py::assemble`
requires exact approved candidate manifest hashes and runner file hashes. It
verifies every selected source and regenerates wheel bytes in memory before
copying the two wheels, source provenance manifests and narrow smoke entrypoints.
The bundle records dirty file hashes separately from baseline Git commits; it is
not a reproducible committed release. SHA-256 checks content consistency against
an independently reviewed digest, not publisher authenticity or tamper immunity.

The one-command external entrypoint validates its manifest and complete input
set, rejects path links, drift and an existing destination, and then performs
bounded ordinary venv/install/smoke steps. The explicit VM approval flag records
human attestation; no software claim of host independence follows. Fixed output
receipts omit stdout, paths and process/session identifiers. Nonzero exit stops;
timeout or invalid response yields UNKNOWN_STOP with no retry. Partial output is
preserved. Direct subprocess completion is not proof of descendant completion:
`family_finalization` remains NOT_VERIFIED, requiring independent VM/host job
evidence. No new Job manager or cleanup mechanism is introduced.

Bootstrap trust begins in the independently reviewed inline PowerShell launcher
(manual README block or pinned workflow), which checks the supplied manifest hash,
rejects reparse-point ancestry and checks `qualify.py` against that manifest before
executing it. The Python script's own checks are not its bootstrap trust root.
The bundle must remain read-only or in exclusive custody with no concurrent writer
through execution. This precondition is not an OS isolation claim; a privileged
file-swap adversary remains outside this narrow test's assurance. No ACLs are changed.

| Gate | This round | Evidence required next |
|---|---|---|
| Bundle/source/resource consistency | offline tests | final freeze SHA receipt |
| Install, RECORD, doctor, Project init | NOT_RUN_EXTERNALLY | independent VM receipt |
| Whole AF import/dependency qualification | NOT_RUN | approved wider wheelhouse/suite |
| External VM/family completion | NOT_VERIFIED | VM owner/host job observation |
| Native four-role calls | Main reports separately | actual native tool dispatch |
| Desktop `@GDCAE` | NOT_TESTED | disposable project official manual activation |
| HIL enforcement / real A / B / ODB | BLOCKED / NOT_RUN | separate exact approvals |

The portable root plugin manifest layout and skills directory follow
[official OpenAI packaging documentation](https://developers.openai.com/plugins/build/plugins).
Resource closure does not establish native role loading, Desktop selection or
independent numerical authority. The README includes a bounded disposable-project
smoke prompt; it has not been sent. This offline smoke cannot qualify local Abaqus,
licensing, Standard dispatch, protected Operator isolation, V2/V4 or real results.

Action pins were checked against the official repositories:
[checkout v4.2.2](https://github.com/actions/checkout/releases/tag/v4.2.2) and
[setup-python v5.6.0](https://github.com/actions/setup-python/releases/tag/v5.6.0).
Only a separate approval may launch the VM or publish/dispatch the private draft.
# Disposable Desktop activation gate (prepared, not performed)

After separate installation/activation approval, the human may open one fresh,
empty disposable project and invoke the officially installed `@GDCAE` entry.
This is part of the product-activation branch, not permission to run a Solver or
reuse the original development Main. Use this single-turn smoke prompt:

> @GDCAE This is a disposable installation smoke check. Report packaged doctor
> and new-project initialization status for this empty workspace. Attempt bounded
> synthetic read-only handoffs to the actual CAE, Results/ODB, Inverse and
> Independent Reviewer custom roles if available. Do not install anything, use
> credentials, read other conversations or projects, start App Server or AF Owner,
> issue a Grant, execute Abaqus/ODB, or claim physical verification. Report missing
> activation or dependencies as BLOCKED; do not substitute default agents.

No Desktop activation was performed in D3. Native calls from the current Main
prove only the observed current role dispatch, not installed-plugin/Desktop sync.

