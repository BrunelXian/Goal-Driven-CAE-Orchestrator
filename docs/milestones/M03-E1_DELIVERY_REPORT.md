# M03-E1 delivery — controlled owned CLI/App Server continuation

Date: 2026-10-29 (Asia/Shanghai). Scope: GD-CAE only, TEST_SYNTHETIC read-only ACK.
Starting/final checkpoint: `6c549dc98c25a12dcb9c93baa4fbf8d629c80ec1`, branch `main`.
No commit, staging, push, CI, installation, AF Owner, Abaqus or ODB operation.

**Result: `M03E1_OWNED_CLI_THREAD_CONTINUATION_PASS` within the owned-test-thread scope.**
Full applicable regression passed. Overall acceptance remains limited by E1-15's
interpretation; this is not an unconditional full-milestone/scientific PASS.
E1-15 has an explicit semantic limitation described below; no unconditional
scientific or Desktop-main capability is claimed.

| Capability flag | Evidence/result |
|---|---|
| `OUTBOX_CONTRACT_PASS` | True: focused core/architecture and complete applicable regression passed |
| `OWNED_THREAD_APP_SERVER_SMOKE_PASS` | True: one real event Turn, completed and persisted |
| `EVENT_REDELIVERY_NO_DUPLICATE_PASS` | True: two same-process and two fresh-process redeliveries, zero further starts |
| `DESKTOP_MAIN_AUTO_RESUME_VERIFIED` | **false** |
| `SCIENTIFIC_VERIFICATION_AVAILABLE` | **false** |
| `AF_EXECUTION_INTEGRATION_VERIFIED` | **false** |

## Actual live result and ownership

Installed CLI: `codex-cli 0.165.0-alpha.1.2`.
Executable: `C:\Users\wuxia\AppData\Local\OpenAI\Codex\bin\08d187884f2330d1\codex.exe`.
No upgrade or experimental API enablement. Model remained the configured
`gpt-6-astra`; no silent model switch or capacity bypass occurred.

Fresh isolated CODEX_HOME had no account, so it made zero thread/model calls. The
task-authorized fallback used the existing authenticated home with process-scoped
disable/readonly flags; no credentials were copied or printed, no login was started,
and no global configuration file was edited. Restricted read-root properties are
absent from the installed stable schema. The test used an empty TEMP cwd, readonly
no-network sandbox, approval `never`, and disabled tools/MCP/hooks/web/notifications.

An initial **zero-Turn capability probe** created empty thread
`01a1839b-a7a0-79f0-8bf1-42c5aa47def0`. `thread/turns/list` reported not materialized;
after close, `thread/resume` reported no rollout. This was not counted as a resume
success. It received no seed, event Turn or retry. A single separate persistent test
thread was then created and seeded within the explicit seed authorization.

| Identity | Actual value |
|---|---|
| Persistent test thread | `01a1839f-3cab-7d31-83c5-8ac2edad478f` |
| Explicit setup seed Turn | `01a1839f-3cd5-7763-8d96-89a2eab19c13` |
| Event-derived Turn | `01a183af-fe75-7993-bd75-d7aa7f07707f` |
| Continuation key | `sha256:40c347a532ef0e7be41be392747961f6993f6a6044e4daf683ff2da6c142fa7c` |
| Exact input digest | `sha256:5cb8d4e04a205468bd8a1bd0e7e641f92105a657f61f1f9579846f1760d8503c` |
| Baseline → final history | 1 seed → 2 Turns (seed + event) |
| Actual `turn/start` for event | 1 |
| Terminal notification | `turn/completed`, `status=completed` |
| Persisted output | `CONTINUATION_ACK`, exact event/evidence refs, `NOT_ABAQUS_QUALIFIED` |

The seed completed once. A new process resumed the same thread and read its full
seed history. A test adapter initially rejected any nonempty MCP status list;
read-only diagnosis established that its only entry was disabled `node_repl`, with
zero tools/resources/templates and no error/pagination. The gate was corrected to
accept only that verified disabled state. No extra seed or replacement thread was
used to bypass the gate.

