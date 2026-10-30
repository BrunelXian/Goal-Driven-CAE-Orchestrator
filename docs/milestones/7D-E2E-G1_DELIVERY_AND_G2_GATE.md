# 7D-E2E-G1 delivery and G2 gate

Date: 2026-10-30. This record covers scoped OFFLINE implementation only.
Status: PARTIAL / BLOCKED for full G1 closure; applicable offline regression complete.
Real full-chain release and G2-A/G2-B remain NO-GO. No actual solver result is
claimed by this record or by offline fixtures.

## Protected baselines

- GD-CAE main: `184245cc8a67859484406d70fb1e2d1cf2e347c7`.
- AF Develop: `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`.
- Entry checks: both expected branches/HEADs; zero tracked changes or staged files.
- Pre-existing untracked counts: GD-CAE 5, AF Develop 59,597. Historical names,
  contents and credential/session material are not reproduced. Preserve all.
- Stable is outside scope and was not inspected. No reset, cleanup, commit, push,
  tag, CI trigger, repository publication or global Codex edit is authorized.
- Interpreter: existing LangChainEnv, Python 3.12.10, pytest 9.1.0. Ruff 0.12.0.
  No dependency/environment changes. Test stdout/stderr use the accepted P1
  bounded capture and allowlisted counter/source projection.

## Distribution evidence and limits

The source package provides a portable manifest, repo marketplace, two Skills,
four native-role templates, a read-only doctor, a pinned installation-plan
generator and exclusive fresh-workspace preparation. No MCP execution endpoint
or Operator credential is bundled. Existing seven AF read tools are unchanged.

An isolated new workspace outside the source checkout was prepared automatically
from the explicit package allowlist. Package preparation is not Codex plugin
installation or activation. Neither global cache nor user config was modified.
GitHub access, public distribution and installed `@GDCAE` remain untested.

The current Main's native spawn interface rejected `agent_type=gdcae-cae` with
`unknown agent_type`. That is the observed custom-role-loading blocker; its cause
is not inferred. Newly written TOML alone does not prove native registration.
Any subsequent default-agent role behavior probes are recorded separately and
cannot close this blocker or count as installed four-custom-role acceptance.

## Implemented offline interfaces

AF adds `axial_rod_cload_v1`: exactly one finite in-range CLOAD, independent byte
comparison, new artifact directories, an exact RodPlanPreview and materialized
file revalidation. Old fixed SHA/profile behavior is unchanged. A new public
adapter registers an actual OFFLINE_ONLY ExecutionPlan in existing jobs/plans
tables and supports public inspect/revalidation; it issues no Grant or Run.
The preview alone is not an ExecutionPlan, and neither form authorizes dispatch.
The service rejects this backend even with an injected OPEN gate or TEST_ONLY
Grant. B registration requires a qualified real A handoff and currently blocks.
Dynamic
DAT checks validate complete node/element rows, U1, S11, RF1 and force balance.
Only OFFLINE_AF_SUBSTITUTE is accepted; actual artifact acquisition is unqualified.
The registered verifier takes tolerances only from the persisted exact Plan; a
caller cannot replace stricter frozen tolerances with the profile defaults.
The 18 cross-repository cases consume RodPlanPreview; the 12 registered-Plan
cases run within AF. They do not jointly prove a GD-CAE-to-persisted-ExecutionPlan
bridge or its registered verifier. That integration remains unqualified.

The TEST_ONLY review control uses the existing trusted AF test issuer/validator
inside the same transaction as approval/denial receipt. Original public issuance
behavior is preserved. Wrong capability, stale Plan, conflicts and denial replay
are tested. No real Standard/rod Grant is issued. No Operator capability is
bundled into Main tools. A same-user process can still access trusted code/files:
BLOCKED_HIL_STRONG_ISOLATION remains, and no actual human approval is claimed.

GD-CAE adds a newly-created schema-2 ResearchProject, using the existing tables,
identity, revision and workflow-event transaction path. No historical migration,
additional store type/table, second orchestration store, scheduler or Agent
harness is introduced. Each new ResearchProject creates its own ordinary database.
A new frozen rod contract
captures model, goal, units, tolerances and exactly two intent allocations. Old
schema-1 synthetic contract/budget/mutation paths are retained. A second attempt
requires a committed valid A not-met observation, its Run/output/metric/decision/
contract/revision and later proposal order. UNKNOWN holds budget and blocks B.

