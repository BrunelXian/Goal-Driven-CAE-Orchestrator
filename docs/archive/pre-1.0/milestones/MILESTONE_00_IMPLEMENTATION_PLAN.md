# AegisCAE Runtime — Milestone 0 Implementation Plan

> Relocation note (2026-07-26): 本文件从规划阶段文件整理进入
> `docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md`，不改变 Runtime-first、
> selective migration 或 Batch 边界。

```text
document: docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md
project: AegisCAE Runtime
milestone: Milestone 0 — Architecture Freeze and New Repository
status: IMPLEMENTATION_PLAN_READY
scope: architecture, repository bootstrap, package skeleton, CI architecture guards, test skeleton, Git history
out of scope: runtime implementation, legacy code migration, Abaqus execution, MCP, Skill, GUI, queue, real solver integration
baseline precedence: LEGACY_MIGRATION_DECISIONS.md overrides the other three baseline documents where conflict exists
```

---

## 1. Executive Decision

Milestone 0 shall create a **new and independent repository** named:

```text
AegisCAE-Runtime
```

The installable Python distribution and import package shall be:

```text
distribution name: aegiscae
Python package:    aegiscae
```

The first solver-specific namespace shall be reserved as:

```text
aegiscae.adapters.abaqus
```

Milestone 0 does **not** implement Runtime Core behavior. It freezes ownership, dependency direction, prohibited paths, repository structure, architecture tests, and the legacy migration boundary. Package files created in this milestone are namespace markers only; they must not contain execution, validation, mutation, workflow, queue, evidence, or Abaqus logic.

The repository must not depend on, import, vendor, or invoke either legacy package:

```text
abqjobpilot
abqpilot
```

The only permitted use of the legacy projects during Milestone 0 is as read-only architectural evidence represented by the four authoritative baseline documents.

---

## 2. Authoritative Baseline and Precedence

### 2.1 Baseline documents

Milestone 0 is governed by these four documents:

1. `AegisCAE Runtime 项目计划书.md`
2. `LEGACY_ABQJOBPILOT_SUMMARY.md`
3. `LEGACY_ABQPILOT_SUMMARY.md`
4. `LEGACY_MIGRATION_DECISIONS.md`

### 2.2 Precedence rule

Where wording, sequencing, ownership, or scope differs, apply this order:

```text
LEGACY_MIGRATION_DECISIONS.md
    > AegisCAE Runtime 项目计划书.md
    > legacy summaries as evidence of historical implementation
```

The two legacy summaries describe what the old repositories contain; they do not authorize migration. `LEGACY_MIGRATION_DECISIONS.md` is the final authority for KEEP / REFACTOR / REPLACE / DO NOT MIGRATE decisions.

### 2.3 Baseline preservation in the new repository

Milestone 0 shall preserve the four documents as immutable documentation snapshots under:

```text
docs/baseline/
```

A `BASELINE_REGISTER.md` shall record:

- canonical filename;
- document role;
- precedence rank;
- SHA-256 hash of the copied snapshot;
- snapshot date;
- statement that the files are documentation evidence, not runtime inputs;
- statement that later edits require a new decision record rather than silent replacement.

Copying these four documentation files is not legacy code migration and must not be used as a route to copy source trees, tests, runtime state, fixtures, or generated artifacts.

---

## 3. Resolved Conflicts and Ambiguities

The following differences exist among the baseline documents. This plan resolves them according to the final migration decision.

| Topic | Earlier baseline position | Final decision / resolution for Milestone 0 |
|---|---|---|
| New project location | The project plan allowed “a new repository or a new top-level package.” | Create a completely independent repository. A new package inside either legacy repository is prohibited. |
| Repository name | The final migration document left the exact GitHub slug as an open question while recommending `AegisCAE-Runtime`. | Freeze the repository slug as `AegisCAE-Runtime` for Milestone 0. Local filesystem path and hosting organization remain environment configuration, not architecture. |
| Compatibility namespace | The project plan visually included an `abqpilot` compatibility package. | Do not create `abqpilot` compatibility imports in Milestone 0–2. Reconsider only after the Abaqus adapter is stable and an ADR approves the compatibility surface. |
| MCP surface | The project plan’s illustrative interface tree included `mcp.py`. | Do not create MCP code or an MCP placeholder module. MCP is deferred until the Python API and JSON CLI schemas are stable. |
| JSON CLI timing | The project plan presented JSON CLI as part of the general interface. | Create only the `interfaces` namespace in Milestone 0. JSON CLI implementation is deferred to Batch 7. |
| Legacy “preserved capabilities” | The project plan listed evidence report and fixed pipeline among capabilities to preserve. | Preserve only concepts and test intent. Replace legacy evidence authority; defer fixed-pipeline compatibility; migrate neither in Milestone 0. |
| Migration document naming | The project plan named `MIGRATION_FROM_ABQPILOT.md`, although two legacy projects are now authoritative inputs. | Use `MIGRATION_FROM_LEGACY.md` for the operational policy and retain the final decision document verbatim under `docs/baseline/LEGACY_MIGRATION_DECISIONS.md`. |
| Runtime Foundation PR | It could appear to be the natural starting implementation. | Do not merge it into legacy main and do not copy it wholesale. It is a read-only design seed for Batch 1. |
| Milestone sequencing | The project plan grouped Tool Registry, authorization, workflow, and evidence differently from the final migration batches. | Follow the final migration batch order. Milestone 0 creates no functional implementation of these modules. |
| Validator placement | The project plan displayed Validator inside Runtime Core, while the target structure separates `validation/`. | Generic deterministic validation contracts live in `aegiscae.validation`; Runtime owns orchestration and final authority; adapter-specific validators stay inside the adapter. |
| Queue priority | AbqJobPilot provides queue semantics and the project plan discusses session management. | No generic queue subsystem in Milestone 0–2. Local sequential workflow is considered only after the control plane exists. |
| Rollback | Legacy material used rollback terminology. | Do not create a generic rollback subsystem. The governing strategy is immutable source, staging, checkpoint, atomic promotion, and quarantine. |

