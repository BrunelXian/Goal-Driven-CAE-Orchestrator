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
If `research_core` is MISSING or UNKNOWN, stop before research API operations.
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
It requires an installed `site-packages` Core, freezes the versioned preview
contract, and leaves A/B unexecuted. It refuses a source-checkout import or an
existing destination. A partial failure is retained for diagnosis, not overwritten.

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
