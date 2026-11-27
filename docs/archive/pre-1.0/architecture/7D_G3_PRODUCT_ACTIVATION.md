# G3 product activation and installed-source boundaries

Date: 2026-10-30. Internal local rehearsal only. Plugin version stays
`0.1.0-alpha.2`; no frozen ResearchProject/Contract schema or execution authority
changes. GitHub publication, fresh authenticated role loading and Desktop
activation remain separate gates.

## Implementation

`plugins/gdcae/scripts/gdcae.py doctor` inspects the two exact distributions
`aegiscae` and `abqjobpilot_gdcae_internal` without importing their package code.
Each import origin must match the current interpreter's purelib/platlib,
distribution metadata, package file closure and SHA-256/size RECORD entries.
Editable sources, an arbitrary directory named site-packages, changed files and
unrecorded package files are rejected. `RECORD_VERIFIED` is local consistency,
not publisher authenticity or resistance to a principal able to rewrite both
files and metadata. Core discovery alone is insufficient installation evidence.

`doctor --workspace <absolute-path>` checks copied Plugin bytes and exactly four
matching role files. The status is `PACKAGE_AND_FOUR_ROLE_BYTES_VERIFIED`, while
`native_role_loading` and `plugin_activation` stay `NOT_TESTED`. A malformed,
missing, substituted or extra role produces `INVALID_WORKSPACE_CLOSURE`. No
credentials, execution state, thread history or solver is accessed.

`init-research` retains the real offline ResearchProject API and writes an
additional `gdcae-source-receipt.json` outside its database. This binds the plugin
package SHA, four role hashes and installed Core RECORD/package-file digest.
The initialization receipt includes that file's SHA. Its source classification is
`CONTENT_ADDRESSED_LOCAL_BYTES`, with `commit_inclusion=NOT_ASSERTED`. It neither
rewrites a frozen contract nor treats an installed package as execution approval.
An interrupted setup retains its partial fresh workspace; reusing it is refused.
The ordinary `prepare-workspace` file set and its no-install behavior are unchanged.

## Source identity and actual host observations

The local GD checkpoint is `69b144cea9aecc515e15cc830368972b09258af9`.
The task exported only the ten Plugin files and marketplace JSON from those exact
local Git objects, without cloning repository history. It separately hashed the
current local copy and recorded changed files as a dirty overlay. Those overlay
bytes are not asserted to be contained in the checkpoint commit.

The CLI install uses a local marketplace directory. No claim is made that CLI
`--ref` pinned this local directory: `--ref` is a Git-marketplace facility, and
the measured evidence here is an exact Git-object export plus explicit byte/hash
comparison, followed by a local-copy installation. No remote repository was
accessed. Public GitHub pinned-ref installation remains untested.

Actual CLI version: `0.166.0-alpha.5.1`. In a new task-only `CODEX_HOME`, with no
copied authentication and no external Turn, these commands returned exit 0:

```text
codex plugin marketplace add <fresh-local-marketplace> --json
codex plugin marketplace list --json
codex plugin add gdcae --marketplace gdcae-preview --json
```

The installed cache contains exactly one matching ten-file Plugin closure. Its
package digest is `1f2aeec53f907bc6e326244af4d66810e4b6ac060ce7c4e6504f7a61568af39c`.
The expected documentation-derived cache suffix `/local` was absent; inspection
was restricted to the newly created home/plugins directory and verified the
actual cache by content rather than guessing another user directory.

Evidence under this G3 task's `product/` directory:

- `preflight.safe.json`: bounded version/help flags and owned-process exits.
- `installation.safe.json`, `cache-closure.safe.json`: pre-checkpoint installation;
  these are historical for this task, not the current source identity.
- `source-identity.safe.json`: exact checkpoint file hashes and explicit overlay.
- `installation-g3.safe.json`: post-checkpoint local installation/cache closure.

For the post-checkpoint export/install, all 14 owned Git/CLI processes and observed
descendants exited; no survivors or cleanup uncertainty were recorded. No model
Turn, global configuration write, authentication copy, deletion or dependency
installation occurred in this plugin experiment.

## Tests and remaining integration work

First G3 product run: 52 passed, zero failed/errors/skipped (20.89 s). A subsequent
ten-test G3 run passed (10.45 s), adding a real offline Project API/source-receipt
handoff with explicitly mocked installation qualification. Actual temporary venv
installation tests separately install original synthetic GD and AF fixture wheels
and verify both RECORD identities without importing package code. They do not
substitute for Main's final two-product installed integration rehearsal.

Final product regression: 53 passed, zero failed/errors/skipped (20.86 s), recorded
in `product-g3-final.safe.json`. Ruff and scoped Git diff checks returned exit 0;
the updated Setup Skill validator returned exit 0. No total full-suite success is
inferred from these targeted runs.
The final installed integration should check both installed-package statuses, the
new initialization source receipt and copied-role closure in its fresh workspace.

| Surface | Qualification |
| --- | --- |
| Local marketplace add/list and plugin install | PASS_LOCAL; exact cache bytes verified |
| Current project role files | Byte closure verified; native runtime loading separate |
| Current Main's native custom roles | Earlier collaboration evidence; not fresh installation proof |
| Fresh authenticated CLI four-role dispatch | BLOCKED by previously observed test authentication; not retried |
| New Desktop project `@GDCAE` activation | NOT_TESTED; user UI participation needed |
| Real A/B, Operator isolation, Solver/ODB | Not granted or verified by product installation |
| Public release / clean-machine deployment | BLOCKED; separate licensing/deployment/qualification required |

The minimal later human action is to open a separately approved new non-sensitive
project in the authenticated Desktop client, select the GDCAE marketplace/plugin
through its official interface and confirm visibility. A fresh native four-role
handoff requires its own bounded evidence capture; do not use copied TOML or
default-agent fallback as proof. Do not copy login secrets into the isolated home
or repeat the known failing CLI Turn.

Official format references:
[Plugin packaging and local marketplaces](https://developers.openai.com/plugins/build/plugins),
[native subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
Those documents describe supported configuration surfaces; actual installed-host
acceptance and Desktop UI behavior require the distinct evidence above.