The independent GD-CAE parser does not invoke AF's parser or trust its verdict.
Both parsers agree on controlled fixtures; this is not live-source authentication.
All real_goal fields stay INCONCLUSIVE; execution_authorized=false;
V4=NOT_ASSESSED and ODB=NOT_VERIFIED. AF_REAL is rejected. This is an offline
real-preview prerequisite, NOT a completed real execution adapter.

## Exact changed-path whitelist

GD-CAE (30 files; 4 modified, 26 new):

```text
README.md
.agents/plugins/marketplace.json
.codex/agents/gdcae-cae.toml
.codex/agents/gdcae-results.toml
.codex/agents/gdcae-inverse.toml
.codex/agents/gdcae-reviewer.toml
plugins/gdcae/plugin.json
plugins/gdcae/scripts/gdcae.py
plugins/gdcae/skills/setup/SKILL.md
plugins/gdcae/skills/research/SKILL.md
plugins/gdcae/references/handoff.md
plugins/gdcae/agents/gdcae-cae.toml
plugins/gdcae/agents/gdcae-results.toml
plugins/gdcae/agents/gdcae-inverse.toml
plugins/gdcae/agents/gdcae-reviewer.toml
src/aegiscae/research/project.py
src/aegiscae/research/rod_preview.py
src/aegiscae/research/rod_preview_rules.py
src/aegiscae/research/rod_preview_dat.py
tests/architecture/test_package_skeleton.py
tests/unit/test_mcp_read.py
tests/unit/test_real_rod_preview.py
tests/unit/test_gdcae_distribution.py
tests/unit/test_g1_safe_checks.py
tests/integration/g1_safe_checks.py
tests/integration/test_g1_cross_repo_offline.py
docs/architecture/7D_G1_REAL_ROD_PREVIEW_OFFLINE.md
docs/architecture/7D_G1_PLUGIN_INSTALLATION.md
docs/milestones/7D_G1_NATIVE_ROLE_PROBES.md
docs/milestones/7D-E2E-G1_DELIVERY_AND_G2_GATE.md
```

AF Develop (9 files; 2 modified, 7 new):

```text
abqjobpilot/execution/rod_profile.py
abqjobpilot/execution/rod_dat.py
abqjobpilot/execution/rod_authorization.py
abqjobpilot/execution/rod_plan_adapter.py
abqjobpilot/execution/test_authority.py
abqjobpilot/execution/service.py
tests/test_rod_preview.py
tests/test_rod_plan_adapter.py
docs/agent_first/GDCAE_7D_G1_OFFLINE_ROD_PROFILE.md
```

## Actual test evidence

Counts below are separate invocations with overlap, not additive totals.

