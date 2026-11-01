# G3-D5 — release gates and real-A decision

**D5 PARTIAL. REAL_A_ADMISSION=NOT_READY; REAL_A=NOT_RUN;
REAL_B=NOT_RUN; FULL_CHAIN_RELEASE=NO_GO.**

`D5_OFFLINE_READY` is not claimed: campaign-wide authority and complete external
Fake IPC qualification still have implementation gaps. Safe tested partitions passed.
`OPERATOR_DEPLOYMENT=NOT_AUTHORIZED`; `EXTERNAL_INSTALL=NOT_RUN`;
`DESKTOP_AT_GDCAE=NOT_TESTED`.
No real Grant, Standard Owner, Solver/ODB, OS deployment, external execution,
global configuration mutation, installation, Git commit/push or publication is
authorized or performed. Historical build_04/B1/D2 UNKNOWN/BLOCKED are preserved.

## Entry and bounded work

GD main `69b144cea9aecc515e15cc830368972b09258af9`: 9 tracked dirty / 60
untracked. AF Develop `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`: 11 tracked
dirty / 59622 untracked. Both indexes empty. D4 final source matched before edits;
386 scoped source hashes, 13 historical document hashes and D4 receipt digests
were frozen under private `D5_ROOT/evidence/entry.safe.json`.
`D5_ROOT=%LOCALAPPDATA%/GDCAE-G3-D3-OFFLINE-20261030-A01/D5-20261031-A01`.
No Stable, production Project, real model, historical Owner or private chat was read.

AF, Core and Product native engineering workers had disjoint file ownership;
Main owned HIL preview, cross-repo tests and reporting. Independent Reviewer was
read-only. Existing F1 and installer lifecycle code were not expanded.

## Implementation and remaining boundaries

- AF adds explicit public preflight and exact dynamic-real Plan review compatibility
  to the existing rod facade. The old inert review route remains separate. New
  requests and decisions are persistent but non-executable, with TEST_ONLY canary
  approval/denial, replay/expiry and exact-context checks. No Grant is created.
- Original-source acquisition now rechecks DAT, STA and MSG against collector
  identities, unique Receipt/Validation and the managed completion/event chain.
  Hash/record consistency is not an authenticated publisher or immutable history.
- GD `pre_a_dossier()` derives the frozen A, input, policy and budget from one
  read-only snapshot. Independent verification checks the caller's expected
  backend, candidate-output and resource bindings as well as the acquired payload.
- Source bytes are contract-pinned. D5 uses a fresh Project; historical D4 Projects
  retain their matching D4 snapshot and are not silently migrated. Existing
  consumer limits remain 16 KiB DAT / 64 events / 512 lines / 1024 normalized chars.
- Budget protection is **ResearchProject-local**. Foreign evidence is rejected,
  but a newly created Project has its own cap. Campaign-global two-attempt
  enforcement and non-agent-controlled approval/OS peer binding remain unqualified.
  Caller `budget_remaining` in the canary request is not such an enforcement layer.
- Existing `ProductStandardControl.invoke(authorize)` / `standard_contract._issue`
  recognize the exact dynamic Plan and one-shot REAL_ROD_STANDARD Grant. They were
  not invoked. Product provisioning is still fixed-profile only; `prepare_real`
  does not install Standard profile/operator extensions. A protected dynamic
  provisioning adapter and independent SID-bound human UI/peer adapter remain
  missing software, separately from the unapproved OS deployment. Canary review
  does not feed real authorize. Account/ACL approval alone cannot close this gap.
- There is no pre-produced B Plan or Grant. The real positive B route remains
  unimplemented/unqualified pending authenticated A, native proposal, deterministic
  admission and separate approval. No analytical 2 N candidate is substituted.

## Non-executable A-only scientific draft

