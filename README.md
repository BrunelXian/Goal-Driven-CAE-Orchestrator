# VeriCAE 0.5.5
**Agentic Research Framework for Computational Engineering**

VeriCAE helps CAE researchers turn an engineering question into a testable contract, a qualified reference model and a sequence of experiments whose conclusions another engineer can check. Research lives in Markdown and YAML files. Codex Desktop provides the skills and persistent role conversations. The research layer runs without a separate agent runtime, database or message broker.

## Research principles

- **Verified-Model-First.** Establish what a simple reference model predicts, document its assumptions and qualify it for the intended use before extending it.
- **Goal-Driven.** The Research Contract defines the observable, units, acceptance criterion and stopping conditions. The Research Card tracks the model, its qualification and the next decision.
- **Verifiable.** Connect each claim to its inputs, model version, Task Card and evidence. For execution claims, check the actual Run and Receipt and retain the scope of each verdict.

## From a question to a research decision

**Initiate** drafts a six-part Research Card and confirms the project name and scope with the researcher. It prepares the file workspace and a Handoff. **Conduct** reads those files to resume the investigation. **Setup** inspects the environment and reports which capabilities the current Desktop conversation can actually use.

| Persistent role | Responsibility |
|---|---|
| Main | Owns research state, writes bounded Task Cards, dispatches them to existing role conversations and reads their original replies. |
| CAE | Reviews geometry, materials, boundary conditions and units. Derives a reference response and produces the artifacts allowed by the task. |
| Results | Checks the selected quantity, units, location and frame against the recorded outputs and execution evidence. |
| Independent Validation | Derives or checks the result independently, challenges assumptions and reports what the evidence can support. |

Researchers can consult a role directly. File changes require a bounded dispatch from Main. Version 0.5.5 also supports model and reasoning-effort requests for role conversations, verification of the effective settings when exposed by the host, and a capability assessment before adding a specialist.

AbqJobPilot forms the execution layer. It owns project bindings, grants, runs, receipts and execution verdicts. VeriCAE uses an explicitly configured MCP connection for the permitted operations. To verify an external server, the current Desktop Main must discover the expected tools and obtain a matching response to an authorized read. A researcher can plan a project and review models offline.

## Install the public 0.5.5 snapshot

Use Git and a Codex installation with the `codex plugin` and `codex plugin marketplace` commands. In PowerShell, run the following from a directory where you want to keep the checkout. The local marketplace uses that checkout as its source.

```powershell
git clone --branch codex/vericae-0.5.5-public --single-branch https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator.git
cd Goal-Driven-CAE-Orchestrator
codex plugin marketplace add ./product/vericae
codex plugin add vericae-research --marketplace vericae-public --json
codex plugin list --marketplace vericae-public --json
```

Check that the entry is installed and enabled, with version `0.5.5`. The plugin's Desktop display name is **VeriCAE Research (Test)**. Open your research directory as a Codex project and use **Set Up Research Environment** to check the three skill entries. If Desktop still references an obsolete skill path, save the research checkpoint, safely finish running tasks and restart Desktop. Return to the same project and Main conversation.

For a first study, ask: *“Plan a study of the tip displacement of a uniformly loaded cantilever. Propose a project name and show me the Research Card before creating files.”* Check the load definition, observable and acceptance criterion before confirming. Later, ask Conduct to resume from `docs/initiation/HANDOFF.md` and review the assumptions for the first model. The plugin includes the [workspace template](product/vericae/vericae-research/templates/research-project/README.md) and [role protocol](product/vericae/vericae-research/references/cross-thread-protocol.md). An [optional developer checker](product/vericae/developer) verifies local file consistency.

## Verification status

**VeriCAE 0.5.5 + AbqJobPilot 0.5.3 DEV** completed INT-001, a read-only cross-system verification of an existing axial-bar run.

| INT-001 dimension | Verdict |
|---|---|
| MCP Integration | PASS |
| Native Agent Orchestration | PASS |
| Scientific / Numerical Verification | PASS |
| Independent Validation | PASS |
| Evidence Qualification | PARTIAL |

The analytical displacement and the historical DAT result agreed at printed precision. Overall qualification remains **PARTIAL** because the historical extraction output lacks a verified binding to its owner. INT-001 did not submit a new job or establish an autonomous solve cycle for a new task. [INT-001 scope and findings](docs/vericae/INT-001.md)

## Limits and next validation steps

Native thread visibility, cross-thread messaging and effective model settings depend on the Codex host. The public plugin supplies the research workflow. The validated history interface requires a separately provisioned AbqJobPilot DEV environment. The next execution milestone is a separately authorized new task with verified inputs, execution containment and output binding, followed by independent review.

The repository and plugin carry the [Apache License 2.0](LICENSE).