No other material conflict affects Milestone 0. Differences in legacy test counts, repository state, and implementation maturity are historical evidence rather than competing architectural requirements.

---

## 4. Milestone 0 Objectives

Milestone 0 shall produce five outcomes:

1. **Independent identity** — a new repository and the `aegiscae` package exist without legacy imports or dependencies.
2. **Frozen architecture** — ownership boundaries, dependency direction, trust boundaries, and non-negotiable invariants are documented.
3. **Executable architecture policy** — CI contains static guards that reject prohibited imports, calls, paths, and package surfaces.
4. **Reviewable development boundary** — the package skeleton is intentionally empty and cannot be mistaken for implemented Runtime capability.
5. **Clean Git baseline** — repository history separates bootstrap, architecture decisions, and CI guards into reviewable commits.

Milestone 0 is complete only when these outcomes are simultaneously true. A directory tree alone is not sufficient.

---

## 5. Repository and Package Naming

### 5.1 Repository

```text
canonical repository slug: AegisCAE-Runtime
default branch: main
legacy repository relationship: none
```

The repository remote must not point to either legacy repository and must not share their Git history.

### 5.2 Python package

```text
project/distribution name: aegiscae
import root: aegiscae
minimum Python: 3.11
supported Milestone 0 CI versions: 3.11 and 3.12
```

Python 3.11 is selected as the minimum for modern typing and dataclass support while remaining compatible with the project’s known Python 3.11 and 3.12 environments. Changing the minimum version later requires an ADR because it affects contracts, packaging, and test environments.

### 5.3 Names explicitly not used

The following must not be used as the new repository or root package:

```text
AbqPilot
AbqPilot-v2
AbqJobPilot
abqpilot
abqjobpilot
```

These names may appear only in baseline documentation, migration provenance, tests that enforce prohibition, or a future separately approved compatibility layer.

---

## 6. First-Version Directory Structure

The Milestone 0 repository shall have this structure:

```text
AegisCAE-Runtime/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── adr/
│   │   ├── ADR-001-runtime-first.md
│   │   ├── ADR-002-legacy-selective-migration.md
│   │   └── README.md
│   ├── baseline/
│   │   ├── AegisCAE Runtime 项目计划书.md
│   │   ├── LEGACY_ABQJOBPILOT_SUMMARY.md
│   │   ├── LEGACY_ABQPILOT_SUMMARY.md
│   │   ├── LEGACY_MIGRATION_DECISIONS.md
│   │   └── BASELINE_REGISTER.md
│   └── milestones/
│       └── MILESTONE_00_IMPLEMENTATION_PLAN.md
├── src/
│   └── aegiscae/
│       ├── __init__.py
│       ├── contracts/
│       │   └── __init__.py
│       ├── runtime/
│       │   └── __init__.py
│       ├── validation/
│       │   └── __init__.py
│       ├── interfaces/
│       │   └── __init__.py
│       └── adapters/
│           ├── __init__.py
│           └── abaqus/
│               └── __init__.py
├── tests/
│   ├── architecture/
│   │   ├── test_baseline_integrity.py
│   │   ├── test_dependency_direction.py
│   │   ├── test_fixture_evidence_policy.py
│   │   ├── test_forbidden_direct_writes.py
│   │   ├── test_forbidden_execution_calls.py
│   │   ├── test_forbidden_legacy_dependencies.py
│   │   ├── test_forbidden_paths_and_cwd.py
│   │   ├── test_forbidden_surfaces.py
│   │   ├── test_no_symlinks.py
│   │   ├── test_package_skeleton.py
│   │   └── test_verdict_authority.py
│   ├── unit/
│   │   └── test_package_import.py
│   ├── integration/
│   │   └── README.md
│   ├── fixtures/
│   │   └── README.md
│   └── conftest.py
├── .editorconfig
├── .gitignore
├── ARCHITECTURE.md
├── MIGRATION_FROM_LEGACY.md
├── README.md
├── RUNTIME_INVARIANTS.md
├── THREAT_MODEL.md
└── pyproject.toml
```

### 6.1 Deliberately absent directories and files

Milestone 0 must not create:

```text
src/aegiscae/runtime/context.py
src/aegiscae/runtime/workspace.py
src/aegiscae/runtime/executor.py
src/aegiscae/runtime/authorization.py
src/aegiscae/runtime/registry.py
src/aegiscae/runtime/workflow.py
src/aegiscae/runtime/evidence.py
src/aegiscae/interfaces/json_cli.py
src/aegiscae/interfaces/mcp.py
src/aegiscae/legacy_compat/
src/abqpilot/
src/abqjobpilot/
gui/
skills/
mcp/
queue/
```