The trusted smoke then prepared a fresh synthetic A-only fixture using the existing
test creator. This fixture preparation is distinct from the continuation: it creates
the initial test budget/A evidence; the continuation cannot mutate either. The
committed A decision generated the event, and its Outbox intent committed before
the single remote start. A separate client process subsequently resumed/read the
same thread and verified the original input and identical two-Turn history.

| Before/after continuation | Both observations |
|---|---|
| Project revision | 10 |
| Budget limit / held / charged / available | 2 / 0 / 1 / 1 |
| Ledger revision | 3 |
| Synthetic effects / Candidate directories | 1 / 1 (A only) |
| B admission | null |
| Main ResearchProject SQLite bytes | Identical SHA-256 |
| Real AF Grant/Run / Abaqus/ODB | None |

Within ResearchProject state, only the new continuation sidecar changes. No proposal is submitted and no Candidate
B is created. Codex response text has no approval, numerical or physical authority.

## Acceptance matrix

Paths abbreviated below: `core` = `src/aegiscae/research/continuation.py`, `rules` =
`continuation_rules.py`, `store` = `continuation_store.py`, `unit` =
`tests/unit/test_continuation.py`. Architecture/store design and state diagram are
in `docs/architecture/M03_EVENT_DRIVEN_CODEX_CONTINUATION.md`.

| ID | Result and proof |
|---|---|
| E1-01 | PASS — installed-version schema/handshake, empty-home auth probe, scoped authenticated fallback, exact owned thread. `m03e1_protocol.py`; probe JSONs. |
| E1-02 | PASS — `core.observe/_source` replays committed `WORKFLOW_RECORDED/DECIDE`; actual A reason `VALID_SYNTHETIC_TARGET_MISS`; no log/LLM trigger. |
| E1-03 | PASS — exact source reconstruction, frozen/Project/file/audit identities and A byte recheck. `test_foreign_stale_tampered_event_rejected`, `test_source_candidate_tamper_blocks`. |
| E1-04 | PASS — fixed exclusive v1 sidecar, canonical source/policy, semantic journal replay. Main database bytes unchanged; no frozen migration. |
| E1-05 | PASS — owner/thread/version/config/seed binding and policy checks; actual owned thread IDs above. `test_bad_port_fails_before_intent`. |
| E1-06 | PASS — transactionally committed intent precedes port call. `test_committed_intent_before_effect_completed_redelivery_no_research_writes`, transaction and hard-exit tests. |
| E1-07 | PASS — one persistent seeded thread, close/reopen/resume and full seed history. Empty probe separately reported as not resumable. |
| E1-08 | PASS — real event Turn completed; exact same thread, +1 history, input digest and qualified ACK confirmed independently. |
| E1-09 | PASS — two in-process plus two fresh-process real-event redeliveries, zero additional starts; deterministic duplicate tests. |
| E1-10 | PASS — full-envelope equality rejects changed/stale/foreign identity or extra injected field; no source digest/key shortcut. |
| E1-11 | PASS — SQLite claim plus threaded and two independent Python process race tests; only winner may dispatch. |
| E1-12 | PASS — doubles cover response/terminal loss, capacity, second preflight failure, KeyboardInterrupt and hard `os._exit(23)` around commit. No live negative model calls. |
| E1-13 | PASS — positive exact normalized history reconciliation, wrong/multiple/absent/digest/tool/output evidence stays UNKNOWN. Actual client restart readback confirms completed Turn. |
| E1-14 | PASS — wrong owner/thread/version/config, unauthenticated, unsafe sandbox/network/approval/tools, busy/absent target rejected. No substitute session. |
| E1-15 | **LIMITED** — source corruption, busy journals and missing/contradictory evidence block; a ContinuationPolicy requiring real V2/V4 or AF scope is rejected. Frozen scientific V2/V4 requirements remain unmet and do not bar this separately scoped read-only ACK. See interpretation below. |
| E1-16 | PASS — fixed template; bounded reconstructed JSON; free-text narrative omitted; injected event rejected; unknown history items conservatively count as tools. |
| E1-17 | PASS — measured before/after revision, ledger, effect/candidate/admission and SQLite digest invariant; no AF/solver/proposal execution channel. |
| E1-18 | PASS — independent Python readback for ELIGIBLE/UNKNOWN/completed; actual fresh-process duplicate handling needs no chat memory. |
| E1-19 | PASS — 703 passed / 21 expected AF-live skips; existing AF seven-read and proposal two-tool interfaces unchanged. |
| E1-20 | PASS with stated scope limits — full tests/Ruff/diff checked, independent source/evidence/document review completed; owned servers all closed with exit 0; no next-stage work. |

