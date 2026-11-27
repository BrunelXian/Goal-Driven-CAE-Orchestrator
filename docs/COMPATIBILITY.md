# VeriCAE 1.0.0 compatibility and verification

## Pinned distributions

| Product | Release source | Download and SHA-256 |
|---|---|---|
| VeriCAE 1.0.0 · local Codex marketplace | Tag `v1.0.0` identifies the [frozen build commit](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/commit/b0ead2e06dd11ebf5b169f8368d2fcb4ffe3d20e), `b0ead2e06dd11ebf5b169f8368d2fcb4ffe3d20e`. | [VeriCAE-1.0.0.zip](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/v1.0.0/VeriCAE-1.0.0.zip) · 144,801 bytes · `273172ba70763269571f872703e3ba30924e9459d804212f4a132c1c536e4d0b`. [Release](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/tag/v1.0.0) |
| AbqJobPilot 1.0.0 · Windows x64 | Tag `v1.0.0` resolves to [`a7cbf27cee4e049f5cccb21416bdbfb7e8836808`](https://github.com/BrunelXian/AbqJobPilot/commit/a7cbf27cee4e049f5cccb21416bdbfb7e8836808). The installer was built from [`34632670680c25227c851a2368d9f3b0d8987e86`](https://github.com/BrunelXian/AbqJobPilot/commit/34632670680c25227c851a2368d9f3b0d8987e86). [Build record](https://github.com/BrunelXian/AbqJobPilot/blob/a7cbf27cee4e049f5cccb21416bdbfb7e8836808/docs/LAUNCH_100_ABQ_PUBLIC_PACKAGE_FIX.md) | [AbqJobPilot-1.0.0-Windows-x64-Setup.exe](https://github.com/BrunelXian/AbqJobPilot/releases/download/v1.0.0/AbqJobPilot-1.0.0-Windows-x64-Setup.exe) · 71,418,880 bytes · `078392d3ccc09c6a6af2f14e8fb7139c127be2b2951db60734bfd504bf22984d`. [Release](https://github.com/BrunelXian/AbqJobPilot/releases/tag/v1.0.0) · [Publisher checksums](https://github.com/BrunelXian/AbqJobPilot/releases/download/v1.0.0/SHA256SUMS.txt) |

VeriCAE requires a Codex host supporting local plugin marketplaces. Live collaboration also requires native thread discovery and messaging. AbqJobPilot is optional for planning and offline analysis. Its unsigned Windows installer supplies the application runtime. Users provision Abaqus, a license and scoped execution authority when needed. [VeriCAE installation](INSTALL.md) · [AbqJobPilot installation](https://github.com/BrunelXian/AbqJobPilot/blob/a7cbf27cee4e049f5cccb21416bdbfb7e8836808/docs/RELEASE_1_0_0.md)

## What has been verified

| Evidence | Actual configuration or operation | Verdict and boundary |
|---|---|---|
| VeriCAE package freeze | Repeated builds from the frozen commit. Isolated Codex installation of the extracted marketplace. | **PASS** for packaging and installation. Installed version 1.0.0 and all 34 plugin files matched. |
| UAT-100 | VeriCAE 0.5.6 Desktop Main and AbqJobPilot 0.5.3 DEV. Main discovered three historical read tools and successfully queried the environment and an existing Receipt. | **PASS** for real Desktop MCP read-only communication. No execution operation took place. The public 1.0.0 pair has no separately recorded end-to-end Desktop qualification. |
| INT-001 | Four roles reviewed a historical real Abaqus axial-bar result. MCP integration, orchestration, numerical verification and independent review passed. | **PARTIAL overall**. Solver completed. Execution and extraction qualification remained `REVIEW_REQUIRED`. Original extraction Receipt `FAILED`; historical result data integrity `INSUFFICIENT`. |
| INT-002A.1 | Independent transaction with real MCP submission, scoped Grant, fake backend, terminal Run and bound test output. | **TEST_ONLY PASS**, `solver_conclusion=NOT_RUN`. The original bridge qualification reported 250 targeted regressions. |
| INT-002B and general REAL execution | INT-002B planning passed. Execution stopped with zero new submissions and unknown current Grant balance. General Plan/environment binding remains open. | **BLOCKED / STOPPED** for INT-002B execution. The autonomous new-task REAL solver loop remains **NOT_READY**. |

The release review checked distribution identities and evidence scope. It carried forward the studies above without rerunning a solver or requalifying historical outputs.
