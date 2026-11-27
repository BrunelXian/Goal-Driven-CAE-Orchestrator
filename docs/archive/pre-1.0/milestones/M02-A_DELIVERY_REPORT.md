# M02-A — Delivery report

Status: **PASS — M02-A scoped acceptance completed, 2026-10-28.**

PASS covers persistent declarations, transactional storage and the synthetic tests below. It does not establish scientific correctness, human approval, execution authority, automatic crash recovery or live AF integration. Stop for architecture review; M02-B has not been implemented.

## Outcome and implementation

The interrupted implementation was preserved and extended. The prior interruption was recorded as `Selected model is at capacity`, not a source failure. The recovery syntax check covered 893 existing source lines. This continuation fixed the two identified gaps, added 65 functional cases and completed documentation. Existing four architecture migrations remain in place; the new exact SQL allowlist was updated for the metadata columns, without granting M01 writable access.

ResearchProject now has a separate explicit root, UUID identities, storage generation, revision and four SQLite tables. Goal/Model/Verification form one versioned canonical Bundle, with three part digests and a Bundle digest. `BEGIN IMMEDIATE`, revision checks, immutable logical part versions and exact-key idempotency protect atomic changes. DTOs are strict standard-library dataclasses; units and canonical Decimal strings are validated before storage. See [implemented architecture and example](../architecture/M02_RESEARCH_PROJECT_AND_CONTRACTS.md).

### Issue A — freeze/audit metadata

Root cause: the Bundle row and audit writer generated independent UTC values, and reread did not validate all freeze timestamps or correlate audit provenance, revision and transaction identity.

Fix: a single UTC and `tx_` ID per creation/freeze; Project creation/latest-revision stamps; Bundle metadata digest binding Project ID, content digest, revision, idempotency key, UTC and transaction; exact schema/type/calendar checks; cross-table matching and audit revision/provenance/sequence checks. Tests corrupt freeze columns, rehash malformed audit events, remove metadata and inject contradictory revision/date/schema values. All reject without readonly mutation.

UTC is host wall-clock and may regress. Order derives from revision/sequence, not clock monotonicity. Digests detect consistency failures, not coordinated rewriting by a database owner. No cryptographic signature or trusted-time claim is made.

### Issue B — hard constraint coverage

Root cause: VerificationContract required evidence for the objective, but did not require every hard constraint to have a corresponding check.

Fix: mandatory `hard_constraint_checks`; each ID maps exactly once to a V3 check with the entire matching ScientificConstraint rule, and its evidence must be explicitly required. Missing, duplicate, unknown, wrong-level, changed-rule and omitted-evidence cases reject. Incomplete drafts cannot freeze; `COMPLETE_DECLARED` denotes coverage only. No constraint evaluation, Solver result or physical verdict was synthesized.

## R-01–R-17 acceptance matrix

Unless indicated otherwise, test references are in `tests/unit/test_research_project.py`. All mutable data is synthetic and isolated outside the repository.

| ID | Result | Actual evidence |
|---|---|---|
| R-01 | PASS | `test_r01_r03_independent_process_reopen_is_readonly`: fresh `sys.executable -B` child reconstructs same Project and frozen digest; DB bytes/mtime unchanged |
| R-02 | PASS | existing root, relative path, traversal, missing root, absent explicit argument, readonly write rejected; actual Windows test junction rejected; creation failure root quarantined |
| R-03 | PASS | complete Bundle reread; three parts stored atomically; canonical key-order independence and matching Project ID |
| R-04 | PASS | same-key replay preserves bytes/mtime and returns original digest; changed content is `IDEMPOTENCY_CONFLICT`, no duplicate freeze |
| R-05 | PASS, bounded schedule | two independent SQLite connections concurrently pass preflight: one commit and one `REVISION_CONFLICT`; separate active-journal case returns `STORE_BUSY`, then explicit retry after commit returns revision conflict |
| R-06 | PASS, recovery limitation | exception and `os._exit(73)` at before_begin/after_bundle/after_parts/before_commit/after_commit; old or new complete state; journal-bearing crash state quarantined, not silently repaired |
| R-07 | PASS | changed target or tolerance/verification requires new relevant part versions; original frozen bytes remain identical; new versions remain pending approval |
| R-08 | PASS | float/NaN/Infinity/noncanonical decimals/wrong dimensions or units/negative tolerance rejected; 39 decimal places retained exactly |
| R-09 | PASS | Project/entity/step/frame/schema/bool-revision/invalid-date/missing-metadata negatives; copied root identity fails with no mutation |
| R-10 | PASS | explicit synthetic `.txt` bytes match only as declared; changed bytes→STALE; missing file/dependency→INCOMPLETE |
| R-11 | PASS | readonly handle cannot freeze; frozen read and summary still no execution/human authority, even with an instruction-like approval label |
| R-12 | PASS | V4 explicitly required with absent reference remains NOT_ASSESSED; no Goal or physical PASS |
| R-13 | PASS | fresh-process audit hook rejects process/network/AF imports during module import/create/readonly open; architecture import guards pass |
| R-14 | PASS | unsafe metadata strings rejected without echo; benign-format prompt injection retained only as untrusted declaration and excluded from summary; binding rejects credential fields |
| R-15 | PASS, offline regression | existing MCP SDK enumeration test still exactly seven readonly tools; unchanged adapter/MCP/Skill/agent contents; M01 unit and guard regressions pass, no new live AF run |
| R-16 | PASS | full pytest 318 passed/2 existing live opt-in skips; whole-repository Ruff PASS; tracked and new-file diff whitespace checks PASS |
| R-17 | PASS | original 63-file manifest: 59 byte-identical, four authorized guard migrations, zero missing; no staged changes, unchanged HEAD; ignored private areas retained |

