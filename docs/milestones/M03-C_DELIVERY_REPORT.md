# M03-C — Codex-Native Evidence-Driven Candidate Proposal

Date: 2026-10-28. **PASS within the separately qualified results below.**
No real Solver/AF execution or automatic original Main continuation is claimed.

| Dimension | Observed result |
|---|---|
| Actual Codex Main proposal | Two exact JSON captures from the current operator-started native Main turn |
| Deterministic admission | Both captured byte streams ADMITTED_SYNTHETIC_ONLY, revision 10→11 |
| Evidence-conditioned change | Separate frozen targets produced distinct proposals: 10 N and 25 N |
| Synthetic continuation | Both completed SYNTHETIC_TARGET_MET in a new Python process, revision 18 |
| CODEX_PROPOSAL_GATED_PASS | true, actual Main captures plus deterministic admission |
| AGENT_CONDITIONAL_DECISION_OBSERVED | true, independently frozen target change |
| SYNTHETIC_CONTINUATION_PASS | true, two separately observed synthetic continuations |
| AF_DYNAMIC_CANDIDATE_EXECUTION_VERIFIED | false; both new candidates NOT_AF_EXECUTED |
| SCIENTIFIC_VERIFICATION_AVAILABLE | false; V2 NOT_RUN, V4 NOT_ASSESSED, real Goal INCONCLUSIVE |
| AUTO_CONTINUE_ORIGINAL_DESKTOP_MAIN | NOT_TESTED; no SDK/app-server turn initiation |

Design and compatibility: [M03 native proposal architecture](../architecture/M03_CODEX_CANDIDATE_PROPOSAL.md).

## Scope, preflight and actual changes

`main@6c549dc98c25a12dcb9c93baa4fbf8d629c80ec1` remains the local M02-G checkpoint.
The starting index was empty; all M01–M03-B tracked/untracked work and the M01-C review
patch were preserved. No Git fetch, commit, push, PR, merge or CI action occurred.
Read the complete M03-C taskbook, applicable global Python policy/registry, existing
reports, source/architecture guards, frozen contract/mutation/budget mechanisms,
M01 role/Skill and read-only Bridge. The AF-specific Skill/role was not repurposed
into a synthetic physical validator. No AF Owner was required or launched.

Existing interpreter verified before use:
`D:\XianLab\envs\LangChainEnv\Scripts\python.exe` — Python 3.12.10, pytest 9.1.0,
SQLite 3.49.1. Existing Ruff `D:\ProgramData\anaconda3\Scripts\ruff.exe` — 0.12.0.
No dependency installation, interpreter creation or environment modification.

Entry manifest: 92 nonignored files. 88 remain byte-identical. Four existing files
have scoped additive changes:

- `src/aegiscae/research/workflow.py`: read-only Brief, explicit proposal ingress and waiting/admission glue.
- `src/aegiscae/research/workflow_rules.py`: separate definition discriminator, ADMIT_B replay and admitted-template selection.
- `tests/fixtures/synthetic_workflow_port.py`: extract the existing fixed metric expression into an overridable TEST helper method; original values/behavior remain.
- `tests/architecture/test_package_skeleton.py`: allow exactly the two new research modules.

Six new files:

- `src/aegiscae/research/candidate_proposal.py` — strict untrusted DTO.
- `src/aegiscae/research/proposal_rules.py` — new A-only definition, bounded projection and pure admission rules.
- `tests/integration/m03c_support.py` — trusted synthetic challenge/capture-ingress helper, no model invocation.
- `tests/unit/test_candidate_proposal.py` — 23 deterministic safety, race and restart cases.
- `docs/architecture/M03_CODEX_CANDIDATE_PROPOSAL.md`.
- `docs/milestones/M03-C_DELIVERY_REPORT.md`.

ResearchProject SQL/schema, frozen contract DTOs, old ADRs/baseline, M01/MCP source,
README/.gitignore, local Codex config and M03-B helpers/reports are unchanged from
entry. Kickoff_Docs was only read for authorized instructions and remains ignored.
CAE models and historic credential/test data were not accessed. AbqJobPilot source
was not modified or used for execution in this milestone.

