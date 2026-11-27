# VeriCAE 1.0.0 · Local source freeze

Frozen 2026-11-27 from the 0.5.6 public package. The baseline implements scientific planning, multi-agent orchestration, file-based research state, MCP integration, results analysis and independent validation. Publication awaits selection of the unified distribution repository.

| Research component | Responsibility |
|---|---|
| Initiate | Agree the objective, reference model, observables and acceptance conditions. Create the Markdown/YAML workspace after confirmation. |
| Conduct | Resume through the Handoff. Main owns the primary state, dispatches Task Cards to the existing CAE, Results and Independent Validation conversations, and collects original replies. |
| Setup | Inspect the active Desktop environment. Check MCP registration, discovery, invocation, and the response's identity and permission scope. |

Four persistent roles use Codex Desktop. The three specialist TOML files are optional native configurations. The package preserves workspace schema v1, the six-part Research Card, role protocols and conditional recovery. AbqJobPilot separately owns execution control, Grants, Runs and Receipts. External execution and environment setup remain operator responsibilities.

## Evidence and limits

- UAT-100 passed on the 0.5.6 baseline in Desktop. Main discovered three historical read tools and made two actual read-only calls against AbqJobPilot 0.5.3 DEV, for environment identity and a historical Receipt. New delegated requests were disabled. This freeze carries forward that evidence.
- INT-001 previously supported the axial-bar displacement. Overall evidence qualification remained **PARTIAL**. The extraction Receipt was **FAILED**, execution and extraction qualification **REVIEW_REQUIRED**, and historical result integrity **INSUFFICIENT**.
- INT-002A.1 demonstrated a **TEST_ONLY** fake-backend bridge with `solver_conclusion=NOT_RUN`. INT-002B stopped after planning with zero new submissions. A fresh autonomous real-solver cycle remains unqualified.
- Persistent-thread visibility, model selection and tool availability depend on the host. An installed package alone cannot establish the capabilities of a particular Desktop conversation.

## License and dependencies

The plugin carries the repository's Apache License 2.0 verbatim in `vericae-research/LICENSE`. The distributable contains first-party skills, TOML role definitions, workspace templates, static protocols, documentation and marketplace metadata. No third-party libraries, native binaries, solver, or hosted service are redistributed. Codex is an external host. An AbqJobPilot MCP connection is optional and separately provisioned.

The source-only developer checker declares Python 3.11+ (below 4) and PyYAML (MIT). Its setuptools build system and optional pytest/ruff development extras are excluded from this ZIP. Rebuilding the ZIP uses Git and Python 3.11+ standard library only.

## Reproduce the archive

Check out the full Git commit identified by `SOURCE_COMMIT` inside the delivered ZIP. From that checkout run the following with a developer Python 3.11+ interpreter and an unused output directory:

```text
python product/vericae/release/build.py --ref HEAD --output dist/vericae-1.0.0
```

The builder reads committed Git blobs. It includes the VeriCAE marketplace catalog, this plugin subtree, the installation guide and these notes. It records the resolved commit, orders ZIP members by path, uses stored entries and fixes timestamps and file modes. `FILES.sha256` covers every payload file except the checksum list itself. The external ZIP checksum covers that list as well.