## Actual execution evidence

Verified interpreter `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`, Python 3.12.10, SQLite 3.49.1, pytest 9.1.0, mcp 2.3.0, pydantic 2.13.4. No installation or environment modification. Commands used `PYTHONDONTWRITEBYTECODE=1`, explicit repository `PYTHONPATH`, `-p no:cacheprovider` and unique `%TEMP%\gdcae-m02a-...-<UUID>` basetemp roots. Live opt-in variables were unset only in the test child shell.

```text
G0 inherited baseline:                  231 passed, 2 skipped in 4.32s
Updated architecture suite:            120 passed in 2.37s
Focused functional suite (test author): 65 passed in 4.42s
Final full pytest:                     318 passed, 2 skipped in 9.70s
Ruff check .:                          All checks passed!
git diff --check:                      exit 0; no whitespace errors
```

The final full command was the absolute interpreter with `-m pytest -q -p no:cacheprovider --basetemp <fresh external TEMP root>`. Ruff was `D:\ProgramData\anaconda3\Scripts\ruff.exe check .`. Git emitted existing LF→CRLF advisory warnings; no newline conversion was performed. New untracked delivery files were separately included in diff whitespace checks because plain `git diff --check` excludes them.

Exact inherited skip reasons:

- `tests/integration/test_af_read_live.py:403`: `Explicit M01-B approval, fresh TEMP root and isolated invocation required`.
- `tests/integration/test_mcp_read_live.py:228`: `M01-C fresh TEST root and explicit live opt-in required`.

These are live TEST Owner lifecycle integrations, not skipped mandatory offline safety cases. M02-A does not authorize those starts; this report neither replaces nor recertifies M01 live compatibility evidence.

Crash evidence distinguishes durability from availability: intermediate hard exits leave a journal and product readonly open returns STORE_BUSY with unchanged bytes/mtime. A separate trusted synthetic fixture SQLite inspection checks `integrity_check=ok`, 0 bundles, 0 parts, 1 audit and revision 1. Test inspection may invoke SQLite's own recovery; it is not a product API and any remaining journal is preserved. Before-BEGIN crashes reopen the old state; after-COMMIT crashes reopen the new state and exact-key replay acknowledges it. Five ordinary exceptions roll back or preserve the committed state accordingly. No crash stage yields a mixed triple.

## Exact M02-A file scope and preservation

New files over the pre-M02 baseline (some already present at the interruption):

| Path | Purpose |
|---|---|
| `src/aegiscae/contracts/research_contracts.py` | strict DTOs, canonical digests, units and hard-constraint coverage |
| `src/aegiscae/research/project.py` | independent SQLite Project, atomic freeze, readonly checks and synthetic identity |
| `src/aegiscae/research/__init__.py` | package marker, preserved during continuation |
| `tests/architecture/test_research_boundary.py` | exact store/SQL write allowances with controlled negatives |
| `tests/unit/test_research_project.py` | 65 synthetic acceptance cases |
| `docs/architecture/M02_RESEARCH_PROJECT_AND_CONTRACTS.md` | schema, example and limitations |
| `docs/milestones/M02-A_DELIVERY_REPORT.md` | results, matrix, risks and preserved pre-change manifest |

