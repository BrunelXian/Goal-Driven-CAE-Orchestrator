# M03-D — Controlled Proposal Ingress and Review Gate

Date: 2026-10-29 (Asia/Shanghai). **M03-D required ingress/review acceptance complete**, with the separate labels and optional continuation exclusion below.

| Independent result | Evidence / qualification |
|---|---|
| MCP_PROPOSAL_CONTRACT_PASS | Two-tool protocol, strict capture, durable slot/replay and bounded errors verified |
| CODEX_PROPOSAL_INGRESS_PASS | Two actual, explicitly authorized Codex CLI Main sessions called the new MCP tools |
| DETERMINISTIC_ADMISSION_PASS | Separate trusted runner produced two ADMISSIBLE_SYNTHETIC_ONLY decisions |
| Frozen-policy review | Both POLICY_ACCEPTED_SYNTHETIC_ONLY; no model approval or human identity claim |
| SYNTHETIC_CONTINUATION_PASS | **NOT_RUN / NOT_IMPLEMENTED in M03-D**; optional branch deliberately omitted |
| AF_DYNAMIC_EXECUTION_VERIFIED | false |
| SCIENTIFIC_VALIDATION_AVAILABLE | false; V2 NOT_RUN, V4 NOT_ASSESSED |
| AUTO_CONTINUE_ORIGINAL_MAIN | NOT_TESTED; no desktop recovery or event-triggered turn |

These labels must not be combined into a real-execution or scientific PASS.
The receipt tool did not admit a Workflow Candidate, reserve budget or execute B.
See [architecture, authority model and M03-E proposal](../architecture/M03_PROPOSAL_INGRESS_AND_REVIEW.md).

## G0 and preserved baseline

Branch `main`, HEAD `6c549dc98c25a12dcb9c93baa4fbf8d629c80ec1` remains the M02-G
Checkpoint. Entry index empty; M03-A/B/C tracked and untracked work retained.
An entry SHA-256 manifest covered 98 nonignored files: 91 remain byte-identical,
seven have scoped changes below. No cleanup, reset, fetch, staging, commit, push,
PR or CI action was performed. Read the M03-D taskbook, global AGENTS/environment
registry, M03-C implementation/reports, existing MCP and ADR-003/004 boundaries.

Environment verified before Python work:

- `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`, Python 3.12.10.
- pytest 9.1.0, MCP SDK 2.3.0, SQLite 3.49.1.
- Existing Ruff `D:\ProgramData\anaconda3\Scripts\ruff.exe`, 0.12.0.
- Existing Codex CLI `0.165.0-alpha.1.2`; no installation or upgrade.

The original `research.sqlite3` schema and frozen contract DTOs are unchanged.
No migration of archived data was attempted. Compatible sidecar initialization
is tested against a freshly frozen pre-ingress M03-C Project and byte-for-byte
comparison of its database before and after receipt/gate, plus old-reader reopen.
Unknown sidecar schemas and incomplete initialization fail closed.

AbqJobPilot Develop tracked state remained clean at
`7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`; Stable was not accessed or modified.
Existing AF seven-tool server/facade, README, .gitignore, historical ADRs, baseline,
M01-C review patch and earlier delivery reports remain byte-preserved from entry.
Kickoff_Docs, CAE models and .codex/config.toml retain their ignore rules; only the
authorized taskbook was read. No private models or historical credentials/journals
were opened, reused or deleted.

## Exact source delta

Seven existing files changed relative to entry:

1. `src/aegiscae/research/workflow.py`: extract shared deterministic snapshot evaluation; add pure historical Brief reconstruction. Existing admission still uses the same model/file/diff checks.
2. `tests/architecture/test_af_read_boundary.py`: recognize only exact sidecar SQL calls; retain all other AF write/lifecycle prohibitions.
3. `tests/architecture/test_dependency_direction.py`: allow only the named ProposalIngress import in the new interface.
4. `tests/architecture/test_forbidden_direct_writes.py`: exact exclusive sidecar creation exception.
5. `tests/architecture/test_forbidden_surfaces.py`: exact MCP SDK imports for the new named server file.
6. `tests/architecture/test_package_skeleton.py`: four exact new implementation module paths.
7. `tests/architecture/test_research_boundary.py`: exact sidecar connection/SQL/creation predicates; no general database permission.

Ten new files:

- `src/aegiscae/interfaces/mcp_proposal.py`.
- `src/aegiscae/research/ingress_store.py`.
- `src/aegiscae/research/proposal_ingress.py`.
- `src/aegiscae/research/proposal_review.py`.
- `tests/architecture/test_proposal_boundary.py`.
- `tests/unit/test_proposal_ingress.py`.
- `tests/integration/m03d_support.py`.
- `tests/integration/test_proposal_mcp.py`.
- `docs/architecture/M03_PROPOSAL_INGRESS_AND_REVIEW.md`.
- This delivery report.

`git diff` against HEAD also includes earlier uncommitted stages. The list above
is based on entry hashes, not an inaccurate attribution of all HEAD differences
to this milestone. No second workflow/agent framework or execution bridge was added.

## Protocol and permission analysis

Startup fixes one root, ResearchProject and challenge. MCP arguments cannot select
a Project, path, workflow backend, command, SQL or arbitrary RPC. The only new
write is `gdcae_record_candidate_proposal(proposal_key, proposal_json)`;
`gdcae_get_proposal_status({})` is readonly. Both use the official STDIO MCP SDK.
The old seven AF reading tools were not extended.

| Record | Meaning | Does not confer |
|---|---|---|
| ProposalReceipt | Original untrusted bytes recorded in one challenge slot | Candidate admission, approval, budget or job receipt |
| AdmissionDecision | Deterministic eligibility at named checked revision | Human consent or future resource guarantee |
| ReviewDecision | Frozen TEST_SYNTHETIC policy disposition | Authenticated human action or production permission |
| AF ExecutionGrant | Owned by AbqJobPilot; absent here | Nothing in this milestone creates or consumes one |

AUTO_TEST_SYNTHETIC permits in-contract snapshot acceptance. REQUIRE_HUMAN_REVIEW,
STOP/REQUEST_REVIEW and inconclusive/invalid cases stop. No human confirmation UI
or token is implemented, and no model-authored consent is accepted. Local process
and shell ownership remain the same Windows user: these are application guards,
not OS isolation from an Agent with shell access.

## Real Codex Main MCP evidence

Owned evidence root, outside the repository:
`C:\Users\wuxia\AppData\Local\Temp\gdcae-m03d-native-knon7261`.

The desktop tool registry did not have a dynamic proposal MCP attached. The taskbook
explicitly permits a scoped CLI session, so each actual Main ran using the installed
CLI with ignored user config, ephemeral history, a fresh empty test cwd, read-only
shell sandbox, shell/unified-exec/apps/plugins/subagents disabled, web disabled,
and one inline required MCP server binding. The CLI used its existing sign-in
mechanism; the Agent did not read or copy credential contents. No persistent/global
MCP config was changed.

The saved `native-prompt.txt` tells Main to read the Brief, derive one bounded scalar,
record it once and read status. It supplies the DTO shape but no B answer. The only
completed model tool calls in each original JSONL are:

1. `gdcae_get_proposal_status({})`: exact challenge/Brief, no receipt or decision.
2. `gdcae_record_candidate_proposal(...)`: actual model-authored JSON string.
3. `gdcae_get_proposal_status({})`: identical Receipt, `decisions=null`.

| Identity/result | Scenario one | Scenario two |
|---|---|---|
| Main thread ID | `01a18364-a0e3-7c31-af6e-a391fb52c5e1` | `01a18365-85d9-7773-821c-49d8802f7bb3` |
| Project | `rp_971db96158664d7e98e4be9ccda91bdf` | `rp_dcd8080f80ca4304a9cea8d6e45ba63b` |
| Challenge | `challenge_0bf09776accd499aaaa6163b7b8c0576` | `challenge_04c20c5b3d554adca0c915830475f0a1` |
| Workflow | `workflow_3f7b332f030346f087d78c5fbdea1f70` | `workflow_b1a43125851f47dbac0fb75f05b728a4` |
| A evidence | TEST_ORACLE: 40 N → 2 mm | TEST_ORACLE: 40 N → 2 mm |
| Independently frozen target | 0.5 mm | 1.25 mm |
| Main proposal | 10 N | 25 N |
| Receipt | `proposalreceipt_aeea0e320d824fb344be6e8f9e386629` | `proposalreceipt_179d9b07674484a432a5112172f8b328` |
| Independent gate | ADMISSIBLE_SYNTHETIC_ONLY | ADMISSIBLE_SYNTHETIC_ONLY |
| Frozen review | POLICY_ACCEPTED_SYNTHETIC_ONLY | POLICY_ACCEPTED_SYNTHETIC_ONLY |

Proposal SHA-256 values:

- One: `aeea0e320d824fb344be6e8f9e386629b62e844766b07e57a6dbf607e51098c0`.
- Two: `179d9b07674484a432a5112172f8b328b0dec2af9692ca0d6017b8e7a7ff3153`.

Original JSONL SHA-256 values:

- `native-one-events.jsonl`: `c56752436a37905cb309ed37e27ffbc97356f174bf8c89d51e784984cbcb02e0`.
- `native-two-events.jsonl`: `83c0f63516d21a2e0dbda5add8de6439968bd6e92b460c2fa01aab8736bdb908`.

Each scenario retains `native-provenance.json` with exact proposal chunks, original
event hash, receipt, checked decisions and thread ID; `challenge.json`,
`before-ingress.json`, `recorded-before-gate.json`, `gate-result.json`,
`status-after-gate.json` and `after-gate-invariants.json` provide the state chain.
Independent Reviewer recalculated the hashes and checked exact tool argument bytes
against the stored capture. Hashes alone are not author authentication; native CLI
events establish the observed model/tool interaction. Neither scenario is a blind
scientific benchmark or a recovery of the original desktop Main.

Both CLI processes exited 0. The only CLI stderr was its PowerShell shell-snapshot
unsupported warning; the MCP lifecycle tests require protocol-only stdout and empty
server stderr. A process query scoped to this exact root found zero matching
Python/Codex processes after completion; no nonowned process was stopped.

Independent gates ran after reception, outside the MCP server. Before and after
each gate: Project revision 10, A effect count 1, Candidate directory count 1,
ledger charged 1/held 0/available 1, Workflow proposal_admission null. Therefore B
was not materialized, reserved or executed. Optional continuation was not attempted.

## DP-01–DP-20 acceptance matrix

| ID | Result | Proof |
|---|---|---|
| DP-01 | PASS | Fixed startup binding; tool schemas have no root/project selector; wrong Project rejects |
| DP-02 | PASS | Issued challenge, historical Brief equality, bounded expiry, immutable policy; copy/schema/rehashed metadata negatives |
| DP-03 | PASS | Actual SDK STDIO lifecycle exposes exactly two tools; unchanged original seven-tool regression |
| DP-04 | PASS | Two native CLI Main JSONL call sequences and matched durable receipts, independently reviewed |
| DP-05 | PASS | Strict raw DTO matrix rejects extra fields, duplicate keys, floats, NaN/Infinity, paths, unsafe prose and entity/unit errors |
| DP-06 | PASS | Receipt-only effect; exact original Project DB bytes and state unchanged |
| DP-07 | PASS | Exact replay returns same receipt; after-commit failure/hard exit retains original key/content |
| DP-08 | PASS | Different content/key conflict; two Python processes contend for one slot, exactly one wins |
| DP-09 | PASS | Project/goal/evidence/revision mismatch, stale duplicate, expired and revoked challenge negatives |
| DP-10 | PASS | Independent current Project snapshot plus shared M03-C gate; no copied Agent budget/PASS accepted |
| DP-11 | PASS | Native proposals accepted by pre-existing synthetic policy with no model self-approval |
| DP-12 | PASS | Illegal range recorded as untrusted then rejected; wrong entity/material/BC/criteria blocked by strict DTO; actual file drift inconclusive |
| DP-13 | PASS | Frozen human-required policy and STOP/REQUEST_REVIEW stop; approved fields rejected |
| DP-14 | PASS | Unknown A cannot issue challenge; budget exhaustion/revision drift, Project/sidecar journal block; no refund or continuation |
| DP-15 | PASS | Sanitized bounded SDK outputs/errors; tampered extra Brief field rejected against authoritative historical reconstruction |
| DP-16 | PASS | Actual native pre-gate artifacts and unit DB-byte/candidate/ledger/effect equality |
| DP-17 | OPTIONAL NOT_RUN | No M03-D continuation API; receipt or policy acceptance never inferred as execution |
| DP-18 | PASS | Exception and hard-exit 73 at before/after RECORD/GATE commits; retained hot journal or exact durable record |
| DP-19 | PASS | Solver/ODB/AF Owner/private models/AF write/auto-Turn all NOT_USED |
| DP-20 | PASS | Full regression 637 passed/21 historical live skips; Ruff and tracked/untracked whitespace checks pass; independent review complete; owned processes closed |

Detailed test sources: `tests/unit/test_proposal_ingress.py`,
`tests/integration/test_proposal_mcp.py`, `tests/architecture/test_proposal_boundary.py`.
Concurrency/fault tests use fixture proposals and never label them native Codex output.

## Actual tests and independent review