Those names would falsely imply implementation or prematurely establish contracts. The only Python files in `src/` during the first Codex batch are package markers.

---

## 7. Dependency Direction and Ownership

### 7.1 Import graph

In the diagram below, `A → B` means “A may import B.”

```text
contracts → Python standard library only

validation → contracts
runtime    → contracts, validation public contracts
adapter    → contracts, validation public contracts
interfaces → contracts, runtime public facade
composition root (future) → runtime public facade, concrete adapters
```

The corresponding forbidden directions are:

```text
contracts -X-> runtime / validation / adapters / interfaces
validation -X-> runtime internals / adapters / interfaces
runtime    -X-> concrete adapters / interfaces / clients / LLM
adapter    -X-> interfaces / runtime internals / executor launcher
interfaces -X-> runtime private internals
```

### 7.2 Runtime Core

Runtime Core owns:

- context and identity;
- session/run lifecycle;
- workspace authorization;
- risk policy;
- authorization lifecycle;
- tool registration;
- plan and state machine;
- external process execution;
- checkpoint, staging, promotion, and quarantine;
- artifact provenance;
- event ledger and evidence freeze;
- final machine authority.

Runtime Core must be solver-neutral. It must not import `aegiscae.adapters.abaqus` or contain Abaqus command syntax, file extensions, field names, or solver log patterns.

### 7.3 Validation

`aegiscae.validation` owns generic deterministic result types and validation protocols for:

- execution integrity;
- artifact provenance;
- required output contracts;
- physics plausibility severity.

It does not own Abaqus-specific parsing or thresholds. Abaqus-specific rules belong under `aegiscae.adapters.abaqus` and return generic validation result contracts.

Validation cannot execute processes, authorize work, write evidence, or promote artifacts.

### 7.4 Interfaces

Interfaces are clients of Runtime, not security boundaries. The namespace is reserved in Milestone 0, but no Python API facade, JSON CLI, MCP, Skill, or GUI is implemented.

When implemented later, interfaces may submit structured requests and render structured results. They must not:

- create authorization validity;
- resolve unrestricted paths;
- invoke the raw launcher;
- create or override machine verdicts;
- write source, output, or evidence directly.

### 7.5 Abaqus Adapter

The Abaqus adapter owns only Abaqus domain semantics, including future command plans, INP inspection, CAE/ODB bridge plans, job log diagnosis, field contracts, and Abaqus-specific validation.

The adapter must return structured requests, plans, or results. It may never:

- call `subprocess`, `os.system`, shell APIs, or a public process launcher;
- perform production writes directly;
- import Runtime private execution or workspace internals;
- authorize execution;
- freeze evidence;
- declare final Runtime acceptance.

### 7.6 Composition boundary

A future composition root will register concrete adapter handlers with Runtime through public contracts. This is the only permitted location where Runtime and concrete adapters are assembled. Runtime modules themselves remain unaware of concrete adapters.

The composition root is not created in Milestone 0 because the registry and public facade do not yet exist.

---

## 8. Milestone 0 File Creation Matrix

### 8.1 Root governance and architecture files

| File | Purpose | Minimum content requirement |
|---|---|---|
| `README.md` | Identify the project without overstating capability. | Project definition; Milestone 0 status; explicit “no runtime implementation yet”; links to architecture, invariants, threat model, migration plan, and ADRs; no claims of Abaqus execution. |
| `ARCHITECTURE.md` | Freeze ownership and dependency direction. | System boundary; module ownership; import graph; trust boundaries; composition rule; lifecycle target; architecture changes requiring ADR. |
| `RUNTIME_INVARIANTS.md` | State non-negotiable machine-enforced rules. | Unique executor; unique workspace write authority; immutable source; deterministic verdict authority; LLM non-authority; no legacy dependency; no implicit CWD; no fixture-as-evidence; fail-closed rule. Each invariant requires a stable ID such as `INV-EXEC-001`. |
| `THREAT_MODEL.md` | Define what the runtime must defend against. | Assets, actors, trust boundaries, misuse cases, directory escape, symlink escape, stale/wrong artifacts, command injection, authorization reuse, report/verdict spoofing, legacy bypass, LLM overreach, fixture confusion, and deferred mitigations by Batch. |
| `MIGRATION_FROM_LEGACY.md` | Convert migration decisions into an operational extraction policy. | Legacy roles; KEEP/REFACTOR/REPLACE/DO NOT MIGRATE summary; code provenance requirements; extraction checklist; prohibition on direct dependency and whole-repository copy; no extraction in Milestone 0. |
| `docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md` | Control execution of this milestone. | The complete content defined by this document; status updated only through reviewed commits. |
| `pyproject.toml` | Establish package identity and development tooling. | Project `aegiscae`; Python `>=3.11,<4`; `src` layout; no runtime dependencies; development extras limited to test/lint tooling; pytest and Ruff configuration; no legacy packages; no console scripts. |
| `.gitignore` | Prevent environment and generated state entering source control. | Python caches, virtual environments, build output, test caches, IDE state, local runtime/output/evidence directories, Abaqus generated artifacts (`*.odb`, `*.sim`, `*.sta`, `*.msg`, `*.dat`, `*.lck`, `*.jnl`, `*.cae`), while not ignoring deliberate test fixtures by broad unsafe rules. |
| `.editorconfig` | Normalize text handling. | UTF-8, LF, final newline, spaces, Markdown whitespace policy, Python indentation. |