Four pre-existing architecture files migrated in the interrupted portion and preserved: `test_af_read_boundary.py` (exact SQLite execute exception), `test_dependency_direction.py` (research→contracts only), `test_forbidden_direct_writes.py` (exact exclusive Project creation exception), `test_package_skeleton.py` (new modules). This continuation only updates the new guard's SQL literals for added metadata columns. M01 interfaces/adapters/contracts cannot import the writable store; sibling files, dynamic SQL, wrong receivers, readonly entrypoints and process/private AF calls remain forbidden.

Branch `main`; HEAD `af3cfd90821cddf65ef93827a20fc2b26d98f0fc`; index empty. The final dirty worktree includes pre-existing M01 untracked files and tracked `.gitignore`/guard edits, so a Git-vs-HEAD diff must not be presented as this milestone alone. `test_forbidden_surfaces.py` is inherited M01 work, unchanged against the M02 manifest. README, `.gitignore`, M01 source/Skill/agent files, historical ADRs and frozen baseline all match the captured pre-M02 bytes. No repository files removed.

Ignore verification: `.gitignore` lines 32/33/34 still match `/Kickoff_Docs/`, `/CAE models/`, `/.codex/config.toml`. Only explicitly supplied instruction documents were read under Kickoff_Docs. No model inventory/read/hash occurred; no AbqJobPilot changes or runtime starts, commits, pushes or CI triggers occurred.

## Independent review and risks

Native independent reviewer `/root/m02_review` performed readonly source review and independently ran the then-current 56-case snapshot: **56 passed in 4.54s**, no skips. This is supplemental, not the final 65-case/full-suite count. Reviewer found no blocking contract-validation or authority-boundary defect after A/B fixes, subject to final full regression and documentation. Its four observations are preserved below; the active-journal regression was added in response.

Final readonly review of both completed documents and the expanded tests also returned **no blockers**, explicitly supporting scoped M02-A PASS. The reviewer confirmed that R-05 scheduling limits, R-06 crash quarantine and its own earlier test snapshot are represented accurately. It did not claim to rerun the final full suite and made no repository edits.

| Risk | Boundary / disposition |
|---|---|
| Journal blocks availability | A busy writer may produce STORE_BUSY before revision checking. Crash journals require separately reviewed recovery; no automatic repair here. Tests distinguish both schedules. |
| Clock and digest trust | Host UTC may regress; revision/sequence order events. Hashes are consistency checks, not anti-tamper security or authentication. |
| Native OS error presentation | Some path-preflight permission/IO exceptions are not normalized; callers must not expose raw path-bearing errors. No authority bypass identified. |
| File identity / TOCTOU | Copy/move/reparse detected in tested cases; not hostile same-user/admin isolation, migration or backup-restore support. |
| Declared semantics and limits | No INP/CAE closure parser, real artifacts, evaluator or physics validation. Finite units/metrics, bounded local store, no long-running scalability claim. |
| Metadata privacy | Whitelist summaries exclude prose and private paths; simple text filters are not comprehensive secret detection. Full DTO is untrusted. |
| Old temporary credentials | M01-B/C retained evidence/credentials not reused, copied, inspected or deleted; their earlier retention risk remains unresolved. New fixtures are synthetic and contain no live credentials. |
| Uncommitted work | All deliverables remain local and uncommitted. Preserve the pre-M02 manifest for review and plan a dedicated checkpoint only after user approval. |

## M02-B minimum proposal — no implementation

Propose two narrowly scoped modules after architecture approval: (1) Model Mutation Guard evaluates a declarative synthetic change proposal against frozen allowed/forbidden categories and source digests; (2) BudgetLedger records transactional reservation/consume/release against frozen solver/candidate maxima with unique operation IDs and revision conflicts. Neither module should invoke AF, mutate a real model, mint human approval or reserve an actual Solver license.

Minimum independent acceptance: allowed synthetic change vs forbidden geometry/load edits; changed baseline/missing dependency→STALE/INCOMPLETE; exact-key replay vs divergent conflict; concurrent reservations cannot overspend; interruption yields all-or-nothing ledger; release/consume cannot double count; NOT_ENFORCED auto-Turn stays inactive; MCP remains exactly seven readonly tools; missing approval or physics evidence never upgrades execution rights. First specify reservation lifecycle and failure/reconciliation semantics in a reviewable contract, then implement only after approval. Keep crash-recovery design as an explicit follow-up decision rather than silently enabling SQLite repair.

