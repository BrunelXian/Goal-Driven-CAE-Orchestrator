# D4 product activation and versioned candidate

Status: **local package preparation; not a clean installation or Desktop activation**.

The candidate uses wheel version `0.0.0+g3d4` and plugin version
`0.1.0-alpha.3`. It preserves the D3 artifact rather than replacing its manifest.
The source builder includes all declared plugin resources under
`aegiscae/_gdcae_plugin`, with RECORD hashes. The two approved Operator preview
and read-only audit scripts are optional explicitly selected data under
`aegiscae/_gdcae_operator` and `support/operator_deployment` in the external
bundle. Their presence grants no deployment or execution authority. Missing one
of the two selected Operator resources blocks final assembly.

## Concrete user entry

The current official documentation supports the portable root `plugin.json`,
onboarding Skill, and repository marketplace. Local installation and fresh-chat
activation must be exercised through the official client UI. Marketplace discovery
is separate from installation; a reviewed pushed ref is needed before claiming
GitHub installation success. [Official plugin packaging documentation](https://developers.openai.com/plugins/build/plugins)

`install-plan` returns only the pinned marketplace-add argument vector and a
manual activation requirement. It executes nothing and no longer proposes an
unverified `codex plugin add` command. This round neither changes global config
nor performs account authentication or Desktop operations.

The existing `init-research` remains an offline preview. The separate
`init-real-research` command calls `create_real_research` from a verified Core
installation. It creates a fresh ResearchProject with fixed A=1 N, goal
U1 in [0.019,0.021] mm and two-call budget. It never creates an AF Plan, Grant,
Owner or Solver invocation. It refuses the source checkout as an installation
and refuses an existing workspace. Partial failures remain for diagnosis.

The initialization receipt persists local Project identity but omits it from the
public CLI summary. A real-intent frozen contract does not establish a trustworthy
host, approved Operator, authenticated DAT source or physical validity.

## Package and dependency closure

The packaged runtime contract declares the seven existing TEST_ONLY read tool
names, required Core factory, qualified optional MCP/pywin32 versions and absent
activation. It is data, not a launch configuration. No unbound `mcp.json`, writable
tool or credential mapping is added. Doctor reports missing/unqualified optional
dependencies without importing them and retains `UNBOUND_REQUIRES_EXPLICIT_TEST_PROJECT`.
Python core installation and optional dependency installation remain separate
approved actions; plugin installation alone does neither.

The pure tests extract wheel bytes only into a synthetic file-layout fixture,
validate its actual RECORD, load the packaged setup helper and Core from that
fixture and initialize a new Project away from the checkout. Their installation
root/metadata lookup is explicitly fixture-scoped. This proves packaged import
and resource closure; it does **not** prove pip installation, clean-environment
dependency closure, native custom-role activation or Desktop availability.

## One necessary activation action, after separate approval

In one new disposable project, install/activate the reviewed GDCAE package through
the official plugin UI, complete official authentication if required, open one
fresh chat and send:

> @GDCAE Run the packaged read-only doctor for this disposable workspace. Report
> package/role closure, missing dependencies and activation separately. If the
> actual custom types are available, delegate a bounded synthetic review to
> gdcae-cae, gdcae-results, gdcae-inverse and gdcae-reviewer and collect their
> results. Do not install dependencies, change global configuration, read other
> projects or chats, issue a Grant, start an Owner, run Solver/ODB or claim
> scientific validation. A missing custom role must remain BLOCKED.

Until that occurs: Desktop `NOT_TESTED`, GitHub install `NOT_TESTED`, external VM
`NOT_RUN_EXTERNALLY`, protected HIL `BLOCKED`, real A `NOT_READY`. Existing native
Main role calls are separately recorded by Main and are not installed-plugin proof.