New `proposal-workflow-v1` records do not rewrite old fixed `synthetic-workflow-v1`
definitions. Existing readers can still read their old data; older binaries may
reject new variant/action records. This is not a claim of bidirectional compatibility.
The original four SQLite tables and frozen bundle bytes require no migration.

## Actual native Main experiment

The user explicitly started this Main turn. No runner starts a model, Codex CLI,
SDK/app-server request, new desktop turn, or retry loop. Native `/root` read the two
fresh Briefs in the tool response, explained the candidate reasoning, and authored
literal JSON in an `apply_patch` call. That literal output, including whitespace,
was saved as `main-proposal.json`. The trusted ingress consumed exactly those bytes.

The current native thread identity was observed as
`[REDACTED: private development-Main Codex thread ID; original evidence retained locally]`. Safe provenance records include role `/root`,
capture UTC, original digest, brief digest and the literal-tool-input capture mechanism.
The conversation's Main/tool events provide the observation of Main authorship;
local hashes only prove content consistency. This is an **implementation-aware
same-turn demonstration**, not a blind model evaluation or independent fresh-session
benchmark. Two scenarios demonstrate a conditional decision, not general reliability.

Owned evidence root, home redacted:
`%TEMP%\gdcae-m03c-native-89edc0761e524467bdd254ce68dbb95c`.
Each challenge contains `brief.json`, `main-proposal.json`, `capture-provenance.json`,
`before-ingress.json`, `admission-result.json`, `continuation-result.json`, its own
ResearchProject, synthetic workspace and separate synthetic fixture database.
No credential or real model is present.

| Field | Challenge one | Challenge two |
|---|---|---|
| ResearchProject | `rp_9bafef9c8beb4eeeac5a558a689720bb` | `rp_958bb0c4f9594e3c8b4df53eaa67b4a5` |
| Workflow | `workflow_9c30b3c986224425b19d2e65c9ae30c4` | `workflow_90b30947344f47f6ab674085703bf21b` |
| Challenge | `challenge_2ea65682955f4908baa1abe02a53546b` | `challenge_a4c881bdf5ca48129c07aaedbcc7588b` |
| Frozen target | 0.5 mm, tolerance 0.01 mm | 1.25 mm, tolerance 0.01 mm |
| A TEST_ORACLE feedback | 40 N → 2 mm | 40 N → 2 mm |
| Main-proposed B | 10 N | 25 N |
| Published B | `candidate_bc4044097f1a353a2f0bb5bed1c8ef8f` | `candidate_3ab4c41fd34d58b588c9c600d3d4a98c` |
| Independent synthetic continuation | 0.5 mm | 1.25 mm |
| Effects / charged / held / available | 2 / 2 / 0 / 0 | 2 / 2 / 0 / 0 |

Frozen Goal digests, respectively:
`sha256:85414d3e94f93517c60e149ebc22b2a18af1706e2f856ba8c897f5965cc34f3c`
and `sha256:1133bb2f74f1bcdbe95ab3063873bb707268d12949de1e6ab8ae6e13a15854a0`.
Brief digests:
`sha256:1afb0ab60697763060f330e302e2acd0afe4b72a37592918b98df58482bf70d7`
and `sha256:c2bb5b92b2cff0bc2a58998c2b719da7fc32f0dbf2d90e86e171f1d3eb468088`.
Original proposal-byte digests:
`sha256:91841452b35b97b2ba21e2e889104be6d37414471b00cffde1509e504d8d8b99`
and `sha256:1308375457ac6788a1a28d06e82d33ef113fd071528c4b6cf2cf9443f3f4ebed`.
The complete Model/Verification/Bundle/source/evidence references are in each Brief
and exact proposal capture; they were cross-checked independently by Reviewer.

Main reasoning: under the explicitly declared synthetic proportionality assumption,
scale 40 N by the ratio of the respective frozen target to A's 2 mm response.
The changed independent target therefore leads to a different proposed scalar.
Main did not receive a B answer or post-proposal oracle outcome in either Brief.
Both values use Beam.Tip / Load / load_magnitude, range 0–100 N. Frozen baseline
was prepared as 0 N before either workflow existed; A is 40 N. The baseline choice
avoids mistaking a valid target-derived proposal for an unchanged baseline.

