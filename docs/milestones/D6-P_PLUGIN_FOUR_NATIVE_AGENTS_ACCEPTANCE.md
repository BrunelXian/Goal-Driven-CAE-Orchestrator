# D6-P — Desktop Plugin and four native agents acceptance

Date: 2026-10-31. **PLUGIN_ACTIVATION_PASS / CUSTOM_AGENT_SELECTOR_BLOCKED.**
Final user-observed UI outcome supersedes the earlier pending status below.
`D6_PLUGIN_FOUR_ROLE_ACCEPTANCE_PASS` has not been established.

Latest consolidated disposition after the separately authorized R2 identity
closure: **BLOCKED_PLATFORM_ROLE_ATTESTATION / INVESTIGATION_FROZEN**.
The following original D6-P record is historical; the final matrix at the end
incorporates R2 without retroactively changing that original experiment.

The user completed the single Desktop test and confirmed that the official
selector recognized GDCAE and selected **Gdcae: Research**. All four exact
native delegations remained BLOCKED: that test's model-visible `spawn_agent`
did not expose an observable custom-type selector. No child was spawned;
no generic agent or role-play substituted for it. The user reported no file
changes, CAE execution or other side effects. This is attributed user/UI evidence,
not a private-session inspection by development Main. The subsequent architecture
decision accepted this result and authorized a separate D6-P-R1 compatibility audit.
The selected UI version was not separately reported; cache alpha.5 identity and
the unresolved CLI catalog discrepancy remain separate facts.

## Authorized experiment and isolation

The mandate and existing NEXT_PLUGIN_ROLE_ACCEPTANCE plan were read in full.
The only experimental context is a new empty chat in the existing **GDCAE D6
Plugin Test** project. Its directory is identified here without a private user
path as `TEST_WORKSPACE`, the mandate's `disposable-plugin-project` beneath the
existing D6 evidence root. It is not the Setup chat's separate workspace or the
original development Main.

One human UI action card was issued: verify that project's directory, create one
new chat, select the already installed GDCAE through the official plugin selector,
and send the mandate's single bounded TEST_SYNTHETIC request. If installation or
global configuration changes are required, stop. The user was asked to return
only completion/failure and, if observable, the four actual native activities and
pure-text responses; no private IDs, credentials or other-chat screenshots.

No experimental role has been spawned by development Main. The development
independent reviewer is separate and cannot count as the test's gdcae-reviewer.
The fresh test Main may use native delegation/wait only, at most once per exact
role. No default substitution, role-play, prefabricated results, file/shell/MCP/
network operations, Project/Plan/Grant or engineering execution is permitted.

## G0 actual read-only evidence

Core installation receipt status remains `CORE_INSTALL_VERIFIED`, Distribution
`aegiscae 0.0.0+g3d6`. Its receipt SHA-256 is
`57677f2bf4e26497f06d61061a5804856571c5daf70a13c323ebcbde7cfaa9de`.
The registered existing interpreter is LangChainEnv Python 3.12.10. Fresh bundled
doctor execution returned exit 0, `RECORD_VERIFIED`, and expected package digest
`513def1455d1eb1485b201e5be619dc6fa697ed0099df6725c5e7f886470e297`.
With TEST_WORKSPACE, doctor returned `PACKAGE_AND_FOUR_ROLE_BYTES_VERIFIED`;
`native_role_loading` and `plugin_activation` remained `NOT_TESTED`.
No Core/AF/dependency installation or environment modification was performed.

The installed-cache manifest declares name `gdcae`, display name `GDCAE`, version
`0.1.0-alpha.5`, source cache family `gdcae-preview/gdcae`. That is file identity,
not proof of active selection or current Installed/Enabled registration.

Official read-only CLI results from this development execution context:

| Command | Exit | Bounded result |
|---|---:|---|
| `codex plugin list --json` | 0 | 21 installed entries, 0 available; no GDCAE identity found |
| `codex plugin marketplace list --json` | 0 | 3 marketplace entries; no GDCAE marketplace found |

Both commands had zero stderr bytes. Each was run twice: the first output
projection lacked collection counts; the second clarified schema/counts and
confirmed no matching GDCAE entry. Both completed normally. No raw catalog,
other plugin names, private paths or identifiers were published. No credentials,
global configuration or session files were read. CLI success is not Desktop
selection success. Cache/host skill visibility and this CLI catalog differ; the
cause is **UNKNOWN**, and Installed/Enabled for the intended Desktop test cannot
be inferred from this conflict. No automatic configuration repair was attempted.