| Invocation | Actual result | Scope / limitation |
|---|---|---|
| P1 privacy gate | 34 passed, 0 failed, 0 skipped; 0.99 s | Existing accepted whitelist/capture boundary |
| Distribution | 18 passed; 1.19 s | Fresh workspace, exact file set, no overwrite/global destination, pinned ref/credential URL rejection, no install |
| Distribution/doctor and baseline final | 24 passed; 1.14 s | 19 package cases plus 5 baseline cases; missing Python Core explicitly reported |
| Core + architecture | 236 passed; 17.50 s | 67 then-current Core and 169 architecture cases |
| Core expanded | 71 passed; 10.30 s | Reopen, hard exit, concurrent intent, response loss, UNKNOWN, causal substitution, rehashed corruption |
| Cross-repository first corrected run | 15 passed; 2.69 s | Both public compilers/parsers and offline A/B persistence |
| Reviewer corrections | 23 passed; 3.30 s | 5 baseline projection cases plus 18 cross-repository cases |
| Cross-repository final | 18 passed; 3.31 s | Includes AF RodPlanPreview resources/output projections, substitutions and valid-preview live-dispatch refusal |
| Changed-surface + architecture | 282 passed, 0 failed/errors/skipped; 21.28 s | Core 71, architecture 169, distribution 19, baseline 5, cross-repository 18 at that revision |
| Distribution privacy final | 26 passed; 1.31 s | 21 distribution cases and 5 baseline cases; fixed CLI error projection and interpreter guard |
| GD-CAE first full applicable no-Solver suite | FAIL: 946 passed, 3 failed, 21 skipped; 2468.99 s | Diagnostic run; failures and subsequent production fix recorded below |
| Import/role regression after fixes | 85 passed; 8.38 s | Cross-repository fixture cleanup, exact six role configurations, original package import guard |
| Schema creation-marker regression | 141 passed; 18.05 s | 76 Core and 65 original ResearchProject cases; includes five new schema-retagging negatives |
| Final disjoint full-suite aggregate | 965 passed, 0 failed, 0 errors, 21 skipped, 0 deselected | Four exclusive partitions cover all 38 discovered test files; source/test hashes unchanged before/after |
| AF focused | 75 passed; 7.783 s | New 71 plus four selected safe legacy tests |
| AF expanded applicable offline | 164 passed, 0 failed/errors/skipped; 47.118 s | One Supervisor-construction case explicitly deselected |
| AF final expanded with actual offline Plan | 176 passed, 0 failed/errors/skipped; 50.702 s | Adds 12 Plan cases including first-registration concurrency, replay, rollback, fixed tolerances and unconditional refusal; same one deselection |
| Ruff | Final GD-CAE PASS, exit 0, 0.47 s; AF limited | Seven AF files PASS; service.py retains seven pre-existing E701, unchanged issue statements versus HEAD, zero new findings; not an all-file PASS |
| Git diff check | Both repositories PASS | Final tracked changes checked; no staging or commit |
| Skill validation | Both exit 0 | Setup and research frontmatter/structure; not behavioral activation |

Full suite uses `g1_safe_checks.py pytest` with explicit AF source, explicit new
basetemp, P1 capture/pytest counter hook, plugin autoload disabled and live M01/M03
environment switches cleared. No raw pytest output is projected. The full run
began before the helper acquired its new internal branch/HEAD check; actual
baseline had been separately checked. Post-review focused tests use the corrected
helper, including pre/post branch/HEAD checks. The later packaging doctor and AF
offline Plan registration additions have separate final focused/regression runs.
The first full run found three failures; it is not claimed to cover later source
versions or to have passed. The subsequent full-suite aggregate runs four
mutually exclusive test-file partitions with a recorded source/test SHA snapshot.

| Final partition | Files | Passed | Skipped | Failed/errors | Elapsed seconds |
|---|---:|---:|---:|---:|---:|
| full-final-1 | 9 | 287 | 0 | 0/0 | 1314.31 |
| full-final-2 | 10 | 226 | 1 | 0/0 | 793.42 |
| full-final-3 | 9 | 164 | 20 | 0/0 | 491.72 |
| full-final-4 | 10 | 288 | 0 | 0/0 | 61.00 |

This is a disjoint-file aggregate, not a claim of a second single-process full
run. The partition union equals the complete source test allowlist, with no
duplicates. All four exits were 0, and their baseline/boundary checks passed.
The final source/test snapshot comparison passed. All task-owned final test
processes exited; a bounded process check found zero remaining. Safe records and
the exact partition manifest remain in this task's isolated temporary audit root.
The 21 skips are excluded from the passing count; live opt-ins remained disabled.

The first failure was an old assertion permitting exactly two native role files.
The test now requires precisely the two unchanged legacy roles and four preview
roles, including the preview feature flags. The second was test isolation:
cross-repository AF imports survived into the package-import side-effect guard.
The fixture now removes only AF namespace modules newly imported by that fixture;
the original package-import guard remains unchanged. The third was an actual
Project integrity defect: a schema-1 Project could be retagged schema 2 with a
recomputed metadata digest. Newly created schema-2 Projects now bind an exact
integer creation_schema=2 into their first CREATED event; reopening checks its
consistency with metadata. Schema-1 events retain their historical format. Five
new negative cases cover both retagging directions and missing/wrong marker
types/values. This is consistency detection, not a cryptographic authenticity
claim. This production fix occurred after the first full run. The independent
Reviewer accepted all three fixes without weakening the original guards.