Before ingress, each Project was revision 10, admission null, exactly one Candidate
directory, one effect, charged=1, available=1, held=0. After ADMIT_B at revision 11,
B files/effects/reservations were still absent. Only a later explicit trusted runner
continued in a new Python process. It reconstructed the sealed proposal and history,
published B with Mutation Guard, reserved/charged through BudgetLedger and used the
existing durable synthetic effect engine. Exact proposal replay and terminal advance
left the effect count at two. Original baseline digest still matched the frozen model.

The continuation policy computes from the actual guarded B scalar/digest using its
predeclared TEST_ORACLE rule; it does not return a predetermined successful B result.
An offline unit proposal of 12 N is admitted safely but yields 0.6 mm and correctly
ends SYNTHETIC_TARGET_UNMET. Admission is not an assertion of target success.

## CP-01–CP-18 acceptance evidence

| ID | Evidence |
|---|---|
| CP-01 | test_cp01_bounded_readonly_brief_no_b_no_paths; actual briefs, exact digests/revision/budget and file recheck |
| CP-02 | Current native Main commentary/tool-authored literal JSON, byte capture provenance, independent Reviewer cross-check |
| CP-03 | Two separately frozen Projects, targets 0.5/1.25, Main proposals 10/25; no predefined B in new definition or Brief |
| CP-04 | Strict JSON/Decimal/unit/field matrix; malformed/duplicate fields; malicious source narrative omitted from Brief |
| CP-05 | Grant/PASS/budget/criterion self-claims rejected; STOP/REQUEST_REVIEW persist a no-effect human-review stop |
| CP-06 | Transaction reload and reducer recomputation; stale Project/revision/digest and actual candidate/baseline/budget damage rejected |
| CP-07 | Existing parser/editor/independent diff used before admission and at publication; native baseline hashes unchanged |
| CP-08 | Before-ingress snapshots and post-admission assertions: one A directory/effect/reservation, no B |
| CP-09 | Exact original-byte replay, content/whitespace conflict, stable B operation/key and terminal effect count unchanged |
| CP-10 | Two independent Python processes compete with different safe proposals; one admission, loser rejects, no B effect |
| CP-11 | A UNKNOWN/missing evidence, rehashed contradictory A, frozen contract update, source/ref/oracle drift, budget and journal stops |
| CP-12 | Out-of-range, material, BC, wrong entity/unit/step, path/shell strings and criterion relaxation rejected |
| CP-13 | Injected capacity/refusal/incomplete output, unavailable invocation, missing/oversized capture all leave state untouched |
| CP-14 | Explicit TEST_ORACLE/proportionality limits, NOT_AF_EXECUTED and V2/V4/real Goal limits in native results |
| CP-15 | Independent process reopens and continues; hard exits before/after admission commit preserve state or STORE_BUSY |
| CP-16 | Full applicable offline regression plus original M01 seven-tool and architecture checks |
| CP-17 | No AF Owner/Abaqus/ODB/model API calls, unchanged MCP and AbqJobPilot, no auto Main continuation |
| CP-18 | Actual test counts/Ruff/diff and independent source/artifact/test review; owned test assets retained and subprocesses observed exiting |

## Tests, failures and independent review

Main pytest invocations use the absolute verified interpreter, `-B`, explicit repository
src on PYTHONPATH, `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`,
`-p no:cacheprovider`, and unique TEMP test roots. All M01/M03-B live opt-ins are unset.
The independent Reviewer used the verified interpreter, PYTHONPATH, bytecode/cache
controls and a fresh TEMP root, but did not explicitly set or verify plugin autoload.
The native smoke uses explicit Python assertions, not a mocked model test or a
fabricated pytest model response. The scripts that capture/admit/continue each exited 0.

Full applicable no-owner regression:

```text
D:\XianLab\envs\LangChainEnv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
  --basetemp <fresh TEMP gdcae-m03c-final-regression-a74aaf8cbca44474af3efd01013cf18e>
587 passed, 21 skipped in 652.52s (0:10:52)
```

The 21 skips are two historical M01-B/M01-C live cases and 19 M03-B real AF live
cases. None is a skipped M03-C Main/gate/continuation obligation. No new AF Owner
permission was inferred merely to remove those skips. Final missing/oversized
capture handling was added during that run and independently tested below on the
final helper/test bytes; it does not alter product admission or continuation logic.