**E1-15 interpretation requiring architecture acceptance:** the existing frozen
VerificationContract requires V2 and may require V4 for scientific acceptance.
Synthetic fixtures cannot satisfy those requirements. The new sidecar policy says
`requires_real_v2=false`, `requires_real_v4=false` solely for read-only continuation
eligibility. True/AF/physical-verdict policies are rejected. This does not weaken or
reinterpret the frozen scientific contract. If E1-15 means no ACK Turn may ever run
while the scientific contract has unmet V2/V4, the milestone is PARTIAL under that
literal reading. This report does not claim an unqualified full E1-01–20 PASS.

## Measured tests and process closure

Verified existing environment:
`D:\XianLab\envs\LangChainEnv\Scripts\python.exe`, Python 3.12.10, pytest 9.1.0,
SQLite 3.49.1. Existing Ruff: `D:\ProgramData\anaconda3\Scripts\ruff.exe` 0.12.0.
No dependencies or global environment settings changed. Tests used absolute
interpreter, `-B`, disabled pytest plugin autoload, no pytest cache provider and
fresh isolated TEMP roots. AF live opt-ins were unset.

```text
Focused core + architecture: 218 passed in 204.60s (0:03:24), exit 0
Full no-Solver regression: 703 passed, 21 skipped in 822.86s (0:13:42), exit 0
Ruff check --no-cache .: All checks passed!, exit 0
git diff --check: exit 0 (LF/CRLF advisories only)
```

Full command: the verified absolute Python interpreter with
`-B -m pytest -q -p no:cacheprovider --basetemp=<owned evidence root>\pytest-full`.
No M03-E1 test is skipped. There are 66 additional passing tests versus the prior
reported baseline. All 10 new files also received explicit `git diff --no-index
--check` against the empty file: no whitespace diagnostics (exit 1 denotes added
file differences, not whitespace failure).

The earlier stage baseline was **reported** as 637 passed, 21 skipped in 859.88s;
it is not substituted for this round's full run. The 21 expected skips require
separate live AF authorization: M01-B (1), M01-C (1), M03-B (19).

Development failures are retained transparently: first focused attempt ended with
43 passed / 1 failed because the parent test process had loaded the earlier policy
while its child loaded newly edited required-verification fields. No persisted
scientific schema was migrated; fresh fixtures and fixed source were rerun. Initial
Ruff found one unused helper import, removed. The seed-resume adapter's empty-MCP
assumption failed safely before any event Turn, then the disabled-state check was
corrected from actual runtime evidence.

All owned App Server processes were closed and awaited; recorded exit codes are 0:

| Purpose | Owned PID(s) |
|---|---|
| Isolated/existing-auth no-thread probes | 8040, 20756 |
| Empty-thread create/resume probe | 3416, 12848 |
| Seed / first resume | 28772, 8816 |
| Read-only resume/inventory diagnosis | 28260, 29508, 14864 |
| Actual event server / independent post-readback | 7512, 2508 |

No unknown process was taken over or killed. Cleanup means closing owned handles,
not deleting test evidence, session history or old M01-B encrypted materials.
Final read-only PID presence check found none of the 11 owned server PIDs remaining.

## Independent Reviewer

Native subagent `/root/m03e1_review` performed read-only source and actual evidence
review. It identified the E1-15 interpretation issue, optimization-mode assert risk
and gaps in hard-exit/fresh-process tests. Explicit optimization rejection, strict
disabled-MCP checks and additional offline cases were added. Final source review
found no blocker to the authorized single smoke.