Recommend a dedicated M01/M02 Git checkpoint after review of the existing dirty worktree, ignored assets and test evidence. No commit/push is performed or authorized by this report. **Stop here; wait for next-stage architecture review.**

## Pre-change scoped content-hash manifest

Captured before M02-A implementation. Excludes ignored local assets and runtime credentials.

```json
{
  "branch": "main",
  "HEAD": "af3cfd90821cddf65ef93827a20fc2b26d98f0fc",
  "status": " M .gitignore\n M tests/architecture/test_dependency_direction.py\n M tests/architecture/test_forbidden_surfaces.py\n M tests/architecture/test_package_skeleton.py\n?? .agents/skills/gdcae-evidence-review/SKILL.md\n?? .codex/agents/gdcae_evidence_analyst.toml\n?? .codex/agents/gdcae_independent_reviewer.toml\n?? docs/architecture/M01-C_READ_INTERFACE.md\n?? docs/milestones/M01-B_DELIVERY_REPORT.md\n?? docs/milestones/M01-C_DELIVERY_REPORT.md\n?? docs/milestones/M01-C_SOURCE_DIFF.patch\n?? src/aegiscae/interfaces/mcp_read.py\n?? tests/integration/test_af_read_live.py\n?? tests/integration/test_mcp_read_live.py\n?? tests/unit/test_mcp_cleanup.py\n?? tests/unit/test_mcp_read.py\n",
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
    "docs/baseline/AegisCAE Runtime \u9879\u76ee\u8ba1\u5212\u4e66.md": "9a89a5ad661a80a69ec159124066e5b34ed6dc74de9295336f426b17079e7448",
    "docs/baseline/BASELINE_REGISTER.md": "9ec1426dc4abd3f8c3add8cb8f036a65a67fb70653ca2c2188dbb987afc1f6aa",
    "docs/baseline/LEGACY_ABQJOBPILOT_SUMMARY.md": "f938b243ff438c6e7587f9337be4c4730e4bddeed78a874a5bd4e0f2a1128dfb",
    "docs/baseline/LEGACY_ABQPILOT_SUMMARY.md": "d1685d26a208f15ad772335fcd927c0c22f31f0fe8901613d9a7b02ac9591a43",
    "docs/baseline/LEGACY_MIGRATION_DECISIONS.md": "d90e35737ee86a3aa77b67afa5d6becf4977a371f35517317615db351e3603c2",
    "docs/milestones/M01-A_DELIVERY_REPORT.md": "eaa87b9ed4d1ced4b7cb0acf24b7d7a76d6a0100864c073507497b853ded8a47",
    "docs/milestones/M01-B_DELIVERY_REPORT.md": "54875e0c3838443a53e0ef9ce03999a3aa9e02c782165d36d33f78ee54f1f8d1",
    "docs/milestones/M01-C_DELIVERY_REPORT.md": "1ae1d2867c930031df4ee4884748f21115b3dd47b1d1ecc95794738162b8e0e5",
    "docs/milestones/M01-C_SOURCE_DIFF.patch": "52232088439a097ed814dfcd9005cc7d2e7d3af5e716bfe7e71ea7aebc764859",
    "docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md": "9bf3a2b11d2b13f9f7e9d1b6b5947aa18b4701a23b935bacd262facc348d0771",
    "pyproject.toml": "9fc0d3c6c8939cbfb72dc9b88673e3c100e79782da317cce57a81912eecd1c8a",
    "src/aegiscae/__init__.py": "03cad15b185a6b873f497355a7f349e3c2771b7a13a84e913c05187d7333e910",
    "src/aegiscae/adapters/__init__.py": "802176739638c040953157b3632ea16c4c06505a3a95a68538d3469350996551",
    "src/aegiscae/adapters/abaqus/__init__.py": "5ecb6d3606d6312a2897a304a0cbace18d8858343d7bebc679d66ac83740af90",
    "src/aegiscae/adapters/abaqus/af_evidence.py": "8b7a1cdd57dd0d4a067bc32037ac8893aa1662348f9d94baec01b34e670a88b0",
    "src/aegiscae/contracts/__init__.py": "9f3e24fec4f6884cf63b3b585e5f041a43fbfac800ef40f87bb1d320c79e4b92",
    "src/aegiscae/contracts/af_evidence.py": "401ecb551591376f854247b7e64cc4d13f82cd54c17c098bdba2b26943d5f012",
    "src/aegiscae/interfaces/__init__.py": "4bf573cf307c6f457faaff35a385e4e9da78fd9d111964a1d2cfac92ee072586",
    "src/aegiscae/interfaces/mcp_read.py": "10d69706b58b1fdec77b21cd8df56a558111c4469ee3b75b143f84480274085d",
    "src/aegiscae/runtime/__init__.py": "2c15584b91a9468f50e5fa9fbbc1d11532d20140cab576a44219ba22a82b96d8",
    "src/aegiscae/validation/__init__.py": "e518637e4813de20fadc7d268e288ec739625692ef156a86324a275ac754e042",
    "tests/architecture/test_af_read_boundary.py": "7c821072b521bdb5654ff67d3faea62a10d464c630a32acec515a93106ec7933",
    "tests/architecture/test_baseline_integrity.py": "a564da95cc8ab8531aec0e8f1efb477ac94285efbd6ea37f2893bd3e12ea172d",
    "tests/architecture/test_dependency_direction.py": "ee8b57c47387da8850915d723a313f23cbf6e0c37c4428b4dfd6929c028dc007",
    "tests/architecture/test_fixture_evidence_policy.py": "98d7247eaeff18a8b383d53fb582bcb4db91b23b15b096a5f0c8c4db06b9c498",
    "tests/architecture/test_forbidden_direct_writes.py": "a1ec9c10924bc23ea476584145de6e85c8ea931380eb068711945ef75035e8e8",
    "tests/architecture/test_forbidden_execution_calls.py": "ec6b8fec7fac7cfc5b6d4a546fa9784d1021ff004f8f7d16011ab49fcf5f1af3",
    "tests/architecture/test_forbidden_legacy_dependencies.py": "fdfb6a2501c5419bab5dbf0e0b95dfeb6454b26b5b2db08790777daeae70fe3e",
    "tests/architecture/test_forbidden_paths_and_cwd.py": "e2b68493c83a1f2d320afbc77c02c98de7b37329888d4f79aa5d9ef45ef0dfe3",
    "tests/architecture/test_forbidden_surfaces.py": "d4e77b8f04027d033118332852f75f0cb8a0c6bafb66815c5556c77a5e90d6bb",
    "tests/architecture/test_no_symlinks.py": "d3d6199a82eb319ba0c374aed61dc1a0f464b3fed4fd78b39396ea5eb233e659",
    "tests/architecture/test_package_skeleton.py": "f273aa094a9058fb3f8214da14ba665ab932a9acf95eb02a2f7f97befcfc7835",
    "tests/architecture/test_verdict_authority.py": "bd2ec5582bb21caf3ebd601bbb39f4b7e218225ca9901fd043752e5517e6d322",
    "tests/conftest.py": "6635df5d72f131657d6e472e72d6ffc91e294c1ed0e9801ce308e9056b66f14d",
    "tests/fixtures/README.md": "97e2adca2c7f6aed8e37adacbf30339a3ffaa1245e982f10781c190f3327b425",
    "tests/integration/README.md": "49de8f43d078c336d4e8e279aa15ba5cc4b78e9d5acf71696103506bb1a939d3",
    "tests/integration/test_af_read_live.py": "3ccf5d5242688a954599a3e2e5623758579ef34bb44f3da8c95800cfd448852f",
    "tests/integration/test_mcp_read_live.py": "ff2c29176cc4571771b710fb4c694fdf34f85f3909aedfef6798f11505c13aaf",
    "tests/unit/test_af_evidence.py": "d7be2b0fae158ab3b5e604c65d4ea99548cc859d70add18644b222615829dd68",
    "tests/unit/test_mcp_cleanup.py": "5bedef4ce2ce757ae3fff29e6513e6b8f2b831d38e588845d041a2ab7a8513da",
    "tests/unit/test_mcp_read.py": "4fadf2d2e7f5c8e0860c9a7d57fa9bc9a2ca6727800a0b648963512677b07c53",
    "tests/unit/test_package_import.py": "bed78fa82cdc7ea1bb2110296da0e8519eba8bcc98680ba4deebbfdb71003241"
  }
}
```