Final `D:\ProgramData\anaconda3\Scripts\ruff.exe check --no-cache .` reports
`All checks passed!`. Whitespace validation includes tracked `git diff --check`
and explicit no-index checks for every changed/new untracked source/test/document.
Git's existing LF→CRLF advisories do not imply a content rewrite or whitespace failure.

Independent Reviewer ran:

```text
D:\XianLab\envs\LangChainEnv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
  --basetemp <fresh TEMP gdcae-m03c-review-8419fa3c829a4787a6c7077bbc780ca4>
  tests/unit/test_candidate_proposal.py tests/architecture
168 passed in 146.87s
```

Final missing/oversized capture handling was additionally verified with:

```text
D:\XianLab\envs\LangChainEnv\Scripts\python.exe -B -m pytest
  tests/unit/test_candidate_proposal.py -k capacity -q -p no:cacheprovider
  --basetemp <fresh TEMP>
1 passed, 22 deselected in 6.30s
```

Two development runs found genuine architecture violations: first, dynamic `getattr`
in DTO validation (1 failed/19 passed in 122.21s), then placement of a shared-primitive
DTO under standard-library-only contracts (1 failed/61 passed in 126.53s). Fixes used
explicit dataclass field access and relocated only the new DTO to research. Existing
guards were not relaxed. Reviewer also identified and verified the pre-freeze baseline
choice and correct AGENT_PROPOSAL_UNAVAILABLE classification. No model capacity error
actually occurred during the two native captures; capacity/refusal failures are
explicit negative test inputs, not claims of an observed provider outage.

Native independent Reviewer `/root/m03c_review` read both actual Brief/capture/provenance/
before-state artifacts, independently recalculated hashes, checked conditional reasoning,
then read admission and continuation records and ran the 168-test suite. Its findings
are advisory engineering review, not an authorization or scientific oracle. This was
real native delegation; no mocked reviewer dialogue is used.
Its final source/artifact/report review found no blocking issue and accepted the
separate Main/admission/synthetic conclusions. The environment wording above was
corrected following its final accuracy comment.

## Retention, limitations and next proposal

No AF credential was created/reused and no Owner launched. Test databases, snapshots
and intentional journal sentinels remain only in fresh TEMP roots, including the
native demonstration and independent Reviewer's test root. No broad cleanup was run.
Child Python processes in concurrency/reopen/interruption tests were bounded and
waited for; normal exits and intentional exit 73 are asserted. Retained journals
remain STORE_BUSY; they are not described as recovered. The old M01-B encrypted
materials and M03-B roots were not opened or deleted.

Limitations remain explicit:

- Main authorship is observed in this native turn; files/hashes alone are not identity authentication. The demonstration is not a blind benchmark.
- The hypothesis and all metric outputs are synthetic. One datum does not prove proportional mechanics, and no true numerical/physical verification is available.
- Brief is a view. Typed proposal/admission is not a Grant, resource guarantee, external Run or scientific PASS.
- Same-user coordinated rewriting or filesystem races are not prevented cryptographically. New source/rule inconsistency is handled conservatively, with budget retained under UNKNOWN.
- The narrow DTO intentionally supports one synthetic entity/step/parameter/metric and conservative prose grammar. It is not a general CAE editing language.
- One-turn proposal budget is an explicit interaction rule; no provider quota or automatic model retry system is implemented.
- The unchanged M03-B live suite is not rerun in M03-C; no new real AF integration claim is made for dynamic B.

Next-stage proposal only: add an operator-selected capture review/ingress surface that
shows the exact Brief revision, mutation and provenance before calling the existing
gate. Test stale capture/duplicate approval/cancel races with synthetic effects only.
Separately design M03-E event-to-turn resumption with explicit ownership, original-turn
identity, deduplication, capacity failure and UNKNOWN behavior; require a new approval
before any SDK/app-server turn is initiated. Dynamic AF exact Plan/Grant preparation
also needs separate authorization and identity proof. No next-stage implementation
has started, and no commit or push is authorized by this delivery.

**STOP: awaiting architecture review.**
