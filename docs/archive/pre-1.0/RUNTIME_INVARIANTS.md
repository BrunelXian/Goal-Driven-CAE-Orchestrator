# AegisCAE Runtime Invariants

Status: Milestone 0 — documented, not yet implemented

These stable IDs define non-negotiable rules for the future Runtime.

## INV-EXEC-001

No production subprocess outside Unified Executor.

## INV-WORKSPACE-001

No production write outside ControlledWorkspace.

## INV-SOURCE-001

Source artifacts are immutable by default.

## INV-LEGACY-001

No direct dependency on `abqpilot` or `abqjobpilot`.

## INV-ADAPTER-001

Adapters cannot execute subprocess or perform uncontrolled writes.

## INV-LLM-001

LLM is Planner/Client only and has no execution, validation, or evidence authority.

## INV-VERDICT-001

Machine verdicts are created only by deterministic Runtime/Validator logic.

## INV-EVIDENCE-001

Markdown reports are views, not evidence authority.

## INV-FIXTURE-001

Test fixtures are not physical evidence.

## INV-CWD-001

Production behavior cannot depend on implicit current working directory.

## INV-FAILCLOSED-001

Unknown tools, paths, contracts, and authorization states fail closed.

These invariants do not claim that their enforcement exists in Milestone 0.
Implementation and machine-enforced architecture guards belong to later reviewed
Batches.