### 8.2 ADR files

| File | Purpose | Minimum content requirement |
|---|---|---|
| `docs/adr/README.md` | Define the ADR process. | Status values; numbering; immutability rule; superseding process; decision template; ADR-required change categories. |
| `docs/adr/ADR-001-runtime-first.md` | Freeze the runtime-first decision. | Context; decision; consequences; rejected alternatives; prohibition on adapter-first construction; relationship to immutable source and deterministic authority. |
| `docs/adr/ADR-002-legacy-selective-migration.md` | Freeze selective extraction. | No direct dependency; no wholesale copy; legacy project roles; Runtime Foundation PR treatment; code provenance; compatibility deferral. |

### 8.3 Baseline files

| File | Purpose | Minimum content requirement |
|---|---|---|
| `docs/baseline/BASELINE_REGISTER.md` | Make baseline provenance explicit. | Four filenames, precedence, SHA-256, snapshot date, copy method, no-runtime-input statement, change policy. |
| `docs/baseline/AegisCAE Runtime 项目计划书.md` | Preserve project intent. | Verbatim snapshot; no editorial changes. |
| `docs/baseline/LEGACY_ABQJOBPILOT_SUMMARY.md` | Preserve AbqJobPilot audit evidence. | Verbatim snapshot; no code import or generated data. |
| `docs/baseline/LEGACY_ABQPILOT_SUMMARY.md` | Preserve AbqPilot audit evidence. | Verbatim snapshot; no code import or generated data. |
| `docs/baseline/LEGACY_MIGRATION_DECISIONS.md` | Preserve final migration authority. | Verbatim snapshot with canonical filename; highest precedence clearly registered. |

### 8.4 Package markers

Every `__init__.py` in Milestone 0 must contain only a concise package docstring. The root package may additionally expose a static pre-release version string if versioning is configured centrally. It must not import sibling packages, auto-register adapters, inspect the environment, resolve paths, or create global state.

| File | Purpose | Minimum content requirement |
|---|---|---|
| `src/aegiscae/__init__.py` | Declare the root package. | Package docstring; optional static version only; no eager imports. |
| `src/aegiscae/contracts/__init__.py` | Reserve solver-neutral contracts. | Docstring stating that implementation begins in later Batch; no schemas yet. |
| `src/aegiscae/runtime/__init__.py` | Reserve Runtime Core. | Docstring stating ownership and no implementation yet; no public exports. |
| `src/aegiscae/validation/__init__.py` | Reserve generic validation. | Docstring stating deterministic generic role; no verdict definitions yet. |
| `src/aegiscae/interfaces/__init__.py` | Reserve client interfaces. | Docstring stating interfaces are not security boundaries; no CLI/MCP code. |
| `src/aegiscae/adapters/__init__.py` | Reserve solver adapter namespace. | Docstring only; no discovery or dynamic imports. |
| `src/aegiscae/adapters/abaqus/__init__.py` | Reserve the first adapter namespace. | Docstring only; no Abaqus command, import, executable path, or legacy alias. |

### 8.5 Tests and CI files

| File | Purpose | Minimum content requirement |
|---|---|---|
| `tests/conftest.py` | Provide repository-root and source-tree helpers for architecture tests. | Read-only helpers only; no mutation of user files; no environment-specific absolute paths. |
| `tests/unit/test_package_import.py` | Confirm the empty package can be installed/imported. | Import `aegiscae`; assert no legacy package is imported as a side effect. |
| `tests/architecture/test_package_skeleton.py` | Freeze the exact M0 package surface. | Assert required directories/files exist and forbidden implementation modules do not exist. |
| `tests/architecture/test_baseline_integrity.py` | Protect authoritative documentation snapshots. | Recompute the four SHA-256 hashes; verify canonical filenames and precedence; reject unregistered baseline changes. |
| `tests/architecture/test_forbidden_legacy_dependencies.py` | Prevent dependency or import of legacy packages. | Inspect `pyproject.toml` and AST imports for `abqpilot` and `abqjobpilot`; documentation and test string exemptions must be narrow. |
| `tests/architecture/test_forbidden_execution_calls.py` | Prevent early or bypass execution paths. | AST scan for `subprocess`, `os.system`, `os.popen`, `asyncio.create_subprocess_*`, `multiprocessing` process launch, shell invocation, and public raw launcher names; Milestone 0 allowlist is empty. |
| `tests/architecture/test_forbidden_direct_writes.py` | Enforce the future single write authority. | AST scan for production write primitives; Milestone 0 allowlist is empty; later exception may name only the private ControlledWorkspace implementation. |
| `tests/architecture/test_dependency_direction.py` | Enforce the import DAG. | AST-based package import checks matching Section 7; fail on runtime→adapter/interface, adapter→runtime internals, and validation→adapter/interface. |
| `tests/architecture/test_forbidden_paths_and_cwd.py` | Reject hidden environment coupling. | Detect `Path.cwd`, `os.getcwd`, drive-letter literals, user-home literals, and known legacy repository roots in production source. |
| `tests/architecture/test_forbidden_surfaces.py` | Keep deferred features out of scope. | Fail if source packages/modules named `mcp`, `skill`, `gui`, `llm`, `queue`, or `legacy_compat` appear before an ADR and milestone update. |
| `tests/architecture/test_verdict_authority.py` | Prevent presentation/client layers creating machine truth. | Reject machine-verdict definitions or assignments in interfaces, reports, clients, docs generators, and future LLM surfaces; allow only contract references. |
| `tests/architecture/test_fixture_evidence_policy.py` | Prevent fixture-as-evidence claims. | Verify fixture policy exists and reject fixture metadata or names that claim real physical evidence eligibility by default. |
| `tests/architecture/test_no_symlinks.py` | Prevent repository-level path ambiguity. | Reject symlinks under `src/`, `tests/fixtures/`, and `docs/baseline/` in Milestone 0. |
| `tests/fixtures/README.md` | Prevent fixture confusion. | State that fixtures are synthetic/non-physical test inputs and can never be cited as real Abaqus or physical evidence. |
| `tests/integration/README.md` | Reserve integration-test policy. | State that Milestone 0 has no integration test and no external process; later tests require explicit marker and isolated environment. |
| `.github/workflows/ci.yml` | Run architecture policy on every change. | Windows and Ubuntu matrix; Python 3.11/3.12; install project with dev test tools; run Ruff and pytest; no Abaqus, network service, legacy checkout, or secret requirement. |

