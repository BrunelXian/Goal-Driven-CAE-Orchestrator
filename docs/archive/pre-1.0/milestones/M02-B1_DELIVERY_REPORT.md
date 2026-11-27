# M02-B1 — Delivery report

Status: **PASS — M02-B1 synthetic-only acceptance, 2026-10-28.**

The first typed, auditable mutation guard is implemented for a deliberately artificial text
fixture, **NOT_ABAQUS_QUALIFIED**. PASS means the bounded permitted mutation and persistence
tests below passed. It is not model/physics/Goal verification, human approval, execution
permission or a qualification of arbitrary Abaqus INP syntax. Stop for architecture review.

## G0 baseline and G1 reconciliation

Branch `main`, local HEAD `af3cfd90821cddf65ef93827a20fc2b26d98f0fc`, no staged changes.
The worktree already contained uncommitted M01/M02-A materials; nothing is inferred to exist
in remote Git. The supplied taskbook states that the architect had not independently read
the M02-A source/logs. This report does not replace that architecture review.

Read global environment policy, the full M02-B1 instruction, current research/contracts source,
M02-A report, ADR-003/004, authority register and bridge/MCP tests. Pre-change manifest below
captures 70 non-ignored files, including all existing dirty materials and protected documents.
No CAE-model inventory or private AF data was read. Existing environment verified:

```text
D:\XianLab\envs\LangChainEnv\Scripts\python.exe
Python 3.12.10 / SQLite 3.49.1 / pytest 9.1.0 / mcp 2.3.0
G0 pytest: 318 passed, 2 skipped in 11.19s
G0 Ruff: All checks passed!
```

**G1 finding:** `ScientificConstraint` is a metric threshold DTO limited to displacement,
stress, reaction_force and strain. That subset properly maps to V3. The M02-A prose “all hard
constraints” was too broad if interpreted as every project constraint. Artifact identity,
allowed model edits, numerical-health requirements, physical reference and resource policy
already occupy distinct fields; their authority does not move to V3.

Implemented a separate `mutation-coverage-v1` derivation with explicit V0/V1/V2/V3/V4/Policy
rules and references, including shared rules and multiple checks for artifact constraints.
Uncovered V3 limits still fail the unchanged M02-A contract validator. Stored coverage must
match the derivation exactly, including mandatory edges. Unknown evidence blocks decisions
requiring it; V2/V3/V4 and real execution authorization are not evaluated by mutation admission.

**No frozen-schema migration was needed.** `research_contracts.py`, all old ADRs and M02-A
documentation remain byte-identical. Existing frozen Bundle/part bytes and historical audit
records remain unchanged in tests. New Candidate events carry explicit new payload versions
in the existing audit table; old readers fail closed on unknown event kinds. No table migration
or automatic upgrade is performed, and no old V3 rule is silently reinterpreted.

## Implemented scope and grammar

