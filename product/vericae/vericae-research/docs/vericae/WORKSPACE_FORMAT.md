# VeriCAE Workspace Format v1 — Native use in 0.5.6

The existing file format is unchanged. This static reference is usable through Codex native file tools;
there is no packaged CLI or language-runtime prerequisite. Native review is NATIVE_FILE_REVIEW, not a
claim of deterministic YAML parsing/hash validation. The optional developer checker stays in the repository.

## Files and ownership

Copy [the workspace template](../../templates/research-project/README.md) to a confirmed new directory.
Required files: `README.md`, `research/RESEARCH_CARD.md`, `research/TASK_CARDS.md`,
`models/SANITY_MODEL_SPEC.md`, `docs/initiation/HANDOFF.md`, `.abqjobpilot/link.json`.
Required directories: `research/`, `models/`, `experiments/`, `scripts/`, `reports/`,
`docs/initiation/`, `docs/research-runs/`, `.abqjobpilot/`. Empty output directories use `.gitkeep`.
Main alone writes primary research state and append-only research decision logs; specialists only write
explicitly allowed artifact files. This discipline does not create a sandbox or concurrency service.

## Research Card YAML schema (existing v1)

Frontmatter starts/ends with `---`. All fields are required. Do not add unknown fields, duplicate keys,
anchors/aliases, unsafe tags or any agent-editable execution approval field.

| Field | Required type and values |
|---|---|
| `schema_version` | integer 1, not boolean |
| `project_name` | nonempty string, <=256 characters |
| `revision` | positive integer; descriptive revision only |
| `phase` | PLANNING / INVESTIGATION / REVIEW / PAUSED / COMPLETE |
| `main_writer` | nonempty string, <=256 characters; identity description, not permission |
| `model` | exactly path (string), version (nonempty string), qualification |
| `model.qualification` | UNVERIFIED / IN_REVIEW / QUALIFIED_FOR_SCOPE, requiring independent evidence |
| `references` | list of {path: string, sha256: string} |
| `receipts` | list of {path: string, sha256: string, receipt_id: string, run_id: string}; initially empty |

SHA-256 uses 64 lowercase hexadecimal characters, at most 1024 entries per list. Main maintains actual
hashes using available native capability after edits, never guesses them. If unavailable, say NOT_VERIFIED;
file reasoning alone is not digest certification. No circular Research Card self-digest.
Keep the two matching borders, native Markdown title, ordered six modules ❶–❻, Model Evolution table,
two distinct two-column role tables, roadmap and quoted Next Action. No schema redesign in this slice.

## Local references and execution evidence

YAML paths are relative to project root; Markdown links relative to the containing file. Targets must exist.
Use forward slashes and simple explicit file links. `../` is allowed only within the project. Reject absolute,
drive/UNC, control/reserved Windows components, URI/query/stream syntax and out-of-project references.
Do not follow symlinks/reparse points as a way to escape scope. External links are not local evidence.
Native tools may not implement the deterministic parser's full rejection rules: report what was actually
inspected and what remains unverified, rather than claiming complete Schema validation.

Receipt references point to existing local JSON, whose receipt_id/run_id match the reference. Identifier
format is `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}`. Duplicate keys and non-finite JSON values are invalid.
Local format/hash agreement does not prove origin, authorization or execution; even consistent files can be
forged. Real Run/Receipt facts require trusted AbqJobPilot verification, currently UNAVAILABLE / NOT_CONNECTED.
No invented execution authorization, model qualification or physical conclusion.

`link.json` contains exactly schema_version=1, project_id, project_instance_id; IDs both null for unbound
projects or both bounded identifiers. No credentials, endpoints or capabilities. Reference IDs are not proof
of binding. Documents remain bounded to 1 MiB, Card frontmatter to 64 KiB, per the existing format.

## Task bodies and modes

Task Card bodies record task ID, objective, actual input references, allowed artifact file changes, expected
outputs and acceptance criteria. Native identity/dispatch/reply references are body evidence, not new YAML.
Human messages default to Consultation, even with a dispatch marker. See the [mode protocol](../../references/subagent-modes.md).
Main pre-submit review covers actual target contents/INP identity/path, scope diffs and trusted Run/Receipt
sources. Clean Git status alone is not trust. Unexplained changes stop submission; do not overwrite/restore.

## 0.5.4 persistent role bindings (body only)

The four roles are Main, CAE, Results, Independent Validation. Main records the real same-project
thread bindings in Handoff/Task Card bodies, not new YAML fields. Unknown IDs are NOT_EXPOSED.
Native cross-thread routing uses actual send/read evidence; headers and Task Cards are not identity tokens.
Persistent role returns retain status, artifacts, receipt_id, key_metrics, open_risks within 15 total lines.
Optional temporary Subagent/TEST_ONLY 10-field receipts remain distinct, not substitutes for persistent threads.