---

## 9. Prohibited Dependencies and Calls

### 9.1 Dependency prohibitions

The following are prohibited in `pyproject.toml`, lock files, editable installs, Git submodules, vendored directories, and runtime imports:

```text
abqpilot
abqjobpilot
BrunelXian/AbqPilot
BrunelXian/abq_job_pilot
local path dependencies pointing to either legacy repository
Git dependencies pointing to either legacy repository
```

Milestone 0 runtime dependencies must be empty. Test/lint tooling is development-only and must not become runtime authority.

### 9.2 Process execution prohibitions

No production source file may use or wrap:

```text
subprocess.run
subprocess.Popen
subprocess.call
subprocess.check_call
subprocess.check_output
os.system
os.popen
asyncio.create_subprocess_exec
asyncio.create_subprocess_shell
multiprocessing.Process for external execution
shell=True
```

Milestone 0 has no exception. Batch 1 may introduce exactly one private raw process launcher behind `UnifiedExecutor`; the architecture test allowlist must then name that private file explicitly and continue to reject all other call sites.

### 9.3 File write prohibitions

Milestone 0 package markers must not write files. In later batches, production writes are permitted only through `ControlledWorkspace` public methods. Direct use of the following outside the private workspace storage implementation must be rejected:

```text
open(..., write/append/create mode)
Path.write_text
Path.write_bytes
Path.touch
Path.mkdir for production run trees
shutil.copy/copy2/copytree/move
os.replace/rename/remove/unlink
```

Tests may write only inside framework-provided temporary directories.

### 9.4 Path and environment prohibitions

Production code must not use:

- implicit current working directory;
- hard-coded drive letters or user-home paths;
- known old repository roots;
- scattered environment-variable reads;
- unrestricted external absolute paths;
- symlink-following without workspace verification.

Configuration and paths will later enter through versioned Runtime contracts, not module globals.

### 9.5 Authority prohibitions

No adapter, interface, report, Markdown generator, fixture, GUI, Skill, MCP layer, or LLM client may:

- create `AUTHORIZED`;
- declare execution complete without Executor evidence;
- declare ODB valid;
- create final physics acceptance;
- freeze evidence;
- rewrite a Validator result;
- promote or delete source artifacts.

### 9.6 Scope prohibitions

Milestone 0 must not add:

- dynamic plugin discovery;
- generic Agent framework;
- queue worker;
- persistent job queue;
- network server;
- database;
- solver license scheduler;
- real CAE/ODB file handlers;
- generated Abaqus scripts;
- example code copied from legacy modules.

---

## 10. CI Architecture Guards

### 10.1 Required CI jobs

The initial CI workflow shall run on:

```text
operating systems: ubuntu-latest, windows-latest
Python versions:   3.11, 3.12
```

Each matrix job performs:

1. clean checkout;
2. Python setup;
3. editable install with development extras;
4. `ruff check .`;
5. `pytest -q`;
6. verification that the working tree remains clean after tests.

CI must not install Abaqus, access the legacy repositories, use network services beyond package installation, or run external solver commands.

### 10.2 Guard implementation strategy

Architecture guards shall use Python AST and repository metadata rather than fragile text-only searches wherever possible.

Required checks:

1. import DAG compliance;
2. no legacy dependency/import;
3. no process execution call;
4. no direct production write primitive;
5. no implicit CWD;
6. no hard-coded user/repository absolute path;
7. no deferred package surface;
8. package skeleton matches Milestone 0;
9. baseline register contains four hashes;
10. test fixtures carry non-physical evidence warning;
11. no symlink exists under `src/` or baseline snapshots;
12. package import has no side effects.

### 10.3 Guard evolution rule

Architecture guards are deny-by-default. A later Batch may narrow an exception only when all of the following are present:

- an approved ADR;
- a specific private implementation path;
- a positive test for the new sanctioned path;
- a negative test proving all bypass paths remain rejected;
- an update to `RUNTIME_INVARIANTS.md` when the invariant representation changes.

Broad directory exemptions are prohibited.

---

## 11. Test Skeleton

### 11.1 Milestone 0 tests