Latest D6 report was checked through bounded metadata only: LIMITED PARTIAL,
real A NOT_READY, historical Desktop activation block retained. It is not reused
as this new chat's result. Its content digest is
`acb9f9e11da8e9b965b50db3f8a81c06acd3abb626c8cf502948688b0f75abca`.

## Role declarations versus runtime evidence

The plugin's `agents/<name>.toml` and TEST_WORKSPACE's
`.codex/agents/<name>.toml` match byte-for-byte. Each declares the exact `name`,
description and developer instructions. The five supported feature switches
for shell, apps, plugins, memories and permission requests are false. These are
capability declarations, not a separate OS security boundary. No project-level
`config.toml` exists in TEST_WORKSPACE; none was created.

Official documentation describes project-scoped standalone TOMLs in
`.codex/agents/` and identifies custom agents by their `name` field; parent
permissions remain inherited. This supports the static layout, not proof of
runtime discovery in this new Desktop chat.
[Official Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)

| Declared role ID | TOML SHA-256 | Runtime type and result |
|---|---|---|
| gdcae-cae | `973f15cc82d2e8b2746ab49e6002e7429c810f4299f6eb6963c4145925a82950` | NOT_TESTED |
| gdcae-results | `df2fe7c3b65f71dd2c6d819c2f3ca3ce4674865a82c4891d1458d031b978e4bd` | NOT_TESTED |
| gdcae-inverse | `d09cb453409b5b5c4f5c576b50196101df5dace602c6285902bd8be653fc4854` | NOT_TESTED |
| gdcae-reviewer | `07675cec361ada79a094ae420e5173c3752657bad3b8df9d6574ba5dbfc5e220` | NOT_TESTED |

Runtime registered IDs, native spawn operations, returned text and tool-use
history for the new test chat have not been observed. A later self-reported list
of four names alone will not close those gates. Insufficient observable evidence
must remain INCONCLUSIVE; do not inspect private session archives to fill gaps.

## D6-P-01 through D6-P-12

| ID | Current status | Evidence / missing fact |
|---|---|---|
| 01 | PASS | Prior install receipt and fresh doctor; no reinstall/environment write |
| 02 | INCONCLUSIVE (R1 mapping caveat) | User confirmed completion; later R1 official project metadata maps that label to a different historical workspace. Prior test cwd cannot be reconstructed without private history; no such history was read |
| 03 | INCONCLUSIVE (version binding) | UI selected Gdcae: Research; cache alpha.5 identified, but selected UI version not independently bound and CLI discrepancy unresolved |
| 04 | PASS (user/UI evidence) | Official plugin selection confirmed, accepted by architecture review |
| 05 | BLOCKED / INCONCLUSIVE identity | No gdcae-cae child; test selector unavailable |
| 06 | BLOCKED / INCONCLUSIVE identity | No gdcae-results child; test selector unavailable |
| 07 | BLOCKED / INCONCLUSIVE identity | No gdcae-inverse child; test selector unavailable |
| 08 | BLOCKED / INCONCLUSIVE identity | No gdcae-reviewer child; test selector unavailable |
| 09 | BLOCKED | No four returns; no side effects reported by user |
| 10 | PASS (user attestation) | No default-agent or role-play substitution; no development-Main experiment |
| 11 | PASS | Bounded projections; no raw thread IDs, credentials or private chat content |
| 12 | PASS (limited independent review) | Reviewer checked G0 and final user/UI addendum; no four-role PASS or real execution claim |

`DESKTOP_PLUGIN_SELECTED=PASS` (user/UI evidence).
All four `NATIVE_ROLE_<ROLE>=INCONCLUSIVE`, reason
`CUSTOM_AGENT_SELECTOR_BLOCKED`; no completed child invocations, no role PASS.
`REAL_ABAQUS=NOT_RUN`; `HIL_ENFORCEMENT=NOT_TESTED`;
`REAL_SCIENTIFIC_VERIFICATION=NOT_PERFORMED`.

## Independent review and closeout

Development reviewer has confirmed that Core, CLI registration, UI selection and
native role activity are distinct facts. An unqualified “completed” response
without observable native activity/type evidence cannot establish roles 05–08.
It must not be supplemented by old-Main trials. The reviewer read the original
interim report and confirmed its bounded G0 claims, then received the final user
UI outcome during R1 review. Final review confirmed plugin selection PASS on
user/UI evidence, test cwd INCONCLUSIVE, and four-role BLOCKED/identity
INCONCLUSIVE. This review approves evidence handling, not four-role operation.
No raw thread identifiers or credentials were found in the interim report.

