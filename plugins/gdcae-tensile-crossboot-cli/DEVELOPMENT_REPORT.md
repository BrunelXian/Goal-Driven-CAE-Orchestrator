# CLI digest boundary repair — Development, pending independent acceptance

GD 0.1.0-tensile.11.1; AF 0.0.0+tensilecrossbootcli1. Scope: one GD CLI serialization boundary. Original .11 and original failed-attempt evidence remain unchanged.

The .11 CLI produced a bare canonical-object SHA256 and forwarded it to AF, which requires `sha256:`. Its tests called AF directly and missed this installed CLI boundary. The real failed call rejected before any native intent or terminal write. This was a developer interface defect.

`cross_boot_archive.py` now emits the native AF digest. CLI input accepts only exact lowercase 64 hex, explicitly converted, or exact `sha256:` plus 64 lowercase hex. Wrong algorithm, whitespace, uppercase and duplicate prefix are rejected. The supplied proposal object and envelope are independently checked. Authorization references are never rewritten: native authorization still requires the tagged identity. File-byte SHA256 is separate from canonical JSON object SHA256.

AF business Python sources, including lifecycle, capability, terminal writer, canonicalization and authorization, are byte-identical to .11. Strict GD_ROOT/catalog qualification prevents using the old AF install with modified GD. Only generated catalog, installation metadata/version and provenance change. No permissions were weakened to preserve an old digest.

Actual installed subprocess CLI tests: 17/17 in `evidence/INSTALLED_CLI_32c9b857b1a2457d8a5d844531df30c7/RESULTS.json`, plus 3/3 commit-boundary negatives in its `COMMIT_BOUNDARY_RESULTS.json`. The current reproducible driver combines all 20. Proposal/check/commit/reconcile children do not patch production. Fixture creation uses synthetic preboot lifecycle and A proof with real isolated SQLite, protected native capability and real host boot sampling. Partial interruption is an exact protected-intent fixture, not a killed process. No real Owner, Solver or actual site archive. Prior unaffected .11 evidence is retained, not claimed rerun.

Reproduce: absolute LangChainEnv Python 3.12.10 `-I -B -S tests/installed_cli_checks.py`. It creates unique OFFLINE_TEST_ONLY directories in this candidate's evidence area. `tests/build_cli_fixture.py` is the standalone fixture constructor. Actual system restart, real archival retry and new B execution are NOT_TESTED/NOT_AUTHORIZED.

Original Proposal file SHA b7ee5acbf40e5e4b9076d6dbfd7f31b9ee19d80e3677c11a9d4f0629df303353 remains unchanged. Its canonical bare 543e9c376b39d9d3adfc9986f3e175a6c6425dc59e0acade564b59636eb9333e and tagged representation identify the same old object. The new read-only proposal preserves operation 44d35ecaa64e4893a119aead1bb9735f and all original scope/evidence, but has a different `implementation` identity. It must receive new exact authorization after independent acceptance; no previous approval is replayed.

Build/source ownership: new `plugins/gdcae-tensile-crossboot-cli` overlay, baseline .11 FREEZE and every source byte pinned, exact patch, two repository HEAD/dirty snapshots. No Git stage/commit/push or shared environment change. Installation is the built wheel via isolated pip target and the exact ZIP payload; RECORD/provenance verified.