Fresh API-created Project revision 3, cap 2 / held 0 / charged 0 / available 2.
An ordinary separate Python invocation reopened it through the read-only API;
all Project file hashes were unchanged and the dossier remained NOT_EXECUTABLE.
This was not a native Job/process-family qualification experiment.
Contract digest `sha256:b72edd4b0939b756f37ec4a8dd1302b72fabc8b1edf38f62dec73351994f9ac6`.
Proposed A input: 420 bytes, SHA-256
`e2f91730b68f3af72b8054bc168d31b72a3f21ae186e899d64ab4b6b761523a3`.

| Field | Known / unresolved |
|---|---|
| Baseline | Code-declared T3D2, 2 nodes / 1 element, L=10 mm, area=1 mm², E=1000 MPa, Poisson=0.3 |
| Boundary and units | Node1 DOF1/2/3 zero, Node2 DOF2/3 zero; N/mm/MPa |
| Permitted change and goal | Only Node2 DOF1 CLOAD [0.5,2.5] N; proposed A=1 N; U1 [0.019,0.021] mm |
| Qualification | Frozen-template compliance checked; model DECLARED_ONLY, physical verification NOT_ASSESSED |
| Real service identity | Actual AF Project/Instance/Plan/Grant, host executable/license, exact output/scratch paths, nonce/expiry and human decision unresolved |
| Before A | Qualify protected authority, host, exact immutable tuple and trusted acquisition/refusal mechanism; no requirement to produce future A DAT |
| After A | Acquire THIS A's original DAT/STA/MSG and exact Run/Receipt/Attempt/managed completion, then independently verify V0–V3 |
| Current result | V2 NOT_VERIFIED; V3 INCONCLUSIVE; V4 NOT_ASSESSED; ODB NOT_VERIFIED |

Draft remains **NOT_EXECUTABLE**. Neither offline preflight nor this report grants
authority. Actual A output does not exist; fixtures cannot fill those fields.

## Actual tests and evidence

Interpreter `D:/XianLab/envs/LangChainEnv/Scripts/python.exe`, Python 3.12.10;
pytest 9.1.0, MCP 2.3.0, pywin32 312. No environment/dependency changes.
Commands use that absolute interpreter with `-B tests/integration/g3_d5_offline_checks.py`
and a unique label/explicit targets. The runner reuses P1/D3 private output capture,
records exact private collection, and blocks native launches/network before effects.
It is a regression guard, not OS isolation. Raw logs are not published.

| Safe receipt / command label | Actual result |
|---|---|
| `privacy-pure tests/unit/test_main_runtime_privacy.py` with exact exclusions | 29 passed / 5 parametrized deselected, zero guard |
| `core-preflight-02` D5 and D4 Core/Verifier | 79 passed, zero guard |
| `hil-first` D5/D4/G3 Operator pure tests | 105 passed, zero guard |
| `cross-lint-final` D5/D4 cross-repo files | 8 passed, zero guard |
| `product-final` D5/D4 Product and D3 external runner | 40 passed, zero guard |
| `af-stat-final` D5/D4 trusted route | 74 passed, zero guard |
| `af-review-corrected` prior review/lifecycle | 99 passed / 1 deselected, zero guard |
| `af-full` current applicable AF partition | 275 passed / 1 deselected, zero guard, 94.14 s |
| `gd-full --reviewed-pure-selection` | 1356 passed / 157 deselected; 0 failed/skipped/errors, zero guard, 1020.67 s |

Counts overlap and are not summed. `af-full` selects D5/D4 trusted tests,
`test_g2_rod_product.py`, `test_g3_rod_evidence_port.py`, `test_rod_plan_adapter.py`,
`test_rod_preview.py` and only two safe Standard nodes:
`test_real_requires_separate_grant_and_opt_in` and
`test_synthetic_cp936_sample_and_malformed_data`; it excludes
`test_reopen_in_independent_python_process`. GD uses 58 reviewed file targets and
70 exact function exclusions inherited from the audited D4 partition plus D5 files.
Private exact collection and selection receipts preserve parameterized node IDs;
live subprocess/IPC/App Server/Owner/Solver suites are not claimed passing.

