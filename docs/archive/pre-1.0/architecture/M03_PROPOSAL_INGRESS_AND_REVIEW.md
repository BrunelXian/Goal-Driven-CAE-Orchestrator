# M03-D Proposal Ingress and Review

Date: 2026-10-29. Implementation and acceptance are recorded separately in the delivery report.

## Pre-implementation threat model

Codex Main and subagents are untrusted proposal authors. They may submit malformed,
stale, conflicting or malicious data, repeat after a lost response, race each other,
or claim approval. The two-tool surface must never forward paths, commands, SQL,
arbitrary RPC or execution authority. Its startup binding is trusted local setup.
Receipt means durable untrusted intent only. Admission is deterministic eligibility;
review is a separately attributed disposition under a previously frozen synthetic
policy. Neither creates an AbqJobPilot Grant.

The project database currently requires an exact four-table schema. Use an explicit,
versioned, fixed-name Project-owned sidecar, leaving research.sqlite3 and frozen
contracts byte-preserved during issue/record/evaluate. One challenge and one proposal
slot per sidecar, bound to Project identity, storage generation, workflow, revision,
Brief, evidence and contracts. Setup must not overwrite an existing sidecar.
Missing, malformed, copied, unsupported or journal-bearing stores fail closed.
Transactions and append-only digest-linked records handle normal corruption and
concurrency. Hashes and timestamps are not signatures, trusted clocks or protection
against coordinated rewriting by the same Windows user.

MCP has record/status only. The trusted gate is independently invoked and reuses
M03-C checks, including actual candidate/baseline files. A positive decision is tied
to the checked revision and is not a resource reservation. Any future continuation
must recheck with the existing Workflow CAS; cached review cannot bypass drift.
No continuation, AF call or Codex turn is triggered by recording or status reads.

Frozen TEST_SYNTHETIC policy permits an in-contract advisory acceptance without a
human click. Escalation policy and STOP/REQUEST_REVIEW produce HUMAN_REVIEW_REQUIRED.
No human approval API is introduced; model prose is never human provenance.

Faults before commit must roll back or leave a conservative STORE_BUSY sentinel.
Faults after commit must preserve the original receipt/decision. No automatic
retry, journal recovery, key replacement or budget refund is permitted.

## Codex integration boundary