All Main pytest commands use the verified absolute interpreter, `-B`, src PYTHONPATH,
PYTHONDONTWRITEBYTECODE=1, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, `-p no:cacheprovider`,
fresh isolated TEMP roots and no M01/M03-B live opt-ins. No dependencies changed.

Focused final command:

```text
python.exe -B -m pytest tests/unit/test_proposal_ingress.py
  tests/integration/test_proposal_mcp.py tests/architecture -q -x -p no:cacheprovider
195 passed in 258.35s (0:04:18)
```

Independent Reviewer final targeted negative/architecture command:

```text
164 passed in 60.33s
exit 0
```

Its root: `gdcae-m03d-review-final-3c074e04300849baba5eee7fc0388254` under TEMP.
Reviewer also read both original native event streams, proposal bytes, receipts and
before/after gate invariants. Final opinion: no remaining blocking issue. Reviewer
advice is engineering review, not scientific verification or execution permission.

Full applicable no-Solver regression:

```text
D:\XianLab\envs\LangChainEnv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
  --basetemp <fresh TEMP gdcae-m03d-regression-*>
637 passed, 21 skipped in 859.88s (0:14:19)
exit 0
```

The 21 skips are one M01-B live test, one M01-C live test and 19 M03-B AF live cases.
Their explicit opt-ins were unset; starting an AF Owner is outside this milestone.
No M03-D test was skipped or replaced with a mock claim of native Main acceptance.

Final Ruff: `D:\ProgramData\anaconda3\Scripts\ruff.exe check --no-cache .` →
`All checks passed!`. `git diff --check` and explicit no-index whitespace checks
for all ten new files and the modified untracked Workflow source passed. Git's
LF→CRLF advisories did not indicate whitespace errors or an applied rewrite.

Development failures retained transparently:

- First targeted run: 1 failed, 6.69s; storing raw JSON as one string exceeded existing bounded-JSON limits. Fixed with exact-byte chunks, without relaxing primitives.
- Second: 1 failed, 10.04s; duplicate setup raised the store's mapped error rather than the expected filesystem exception. Added a structured exclusive-initialization rejection.
- Third Main run: 1 failed/31 passed, 174.60s; new exact sidecar SQL was not connected to the AF architecture guard. Added only the exact predicate.
- Reviewer first full focused run: 1 failed/184 passed, 170.22s, same guard failure. Its security probe reproduced extra Brief projection; source review identified contradictory metadata acceptance. Both findings were fixed with negative tests.
- Native first post-gate helper asserted tuple-versus-JSON-list equality for ledger reservations after a successful gate. Normalized the test comparison with canonical JSON, then verified existing original records/invariants without replacing receipts or producing another gate. This was a test assertion defect, not a budget change.

## Risks, retention and next stage

| Risk/limit | Current handling |
|---|---|
| Same-user filesystem/shell bypass | Explicit application-level boundary; no claim of OS-enforced human identity |
| Hash/time provenance | Detect ordinary corruption/contradiction; no signature or trusted-clock claim |
| Cross-store TOCTOU | No continuation; historical positive gate does not lock budget; future Workflow admission must recheck CAS |
| Expiry/revocation | Record rejects; status retains original receipts and validity; no key rotation/reopen shortcut |
| Crash journal | STORE_BUSY, no auto-repair/retry/refund; intentional sentinels retained |
| Conservative DTO | One synthetic entity/step/parameter; unsafe prose may also reject benign language |
| One challenge per Project sidecar | Deliberate milestone limit; no multi-round/reissuance/migration workflow |
| Real MCP deployment | Only scoped CLI acceptance; no global or current desktop attachment installed |
| AF/science | No AF dynamic B integration, V2 or V4; metrics remain TEST_ORACLE |
| Test retention | Fresh owned TEMP evidence retained for review; no historical materials cleaned |

No AF credentials were created. Process cleanup means closed/awaited owned CLI/MCP
and bounded test children, not deletion of evidence or historical journals. Existing
M01-B encrypted materials and earlier stage TEMP data were not reused or cleaned.

M03-E proposal: begin with one separately approved synthetic session and durable
event-to-thread binding; verify ownership and active-turn state, persist event/turn
deduplication, use one explicit resume/start attempt, and treat response loss as
UNKNOWN. Test capacity failures, duplicate events, crashes and wrong thread before
considering original desktop Main resumption. Official API availability does not
establish desktop ownership or safe automatic continuation. Full feasibility plan
and sources are in the architecture document. Nothing in M03-E has been implemented.

**STOP: awaiting the next architecture review. No next-stage implementation.**