Failed attempts remain: initial privacy selection 32 passed / 2 failed with two
prelaunch guard denials; corrected selection above. Initial Core 76/3 was test
assertions missing earlier valid Schema rejection. AF initial legacy selection
99/1 with one prelaunch guard denial used a nonmatching absolute deselection;
corrected using collected node names. Cross-first 6/2 and intermediate AF71/1
revealed Windows fstat/path-stat ctime semantics, not changed output bytes. The
fix compares birthtime consistently, retains same-handle ctime stability, and
checks original device/inode/size/mtime/digest; final cross/AF tests above passed.
No guarded launch occurred; no raw private failure output was printed.

Product's delegation prompt contradiction was corrected during the broad run;
final `product-final` covers those exact files. Main's fixture import lint change
was covered by `cross-lint-final`. These affected files have final targeted tests;
no broad result is represented as a perfectly immutable single-snapshot run.

Final GD Ruff: exit 0, zero diagnostics (three fixture-import F811 findings fixed).
Same isolated AF rules on the three modified source files plus the new test versus
D4 source: zero current / zero baseline diagnostics, zero introduced. This does not
claim all historical AF style debt disappeared. Both `git diff --check` exit 0.
Bounded privacy-pattern scan zero matches; P1 projection and no raw history output
remain the evidence boundary, not a claim of arbitrary-secret detection.

## Final candidate and product status

Candidate `D5_ROOT/candidate-final`, wheels `0.0.0+g3d5`, Plugin `0.1.0-alpha.4`.
Only that candidate is proposed; initial D5 candidate is preserved as
`SUPERSEDED_NOT_FOR_QUALIFICATION` after the prompt correction.

| Frozen artifact | SHA-256 |
|---|---|
| GD manifest (61 files) | `34ea4053dc94bef66bc6bfc2d279ddcebd4ee4178fffdd117958c2a3242283d0` |
| AF manifest (118 files) | `2493a931dd7e9c30fc3ee55b01a52e39717977303b879d36fe33f45275725556` |
| External BUNDLE.json (11 files) | `51f35d1fc8b7f3043e15f5495dc1d0f4c706564180b4a5b06966374a0b42d625` |

Independent Reviewer matched 179 current/snapshot/archive files, eight artifacts,
171 wheel source entries, 175 RECORD entries and eleven external bundle files.
No new authority bypass was found. Reviewer required explicit campaign cap and
external Fake IPC/closeout limits and identified the corrected prompt defect.
This review did not install, execute, attest a solver or authenticate an Operator.

Desktop Appx metadata: **26.1027.3384.0**. CLI file version was empty; CLI version
remains `UNKNOWN_EMPTY_FILE_VERSION_METADATA` rather than inferred from Desktop.
Installed-copy checks now reject version mismatch, duplicate RECORD and wrong
size/origin; actual tests use extracted-wheel fixtures. Installed copy is
`NOT_OBSERVED`; fresh Desktop `@GDCAE` and four-role loading are `NOT_TESTED`.
No source/current-Main role call substitutes for that observation.

External entrypoint prepares venv → no-index/no-deps two-wheel install → smoke,
180 seconds per stage; timeout becomes UNKNOWN_STOP with no retry/cleanup. It is
NOT_RUN. Fake IPC scenario records five exact existing harness hashes only; support
files and pytest/pywin32 dependencies are not delivered/qualified. Thus full WP-D
remains PARTIAL. A narrow smoke PASS would not establish Fake IPC or descendant
finalization; those require additional preparation and independent VM evidence.
No new lifecycle controller was introduced.

## One-page User Action Card — three separate decisions

