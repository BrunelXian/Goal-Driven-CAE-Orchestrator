# D6-P-R1 — Custom-agent selector compatibility

Date: 2026-10-31. **BLOCKED_PLATFORM_CUSTOM_AGENT_SELECTOR** for the reported
Desktop test and the one restricted CLI probe. **FOUR_NATIVE_CUSTOM_AGENTS_NOT_VERIFIED**.
Plugin selection remains **PLUGIN_ACTIVATION_PASS**; Core remains
`CORE_INSTALL_VERIFIED`. No four-role or overall product-release PASS is claimed.

## Scope and evidence sources

The R1 mandate, existing D6-P report and Python environment registry were read.
Repository-root AGENTS.md was absent; the user-provided environment policy applies.
The only repository writes are this R1 report and the explicitly requested final outcome
update to the existing, still-untracked D6-P report. No product source changed.
The earlier D6-P user/UI result is attributed evidence: GDCAE was selected as
**Gdcae: Research**, no exact child was spawned, and no generic replacement or
engineering side effect occurred. R1 does not reconstruct that conversation.

## Client and model observations

| Surface | Observed version / model | Selector evidence and limit |
|---|---|---|
| Installed Desktop package | OpenAI.Codex `26.1027.3384.0`; selected model UNKNOWN | Package metadata, not an independently captured running-process build or test model |
| Prior Desktop test | Model UNKNOWN; full argument list unavailable | User reported no observable type selector; no private history was read |
| Current development Main | Exact model UNKNOWN | Actual exposed `collaboration.spawn_agent` arguments: `agent_type`, `fork_turns`, `message`, `model`, `reasoning_effort`, `task_name`; its type list contains the four exact GDCAE names. This is this development session only, not a test dispatch |
| Installed and invoked CLI | `0.166.0-alpha.5.1`; probe model UNKNOWN | Probe reports arguments `fork_turns`, `message`, `model`, `reasoning_effort`, `task_name`; no typed selector and no custom types exposed |

CLI executable SHA-256:
`3097c909fb6d5cd63510d44aceb1d42df9f6e85722a3e447e477def1ecf60e16`.
Read-only version/help/login-status/features commands completed with exit 0.
Login status reported ChatGPT login. The later successful text turn demonstrates
that this single invocation was not blocked by authentication; it does not repair
or reinterpret historical `PENDING_TEST_AUTH` evidence. No credential value was
read or copied by the audit. No model override, catalog edit, install or upgrade
was performed. Model-dependent causality remains **UNKNOWN**.

## Workspace identity and static registration boundary

`TEST_WORKSPACE` means the exact D6 disposable-plugin-project specified by the
mandate; private user paths are omitted here. Official project inventory returned
the label **GDCAE D6 Plugin Test**, but its saved path points to the historical
E2B workspace, not TEST_WORKSPACE. `os.path.samefile` returned false; both paths
exist. The inventory had no path ending in the intended D6 workspace suffix.
No new Desktop chat was created, and no old chat or session archive was accessed.

The first combined identity/file check attempted the expected role filename in
the saved project's directory and returned FileNotFoundError; it read no role
contents there. That directory was not probed further. This mismatch does not
prove which cwd the user's earlier test actually used; D6-P-02 is consequently
INCONCLUSIVE. Project labels alone must not establish isolation or registration.

At the actual TEST_WORKSPACE, `.codex/agents/<role>.toml` files parse successfully
using existing LangChainEnv Python 3.12.10, absolute interpreter with `-I -B`.
Each has matching `name`, nonempty description/developer instructions, and is
byte-identical to its installed alpha.5 plugin counterpart. No AGENTS.md or
`.codex/config.toml` exists at that workspace root. None was created.

| Role | TOML SHA-256 | Runtime acceptance |
|---|---|---|
| gdcae-cae | `973f15cc82d2e8b2746ab49e6002e7429c810f4299f6eb6963c4145925a82950` | BLOCKED; no child |
| gdcae-results | `df2fe7c3b65f71dd2c6d819c2f3ca3ce4674865a82c4891d1458d031b978e4bd` | BLOCKED; no child |
| gdcae-inverse | `d09cb453409b5b5c4f5c576b50196101df5dace602c6285902bd8be653fc4854` | BLOCKED; no child |
| gdcae-reviewer | `07675cec361ada79a094ae420e5173c3752657bad3b8df9d6574ba5dbfc5e220` | BLOCKED; no child |

All four inherit model/effort; shell_tool, apps, plugins, memories and
request_permissions_tool are false. These valid declarations establish file
provenance, not effective registration or a separate security sandbox.
The prior manifest establishes cached plugin `gdcae 0.1.0-alpha.5`; user selection
establishes Gdcae: Research, but no independent selected-version binding is added.

## Single CLI compatibility experiment

After independent scope review, one fresh ephemeral CLI turn used TEST_WORKSPACE
explicitly. All flags were confirmed through local public help/features output:

```text
codex --no-daemon -a never
  --disable hooks --disable apps --disable plugins --disable shell_tool
  --disable memories --disable request_permissions_tool
  exec --ignore-user-config --ephemeral --sandbox read-only
  --skip-git-repo-check --json -C TEST_WORKSPACE <bounded text-only prompt>
```

These were invocation-only restrictions, not global edits. No model was selected
by the audit. Ignoring user config and disabling plugins narrows this probe: it
tests the local project-role path under those restrictions, not production
plugin loading or the user's full Desktop configuration. Project trust and
effective registration were not separately established under that configuration.