The Reviewer independently rehashed the raw persisted `userMessage`, confirmed
exact thread/Turn/terminal, one start and +1 history, fresh-client zero-start trace,
unchanged Project SQLite/revision/budget/A-only state, and exit-0 cleanup records.
It supports `OWNED_THREAD_APP_SERVER_SMOKE_PASS` and
`EVENT_REDELIVERY_NO_DUPLICATE_PASS` only within those boundaries. It did not execute
tests or services and its review does not substitute for measured test results.

## Files, preservation, Git checkpoint readiness

New source: `src/aegiscae/research/continuation.py`, `continuation_rules.py`,
`continuation_store.py`.

New tests/support: `tests/unit/test_continuation.py`,
`tests/architecture/test_continuation_boundary.py`,
`tests/integration/m03e1_protocol.py`, `m03e1_support.py`, `m03e1_owned_smoke.py`.

New documents: this report and
`docs/architecture/M03_EVENT_DRIVEN_CODEX_CONTINUATION.md`.

Modified existing tests only: `tests/architecture/test_af_read_boundary.py`,
`test_forbidden_direct_writes.py`, `test_package_skeleton.py`,
`test_research_boundary.py`. These add exact new module/SQL/creation exceptions;
the original seven AF tools and two proposal tools receive no new authority.

Entry audit covered 108 nonignored files. The four named architecture files are the
only pre-existing files changed this round. All other pre-existing hashes match,
including all M01–M03-D source, README, `.gitignore`, historical ADRs, frozen baseline
and the untracked review patch. Starting/final index is empty. The accumulated
uncommitted M03-A/B/C/D work is retained, not staged or reset.
Final accumulated status: 8 modified tracked files, 39 untracked files, zero staged
paths. This milestone contributes 10 new files and changes to the 4 named existing
architecture tests; other dirty paths predate M03-E1.

`git check-ignore` confirms Kickoff_Docs, the precise existing CAE-model exclusion
and local `.codex/config.toml` stay ignored; the CAE-model check used a nonexistent
probe name only, without reading model files. AbqJobPilot was not read/modified in
this phase. No production Project, historical credentials/journals, another existing
thread or Desktop Main was accessed. No session index or rollout file was directly
opened/edited by the harness; App Server itself normally persists its owned test history.

Checkpoint readiness remains **review-only**, not permission to commit: first accept
the E1-15 scope and final test results, review the accumulated explicit whitelist,
exclude all TEMP databases/journals/protocol dumps/config/credentials and keep private
areas ignored. No broad `git add`, commit or push was performed.

## Evidence retention, risks and stopping point

Owned evidence root (local, deliberately not committed):
`C:\Users\wuxia\AppData\Local\Temp\gdcae-m03e1-870bf6a23d0c4d08a082e30c0ce10fd0`.
Important files: `seed-evidence.json`, `resume-diagnostic.json`,
`runtime-status-diagnostic.json`, `event-source.json`, `event-start-response.json`,
`event-terminal.json`, `event-receipt.json`, `smoke-evidence.json`,
`post-event-readback.json`, `*-cleanup.json`, `pytest-full.log`.
They contain owned test identities and synthetic data, not copied authentication
secrets. Test-owned persisted Codex history remains in its authenticated home;
no session-index/rollout editing or deletion was attempted.

Remaining limits: one event/one Project sidecar/one version/one owned thread; no
multi-round loop, durable remote idempotency or cross-system exactly-once; pending
intent may conservatively block a never-sent request; model/network/capacity failure
requires human review or positive read-only reconciliation. Readonly sandbox and
SHA/time are not cryptographic or hostile same-user security boundaries. The source
read transaction can delay writers. Hard-exit journals are retained and block rather
than auto-repair. Real V2/V4, AF execution and current Desktop Main continuation are
unavailable/unverified.

M03-E2 is **feasibility research only**: establish documented Desktop ownership,
attachment/visibility and concurrency semantics using a separately approved
disposable thread before considering the original Main. Do not select by recency,
edit history, start a daemon or add execution rights. The one-page bounded proposal
is in the architecture document. No E2 implementation or automatic continuation of
this development Main was started.

**STOP: implementation, real smoke, regression and report audit complete within
the stated scope; await architecture review, including E1-15 interpretation.**
