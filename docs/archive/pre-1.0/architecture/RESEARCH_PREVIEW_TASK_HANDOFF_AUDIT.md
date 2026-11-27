# Research Preview .15 — Setup, task records and scoped sessions

This source audit distinguishes the installed Research Preview, the developer checkout and Host capabilities. It contains no user conversation, private identifiers, model data or service credentials.

| Finding | Available evidence | Repair boundary |
|---|---|---|
| Setup keeps doing research | The shipped Mode D guidance directs setup to the first Main research turn and to provide a next step when Main creation is unavailable. A read-only A-side reproduction proposed an inverse-search approach without returning a short name, two task drafts or a verified handoff. No solver execution was observed in that reproduction. | Give setup its own terminal branch. On failure return drafts and a handoff summary with the exact blocker. Require a trusted Main caller at any dispatch or scientific state transition. |
| The question table has no task identity | The public launcher offers bind, doctor, main and agreement. The agreement Core implements project persistence, contract freezing and scoped baseline qualification. Its source allowlist does not include SessionHub or a generic task registration API. | Reuse the project lock and SessionHub binding/reconciliation logic. Require authoritative write plus readback before claiming a registered task. Drafts carry DRAFT_NOT_PERSISTED until then. |
| The specialist and backend paths are disconnected | The separate AOO implementation records scoped tasks and results. The Desktop session adapter explicitly blocks unrestricted creation without role/tool binding. Read-only AbqJobPilot tooling exists separately; it is not wired into the .15 plugin manifest. | Require verified visible chat, project, role, task and effective tool restrictions. Separate product detection, connected backend, project identity and operation-specific permission. |

Setup should hand over a baseline-qualification draft and a capability-discovery draft to the unique Main. A task record needs project/task IDs, owner, dependencies, input and contract digests, allowed actions, approval references, expected deliverables, evaluation criteria and artifact hashes. Preserve separate execution, evidence-validation and scientific-disposition states. Reopening a project must reproduce the same records. A lost create/delivery receipt remains unknown until reconciled with its original request; do not retry by inventing a new identity.

CAE handles model review and candidate input preparation. ODB handles read-only result extraction and validation. Main owns scientific decisions. Neither a chat title nor a completed native child proves a visible independently scoped specialist session. A file path returned by a backend does not establish ODB field, frame, units or scientific validity.

The 43 scoped-session unit cases exercise a synthetic Host. Task Card lifecycle integration in the installed product, production specialist role attestation and a general AbqJobPilot-to-ODB loop remain open. Synchronizing the source does not implement those features.

Code references: plugins/gdcae-research/references/project-main.md and scripts/main-handoff.ps1 in that plugin, src/aegiscae/research/scoped_sessions.py, src/aegiscae/interfaces/codex_sessions.py and src/aegiscae/interfaces/mcp_read.py.