1. **Protected Operator — NOT_AUTHORIZED.** Proposed new local standard users:
   `GDCAEResearch`, `GDCAEReviewer`, `GDCAEIssuer` (not asserted to exist). A human
   administrator outside the Agent session resolves SIDs and creates only approved
   identities/new roots. No existing account is changed; no new Windows service.
   Human explicitly starts the existing AF Owner under issuer only in a later task.
   Proposed roots: `C:/Program Files/GDCAE Operator` (code),
   `C:/ProgramData/GDCAE Operator/{config,capability,project,engineering,audit,review}`.
   Protected explicit DACL; Administrators/SYSTEM full control. Research gets code
   RX only; reviewer gets code RX/config R/review R; issuer gets code RX/config R/
   capability R and Modify on Project/engineering/audit/review. No inherited or
   unlisted user rights. Admin/issuer remain privileged trusted actors; issuer
   audit Modify is not append-only or tamper-proof. Current token is non-elevated
   but has administrator/linked-admin risk; no isolation PASS. New issuer-scoped
   DPAPI/license access must be qualified without exporting existing secrets.
   Exact approve/terminal-deny UI must show Plan/input/resources/output/revision/
   nonce/expiry/one-attempt; Agent text/boolean is never authority. UI/OS peer adapter
   remains unqualified. Rollback: disable requests/revoke unused grants, reconcile
   only owned handles, preserve audit, human-disable new accounts and restore recorded
   security descriptors; no unknown process termination or historical deletion.
   The bound preview request digest is
   `43c0e4b3c3b7d66522d3e7917b55ecc132e8d26cdde1bcd058d8cb6756a13764`;
   it names the exact final candidate manifests. Its configuration digest binds an
   explicitly undeployed preview, not an observed installed runtime configuration.
2. **Independent Windows qualification — NOT_RUN.** Prefer a disposable independent
   local Windows VM (availability not inspected), not the blocked current host.
   Transfer only the exact allowlisted candidate; no credentials, private logs,
   models or research databases. No upload or billed Actions run now. Host/Python,
   dependencies, entry hash, expected children, halt/cleanup and missing Fake IPC/
   closeout qualification must be explicitly approved before execution. Current
   unpushed overlays are not a remote release. GitHub manual dispatch requires the
   workflow on the default branch; no push/workflow execution is authorized.
3. **Desktop Plugin — BLOCKED_USER_ACTION / NOT_TESTED.** One disposable project,
   one official UI activation/consent and one bounded text-only test. No thread ID,
   credentials or private-chat screenshots are requested. Open
   `D5_ROOT/disposable-plugin-project-final`, select **GDCAE** in the official UI,
   then send the bounded text in `D5_ROOT/evidence/activation-request-final.safe.json`.
   Main may only delegate to `gdcae-cae`, `gdcae-results`, `gdcae-inverse`,
   `gdcae-reviewer`; roles may not use tools. Report actual recognition and four
   distinct returns, no default-role substitution. Plugin key is
   `gdcae@gdcae-preview`. Installed-copy inspection is a separate read-only gate;
   source roles/current Main are not Desktop activation proof.

These decisions do not authorize real A. A needs a separate fully populated exact
approval; B needs authentic A evidence and its own separate consent.

