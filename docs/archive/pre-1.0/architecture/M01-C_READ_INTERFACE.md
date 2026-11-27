# M01-C read-only research interface

This is an opt-in TEST evidence interface, authorized by the M01-C task. It does
not revise ADR-003/004, start AF, implement another Agent Harness, or confer any
execution permission. Codex Main and native custom agents interpret recorded
facts; scientific verification remains unavailable.

## Installation assumptions and binding

Use an existing approved Python environment with the official MCP Python SDK
2.3 API and Pydantic 2. No automatic installation occurs. Package metadata remains
the frozen skeleton's metadata; this optional interface is not advertised as
working in an environment without MCP. Run the module with an absolute Python
interpreter, `-B`, and explicit import paths for this repository's `src` and the
approved AF source. No AF private module is directly imported by the interface.

An operator must first select an already running, authorized TEST_ONLY/Fake
project. Store this machine-local JSON outside Git, with restrictive access:

```json
{
  "test_only": true,
  "binding": {
    "root": "<absolute-local-AF-project-root>",
    "project_id": "p_<32-lowercase-hex>",
    "project_instance_id": "pi_<32-lowercase-hex>",
    "context_digest": "sha256:<64-lowercase-hex>",
    "owner_id": "owner_<32-lowercase-hex>"
  }
}
```

Place no credential, endpoint or operator token in this document. Values must
come from the authorized fixture/operator, never guesses or GUI Recent. The
file is read once, at startup, through an explicit absolute path (8 KiB maximum).
Its contents become a frozen `ProjectBinding`. Unsupported/missing/stale binding
fails startup with constant `GDCAE_MCP_UNAVAILABLE` on stderr. There is no repair,
initialization, fallback, owner start or retry. After owner exit, this binding is
stale and must remain unavailable until a fresh binding is explicitly approved.

Startup and every tool invocation require verified capabilities with
`simulation=true`; each subsequent bridge read also independently verifies the
same project/instance/context/owner. These are successive, non-atomic checks.
The explicit `test_only` flag is operator attestation, not an AF credential or
proof of OS isolation. Real test preflight separately checks the native health
record's TEST_ONLY scope, fake-v1 backend and absent process fixture. The bridge's
public capability projection does not expose all those native health fields.

## Project-scoped Codex configuration template

Only use a trusted project. Fill placeholders locally in `.codex/config.toml`;
that precise path is ignored. Never overwrite an existing user's configuration.
This template has no working personal path or credential:

```toml
[mcp_servers.gdcae_read]
command = '<absolute-approved-python-executable>'
args = ['-B', '-m', 'aegiscae.interfaces.mcp_read', '--binding-file', '<absolute-binding-json>']
cwd = '<absolute-GD-CAE-repository>'
startup_timeout_sec = 30
tool_timeout_sec = 30
required = true

[mcp_servers.gdcae_read.env]
PYTHONDONTWRITEBYTECODE = '1'
PYTHONPATH = '<absolute-GD-CAE-src>;<absolute-approved-AF-source>'
```

The separator shown is Windows-specific. Project trust and config precedence
follow [Codex config basics](https://learn.chatgpt.com/docs/config-file/config-basic).
STDIO command/args/env/cwd and timeouts follow the
[official MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
M01-C does not edit global configuration or install a plugin. Other global MCP
connections may exist; they are outside this server's tool allowlist.

With the tested CLI `0.165.0-alpha.1.2`, use the normal trusted-project config
path and normal session persistence. In this environment, `exec
--ignore-user-config` also left the project MCP unavailable, and `--ephemeral`
caused an initial native context-fork failure (`no rollout found`). A normal
session supplies auditable native spawn metadata and reviewer tool records.
Invocation-local `-c mcp_servers.<unrelated-name>.enabled=false` does not edit
the user's global connections. Do not assume the CLI and already-open desktop
conversation hot-reload the same new tools or agents.

## Seven tools

| Tool | Inputs | Bridge method |
| --- | --- | --- |
| `gdcae_capabilities` | none | `capabilities` |
| `gdcae_list_runs` | optional cursor, limit 1–32 | `list_runs` |
| `gdcae_get_run` | run_id | `get_run` |
| `gdcae_get_receipt` | original key, 1–256 characters | `get_receipt` |
| `gdcae_list_events` | optional cursor, limit 1–64, run_id | `list_events` |
| `gdcae_get_validations` | run_id | `get_validations` |
| `gdcae_get_diagnostic` | run_id | `get_diagnostic` |

All schemas reject extra properties and coercion. Cursors retain source identity,
operation and original AF position. They are not arbitrary Project selectors.
Every response contains the existing sanitized `gd-af-read-v1` envelope in both
MCP text and structured content. The combined result has a 261120-byte budget,
reserving 1 KiB for the ordinary SDK JSON-RPC wrapper, in addition to the bridge's
raw response/depth/node bounds. Caller-controlled unusually large JSON-RPC IDs
and malformed transport frames remain the official SDK's protocol responsibility.
No arbitrary raw event text, file paths or logs are projected.

Known upstream errors retain their typed code/stage. Invalid tool arguments,
unknown tool names and serialization failures produce bounded constant errors,
without echoing arguments or exception text. Read failure is not an empty page.
Empty filtered event pages can have `more_possible=true`; follow the returned
source cursor. Successive reads are not an atomic snapshot.

The official low-level `Server`, `stdio_server` and SDK request/result types own
protocol handling. Seven fixed branches invoke seven public bridge methods.
No generic AF call is exposed. SDK telemetry middleware is explicitly disabled;
GD-CAE adds no threads, monitors, network listeners or background Agent loop.
The SDK itself uses transport concurrency to service STDIO.

## Researcher workflow and delegated review

1. Open the trusted repository in a fresh Codex session after preparing the
   approved binding. Verify `gdcae_read` loads and lists exactly these tools.
2. Ask Codex to use `gdcae-evidence-review` to summarize TEST execution history.
   Supply only safe original receipt keys when receipt lookup is needed.
3. Main checks capabilities, pages Runs/Events within a read budget, and cites
   safe Project/Run/Receipt/sequence identifiers plus read times and uncertainty.
4. Main can delegate evidence collection to `gdcae_evidence_analyst` and an actual
   independent challenge to `gdcae_independent_reviewer`. They inherit its model,
   MCP resources and permissions. Return structured handoffs to the same Main.
5. Main separates recorded facts, contradictory or missing evidence, reviewer
   findings and next authorized reads. Neither FINISHED nor REVIEW_COMPLETE is
   goal/model/numerical/physics verification. No next execution is authorized.

Agent discovery uses `.codex/agents/*.toml` with required `name`, `description`,
`developer_instructions`, per [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
Skill discovery uses `.agents/skills/gdcae-evidence-review/SKILL.md`, per
[Build skills](https://learn.chatgpt.com/docs/build-skills). A file parsing correctly
does not prove the running client loaded it; see the delivery report's live evidence.

## Limits and retained risks

Codex and AF can share one Windows user. The API restriction and role instructions
are not a malicious-same-user sandbox; AF credentials are not intrinsically
read-only. Tool data remains untrusted even after projection. No ODB is read and
no diagnostic digest/artifact is revalidated. LLM agreement is not an independent
numerical oracle. Test fixture setup writes are separate from measured read phases.

This milestone does not implement SDK/app-server turn resumption, scheduled
monitoring, ResearchProject storage, Goal/Model editing or execution agents.
Original desktop Main automatic continuation is NOT_TESTED. M01-B retained
credentials/evidence are neither accessed nor reused or deleted by M01-C.