Only this report is newly written in the GD repository. Entry HEAD remains
`69b144cea9aecc515e15cc830368972b09258af9`, with 9 tracked changes and 73 untracked
files inherited before this report. No prior report, source, contract or baseline
was altered; no staging, commit or push occurred. No other chat was read.
The subsequent workspace count is 9 tracked changes and 74 untracked files,
including this one new report. `git diff --check` returned 0, with six existing
LF-to-CRLF warnings and no other messages. This checks tracked differences and
does not establish runtime acceptance of the new report's pending experiment.

The single G1 action card is complete. This D6-P experiment is closed with the
blocker preserved. No retry, reinstall, configuration change or research execution
was performed. Any D6-P-R1 experiment has separate authorization and evidence;
it must not retroactively turn this experiment into four-role PASS.

## Final consolidated D6-P matrix after R2 identity closure — 2026-10-31

The accepted R2 experiment independently established correct D6 project binding
and four distinct completed native children with pure-text returns and no observed
child tool calls. It did not independently attest effective custom-role identities.
One subsequent official read-only closure checked only that completed test Main
and those four linked children. No new experimental invocation was made.

| ID | Final disposition | Source and limit |
|---|---|---|
| D6-P-01 | PASS retained | Accepted Core installation; no reinstall or environment change |
| D6-P-02 | PASS for R2 | Exact new project binding and runtime samefile; original D6-P cwd remains inconclusive |
| D6-P-03 | PARTIAL | Cache alpha.5 provenance and accepted UI selection; selected UI version binding/catalog discrepancy not independently closed |
| D6-P-04 | PASS retained | User confirmed official Gdcae: Research selection; no repeated activation |
| D6-P-05 | BLOCKED_PLATFORM_ROLE_ATTESTATION | Real child-1 completed; gdcae-cae identity is self-reported, no effective role field |
| D6-P-06 | BLOCKED_PLATFORM_ROLE_ATTESTATION | Real child-2 completed; gdcae-results identity is self-reported, no effective role field |
| D6-P-07 | BLOCKED_PLATFORM_ROLE_ATTESTATION | Real child-3 completed; gdcae-inverse identity is self-reported, no effective role field |
| D6-P-08 | BLOCKED_PLATFORM_ROLE_ATTESTATION | Real child-4 completed; gdcae-reviewer identity is self-reported, no effective role field |
| D6-P-09 | PASS observed text-only scope | Four real responsibility returns; no engineering/tool activity in returned test records |
| D6-P-10 | REPORTED_COMPLIANT / identity unverified | Main reports agent_type selection and no generic fallback; actual selector payload not exported |
| D6-P-11 | PASS bounded evidence handling | No private history scans, raw IDs or credential values in closure report/output |
| D6-P-12 | PASS limited independent closure review | Reviewer confirmed observable fields, identity gap, privacy and frozen disposition; not four-role identity PASS |

The inspected official `read_thread` interface returned no structured agent_role,
agent_type, effective-role or loaded-role-configuration attestation for any child.
Main's activity summary did not export actual spawn arguments. No response was
marked truncated or had an older turn page. Names in task labels or response text
are not identity metadata. This is an observable-interface limitation, not a claim
about uninspected UI or every Codex backend API.

Final status: `PLUGIN_ACTIVATION_PASS`; four native completions verified;
`FOUR_CUSTOM_ROLES_VERIFIED=NOT_ESTABLISHED`;
`BLOCKED_PLATFORM_ROLE_ATTESTATION`; compatibility investigation **FROZEN**.
No full four-role or full-chain release PASS. Detailed closure evidence and field
inventory are in `D6-P-R2_WORKSPACE_AND_NATIVE_ROLE_ROUTING_REPORT.md`.
Research priorities return to protected Operator, real A-only readiness and
independent verification, subject to their separate approval gates. No Solver,
system-rights deployment, new Grant, installation, Git commit or push was authorized
or performed by this identity closure.

Final independent Reviewer accepted both closure addenda: verified native
completion is preserved, missing identity metadata remains a scoped interface
limitation, and no self-report is promoted to role attestation. Both updated
reports passed bounded identifier/credential-pattern and trailing-whitespace
checks. `git diff --check` returned 0 with six existing line-ending warnings;
HEAD, 9 tracked dirty files and 76 untracked files remained unchanged.
