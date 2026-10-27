# ADR-003: Codex-native harness and delegated Abaqus execution

## Status and authorization

**ACCEPTED — architecture principles and M01-A scope only.**

Date: 2026-10-28.

Authority: the researcher's explicit approval of M01-A in the development
conversation. The M00-P audit was delivered in that conversation; it is not a
report file committed to this repository. Acceptance of this ADR is not an
Abaqus Grant, a production connection permission, or a claim of runtime
qualification.

## Context

The repository began as the AegisCAE Runtime Milestone 0 skeleton. ADR-001 assigned
all production process creation to a future internal Unified Executor. ADR-002
prohibited an AbqJobPilot dependency and allowed only selective extraction of
legacy code. Those decisions predate the adopted Codex-native research product
and the separately developed Agent-first (AF) execution service.

M00-P reviewed GD-CAE at `488e0a1597b703dc86ce36158836d1b7a7fa07ab` and
AbqJobPilot Develop at `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`. Those are source
audit references, not a promise that a running installation has been qualified.

## Decision

1. **Codex is the sole Agent Harness.** Native Codex mechanisms own agent loops,
   subagent coordination, and conversation context. GD-CAE does not implement a
   second agent framework or require LangGraph or the OpenAI Agents SDK.
2. **GD-CAE owns the research control plane.** Its intended responsibilities are
   goals, model contracts, permitted mutations, budgets, persistent research
   decisions, and research verification. M01-A implements only read contracts and
   an offline-testable evidence adapter; it does not implement that whole plane.
3. **AbqJobPilot is the sole authorized Abaqus execution owner.** Solver, CAE/noGUI,
   and production postprocessing requiring Abaqus processes must use separately
   approved AF capabilities. GD-CAE has no Solver launcher, process supervisor,
   Grant issuer, private execution database access, or hidden retry path.
4. **A narrowly scoped public product seam is permitted.** M01-A permits a lazy
   `from abqjobpilot.service_discovery import discover` inside `_discover` in
   `src/aegiscae/adapters/abaqus/af_evidence.py`. It receives an explicit Project
   root and uses the returned client internally for the seven approved read
   methods. Import and adapter construction must not call discovery.
5. **The seam is not an import exception for the whole package.** Direct coupling
   to AF Store, Service, Backend, Operator, lifecycle, or recovery-management
   internals remains forbidden. No AF vendoring, generic `call` forwarding,
   dynamic command dispatch, raw client exposure, or private database fallback
   is permitted. Transitive implementation details of the public AF seam remain
   owned by AbqJobPilot and must not be copied into GD-CAE.
6. **Read compatibility and safety are bounded claims.** AF connection credentials
   can support operations beyond this facade. A seven-method facade and static
   checks do not create a same-user OS sandbox. Live compatibility, discovery
   side effects, and deployment permissions require M01-B's separate approval.

The package remains `aegiscae` version `0.0.0`, without new dependencies.

## Exact supersession

| Historical provision | Superseded scope | Retained scope |
| --- | --- | --- |
| ADR-001: internal Unified Executor owns all production execution | GD-CAE does not build an Abaqus executor; authorized Abaqus execution is delegated to AF | Deterministic controls, immutable sources, fail-closed behavior, reviewed boundaries |
| ADR-002: no AbqJobPilot direct or indirect dependency | The single audited public AF read seam is allowed | No `abqpilot` imports, private AF coupling, vendoring, whole-repository copy, or legacy Git-history import |
| ADR-002: selective extraction is the only integration route | Public AF product calls do not require copying its implementation | Any future code extraction remains separately reviewed |
| M00: exactly seven empty namespace files, no client surface | Two exact M01-A modules and their read API are allowed | All other unapproved implementation surfaces remain forbidden |
| Frozen baseline's precedence statements | They govern their historical 2026-07-26 snapshot, not conflicting newly adopted scope | Original bytes, provenance, hashes, and non-runtime status remain unchanged |

ADR-001, ADR-002, root architecture documents, and `docs/baseline/**` remain
unchanged. This ADR records supersession externally rather than rewriting history.
See the [current authority register](../architecture/CURRENT_AUTHORITY.md).

## Consequences and deferred work

M01-A must retain controlled-negative architecture tests while admitting only the
two reviewed source modules. Synthetic discovery/transport doubles establish
offline behavior; they do not establish AF runtime compatibility.

No Supervisor, Abaqus, ODB tool, SDK/app-server, MCP server, professional Agent
configuration, Skill, ResearchProject store, or workflow is started or implemented
by this decision. No execution request or deployment permission is granted.
M01-B, M01-C, and later milestones require separate authorization. A future Codex
runtime integration must receive its own narrow process boundary; it cannot
reintroduce a generic executor through an exception.

Rejected alternatives: duplicate AF execution infrastructure; move all research
logic into its trusted Supervisor; bypass AF through Classic tooling; replace
Codex's agent loop with a second harness.

## Related decisions

- [ADR-001: Runtime-first](ADR-001-runtime-first.md), partially superseded above.
- [ADR-002: Legacy selective migration](ADR-002-legacy-selective-migration.md), partially superseded above.
- [ADR-004: Execution evidence and research verification](ADR-004-execution-evidence-research-verification.md).
- [M01 Evidence Bridge contract](../architecture/M01_EVIDENCE_BRIDGE.md).