Milestone 0 tests verify architecture and packaging only. They do not claim Runtime functionality.

```text
tests/unit/
  package import and side-effect checks

tests/architecture/
  repository structure
  dependency direction
  execution prohibition
  write/path/CWD prohibition
  legacy dependency prohibition
  deferred-surface prohibition
```

### 11.2 Test categories reserved for later batches

The following test families are documented but empty in Milestone 0:

```text
unit runtime-contract tests
property tests for path resolution
mock-executor tests
adapter pure-function tests
artifact provenance tests
workflow recovery tests
Abaqus read-only environment tests
real solver integration tests
```

### 11.3 Fixture policy

Any later fixture must carry metadata that distinguishes:

```text
synthetic fixture
legacy captured sample
mock solver output
real solver artifact
physical evidence eligible / ineligible
```

The default is `physical evidence eligible: NO`. A test cannot change this classification.

### 11.4 No-execution guarantee

The Milestone 0 test suite must be safe to run on a machine with Abaqus installed. It must not discover, probe, launch, or inspect Abaqus executables and must not read any legacy runtime directories.

---

## 12. Git Initialization and Commit Structure

### 12.1 Repository initialization

The repository shall be initialized independently:

```text
git init -b main
```

Before the first commit, verify:

- no `.git` directory was copied from a legacy repository;
- no legacy remote is configured;
- no source or test file was copied from a legacy repository;
- only the four approved baseline documentation snapshots were copied;
- all package markers are newly authored;
- all paths are repository-relative.

### 12.2 Initial commit series

Milestone 0 shall use three commits, each reviewable on its own.

#### Commit 1 — Repository identity and empty package skeleton

```text
chore(repo): initialize independent AegisCAE Runtime skeleton
```

Contains:

- `.gitignore`;
- `.editorconfig`;
- `pyproject.toml`;
- root `README.md` in bootstrap form;
- `src/aegiscae/**/__init__.py` package markers;
- `tests/unit/test_package_import.py`;
- `tests/fixtures/README.md`;
- `tests/integration/README.md`.

Must not contain architecture implementation modules.

#### Commit 2 — Architecture freeze and baseline decisions

```text
docs(architecture): freeze runtime and legacy migration boundaries
```

Contains:

- `ARCHITECTURE.md`;
- `RUNTIME_INVARIANTS.md`;
- `THREAT_MODEL.md`;
- `MIGRATION_FROM_LEGACY.md`;
- `docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md`;
- ADR files;
- four baseline snapshots;
- `BASELINE_REGISTER.md` with hashes;
- final update to root `README.md` links/status.

#### Commit 3 — Architecture guards and CI

```text
test(architecture): enforce Milestone 0 boundaries in CI
```

Contains:

- `tests/conftest.py`;
- all `tests/architecture/*.py` files;
- `.github/workflows/ci.yml`;
- any test/lint configuration updates required in `pyproject.toml`.

### 12.3 Commit hygiene

Each commit must satisfy:

- no generated build output;
- no Abaqus artifact;
- no local environment path;
- no secret;
- no unrelated file;
- no legacy code;
- tests applicable to that commit pass;
- working tree clean after commit.

### 12.4 Milestone freeze tag

After all acceptance checks pass, create an annotated tag:

```text
milestone-0-architecture-freeze
```

The tag message must record:

- repository name;
- package name;
- baseline decision hash/register state;
- CI result;
- final Milestone 0 verdict;
- explicit statement that no Runtime Core or Abaqus capability exists yet.

Do not create a semantic production release at Milestone 0.

---

## 13. Milestone 0 Acceptance Checklist

### 13.1 Repository identity

- [ ] Repository is named `AegisCAE-Runtime`.
- [ ] Default branch is `main`.
- [ ] Git history is new and does not share legacy commits.
- [ ] No legacy remote, submodule, subtree, or path dependency exists.
- [ ] Package distribution and import name are `aegiscae`.

### 13.2 Architecture freeze

- [ ] `ARCHITECTURE.md` defines ownership and import direction.
- [ ] `RUNTIME_INVARIANTS.md` assigns stable IDs to mandatory invariants.
- [ ] `THREAT_MODEL.md` covers process, path, artifact, authority, LLM, and legacy bypass risks.
- [ ] ADR-001 and ADR-002 are accepted.
- [ ] Conflicts listed in Section 3 are reflected consistently across documents.

### 13.3 Baseline provenance

- [ ] All four authoritative documents are present under `docs/baseline/`.
- [ ] Copies are verbatim and use canonical filenames.
- [ ] `BASELINE_REGISTER.md` contains SHA-256 values and precedence.
- [ ] No baseline document is imported or parsed at runtime.

### 13.4 Package skeleton

- [ ] Exact namespaces in Section 6 exist.
- [ ] `__init__.py` files contain docstrings only, except optional static version metadata.
- [ ] No functional Runtime, Validator, Interface, Adapter, or compatibility module exists.
- [ ] `import aegiscae` has no side effect.

### 13.5 Prohibited paths and dependencies

- [ ] No `abqpilot` or `abqjobpilot` dependency/import exists.
- [ ] No production subprocess or shell call exists.
- [ ] No production write primitive exists in `src/`.
- [ ] No implicit CWD or hard-coded user/repository absolute path exists.
- [ ] No MCP, Skill, GUI, LLM, queue, or compatibility package exists.
- [ ] No test fixture is described as physical evidence.