See [architecture, exact grammar and API](../architecture/M02_MODEL_MUTATION_GUARD.md).
The reviewed [SIMULIA CLOAD documentation copy](https://abaqus.uclouvain.be/English/SIMACAEKEYRefMap/simakey-r-cload.htm)
shows contextual load options beyond a numeric triple. The initially attempted VT 2024 page
returned HTTP 403; the accessible university-hosted SIMULIA reference was used only to bound
the design. No current Abaqus compatibility claim is made. The taskbook's explicit synthetic
fallback is therefore used rather than a general INP parser.

`synthetic-load-v1` supports exactly one ASCII/LF fixture with fixed units/material/BC/mesh/contact,
Beam.Tip NODE_SET, Load step/frame 1, DOF 1, load_tip anchor and one `LOAD_N` scalar. The only
allowed range is 0–100 N inclusive. Optional COMMENT text is inert and unchanged. Requests
cannot widen bounds, choose a path, supply a regex/patch or change another numeric field.
Includes, real CAE/Python inputs, repeated/missing targets, unknown grammar, wrong selectors,
NaN/Infinity/floats/exponents/locale decimals and wrong units fail before candidate publication.

The editor and a separate line/span/prefix/suffix checker must agree. Every non-approved byte
is compared, not merely selected semantic fields. Manifest includes candidate/request/source/
output identities and digests, sizes, line/byte offsets and token lengths. Four immutable parent
digests resolve the original Bundle/Goal/Model/Verification IDs and versions; request also binds
Project ID/revision and baseline artifact ID. No raw source/comment or private path is returned.

New workspaces are explicitly created under OS TEMP, with root/staging identities and a marker.
The trusted fixture writes baseline.txt; the product never writes it. The product creates a new
stage directory and exclusive files, flushes/fsyncs, independently rechecks before and after
commit, and records the proposal/manifest in the existing ResearchProject audit transaction.
`INCOMPLETE.json` remains intentionally: files alone never prove publication.

Project revision remains the contract-state revision; audit sequence serializes candidate
events. A new candidate must use the current frozen parent. Exact-key replay rechecks files
without rewriting; historical replay/read after a later freeze explicitly returns
HISTORICAL_MUTATION and both revisions. It does not authorize a new mutation under the later policy.

## MG-01–MG-16 machine-checked acceptance

Functional references below are in `tests/unit/test_model_mutation.py`; existing M01/M02-A tests
remain separate, unchanged regressions. All filesystem changes used synthetic isolated TEMP.

| ID | Result | Machine-checked evidence |
|---|---|---|
| MG-01 | PASS | Legal scalar, unique stage/Candidate, exact independent diff/manifest; baseline and frozen bytes/audit history unchanged |
| MG-02 | PASS | Below/at/inside/at/above fixed bounds; proposed limit widening rejects |
| MG-03 | PASS | E/material/BC/mesh/contact/selector/extra-line differences reject; malicious editor cannot bypass independent checker |
| MG-04 | PASS | Missing/duplicate anchor, wrong step/entity/DOF/frame and repeated keyword reject/unsupported |
| MG-05 | PASS | INCLUDE and unknown/context-dependent grammar unsupported; declared dependencies not opened |
| MG-06 | PASS | Float, NaN/Infinity, exponents, locale/noncanonical Decimal, wrong dimension/unit reject before output |
| MG-07 | PASS | Stale hash/size/Project/revision/contract refs fail; source changed during staging blocks publication; forged rehashed stale-parent audit rejected |
| MG-08 | PASS | Traversal/nonabsolute roots, synthetic CAE-model-area name, marker/copy identity, source hardlink, workspace/output junction and pre-existing output reject without external modification |
| MG-09 | PASS | Exact replay changes neither DB nor file bytes/mtime; same key/different request conflicts; lost/polluted committed output returns INCONCLUSIVE |
| MG-10 | PASS | Concurrent duplicate creators yield one effective audit publication and one stage; replay/conflict/busy never overwrites or duplicates |
| MG-11 | PASS | Five exception and five actual child hard-exit points; true partial file retained, pre-DB artifacts unaccepted, post-commit loss inconclusive, journal quarantine preserved |
| MG-12 | PASS | Malicious COMMENT remains inert/unchanged and is not echoed as authority |
| MG-13 | PASS | Six owners, unique rule IDs and source references, no orphans, shared/multiple rules; missing mandatory coverage rejected, original frozen DTO unchanged |
| MG-14 | PASS | Only MODEL_MUTATION_PERMITTED_ONLY; V2/V3 NOT_RUN, V4 NOT_ASSESSED, execution_authorized=false; no Grant or physics/Goal success |
| MG-15 | PASS | Existing seven readonly MCP tool enumeration and all M02-A freeze/store tests pass; fresh child readonly Candidate inspection blocks external imports/process/network effects |
| MG-16 | PASS | Full pytest 410 passed/2 inherited skips, whole-repo Ruff, tracked/new-file diff checks; independent reviewer 114 passed and no remaining source blocker |

## Actual test commands, failures and results

All Python commands used the absolute verified interpreter, `PYTHONDONTWRITEBYTECODE=1`,
repository `PYTHONPATH=...\src`, `-p no:cacheprovider`, and fresh external
`%TEMP%\gdcae-m02b1-<purpose>-<UUID>` basetemp. Live opt-in environment variables were unset
only in the test shell; no configuration or Python environment file was modified.

```text
python.exe -m pytest -q -p no:cacheprovider --basetemp <fresh TEMP>
  G0:                     318 passed, 2 skipped in 11.19s
  Initial guards + M02-A:  3 failed, 182 passed in 9.33s
  Corrected guards+A:     193 passed in 9.72s
  Focused mutation tests: 84 passed in 16.08s
  Added scope assertions: 2 passed, 82 deselected in 1.11s
  Final full suite:       410 passed, 2 skipped in 26.75s

D:\ProgramData\anaconda3\Scripts\ruff.exe check .
  All checks passed!
git -c core.safecrlf=false diff --check
  exit 0, no diagnostics
```

Initial architecture failures identified new modules, unapproved mkdir calls, and dynamic
`getattr` in DTO validation. Removed dynamic dispatch, admitted only the two exact new modules,
and added precise module/function/call allowances plus negative tests. Also tightened Path.open
mode checks so a sibling/reader cannot borrow the new exclusive-write exception. No tests were
disabled or marked expected-failure. Test author's first focused run had five fixture failures
from assuming a nonexistent workspace-open helper; fixtures now reconstruct the explicit typed
handle. These were not silently omitted product failures.

Independent Reviewer found a real audit consistency defect during implementation: stored
Candidate parent matching allowed an older revision although admission required the current
revision. Reader matching now requires equality at that historical event position. The regression
reorders/recomputes audit/record hashes and still rejects. Reviewer also requested explicit historical
scope and non-completed wording for derived V0/V1 requirements; both changes and assertions landed.

Exact inherited skips (unchanged):

- `tests/integration/test_af_read_live.py::test_g1_g2_real_authenticated_fake_only`, line 403:
  `Explicit M01-B approval, fresh TEMP root and isolated invocation required`.
- `tests/integration/test_mcp_read_live.py::test_real_stdio_codex_native_review`, line 228:
  `M01-C fresh TEST root and explicit live opt-in required`.

These require AF TEST Owner lifecycles not authorized here; no mandatory offline mutation safety
case is skipped. This run does not recertify live AF compatibility. New untracked files are checked
separately with `git diff --no-index --check -- NUL <file>`; an exit 1 with no diagnostics denotes
content different from NUL, not a whitespace failure.

## Crash and publication evidence

Both exceptions and child `os._exit(73)` cover before_stage, after_partial_file, after_file,
before_commit and after_commit. Partial staging has an INCOMPLETE marker; a separate injected IO
failure writes only seven candidate bytes and proves they cannot be published. Source modification
during staging also blocks the DB event. Completed DB events with renamed/missing/polluted files
return INCONCLUSIVE on direct read and replay. No automatic replay or cleanup occurs.

A hard exit after audit insertion may retain SQLite journal. Product opening then returns
STORE_BUSY without mutation. The B1 hard-exit tests preserve that quarantine and **do not perform
raw SQLite recovery**. When no journal blocks reading, only a committed event plus a complete
digest-matching independently checked file can return PERMITTED. These are process-interruption
tests, not certification of atomic filesystem+DB publication under power loss.

Bounded read-only audit finding: if normal readonly opening succeeds, historical events are
available through audit_events. If journal detection fails preflight, this API cannot inspect
committed records safely and does not try. A separately approved administrative proposal may
record file/journal metadata and hashes into a bounded diagnostic report, or examine an isolated
copy under explicit recovery rules. It must distinguish “not observed” from “not committed”,
never delete journals/force locks, and never infer permission to replay an external action.
No such diagnostic/recovery facility is implemented in B1.

## Independent Reviewer

Native `/root/m02b1_review` performed independent readonly G1, source and test review. It found
no mandatory frozen-schema migration, raised the parent-revision defect and historical-scope
ambiguity described above, then confirmed both fixes and no remaining blocking source finding.
It independently executed:

```text
tests/unit/test_model_mutation.py
tests/architecture/test_research_boundary.py
114 passed in 15.29s
```

Its environment was independently verified and all fixtures stayed in a fresh external TEMP.
It made no repository edits. Native review is advisory engineering review, not an authoritative
scientific VerificationRecord or proof of operating-system isolation.

Final readonly review of both completed documents returned **no blockers**, supporting scoped
M02-B1 PASS. Reviewer confirmed the MG matrix, frozen-schema/event-version distinction,
historical/current scope, journal/publication limitations, B2-only proposal and unstaged
checkpoint claims. It explicitly recommended stopping for next-stage architecture review.

## File changes and Git checkpoint readiness audit

Against the captured 70-file baseline: **66 unchanged, four authorized existing files changed,
zero missing**, five new files. M01 files, M02-A DTOs/tests/reports, README, .gitignore, old ADRs
and frozen baseline are preserved. The working tree remains dirty; the index is empty and HEAD
unchanged. Checkpoint is **prepared for review, not staged or committed**.

| Exact B1 path | Purpose |
|---|---|
| `src/aegiscae/research/mutation_rules.py` (new) | typed profile/request, taxonomy, editor and independent byte oracle |
| `src/aegiscae/research/mutation.py` (new) | TEMP workspace identities, exclusive staging, transactional publication and readonly recheck |
| `src/aegiscae/research/project.py` | versioned Candidate audit payload/uniqueness/parent checks; no SQL schema or frozen-byte changes |
| `tests/unit/test_model_mutation.py` (new) | 84 focused synthetic functional/fault cases |
| `tests/architecture/test_package_skeleton.py` | exact two-module allowlist |
| `tests/architecture/test_research_boundary.py` | exact mutation filesystem exceptions and controlled negatives |
| `tests/architecture/test_forbidden_direct_writes.py` | uses exact exception; rejects writable/dynamic Path.open elsewhere |
| `docs/architecture/M02_MODEL_MUTATION_GUARD.md` (new) | semantics, grammar, compatibility and crash boundaries |
| `docs/milestones/M02-B1_DELIVERY_REPORT.md` (new) | evidence, matrix, risks, checkpoint and B2 proposal |

Checkpoint checks:

- Protected local folders still ignored at .gitignore lines 32/33/34: Kickoff_Docs, CAE models,
  .codex/config.toml. `git ls-files` for these paths returned no tracked entries; no private folder
  contents were traversed. Old retained credentials/evidence were neither reused nor cleaned.
- Scoped text scan of non-ignored checkpoint files found no private-key header or high-confidence
  AWS/GitHub/OpenAI credential pattern. Values are not printed. This is a bounded heuristic review,
  not comprehensive DLP; test credentials are synthetic, and ignored local credentials remain outside
  the checkpoint. Review free-form documents manually before any separately approved commit.
- Whitelist above is relative to B1's manifest, not to HEAD. A future combined M01/M02 checkpoint
  must separately account for earlier untracked files and inherited changes, including .gitignore.
  Never use a broad add operation or infer remote synchronization from local status.
- No staging, commit, push, PR/CI dispatch, dependency installation, global configuration edit,
  AbqJobPilot modification, solver/Owner/ODB start or real-model access occurred.

## Risk register

| Risk | Disposition |
|---|---|
| Synthetic grammar only | Explicit NOT_ABAQUS_QUALIFIED; no general INP/include/CAE semantic claims |
| Contract semantics | V3 metric subset preserved; broader multi-layer coverage is separate and versioned, not a rewritten old contract |
| Historical readers | Old code rejects new event kinds; do not use old writers after Candidate events, no forward-compatibility promise |
| Journal / abandoned stage | STORE_BUSY and retained orphan files require future explicit administrative review; no auto-repair/retry/cleanup |
| Filesystem + DB consistency | Rechecked observations, not a cross-resource atomic transaction or power-loss proof; caller must revalidate before later use |
| Same-user tampering / clocks | Marker, file IDs and hashes are consistency checks, not authentication/sandbox/anti-tamper evidence |
| Capacity | Bounded 8192-byte fixture and existing 1024-audit/64-MiB store limits; no long-term throughput guarantee |
| Authorization / budget | Candidate permit never grants execution; budget values remain declarations with no reservations or active enforcement |
| Existing retained secrets | Prior M01 temporary credential risk remains; no reuse, export or deletion in B1 |
| Uncommitted milestones | Local review/checkpoint required; no automatic Git action |

## M02-B2 independent BudgetLedger proposal — NOT IMPLEMENTED

Keep a ledger owned by the same ResearchProject, bound to frozen Project/Bundle/Policy digests,
unique operation ID and a separately checked ledger revision. Its transaction design and any
store-format extension require the next scoped approval; do not overload Candidate admission
as a budget reservation or change historical frozen bytes. No real AF calls are proposed for
the first B2 implementation: accepted/unknown/start facts come only from explicit synthetic
evidence adapters, always labelled as fixtures.

| Proposed state | Meaning and budget treatment |
|---|---|
| RESERVED | Atomic capacity hold against frozen solver/candidate maxima; no Grant, submission or assumption of acceptance |
| ACCEPTANCE_UNKNOWN | Delivery/acceptance outcome unresolved; retain full hold, no retry or refund inferred from timeout/not-found |
| ACCEPTED | Correlated authoritative acceptance evidence identifies the original request; retain/charge once, never double-count duplicate observations |
| START_OBSERVED | Correlated start observation; previously charged capacity remains charged, not refunded by later failure |
| RECONCILE_REQUIRED | Conflicting/stale/unbound evidence; hold capacity and block dependent actions pending separately authorized reconciliation |
| RELEASED_ONLY_IF_PROVEN_NOT_ACCEPTED | Release exactly once only with explicit scoped proof that acceptance did not occur; no transition from known ACCEPTED/START_OBSERVED based on absence of evidence |

Proposed fields: schema/version, operation/idempotency ID, immutable request digest, Project and
contract refs, resource kind/quantity, current state/revision, evidence references and append-only
transition audit. The implementation must define whether counting starts at reservation or
acceptance and preserve one invariant: available capacity never includes unresolved exposure.
For the minimal conservative design, reservation reduces availability; accepted/start converts
the same hold into spent capacity without a second debit. Only proven non-acceptance releases it.
Wall-time and auto-Turn declarations remain NOT_ENFORCED unless separately approved.

Independent B2 test matrix: exact duplicate replay/different-content conflict; concurrent last-slot
reservation prevents overspend; two independent processes share one ledger; stale revision and
frozen-policy changes reject; before/after commit interruptions are all-or-nothing; duplicate or
out-of-order evidence cannot double-debit/release; timeout/not-found cannot refund; mismatched
request/project/receipt evidence enters RECONCILE_REQUIRED; only correctly bound negative proof
releases once; accepted/start evidence forbids refund; seven MCP tools remain readonly and no
AF/solver/runtime service is started. This is a proposal only—no ledger classes/tables/reservations,
AF submit, workflow, SDK/app-server or next-stage implementation was added.

**Stop after M02-B1 and wait for the next architecture review.**

## Pre-change manifest

```json
{
  "branch": "main",
  "HEAD": "af3cfd90821cddf65ef93827a20fc2b26d98f0fc",
  "status": " M .gitignore\n M tests/architecture/test_af_read_boundary.py\n M tests/architecture/test_dependency_direction.py\n M tests/architecture/test_forbidden_direct_writes.py\n M tests/architecture/test_forbidden_surfaces.py\n M tests/architecture/test_package_skeleton.py\n?? .agents/skills/gdcae-evidence-review/SKILL.md\n?? .codex/agents/gdcae_evidence_analyst.toml\n?? .codex/agents/gdcae_independent_reviewer.toml\n?? docs/architecture/M01-C_READ_INTERFACE.md\n?? docs/architecture/M02_RESEARCH_PROJECT_AND_CONTRACTS.md\n?? docs/milestones/M01-B_DELIVERY_REPORT.md\n?? docs/milestones/M01-C_DELIVERY_REPORT.md\n?? docs/milestones/M01-C_SOURCE_DIFF.patch\n?? docs/milestones/M02-A_DELIVERY_REPORT.md\n?? src/aegiscae/contracts/research_contracts.py\n?? src/aegiscae/interfaces/mcp_read.py\n?? src/aegiscae/research/__init__.py\n?? src/aegiscae/research/project.py\n?? tests/architecture/test_research_boundary.py\n?? tests/integration/test_af_read_live.py\n?? tests/integration/test_mcp_read_live.py\n?? tests/unit/test_mcp_cleanup.py\n?? tests/unit/test_mcp_read.py\n?? tests/unit/test_research_project.py\n",
  "files": {
    ".agents/skills/gdcae-evidence-review/SKILL.md": "076540096f1741a36a02ef90145b17b06c14939337d46400803de38c1499ac4a",
    ".codex/agents/gdcae_evidence_analyst.toml": "2027843f8cd76e528318ea6d1000157963f6abbe54e504ac04539abac00679c8",
    ".codex/agents/gdcae_independent_reviewer.toml": "09b9f681f96729a6b02578e80b387f9fe8204598034d62ff56f77a5d1a81f68f",
    ".editorconfig": "18585eca8767e0886ef3d0a2bd1d7464a165500ee7c2284e58a55611655f2a8c",
    ".gitattributes": "1a1dbe176bc233b499d35a57db7513f2941c99ab9759f177830c9149be99005b",
    ".github/workflows/ci.yml": "e230a76883b9f1dd229f7e45445b6bc26fd09812b0905299028ccd5c70062dec",
    ".gitignore": "41e243b05a6cbad08ad5252f7fb7ce35de61be34abe6c25abc91ab84d46bed24",
    "ARCHITECTURE.md": "ebc33f8fd0cbc9eb8203960df062f81c7964b2fc7f6e2695d82a8d07ed026e08",
    "LICENSE": "17de84ce8b605a18699d04d6d9371da2aacc0e2af58f2128e87f75e6d190f901",
    "MIGRATION_FROM_LEGACY.md": "3778e3db77d42d0fbe642d1cbac3c0d515e79e735875eda56c57ddb4eeb48093",
    "README.md": "ebe31922b1ac9914880dfcf4e2d99caa36aebb322300f74606d4a5171b8661ce",
    "RUNTIME_INVARIANTS.md": "b6440ea1229728e7eedd706f7e7486cec2acd4703524aa99da2db4b8555e20e4",
    "THREAT_MODEL.md": "832aef9e7da7f069fe7d6bc4238c49c1481816ff16da349bc5d0a0e3bc64ac43",
    "docs/adr/ADR-001-runtime-first.md": "23600e64d28e6fe857399cadd063ef0a35bd1928328d0de8fe9d388b4c14b71c",
    "docs/adr/ADR-002-legacy-selective-migration.md": "7776428482bbc64ff79cba8593773cd6ff6aa7dd670bf650f1fc52eb158be5a9",
    "docs/adr/ADR-003-codex-native-delegated-execution.md": "b3347ce62130638c42d108434173312869981fcb864efe47d86843b5030756eb",
    "docs/adr/ADR-004-execution-evidence-research-verification.md": "63e029b1bbdea3a1905d11259143639530f8f840e4d31403034beb90b1463e68",
    "docs/adr/README.md": "52490bf00587c54300b7a9fbace5752f22be123b0f79abf06135b9d34c65d5d6",
    "docs/architecture/CURRENT_AUTHORITY.md": "980b86142a881bb9d1a2283eaea3be38ffb7b00281764932d3300d88560f4a34",
    "docs/architecture/M01-C_READ_INTERFACE.md": "f606677e8f91132da0c4f1c67a61e27ef81d1728f20793e78a76e7628011415f",
    "docs/architecture/M01_EVIDENCE_BRIDGE.md": "88b0af9ccad3a1d993e9157fe9da895c74a4ae89eee852cb303e499aed32ef11",
    "docs/architecture/M02_RESEARCH_PROJECT_AND_CONTRACTS.md": "bb1c74ba7ffc82a18324778dd82414cfff1deabef3c547caad637b6470165e90",
    "docs/baseline/AegisCAE Runtime \u9879\u76ee\u8ba1\u5212\u4e66.md": "9a89a5ad661a80a69ec159124066e5b34ed6dc74de9295336f426b17079e7448",
    "docs/baseline/BASELINE_REGISTER.md": "9ec1426dc4abd3f8c3add8cb8f036a65a67fb70653ca2c2188dbb987afc1f6aa",
    "docs/baseline/LEGACY_ABQJOBPILOT_SUMMARY.md": "f938b243ff438c6e7587f9337be4c4730e4bddeed78a874a5bd4e0f2a1128dfb",
    "docs/baseline/LEGACY_ABQPILOT_SUMMARY.md": "d1685d26a208f15ad772335fcd927c0c22f31f0fe8901613d9a7b02ac9591a43",
    "docs/baseline/LEGACY_MIGRATION_DECISIONS.md": "d90e35737ee86a3aa77b67afa5d6becf4977a371f35517317615db351e3603c2",
    "docs/milestones/M01-A_DELIVERY_REPORT.md": "eaa87b9ed4d1ced4b7cb0acf24b7d7a76d6a0100864c073507497b853ded8a47",
    "docs/milestones/M01-B_DELIVERY_REPORT.md": "54875e0c3838443a53e0ef9ce03999a3aa9e02c782165d36d33f78ee54f1f8d1",
    "docs/milestones/M01-C_DELIVERY_REPORT.md": "1ae1d2867c930031df4ee4884748f21115b3dd47b1d1ecc95794738162b8e0e5",
    "docs/milestones/M01-C_SOURCE_DIFF.patch": "52232088439a097ed814dfcd9005cc7d2e7d3af5e716bfe7e71ea7aebc764859",
    "docs/milestones/M02-A_DELIVERY_REPORT.md": "76708c488046d4cb67071c1b5ba66c0626a3e9c9ecf05e7944d019cc63ef8cfa",
    "docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md": "9bf3a2b11d2b13f9f7e9d1b6b5947aa18b4701a23b935bacd262facc348d0771",
    "pyproject.toml": "9fc0d3c6c8939cbfb72dc9b88673e3c100e79782da317cce57a81912eecd1c8a",
    "src/aegiscae/__init__.py": "03cad15b185a6b873f497355a7f349e3c2771b7a13a84e913c05187d7333e910",
    "src/aegiscae/adapters/__init__.py": "802176739638c040953157b3632ea16c4c06505a3a95a68538d3469350996551",
    "src/aegiscae/adapters/abaqus/__init__.py": "5ecb6d3606d6312a2897a304a0cbace18d8858343d7bebc679d66ac83740af90",
    "src/aegiscae/adapters/abaqus/af_evidence.py": "8b7a1cdd57dd0d4a067bc32037ac8893aa1662348f9d94baec01b34e670a88b0",
    "src/aegiscae/contracts/__init__.py": "9f3e24fec4f6884cf63b3b585e5f041a43fbfac800ef40f87bb1d320c79e4b92",
    "src/aegiscae/contracts/af_evidence.py": "401ecb551591376f854247b7e64cc4d13f82cd54c17c098bdba2b26943d5f012",
    "src/aegiscae/contracts/research_contracts.py": "8f8fb5017fa9b9f0bfcdd827dab6915da8af93d488b81500bd6a440167fcff16",
    "src/aegiscae/interfaces/__init__.py": "4bf573cf307c6f457faaff35a385e4e9da78fd9d111964a1d2cfac92ee072586",
    "src/aegiscae/interfaces/mcp_read.py": "10d69706b58b1fdec77b21cd8df56a558111c4469ee3b75b143f84480274085d",
    "src/aegiscae/research/__init__.py": "865f21faca277a7de68665865ba9ea2cffa6537464594cd526ac148b5b6654f6",
    "src/aegiscae/research/project.py": "8c5dcc4b0c953f14168796abdd01a61ab5eb33bcedb6cb488085a4c8c0b8b6ba",
    "src/aegiscae/runtime/__init__.py": "2c15584b91a9468f50e5fa9fbbc1d11532d20140cab576a44219ba22a82b96d8",
    "src/aegiscae/validation/__init__.py": "e518637e4813de20fadc7d268e288ec739625692ef156a86324a275ac754e042",
    "tests/architecture/test_af_read_boundary.py": "5ea98c4295df7a1ea97280fe57e6a822cf0a97d14745c41d69140c55f435f1fe",
    "tests/architecture/test_baseline_integrity.py": "a564da95cc8ab8531aec0e8f1efb477ac94285efbd6ea37f2893bd3e12ea172d",
    "tests/architecture/test_dependency_direction.py": "3e0f850934735fa17a1cd412b97ecd25ffec6cb9124b2380005ffbe5a4316377",
    "tests/architecture/test_fixture_evidence_policy.py": "98d7247eaeff18a8b383d53fb582bcb4db91b23b15b096a5f0c8c4db06b9c498",
    "tests/architecture/test_forbidden_direct_writes.py": "39beb36f55d37c800fd0bf977780d30a7ffbbbe4feba9121cb7529af98835093",
    "tests/architecture/test_forbidden_execution_calls.py": "ec6b8fec7fac7cfc5b6d4a546fa9784d1021ff004f8f7d16011ab49fcf5f1af3",
    "tests/architecture/test_forbidden_legacy_dependencies.py": "fdfb6a2501c5419bab5dbf0e0b95dfeb6454b26b5b2db08790777daeae70fe3e",
    "tests/architecture/test_forbidden_paths_and_cwd.py": "e2b68493c83a1f2d320afbc77c02c98de7b37329888d4f79aa5d9ef45ef0dfe3",
    "tests/architecture/test_forbidden_surfaces.py": "d4e77b8f04027d033118332852f75f0cb8a0c6bafb66815c5556c77a5e90d6bb",
    "tests/architecture/test_no_symlinks.py": "d3d6199a82eb319ba0c374aed61dc1a0f464b3fed4fd78b39396ea5eb233e659",
    "tests/architecture/test_package_skeleton.py": "9a0163fdf3572445a4ff523ca161d69aab076ce5237e95ab27cf101f92c52b38",
    "tests/architecture/test_research_boundary.py": "1e01f5be82ed871228e7afc746bcfa0905c4acd19c3da14ad3dc33818559244e",
    "tests/architecture/test_verdict_authority.py": "bd2ec5582bb21caf3ebd601bbb39f4b7e218225ca9901fd043752e5517e6d322",
    "tests/conftest.py": "6635df5d72f131657d6e472e72d6ffc91e294c1ed0e9801ce308e9056b66f14d",
    "tests/fixtures/README.md": "97e2adca2c7f6aed8e37adacbf30339a3ffaa1245e982f10781c190f3327b425",
    "tests/integration/README.md": "49de8f43d078c336d4e8e279aa15ba5cc4b78e9d5acf71696103506bb1a939d3",
    "tests/integration/test_af_read_live.py": "3ccf5d5242688a954599a3e2e5623758579ef34bb44f3da8c95800cfd448852f",
    "tests/integration/test_mcp_read_live.py": "ff2c29176cc4571771b710fb4c694fdf34f85f3909aedfef6798f11505c13aaf",
    "tests/unit/test_af_evidence.py": "d7be2b0fae158ab3b5e604c65d4ea99548cc859d70add18644b222615829dd68",
    "tests/unit/test_mcp_cleanup.py": "5bedef4ce2ce757ae3fff29e6513e6b8f2b831d38e588845d041a2ab7a8513da",
    "tests/unit/test_mcp_read.py": "4fadf2d2e7f5c8e0860c9a7d57fa9bc9a2ca6727800a0b648963512677b07c53",
    "tests/unit/test_package_import.py": "bed78fa82cdc7ea1bb2110296da0e8519eba8bcc98680ba4deebbfdb71003241",
    "tests/unit/test_research_project.py": "49fd300f00c6432a767e57060b09c4dc1a1ba6c0c2d6076e8fd82f9c636d52e9"
  }
}
```