The prompt required inspecting only the already exposed schema, then zero spawns
unless a supported typed selector and all four exact registered types existed.
Only in that case were sequential native spawn/wait calls permitted, one per type,
with zero child tools. No template instructions were injected into generic agents.

Actual result: CLI exit **0**, final status **BLOCKED_PLATFORM_CUSTOM_AGENT_SELECTOR**,
`ROLE_REGISTRATION_UNVERIFIED`, empty exposed custom-type list and empty role results.
Model report: UNKNOWN. It reported no tools or children; the public JSONL stream
contained exactly `thread.started`, `turn.started`, one `item.completed` of type
`agent_message`, and `turn.completed`. There were no reported tool/child events
and no non-JSON stdout lines. No retry or model switch followed.

Raw identifiers were withheld before tool output. Only argument names, status,
event shapes and bounded text were emitted; no raw session log was saved.
Stdout digest: `99fade868882366cb474e9d3fd8623a05f95d3f212f0e66c4430320082f7cec2`.
Stderr was 197 bytes, withheld/unclassified; digest:
`9bec1d2fdc0ea117f039753bfb0ee668c7b52c1db274d95178d2defd3a27b0f7`.
No authentication/capacity error indicators matched the bounded classifier.
The process completed normally through its original subprocess handle; the outer
tool session also exited 0. This is not an installation-family closeout test.
The schema list is the probe Main's direct report of its visible tools, not a
separately exported server schema. No effective child metadata exists because
there were zero children; **METADATA_NOT_AVAILABLE** applies to all four roles.

## Decision matrix and independent review

| Gate | Result | Evidence limit |
|---|---|---|
| Plugin selection | PASS, user/UI evidence | Gdcae: Research selected; no new installation or version claim |
| Project-local declarations | PASS static / ROLE_REGISTRATION_UNVERIFIED runtime | Four parsed and matching files; saved Desktop project maps elsewhere |
| Exact selector, prior Desktop test | BLOCKED_PLATFORM_CUSTOM_AGENT_SELECTOR | User-reported absence; full schema/model unknown |
| Exact selector, restricted CLI probe | BLOCKED_PLATFORM_CUSTOM_AGENT_SELECTOR | Actual text turn reported five fields without agent_type |
| Four distinct native dispatches | FOUR_NATIVE_CUSTOM_AGENTS_NOT_VERIFIED | 0 dispatches, 0 child returns, 0 effective role metadata |
| No engineering effects | PASS within observed probe scope | No tool events; no CAE, AF, Plan/Grant, environment/config or source changes |
| Independent review | PASS (report accuracy and bounded scope) | Reviewer read both reports and confirmed evidence limits; this is not four-role acceptance |

The development reviewer is not the experimental `gdcae-reviewer`; its work never
counts toward the four-role requirement. Desktop and CLI results remain separate:
**DESKTOP_TYPED_ROLES_BLOCKED; CLI_TYPED_ROLES_BLOCKED_IN_RESTRICTED_PROBE**.
The current development session's typed surface prevents a universal claim that
every installed Codex session lacks support. No configured-role success is inferred
from that unexercised surface.

Final reviewer found no unresolved report blocker and no raw thread identifier,
credential or private user path. The reviewer specifically required preserving
UNKNOWN models, unverified runtime registration, the CLI's restricted configuration,
and the distinction between a probe Main's schema report and independent service
metadata. Its wording correction to the reproduction summary is incorporated.

## Shortest compatibility recommendation

Keep the accepted plugin/Core entry, but fail closed on the four-role feature
until a supported fresh test client exposes a typed selector and verifiable role
registration in the exact D6 workspace. First resolve the saved-project directory
mismatch through supported project selection, then qualify one already available
client/model combination by its actual schema; do not downgrade, change global
configuration, or substitute task labels. This is a targeted compatibility gate,
not another harness. No new user action or test is initiated by this report.

For an upstream reproduction, the minimal facts are installed versions, four
valid standalone role files, one text-only request, five schema fields reported by the probe Main,
zero dispatches, and model UNKNOWN. Exclude private paths, identifiers and logs.
Public reports are context rather than local root-cause proof:
[official subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
describes project-local definitions and name-based identity;
[issue 33244](https://github.com/openai/codex/issues/33244) reports a missing selector;
[issue 15250](https://github.com/openai/codex/issues/15250) describes tool-backed
registration gaps; [issue 31893](https://github.com/openai/codex/issues/31893)
reports model-dependent schemas. No issue workaround was applied.

`REAL_ABAQUS=NOT_RUN`; `HIL_ENFORCEMENT=NOT_TESTED`;
`REAL_SCIENTIFIC_VERIFICATION=NOT_PERFORMED`. Historical BLOCKED/UNKNOWN evidence
is unchanged. No commit, push, publication, installation or configuration edit.
Workspace HEAD remains `69b144cea9aecc515e15cc830368972b09258af9`; tracked dirty
count remains 9. Untracked count increased from 74 to 75 for this R1 report;
the D6-P report was already untracked. `git diff --check` returned 0 (six
pre-existing line-ending warnings). Separate checks of both untracked reports
found zero trailing-whitespace lines, raw UUIDs, private user paths or API-key
pattern matches. These are bounded screening results, not a general secrecy proof.
No pytest or regression suite was run for this documentation/compatibility task.
Stop for architecture review.