### 13.6 CI and tests

- [ ] Ruff passes.
- [ ] Unit import test passes.
- [ ] All architecture guards pass.
- [ ] Tests leave the working tree clean.
- [ ] CI passes on Windows and Ubuntu for Python 3.11 and 3.12.
- [ ] CI performs no Abaqus or legacy repository action.

### 13.7 Git history

- [ ] Three-commit structure matches Section 12.
- [ ] Commit file sets are exact and reviewable.
- [ ] Working tree is clean.
- [ ] Annotated freeze tag exists only after CI passes.

### 13.8 Final machine-readable milestone verdict

The Milestone 0 review report must end with exactly one of:

```text
PASS_MILESTONE_0_ARCHITECTURE_FREEZE_COMPLETE
WARNING_MILESTONE_0_REQUIRES_MANUAL_REVIEW
FAIL_MILESTONE_0_ARCHITECTURE_FREEZE_INCOMPLETE
```

A Markdown verdict is a milestone review label only. It is not a CAE execution, ODB, physics, or evidence-freeze verdict.

---

## 14. Content Deferred to Later Batches

### Batch 1 — Runtime Control Plane

Deferred implementation:

- `AegisContext`;
- `ControlledWorkspace`;
- risk policy;
- authorization lifecycle;
- `UnifiedExecutor` and its single private launcher;
- event ledger foundation;
- mock executable tests;
- traversal, symlink, source immutability, authorization consumption tests.

No legacy code is copied before these contracts exist.

### Batch 2 — Pure Abaqus Contracts and Diagnostics

Deferred implementation:

- Abaqus command plan contracts;
- datacheck/full-run semantics;
- latest-attempt parser;
- fatal/success diagnosis taxonomy;
- INP inspection;
- deterministic validator extraction;
- reason codes and evidence spans.

This is the earliest Batch permitted to selectively extract legacy domain logic.

### Batch 3 — Abaqus Job Lifecycle Adapter

Deferred implementation:

- job identity;
- solver preflight plan;
- monitoring;
- adapter artifact discovery;
- controlled Executor integration using mocks;
- timeout/cancel/restart behavior.

### Batch 4 — ODB Provenance and Extraction

Deferred implementation:

- ODB readability;
- stale/wrong-job/corrupt artifact rejection;
- step/frame/field contracts;
- read-only extraction;
- provenance binding.

### Batch 5 — Controlled CAE/INP Mutation

Deferred implementation:

- immutable-source cloning;
- controlled patching;
- CAE export plan;
- DiffGuard/PhysicsGuard/model-condition preservation;
- checkpoint, quarantine, and atomic promotion.

### Batch 6 — Session, Workflow, Artifacts, and Evidence

Deferred implementation:

- resumable workflow;
- structured plan and state machine;
- out-of-plan rejection;
- artifact registry/provenance store;
- append-only evidence ledger;
- hash manifest and mutation detection;
- final machine verdict derivation.

### Batch 7 — Interfaces and Compatibility

Deferred implementation:

- Python public facade;
- JSON CLI;
- deterministic exit codes;
- optional legacy command compatibility that creates requests only.

### Batch 8 — Intelligent Clients

Deferred implementation:

- Codex Skill;
- optional MCP adapter;
- model-client integration tests;
- read-only UI planning.

### Additional deferred architectural decisions

The following require later ADRs and are not implicitly decided by Milestone 0:

- authorization storage or signing mechanism;
- evidence ledger backend: JSONL, SQLite, or hybrid;
- persistent queue need and design;
- Abaqus license-aware admission;
- physics rule serialization/versioning;
- `abqpilot` compatibility import;
- repository license;
- public release/versioning policy;
- real Abaqus fixture ownership and private test environment;
- first production Abaqus domain profile beyond generic job/ODB lifecycle.

---

## 15. First Codex Development Batch — Exact Boundary

### 15.1 Batch identifier

```text
M0-BATCH-01_REPOSITORY_AND_ARCHITECTURE_SKELETON
```

### 15.2 Objective

Create the independent repository identity, documentation baseline, empty namespace skeleton, and only the minimum import smoke test. This batch must not implement architecture guards or CI; those are reviewed separately in the next Milestone 0 batch.

### 15.3 Allowed file set

Codex may create or modify only the following paths:

```text
.gitignore
.editorconfig
pyproject.toml
README.md
ARCHITECTURE.md
RUNTIME_INVARIANTS.md
THREAT_MODEL.md
MIGRATION_FROM_LEGACY.md
docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md

docs/adr/README.md
docs/adr/ADR-001-runtime-first.md
docs/adr/ADR-002-legacy-selective-migration.md

docs/baseline/AegisCAE Runtime 项目计划书.md
docs/baseline/LEGACY_ABQJOBPILOT_SUMMARY.md
docs/baseline/LEGACY_ABQPILOT_SUMMARY.md
docs/baseline/LEGACY_MIGRATION_DECISIONS.md
docs/baseline/BASELINE_REGISTER.md

src/aegiscae/__init__.py
src/aegiscae/contracts/__init__.py
src/aegiscae/runtime/__init__.py
src/aegiscae/validation/__init__.py
src/aegiscae/interfaces/__init__.py
src/aegiscae/adapters/__init__.py
src/aegiscae/adapters/abaqus/__init__.py

tests/unit/test_package_import.py
tests/fixtures/README.md
tests/integration/README.md
```