The initial cross test had six failures from the test's incorrect expected AF
exception class; it was corrected to the actual public ExecutionError. Cross
review also found canonical load rendering disagreement (e.g. 2.00 versus 2),
which was fixed with identical non-rounding canonicalization before the full run.
An initial Ruff failure from an unused test import was corrected. AF's initial
default pytest temp location was inaccessible; a new explicit basetemp resolved
this without cleaning old files. Failed intermediate runs are not counted as PASS.

AF deliberately did not run the entire repository suite: old positive Standard
tests can create REAL_FIXED_STANDARD grants even when launch is mocked; other
tests construct Owners/processes. They exceed G1 authorization. The explicit
Supervisor deselection is not a passed test. Six old fixed/live lifecycle source
files remain equal to HEAD; service.py has the reviewed additive read/refuse
dispatch branches. Safe negatives prove the old profile still
rejects a changed/rehashed load input. See the AF report for exact selection.

## Independent review and native results

Read-only reviewer found two P2 issues: hardcoded test-evidence HEAD without a
runtime baseline check, and an arbitrary resource digest in the cross-repo test.
Both were corrected. Reviewer rechecked the source and closed these findings:
branch/HEAD are now measured before every check; cross-repo bindings derive from
canonical AF Plan resources/output path and have mismatch negatives. No additional
mandatory source fix was identified. This closes those findings only, not G2.
The subsequent actual offline Plan adapter and service branches were independently
reviewed. Reviewer requested a true empty-store concurrent first-registration
case in addition to concurrent replay; it was added and passed. Root's tolerance
binding review also led to the registered verifier's no-override frozen-policy
interface and a strict-versus-default tolerance negative test.
The final document review required the cross-repository RodPlanPreview tests to
be distinguished from AF-local registered ExecutionPlan tests. That wording and
the remaining cross-repository registration gap are now explicit. The Reviewer
accepted the three full-regression fixes and retained the overall PARTIAL /
BLOCKED conclusion; none of these reviews authorizes G2.
Final independent disposition: REVIEW_COMPLETE, no additional mandatory findings.
The Reviewer checked the final arithmetic and evidence boundaries and accepted
G1-13 as applicable-offline PASS, relying on Main's verified safe test projections,
partition-union and snapshot evidence. The Reviewer did not rerun the suite.

Four actual native default-agent behavior probes returned correlated CAE,
Results, Inverse and Reviewer products. Material edits, missing A source and
embedded instructions claiming authorization were refused. Inverse initially
returned an unsupported status enum; Main obtained a format correction. No result
was rewritten to invent acceptance. See `7D_G1_NATIVE_ROLE_PROBES.md`.

The spawn API rejected the new custom type. Package scaffolding and default
behavior probes do not prove custom role loading, enforced role feature flags,
fresh Desktop Main behavior or @GDCAE activation. G1-11/12 remain open.

## G1 matrix

PASS below is limited to the stated OFFLINE evidence; missing required portions
make the overall G1 result PARTIAL/BLOCKED.

| Gate | Status | Evidence / remaining condition |
|---|---|---|
| G1-01 | PASS | Expected baselines, staged empty, exact whitelist, Stable/history untouched |
| G1-02 | PARTIAL | Additive profile, actual offline ExecutionPlan registration and old-SHA refusal tested; real product dispatch unqualified |
| G1-03 | PASS offline | Single token, full byte comparison, canonical decimals, unique directories and stale-file checks |
| G1-04 | BLOCKED | Two-project identity mapping tested; serial real AF ownership/lifecycle/closeout not proven |
| G1-05 | PARTIAL | Actual existing TEST_ONLY issuer/validator approval and denial; no real rod Grant or human consent |
| G1-06 | PARTIAL / BLOCKED | Ordinary interface denied; strong OS Operator isolation not deployed |
| G1-07 | PASS offline | Explicit new schema 2 and source type; schema 1 retained, no migration |
| G1-08 | PASS offline | Committed A causes later B, with substitutions/UNKNOWN rejected; no real A supplied |
| G1-09 | PARTIAL | Dynamic DAT metrics/provenance contracts tested; actual output acquisition not qualified |
| G1-10 | PASS offline | Separate V0..V3, real_goal INCONCLUSIVE, V4/ODB limitations retained |
| G1-11 | PARTIAL / BLOCKED | Four real native default probes; custom-type/fresh Main flow not verified |
| G1-12 | BLOCKED | Package and fresh scaffold tested; no approved global install, GitHub access or @ activation |
| G1-13 | PASS applicable offline | 965/0/21 disjoint aggregate; AF 176 pass with one explicit exclusion; privacy/diff/review complete; seven legacy AF lint findings disclosed |
| G1-14 | PASS within scope | Exact files and exclusions reported; no real Grant/Solver/commit/push/release |

