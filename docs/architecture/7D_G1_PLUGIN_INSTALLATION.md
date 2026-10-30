# G1 source-only Plugin and new-workspace preparation

Status: offline package, not a published release or successful installed `@GDCAE`
experiment. No global configuration is changed by these helpers. No MCP execution
endpoint, credential discovery, solver launcher, network installer or agent harness
is bundled. Existing seven read-only AF tools and legacy role files are unchanged.

## Prerequisites and installation boundary

Use an approved Windows host, an existing Python 3.12+ interpreter selected under
the user's environment policy, and separately licensed/qualified Codex, Abaqus and
AF Develop. The helper has no third-party Python dependencies. In G0 the installed
Codex Desktop was 26.1023.6621.0 and CLI 0.165.0-alpha.1.2; that is not proof of
plugin activation or Abaqus availability. Private GitHub access is UNKNOWN until
the intended new user's approved source fetch succeeds. Never embed access tokens
in URLs or files, or publish the private development tree to solve access failures.

Run `plugins/gdcae/scripts/gdcae.py doctor` using the absolute interpreter. It reads
only its explicit package allowlist and reports bounded status fields. Solver,
license, AF dispatch, native role loading and plugin activation are deliberately
NOT_TESTED / NOT_QUALIFIED. Strong Operator isolation remains blocked.

After separate installation approval, generate an argument-vector plan with:

```text
<absolute-python> plugins/gdcae/scripts/gdcae.py install-plan \
  --repository https://github.com/<approved-owner>/<approved-repository> \
  --ref <reviewed-full-40-character-commit>
```

The placeholders must be replaced with a source-only, release-approved snapshot
that actually contains this package; CP1 predates it. Branch names and credentials
are rejected. The helper does not fetch or execute the plan. Its two commands add
the pinned marketplace and install `gdcae@gdcae-preview`; those Codex commands can
write user configuration/cache, so they are NOT executed under G1 authorization.
No public one-command install is claimed. An immutable commit and content hash
bind content, not publisher trust or an unforgeable approval.

The installed Plugin is skills and project scaffolding, not the Python research
core. The doctor separately reports whether `aegiscae` is discoverable without
importing it. A reviewed Core snapshot must also be installed in the selected
environment before the research Skill can use its API. A future approved setup
can verify the source checkout's exact Git HEAD and run that interpreter with
`-m pip install --no-deps --no-build-isolation <approved-pinned-checkout>` only if
its existing build prerequisites satisfy pyproject.toml. Do not download/upgrade
missing prerequisites automatically. This source installation is not performed
or qualified in G1. AF installation/configuration is a separate prerequisite;
the Plugin package does not redistribute AF or Abaqus.

## Automatic bounded workspace setup

1. Run `package-digest` and review the exact package source.
2. Run `prepare-workspace --workspace <new-absolute-path>
   --expected-package-digest <reviewed-digest>`.
3. The path must not exist, its parent must exist, and it must be outside the
   source checkout, plugin package and Codex configuration home. Links/junctions
   are rejected. Existing files are never overwritten; failed partial setup is
   preserved and cannot be retried into the same destination.
4. Exactly nine package files, four `.codex/agents/*.toml` role files, the repo
   marketplace and a package receipt are created. No arbitrary source tree,
   historical evidence, local model, database or private configuration is copied.
5. After separately approved installation, trust the new project and use a new
   Desktop Main. Observe actual `@GDCAE` selection and actual named native role
   loading. A copied marketplace/TOML or default-agent behavior test is not proof.

The helper prepares project scaffolding only, not a frozen ResearchProject. Goal,
model, qualification evidence, units, mutation limits, verifier tolerances and the
two-attempt budget must then be created through the versioned research API. No
Plan, approval or Grant is created by setup.

## Role and execution boundaries

Four templates are packaged: gdcae-cae, gdcae-results, gdcae-inverse and
gdcae-reviewer. Native configuration disables shell, apps, plugins, memories and
permission requests for these specialists where supported. Main provides bounded
evidence; there is no unrestricted credential or execution endpoint. These flags
are defense in depth, not an independent OS principal. Use a separately qualified
operator environment before claiming resistance to same-user self-approval.

G1 only tests offline fixtures. Future A and B need separate exact human/operator
authorization; B follows accepted A evidence and its frozen goal, never a prefilled
answer. ODB remains NOT_VERIFIED until a separate AF-owned extractor qualifies.

Official format references (consulted 2026-10-30):

- https://developers.openai.com/plugins/build/plugins
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/plugins

The manifest uses the portable root format and OpenAI onboarding extension; the
repo catalog points to `./plugins/gdcae`. Official support does not establish that
the current session reloads newly written custom types. If it rejects the type or
requires a fresh session, record that blocker rather than fabricating a trace.