Official references rechecked: [Plugin packaging/local marketplace](https://developers.openai.com/plugins/build/plugins),
[Plugins](https://learn.chatgpt.com/docs/plugins),
[Developer commands](https://learn.chatgpt.com/docs/developer-commands),
[GitHub manual workflow dispatch](https://docs.github.com/actions/managing-workflow-runs/manually-running-a-workflow).

## D5-01–D5-18 acceptance

| ID | Result | Evidence / remaining gate |
|---|---|---|
| 01 | PASS | Actual heads/index/386 source hashes; preservation checks |
| 02 | LIMITED PASS | New frozen A/template compliance; physical model qualification unresolved |
| 03 | PASS OFFLINE | Explicit real-profile preflight; no config/dispatch activation |
| 04 | LIMITED PASS | Original transactions/owner semantics in fixtures and legacy refusal tests; no real Owner |
| 05 | LIMITED PASS | Public DAT/STA/MSG source binding and contamination negatives; authenticated OS source pending |
| 06 | PASS | Future A output explicitly post-execution; mechanism checks separately graded |
| 07 | LIMITED PASS | B-before-A and causal negatives; no B Plan/Grant; positive real B unimplemented/unrun |
| 08 | PARTIAL | Project-local cap2/UNKNOWN/replay/foreign evidence rejection; campaign-global cap absent |
| 09 | PASS PREVIEW | Exact three-principal/root/DACL/rollback proposal, no actual OS changes |
| 10 | PASS BOUNDARY | Actual current-token admin risk retained; no same-user enforcement claim |
| 11 | LIMITED PASS | Explicit dynamic preflight approve/deny/replay/expiry/tamper/caller tests; TEST_ONLY only |
| 12 | BLOCKED_USER_ACTION | Installed-copy fixture tests pass; actual installed registration NOT_OBSERVED |
| 13 | NOT_TESTED | Fresh Desktop recognition/native loading awaits official activation |
| 14 | PARTIAL | Exact bundle/single entrypoint prepared; external NOT_RUN, Fake IPC support/deps and VM closeout unresolved |
| 15 | LIMITED PASS | GD 1356/157, AF 275/1, final targeted tests, Ruff/diff; explicit live exclusions |
| 16 | LIMITED PASS | Independent source/candidate/report review; 200 files/537 archive entries bounded privacy scan, zero hits; no physical authority |
| 17 | PASS DRAFT | Read-only frozen A dossier remains NOT_EXECUTABLE with missing service/host/authority fields |
| 18 | PASS BOUNDARY | Operator NOT_AUTHORIZED; external NOT_RUN; Desktop NOT_TESTED; A/B NOT_RUN; full chain NO_GO |

## Exact D5 file scope and stop

GD modified: `src/aegiscae/research/rod_real_project.py`,
`src/aegiscae/research/rod_real_verify.py`, `operator_deployment/preview.py`,
`plugins/gdcae/scripts/candidate.py`, `plugins/gdcae/scripts/gdcae.py`,
`plugins/gdcae/plugin.json`, `plugins/gdcae/references/runtime-contract.json`,
`external_runner/package.py`, `external_runner/qualify.py`, `external_runner/smoke.py`,
`external_runner/README.md`, `tests/unit/test_d4_product.py` (version assertion only).
GD new: `tests/unit/test_d5_real_preflight.py`, `tests/unit/test_d5_operator.py`,
`tests/unit/test_d5_product.py`, `tests/integration/g3_d5_offline_checks.py`,
`tests/integration/test_d5_cross_repo_offline.py`, this report.
AF modified: `abqjobpilot/product_rod.py`, `abqjobpilot/execution/rod_trusted.py`,
`abqjobpilot/execution/rod_review.py`; new `tests/test_d5_rod_preflight.py`.
Total: 18 GD / 4 AF files; no other implementation scope.

Current status totals (include all prior work): GD 9 tracked dirty / 66 untracked;
AF 11 / 59623. Heads/branches unchanged, indexes empty. Thirteen historical hashes
match; no changes outside the scoped entry-source whitelist. Detailed source hashes
are in `D5_ROOT/evidence/source-scope.safe.json`; final source, history, candidate,
Git and test-digest closeout is recorded separately in `final-closeout.safe.json`.
Ordinary SHA-256 records prove consistency checks, not tamper-proof authenticity.

Next engineering work is bounded to protected dynamic provisioning, independent
human/OS-peer approval binding, campaign-wide budget enforcement, and delivering
the existing Fake IPC support/dependency closure for a separately approved VM.
No new F1/installer framework is needed. D5 stops here pending architecture review;
no real A, B, deployment, external run, commit, push or publication follows automatically.