## Privacy and working-tree audit

The exact 30 GD-CAE and 9 AF candidate files passed the scope and content audit.
No matches were found
for raw thread URLs/UUID-form identifiers, private-key blocks, long API-key or
Bearer-token patterns. This bounded pattern check plus independent source review
is not proof of absence of every possible secret. Historical report bodies and
credential stores were not read. No raw test logs or live credentials are copied
into the package. Git diff metadata warnings initially made a scope projection
fail closed; per-command newline-check settings were used for the read-only audit,
without changing repository/global configuration. Both staging areas remain empty.
The audit confirmed GD-CAE 4 tracked modifications + 26 new files and AF 2
tracked modifications + 7 new files, exactly matching the whitelist. Both HEADs
and branches remain at the approved baseline. Untracked counts are 31 and 59,604,
respectively (original 5/59,597 plus this task's new files); no historical material
was cleaned. Both staged counts are zero. No commit, push or release was created.
New isolated test databases, substitute artifacts and safe counter records remain
outside the repositories in this task's temporary roots. They were not copied
into the Plugin or reused as real evidence; old test materials were not cleaned.

## Smallest remaining product integration scope

The earlier assumption that all AF lifecycle code lay outside G1 was corrected:
supervisor/lifecycle/closeout modules inside execution/ are not automatically out
of scope. This is why actual offline Plan registration was completed in G1.
The concrete remaining external chain is `abqjobpilot/product_standard.py:17`
(`read_extension` fixed format), `abqjobpilot/service_lifecycle.py:77/175`, and
`abqjobpilot/service_owner.py:30-38` (old StandardConfig/control construction).
They remain unchanged. A narrow follow-on review must specify a versioned product
extension/Owner selection path and associated execution-side integration, without
changing old fixed Plan meaning or Store schema. Offline Plan registration alone
does not qualify the real dispatcher, output source or two-owner lifecycle.
The next offline integration also needs a GD-CAE test of AF's actual registered
ExecutionPlan and frozen-tolerance verifier through public adapters; the current
cross-repository preview test and AF-local registration test are separate evidence.

Strong HIL also needs a separately controlled OS principal/operator environment;
same-user capability fixtures are insufficient. The product install gate needs
separate approved local installation and a fresh Main test. The Plugin does not
install the Python core: the final doctor run without source PYTHONPATH reported
research_core=MISSING. Setup now stops on that condition. No core/dependency
installation occurred, and no public GitHub installation claim is made.

Recommended next gate, in critical-path order:

1. Complete the public registered-Plan cross-repository fixture binding, including
   exact input/resources/output/contract/tolerance substitution negatives.
2. Obtain a narrow offline scope decision for the three external AF product
   files above; implement and review versioned loading, exact dispatch checks,
   UNKNOWN and serial per-Project closeout contracts while retaining old behavior.
3. Qualify an independently controlled Operator environment and its exact
   one-use approval/denial interface; a same-user test secret is insufficient.
4. Separately approve a pinned local Plugin/Core installation and fresh Main
   activation test, then prove all four actual named role configurations load.

Only after those gates should a precise G2-A authorization be presented. None
of these recommendations starts a new Runtime framework or changes the release
goal to a synthetic-only demonstration. G2-B cannot be specified or pre-approved
until accepted actual A evidence exists.

## G2 remains separately controlled

No real execution Grant or Run is issued under G1; offline prerequisite Plan
records are explicitly non-executable. A requires final exact input/Plan digest,
qualified backend and operator boundary, explicit target Project/instance, paths,
resources/time, one attempt and UNKNOWN reconciliation/stop rules. B additionally
requires accepted actual A evidence and a causal later proposal, then its own
separate authorization. An offline green suite is not authorization.
