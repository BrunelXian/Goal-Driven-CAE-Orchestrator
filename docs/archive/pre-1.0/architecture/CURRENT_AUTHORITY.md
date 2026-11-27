# Current architecture and invariant register

Status: accepted M01-A governance scope, 2026-10-28. Implementation and runtime
qualification are separate claims; actual test results belong to the M01-A
delivery report.

## Authority and precedence

The researcher's current approved task bounds permitted actions.
[ADR-003](../adr/ADR-003-codex-native-delegated-execution.md) and
[ADR-004](../adr/ADR-004-execution-evidence-research-verification.md) record the
accepted architecture within that scope. Earlier decisions continue to apply
except for the explicit conflicting provisions superseded by these ADRs.

The root `ARCHITECTURE.md`, `RUNTIME_INVARIANTS.md`, migration documents, ADR-001,
ADR-002, and `docs/baseline/**` retain their historical bytes. The baseline
register's precedence is historical to its 2026-07-26 snapshot. Neither the
snapshots nor this Markdown document are runtime policy inputs. DOC-001's README
and ignore-rule edits are preserved, not revised by M01-A.

## Logical ownership

| Owner | Responsibility | Excluded authority |
| --- | --- | --- |
| Human researcher | Scientific scope, approved baselines, budgets, consequential approvals | Approval is not inferred from an agent's text |
| Codex Main/Subagents | Native agent loop, reasoning, planning, delegated analysis, explanation | Self-issued Solver Grant, changed frozen criteria, authoritative research verdict |
| GD-CAE | Research contracts, budget/decision governance, independent research verification | Abaqus process creation, AF private state writes, fabricated execution facts |
| AbqJobPilot AF | Plan/Grant/Receipt/Run, authorized execution, process and Solver evidence | Whole-research-goal acceptance or physical validity inferred from job completion |

This is a division of logical responsibilities, not a requirement for three
microservices. ResearchProject persistence, budget enforcement, mutation guards,
and a research verification engine are future work, not M01-A deliverables.

## Complete invariant mapping

| Existing stable ID | Treatment | Current meaning | M01-A enforcement boundary |
| --- | --- | --- | --- |
| `INV-EXEC-001` | Conflicting executor ownership superseded by ADR-003 | Authorized Abaqus production execution belongs to AF, not a new GD-CAE Unified Executor | Continue prohibiting every GD-CAE production subprocess/raw-launcher path |
| `INV-WORKSPACE-001` | Scope revised | Future GD-CAE writes belong to its controlled research storage; AF owns its own writes | No production write capability in the read bridge; research storage not implemented |
| `INV-SOURCE-001` | Retained | Sources and frozen baselines are immutable by default | No mutation API; protected historical bytes retained |
| `INV-LEGACY-001` | Blanket AF prohibition narrowly superseded | Allow only the reviewed AF public read seam; forbid private coupling and all `abqpilot` dependencies | Exact module/location/import checks with negative cases; no dependency or vendoring expansion |
| `INV-ADAPTER-001` | Retained and clarified | A service request is not ownership of process creation or unrestricted writes | Seven fixed reads, no client exposure, raw call, lifecycle action, or dynamic dispatch |
| `INV-LLM-001` | Retained and clarified | Codex is a proposal client, not an authorization or verdict issuer | Read DTOs expose observations only; no Agent/Skill implementation in this stage |
| `INV-VERDICT-001` | Authority scope revised by ADR-004 | AF owns its execution facts; deterministic GD-CAE logic owns future research verdicts | Preserve sourced facts; no new scientific verdict engine |
| `INV-EVIDENCE-001` | Retained | Markdown and presentation outputs are views | Documentation and synthetic-test results do not become physical evidence |
| `INV-FIXTURE-001` | Retained | Synthetic fixtures are not physical evidence | Fake inputs test the read contract only; no real AF or Solver compatibility claim |
| `INV-CWD-001` | Retained | Project/root/instance must be explicit | No default CWD, Recent lookup, auto-creation, or implicit Project fallback |
| `INV-FAILCLOSED-001` | Retained | Unknown identity, protocol, authorization, or required evidence cannot be upgraded to success | Typed failure/incompleteness; no repair, resubmit, retry, or success-shaped truncation |

## Exact source scope

The existing seven namespace files remain. Only these new production modules are
admitted for M01-A:

- `src/aegiscae/contracts/af_evidence.py`: read DTOs, explicit binding and bounded
  contract semantics, standard-library-only dependencies.
- `src/aegiscae/adapters/abaqus/af_evidence.py`: `EvidenceBridge` and the single
  lazy public discovery seam; depends on contracts and the standard library.

Root import and adapter construction must not import AF or discover a Project.
The facade uses only the returned AF client's fixed read methods. Actual live
discovery/IPC is outside this run's test authorization. No new package export,
runtime process manager, database, MCP, Skills, custom Agent configuration, or
execution write API is admitted.

## Architecture-guard migration

M00's exact-empty-tree and blanket-client assertions were milestone scope guards.
They are replaced only as needed for the two modules and single seam above.
Positive allowlist cases must be paired with rejection cases for unexpected
modules, private AF imports, alternate import locations, dynamic imports/raw calls,
hidden writes, subprocesses, and untrusted verdict construction.

Continue baseline integrity, import-direction, fixture-evidence, no-link, explicit
path/CWD, direct-write, and executor prohibitions. Tests must not be disabled or
marked expected-failure to permit the change. Static AST guards are maintainability
and regression checks; they are not a proof against malicious same-user code.

## Evidence status vocabulary

- `SOURCE_VERIFIED`: a source/file property was inspected, not runtime-qualified.
- `HISTORICAL_EVIDENCE`: earlier test/experiment material, not rerun this stage.
- `SYNTHETIC_CONTRACT_PASS`: actual offline contract tests passed, once recorded.
- `AF_READ_COMPATIBILITY_VERIFIED`: separate isolated M01-B live compatibility
  evidence; not conferred by M01-A.
- `NOT_VERIFIED`: required real evidence has not been obtained.
- `PROPOSED`: later work requiring its own approval.

The M00-P report exists in the original conversation. No file with that report is
asserted to exist here. The [M01 read contract](M01_EVIDENCE_BRIDGE.md) defines the
bounded interface; the delivery report must separately state real commands,
results, limitations, and unchanged protected files.
