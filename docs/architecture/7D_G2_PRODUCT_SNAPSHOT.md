# G2-LONG internal snapshot installation and product boundaries

Date: 2026-10-30. This is an internal candidate workflow, not publication or proof
of Desktop activation. Real Abaqus A/B remain NOT_RUN. No ordinary agent receives
an Operator capability. Existing historical reports remain unchanged.

## Exact snapshot contract

`plugins/gdcae/scripts/candidate.py` exposes
`export_snapshot(source_root, selection, fresh_destination)`. The selection has
exact keys: `schema=gdcae-source-selection-v1`, `product=gdcae|af_develop`,
`base_commit`, `files` (relative path to SHA-256), `dirty_files` (selected changed
paths with the same hashes), and `license_status`. Base commit is caller-supplied
evidence from the separately verified Git audit, not a Git query by this builder.

Only reviewed runtime source, package resources, Plugin/role files, explicit test
fixtures, selected current G2 documentation and top-level LICENSE/NOTICE metadata
are eligible. Eligibility is not automatic selection. There is no recursive
repository export. Historical milestones, credentials, databases, original models,
session records and unselected files are excluded. Links, path traversal, Windows
reserved names, case collisions, changed bytes, missing files and oversize input
are rejected. Sensitive-pattern checks are bounded checks, not a guarantee that
arbitrary secrets cannot exist; human/source review still defines the allowlist.
The first real AF export was rejected with `PRIVATE_MATERIAL_REJECTED` because
the required runtime module `abqjobpilot/local_credentials.py` was classified by
its basename as credential data. A narrow exception now admits only that exact
path for `af_develop`, still requiring reviewed hashes, stable reads and content
privacy scanning. No credential records or other credential-named paths are
admitted. The failed attempt and earlier GD candidate are retained; regenerated
candidates use new destinations.

Each product has an independent output directory containing `source/`,
`CANDIDATE_MANIFEST.json`, `source.zip`, `SHA256SUMS.json`, `NOTICE_INTERNAL.txt`
and a deterministic pure-Python wheel. GD-CAE never embeds AF's execution kernel.
The manifest states `INTERNAL_CANDIDATE_NOT_FOR_RELEASE`,
`PENDING_RELEASE_REF`, `OFFLINE_RUNTIME_SUBSET_ONLY`, and no execution authority.
The wheel is built with reviewed stdlib ZIP/metadata code, without importing the
selected package, executing source build hooks or downloading dependencies.
Resources under the selected package prefix are included exactly.

The internal wheel distributions are `aegiscae` and
`abqjobpilot_gdcae_internal`, version `0.0.0+g2long`; the latter installs the
separate `abqjobpilot` import package. These candidate metadata do not claim
qualification of AF GUI or all optional dependencies. Missing or unresolved
licensing remains `UNRESOLVED_INTERNAL_ONLY`; no license is invented or granted.

## Installation and diagnosis

Use only the environment approved for the task. The selected existing Python
3.12.10 has pytest 9.1.0 and pip 25.0.1, but no setuptools/wheel package. The
candidate builder does not require those missing build dependencies.

For a separately authorized task-local installation:

1. Verify the candidate manifest, exact source selection, artifact hashes and
   independent review. Do not substitute developer source paths or remote HEAD.
2. Create a fresh temporary venv using the selected absolute interpreter's
   standard `-m venv` (its bundled ensurepip remains offline).
