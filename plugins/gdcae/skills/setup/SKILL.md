---
name: setup
description: Prepare a new GDCAE research workspace from the reviewed plugin package and diagnose offline prerequisites. Use after GDCAE installation or for a new research workspace.
---

Use a reviewed package snapshot and the user's selected existing Python environment.
Read their environment policy first. Never install dependencies or change global
Codex configuration without separate approval.

Run the bundled `../../scripts/gdcae.py doctor` with that absolute interpreter.
The doctor is read-only. Its UNKNOWN / NOT_TESTED statuses are limitations, not
implicit permission. It does not probe Abaqus, credentials, projects or threads.
Require `installed_packages.aegiscae.status = RECORD_VERIFIED` before research
API operations. Discovery alone is insufficient. AF has a separate installed
distribution check; neither check qualifies real execution or HIL isolation.
Plugin installation does not install the Python core. Obtain separate approval
for the reviewed pinned core installation in the selected environment; do not
silently install or fall back to system Python.

For a new empty workspace outside the source checkout, obtain the reviewed package
digest using `package-digest`, then use `prepare-workspace --workspace <absolute>
--expected-package-digest <digest>`. This copies an exact source allowlist and four
native agent templates. It refuses an existing nonempty destination. It neither
installs/enables a plugin in Codex nor creates a ResearchProject/Grant.

When the reviewed Core is installed in the selected temporary or approved
environment, use `init-research` instead of `prepare-workspace` to also create a
new offline ResearchProject. Supply the same package digest, a short project name
and the agreed goal interval through `--goal-min-mm` and `--goal-max-mm`.
It verifies interpreter installation roots, metadata and RECORD hashes, freezes the versioned preview
contract, and leaves A/B unexecuted. It refuses a source-checkout import or an
existing destination. A partial failure is retained for diagnosis, not overwritten.
It writes `gdcae-source-receipt.json`, binding the plugin/package hashes and four
role file hashes to the installed Core RECORD. This is content provenance, not
a claim that uncommitted overlay files belong to a Git commit. Run `doctor
--workspace <absolute>` to inspect the copied plugin and four-role byte closure.
A verified file closure does not prove native role loading or Desktop activation.

For separately approved D4 real-contract preparation, use the explicit
`init-real-research` command with the same fresh workspace, reviewed package
digest and short name. This calls the installed Core's additive real Project
factory. It fixes A at 1 N and the goal interval at [0.019,0.021] mm; it does not
migrate an offline Project or create an AF Plan, Grant, Owner or Solver call.
Keep its `real_a=NOT_READY` until the independent execution and HIL gates close.
Do not substitute `init-research` and relabel its offline contract as real.

The packaged `../../references/runtime-contract.json` declares exact optional
dependency versions and the seven TEST_ONLY read interfaces. Doctor checks those
versions without importing optional modules. `UNBOUND_REQUIRES_EXPLICIT_TEST_PROJECT`
means no MCP server is configured or started; do not invent a production binding.
Plugin installation does not install Python dependencies. Any missing dependency
remains a separate approved environment action.

An explicitly authorized internal-snapshot exercise may install the reviewed local
wheel into its own fresh temporary venv using `--no-index --no-deps`. The bundled
`candidate.py` builder only packages exact pre-reviewed file hashes; it does not
install, download dependencies, run build hooks or grant execution authority.
Follow the snapshot manifest and existing authorization; do not extend this to a
shared environment, uncontrolled Git ref or public release.

Project trust and plugin installation are separate user-controlled steps. After
approved installation, open the new trusted project and a new Main chat, select
the actual GDCAE plugin through `@`, and verify the four custom roles load.
Do not report success from a printed tag, copied TOML, or a fallback skill.
If activation is unavailable, report BLOCKED_PLUGIN_ACTIVATION.

Continue with `../research/SKILL.md` only within the current authorization.