No other file is permitted in Batch 01.

### 15.4 Allowed operations

Codex may:

- initialize a new Git repository at the user-designated empty root;
- create the listed directories and files;
- copy the four supplied baseline Markdown documents verbatim into `docs/baseline/`;
- calculate and record SHA-256 hashes for those copied documents;
- create package markers containing docstrings only;
- configure package metadata and development test/lint dependencies;
- run offline import, packaging, and text-validation checks limited to the new repository;
- create the first two commits described in Section 12 only if the user’s execution prompt explicitly authorizes commits.

### 15.5 Forbidden operations

Codex must not:

- open, edit, stage, commit, clean, checkout, merge, or otherwise modify either legacy repository;
- copy any legacy `.py`, test, fixture, runtime, output, evidence, Git metadata, or generated artifact;
- inspect or execute Abaqus;
- create any functional Runtime or adapter class/function;
- create architecture guard test files or CI workflow in this batch;
- add MCP, Skill, GUI, LLM, queue, JSON CLI, compatibility package, database, network, or solver code;
- add a raw launcher, subprocess wrapper, file writer, path resolver, authorization stub, fake PASS verdict, or placeholder rollback;
- infer unsupported capability from the baseline documents;
- create a remote or push unless separately and explicitly instructed.

### 15.6 Required Batch 01 checks

Before reporting completion, Codex must verify:

```text
repository root is the new root: YES
legacy repository files modified: 0
legacy code files copied: 0
Abaqus executed: NO
subprocess calls in src: 0
production file writes in src: 0
legacy imports/dependencies: 0
functional runtime modules created: 0
baseline documents copied: 4
baseline SHA-256 entries recorded: 4
package import smoke test: PASS
working tree scope matches allowed file set: YES
```

### 15.7 Required Batch 01 report

The final report must include:

- repository root;
- current branch;
- created file count and exact list;
- baseline source/destination/hash table;
- package name and Python requirement;
- test command and result;
- prohibited-operation counts;
- Git status;
- commit hashes if commits were explicitly authorized;
- final verdict.

Allowed final verdicts:

```text
PASS_M0_BATCH_01_REPOSITORY_AND_ARCHITECTURE_SKELETON_COMPLETE
WARNING_M0_BATCH_01_REQUIRES_MANUAL_REVIEW
FAIL_M0_BATCH_01_SCOPE_OR_BASELINE_VIOLATION
```

### 15.8 Stop condition

After Batch 01 checks and reporting, Codex must stop. It must not continue automatically into architecture guards, CI, Runtime Core, adapter extraction, or any later Batch.

---

## 16. Remaining Milestone 0 Development Batches

### M0-BATCH-02 — Architecture Guard Skeleton

Creates only:

```text
tests/conftest.py
tests/architecture/test_package_skeleton.py
tests/architecture/test_baseline_integrity.py
tests/architecture/test_forbidden_legacy_dependencies.py
tests/architecture/test_forbidden_execution_calls.py
tests/architecture/test_forbidden_direct_writes.py
tests/architecture/test_dependency_direction.py
tests/architecture/test_forbidden_paths_and_cwd.py
tests/architecture/test_forbidden_surfaces.py
tests/architecture/test_verdict_authority.py
tests/architecture/test_fixture_evidence_policy.py
tests/architecture/test_no_symlinks.py
```

Acceptance: all guards pass against the empty package skeleton and fail against controlled negative samples stored inside test code or temporary directories.

### M0-BATCH-03 — CI Wiring and Freeze

Creates or modifies only:

```text
.github/workflows/ci.yml
pyproject.toml
README.md
docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md
```

Acceptance: Windows/Ubuntu and Python 3.11/3.12 CI pass; repository remains clean; Milestone 0 checklist is completed; annotated freeze tag may then be created with explicit authorization.

Neither Batch may create Runtime implementation or migrate legacy logic.

---

## 17. Milestone 0 Final Deliverable Set

Milestone 0 ends with:

```text
1 independent Git repository
1 installable but intentionally empty aegiscae package skeleton
4 immutable baseline documentation snapshots
1 baseline hash/precedence register
6 root governance documents
2 accepted ADRs plus ADR process documentation
11 architecture guard tests
1 package import test
1 cross-platform CI workflow
3 reviewable commits
1 optional annotated architecture-freeze tag
0 legacy dependencies
0 legacy code files
0 production subprocess paths
0 production write paths
0 Abaqus executions
0 MCP/Skill/GUI/LLM/queue implementations
```

The next permitted work after acceptance is **Batch 1 — Runtime Control Plane**, starting with new contracts and tests rather than legacy extraction.

---

## 18. Final Milestone 0 Planning Verdict

```text
repository: AegisCAE-Runtime
package: aegiscae
architecture mode: runtime-first
legacy migration mode: selective extraction after new contracts
legacy direct dependency: prohibited
whole-repository copy: prohibited
Milestone 0 runtime code: none
Milestone 0 Abaqus execution: none
first Codex batch: repository, baseline, governance docs, empty package skeleton, import smoke only
next implementation authority: explicit user-approved Codex batch prompt

FINAL_VERDICT: MILESTONE_0_IMPLEMENTATION_PLAN_READY
```