3. With that venv's absolute interpreter run `-I -m pip --isolated install
   --no-index --no-deps --no-cache-dir --no-compile <verified-local-wheel>` for
   each approved product. No editable install, third-party fetch or source hook.
4. Run an isolated import probe outside both repositories and confirm actual
   `aegiscae.__file__` and, when installed, `abqjobpilot.__file__` reside in that
   venv's `site-packages`. Remove development `PYTHONPATH`/`PYTHONHOME` from child
   environment. Package resources must also resolve from the installed artifact.
5. If a test harness needs already installed pytest or other reviewed dependencies,
   label that run `DEPENDENCY_ENVIRONMENT_REUSED`; do not call it a clean-machine
   installation or copy a shared environment wholesale.

`gdcae.py doctor` is bounded/read-only. `prepare-workspace` copies the exact Plugin
closure and four `.codex/agents` templates into an exclusive new directory.
`init-research` additionally uses the installed Core to create `research/` and
freeze the agreed preview contract. It binds Core origin to the current
interpreter's `sysconfig` purelib/platlib and matching installed distribution
metadata, rejects editable provenance, and verifies package files against
SHA-256/size entries in RECORD before import. Missing, changed or unrecorded
package files are rejected. An arbitrary directory named `site-packages` is not
accepted. These are local installation consistency checks, not authenticated
publisher signatures or protection against a party that can rewrite both the
installed files and their metadata. Initialization refuses existing destinations
and reports only bounded status/digest/revision fields.
It does not prepare B, issue a Grant, enable a Plugin or launch a solver.
Existing/partial destinations are preserved and rejected on repeat initialization.

Uninstallation was not performed by this task. The isolated venv and generated
workspace can be retired under later user authorization; no global plugin/config
removal or broad filesystem deletion is part of this procedure.

## Measured Codex surface

Read-only local help on 2026-10-30 reports CLI **0.166.0-alpha.5.1**. It supports
`exec --json --ephemeral --strict-config --sandbox` and `plugin add`. Despite the
current help mentioning `--ignore-user-config`, the task prohibits using it and
the experiment does not use it. `--strict-config` rejects unknown config fields;
it is not an isolation mechanism or an instruction to ignore user config.

An independent CLI probe is limited to one new workspace and one isolated
`CODEX_HOME`, without copying authentication. Shell/apps/plugins/memories and
permission-request features are disabled in that scoped home. The Main prompt
requests the four exact custom agent types, no default-role fallback and no
filesystem/execution tools. Private IDs/raw JSONL remain in bounded memory only;
the projection records known event counts, exact role names, exits and process
ownership. A final model claim alone cannot prove custom-role loading or work
product retrieval. Missing authentication blocks only this branch.

The one CLI probe returned **PENDING_TEST_AUTH**, exit 1: one new thread-start
and turn-start event, one turn-failed event, no completed turn and zero custom
role spawn events. The bounded classifier observed an authentication-related
error; it does not establish the underlying credential/account cause. No final
agent answer or unexpected execution tool was observed. The owned CLI exited;
one observed descendant also exited, with zero survivors, no capture overflow,
no timeout and no cleanup uncertainty. No retry, auth copy or global fallback was
performed. Raw JSONL and private IDs were not saved by the probe.

Desktop `@GDCAE` remains NOT_TESTED; no UI installation or global configuration
change was performed.
Current development Main role availability, fresh CLI roles, Plugin installation
and Desktop activation are separate evidence surfaces.

Actual product checks: the first invocation reported 39 passed and one failed;
the failure was a test fixture sharing one dictionary for source and dirty-file
hashes, so its intended conflict mutated both sides. Copying the fixture map
restored the negative case. The next invocation passed 40 tests. A later source
review found that a literal private-URL pattern matched its own helper source;
escaping the regex slashes preserved real-URL rejection and removed the false
positive. An actual Plugin source-closure test was added; 41 tests then passed.
Independent review then identified the path-name-only installed-Core check.
After binding origin to interpreter installation metadata and RECORD, 42 tests
passed (8.22 s), including real fixture-wheel acceptance, editable rejection,
installed-source digest tamper, unrecorded source and fake `site-packages` cases.
These runs include creation of an isolated venv, actual no-index/no-deps local
fixture wheel installation, and verification of installed import/resource origin.
They do not by themselves prove the final two-product candidate rehearsal; that
is recorded separately by the integration owner after source freeze.

For a later approved role demonstration, use a fresh initialized workspace and
ask Main to delegate bounded raw evidence to `gdcae-cae`, `gdcae-results`,
`gdcae-inverse`, `gdcae-reviewer`. A fixture without accepted A evidence should
cause Inverse to refuse B. Capture native dispatch and result correlation without
private IDs; do not accept a renamed default agent as a custom-role test.

Official references explain formats, not this host's acceptance:
[Plugin packaging](https://developers.openai.com/plugins/build/plugins) and
[native custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## Release notes draft

G2-LONG adds reviewed allowlist snapshot/wheel assembly, fixed diagnostics,
installed-Core initialization and reproducible source/resource closure tests.
Both scientific execution and publication remain separately gated. Internal
snapshots include uncommitted work, so no existing GitHub commit is advertised as
containing them. Real provenance, independent HIL enforcement, Desktop activation
and actual A/B outcomes must each retain their independently measured status.