The current desktop tool registry has no dynamic proposal server attached. The
taskbook explicitly permits a scoped Codex CLI test session. Its feasibility is
checked against the installed CLI and [official MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
No global configuration or existing project MCP configuration is changed. A real
model tool call is required for the native ingress label; Python MCP client tests
alone cannot establish that label.

## Implemented interfaces and data

`aegiscae.interfaces.mcp_proposal` is a separate STDIO server, named
`gdcae-proposal-only`, version `m03d-v1`. Startup requires an explicit absolute JSON
binding file. Its exact fields are `schema=proposal-mcp-startup-v1`, `test_only=true`,
`root`, `research_project_id`, `challenge_id`. These are trusted startup settings,
never tool arguments. Existing `mcp_read.py` and the AF facade remain unchanged.

| Interface | Arguments | Permitted result/effect |
|---|---|---|
| `gdcae_get_proposal_status` | Empty object | Bounded challenge/Brief, original Receipt, historical decisions and current validity projection |
| `gdcae_record_candidate_proposal` | Server-issued `proposal_key`, UTF-8 `proposal_json` string | One durable untrusted capture and Receipt, or conservative fixed-code rejection |
| `issue_challenge` | Trusted coordinator, bounded expiry, policy enum | Explicit exclusive creation; absent from MCP |
| `evaluate_recorded` | Trusted bound ingress and exact SyntheticWorkspace | AdmissionDecision and ReviewDecision in one sidecar transaction; absent from MCP |
| `revoke_challenge` | Trusted bound ingress | Append revocation; absent from MCP |

Proposal JSON is the existing `candidate-proposal-v1` DTO, at most 8192 UTF-8 bytes.
Unknown fields, duplicate JSON keys, floats, nonfinite values, wrong units/entities,
scope/authority fields and unsafe prose are rejected. Decimal is text. Existing
contract criteria and limits cannot be supplied by the author. No new human-approval
endpoint or execution endpoint exists. Strict syntax is checked at recording;
semantically out-of-range but syntactically valid intent can be recorded and then
rejected independently by the gate.

The original proposal string is stored as ordered chunks of at most 512 characters
to preserve exact UTF-8 bytes while respecting existing bounded-JSON primitives.
Receipt digest covers those exact bytes, not merely normalized semantics. Whitespace
changes conflict. The transport envelope's JSON escaping is not claimed to be the
original proposal byte stream. Error outputs never echo submitted text or paths.
Responses are bounded to 24 KiB before the SDK's duplicate text/structured envelope.

## Persistent extension and compatibility

`proposal-ingress-v1.sqlite3` is fixed under the bound ResearchProject root. One
append-only `events(sequence,body,digest)` table stores at most four events:
CHALLENGE, RECORD, GATE and REVOKE. The latter may precede GATE, in which case no
positive gate is possible. Bodies carry `proposal-event-v1`, sequence, previous
digest, UTC timestamp, fresh transaction ID, event kind and data. Every open
verifies exact schema, bounded canonical bytes, digest chain, time order, unique
transaction IDs, permitted order, data fields and cross-field consistency.

Challenge contains `proposal-challenge-v1`, Project identity/generation/root and
database identity, sidecar file identity, exact Brief, frozen review policy,
server-issued key, issue time and expiry (1 second to 24 hours). Setup creates with
O_EXCL and refuses any existing file; no overwrite, repair, alternate filename,
renewal or second challenge slot exists in this milestone. An incomplete initial
file is retained in place and rejected. Read-only status does not create, recover or migrate storage.

The Project retains its exact four-table v1 database and frozen bundle bytes.
Extension tests first build a frozen M03-C Project using the existing creation
path, then prove byte equality of research.sqlite3 after issue/record/gate and
successful reopening by the unchanged Project reader. This is an explicitly
initialized compatible sidecar, not an archived-database migration. Unknown sidecar
schemas, copied file identity, hardlinks/reparse points and journal/WAL/SHM are
rejected. Original Project and frozen contract schemas are unchanged.

Status reconstructs the historical ResearchBrief from the validated Project audit
at the challenge's revision and compares the entire persisted Brief. Thus arbitrary
extra fields, changed hypotheses or rewritten source text cannot leak through a
nominally sanitized dictionary, even if its public hash is recalculated. The
historical builder is pure and does not call the coordinator or modify files.

## Receipt, admission and review semantics

Receipt has `proposal-receipt-v1`, immutable receipt/challenge/key/digest identity,
`RECORDED_PENDING_GATE`, and intent `PROPOSED_UNTRUSTED`, `STOP_REQUESTED` or
`REVIEW_REQUESTED`. The original Receipt never changes after a gate. Status presents
decisions separately, with `CURRENT`, `STALE`, `EXPIRED` or `REVOKED` challenge
validity. Read projections of validity are not new decisions.

AdmissionDecision records `admission-decision-v1`, its unique ID, expected and
actually checked revisions, Receipt/challenge/proposal digests, A evidence refs,
status and a fixed reason code. Positive decisions must have matching revisions,
the eligible reason, appropriate policy and a nonrevoked valid-time snapshot.
Malformed or contradictory stored decisions are rejected. A snapshot timestamp
identifies when eligibility was checked, not how long eligibility will last.

ReviewDecision is a distinct `review-decision-v1` object referencing that admission
ID and the frozen policy digest. AUTO_TEST_SYNTHETIC accepts only admissible
in-contract synthetic intent. REQUIRE_HUMAN_REVIEW, STOP, REQUEST_REVIEW or any
blocked/inconclusive outcome returns HUMAN_REVIEW_REQUIRED. Provenance is
PREEXISTING_FROZEN_TEST_POLICY, human_approval=false, grants_issued=0 and
execution_authorized=false. No natural-language consent is consumed.

The gate takes the sidecar write lock, opens a validated readonly Project snapshot,
replays contracts/workflow/ledger and uses the shared M03-C `_evaluate_snapshot`.
It checks current revision, frozen refs, original evidence, ledger availability and
UNKNOWN, actual A and baseline bytes, the typed mutation and independent diff.
Only the existing trusted Workflow admission API commits a Workflow admission;
M03-D does not call it. The shared extraction preserves the old commit path checks.

Gate/Review records commit atomically with each other, but are not an atomic commit
across the Project and sidecar. A concurrent Project mutation may make them stale
after the snapshot. Positive records are historical eligibility, not reservations.
Any future continuation needs a new policy-validity check and existing Workflow CAS.
**Optional synthetic continuation is deliberately not implemented in M03-D.**

## Idempotency, faults and process boundaries

Only the startup-bound challenge/key can receive a proposal. Record rechecks
revocation, window and current Project revision before either new capture or exact
replay. Exact key/content returns the original Receipt; changed content is a
structured conflict. A stale or expired record call rejects; status can still locate
the original Receipt after a lost reply. No client-generated alternative key or
rejection reset exists. A second gate call returns its historical immutable record.

SQLite BEGIN IMMEDIATE serializes concurrent record/gate/revoke writes. Project
reads use a separate readonly snapshot; no Project revision changes on receipt or
gate. Exception rollback and intentional hard exits are tested before/after RECORD
and GATE commits. A hot journal yields STORE_BUSY and is retained. An after-commit
lost reply preserves one original Receipt/decision. Neither recovery nor refund is
performed. Test processes have bounded waits and explicit exit assertions.

## Actual Codex configuration boundary

Acceptance used installed Codex CLI `0.165.0-alpha.1.2`, with `--ignore-user-config`,
`--ephemeral`, `--skip-git-repo-check`, read-only shell sandbox, disabled shell,
unified exec, apps, plugins and multi-agent features, disabled web, and an inline
MCP server override exposing only the two names above. The exact existing Python
interpreter, src PYTHONPATH and one startup file were supplied to that process.
No user or repository Codex config was edited and no credentials were copied.
The CLI's normal existing sign-in was used without reading credential contents.
See the [documented CLI flags](https://learn.chatgpt.com/docs/developer-commands?surface=cli).

These were two explicitly authorized isolated CLI Main sessions. They were not
desktop Main auto-recovery, a background scheduler, SDK/app-server calls or mocked
MCP clients. Native JSONL calls prove actual model-driven tool use; a local SHA
alone cannot authenticate an author. Both models saw a target and A evidence, not
a supplied B answer. This remains a small synthetic demonstration, not a scientific
benchmark or proof of general agent autonomy.

## M03-E feasibility proposal only

Official [app-server documentation](https://learn.chatgpt.com/docs/app-server)
describes initialize/initialized, thread/resume, turn/start and streamed completion.
The [Codex SDK documentation](https://learn.chatgpt.com/docs/codex-sdk) is a separate
integration route; actual installed SDK availability and its thread ownership must
be checked before selecting a language/API. No SDK dependency is installed here.

Proposed first experiment: one newly created synthetic session owned by the test,
one durable completion inbox, one explicit operator-approved event-to-turn binding
and one bounded resume attempt. Persist event ID, source identity, evidence digest,
target thread ID, last observed turn and submission state before initiation. A
lost response is UNKNOWN: inspect the original target/event, never create another
thread or blindly resend. Test duplicate events, active-turn collision, capacity
failure, malformed output, restart and disconnected client. Reuse M03-D ingress
and frozen policy; the resumed model gains no execution Grant.

Only after that isolated test should a separate review consider an original
desktop-owned conversation: validate ownership, compatible history storage, active
turn status and an approved supported connection. API existence alone does not prove
the current desktop Main can be resumed safely. Separate labels must distinguish
new-session continuation from original-desktop continuation. No M03-E code, watcher,
app-server process or automatic turn was created in this milestone.
