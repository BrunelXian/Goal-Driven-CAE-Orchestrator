# External audit disposition

Input: `EXTERNAL_AUDIT_20261106/DEEPSEEK_ARCHITECTURE_AUDIT_HANDOFF.md`, SHA256
`affabda80b195ec2b98e19ae6bdc6da9dc5c7a686d9bdac5516a7e08ec452aad`;
full text read. It is an engineering input, not execution permission.

| Finding | Disposition | Actual implementation/evidence |
|---|---|---|
| Same-user DPAPI/HMAC cannot prove independent human origin | ACCEPTED | Explicit trusted-local model; reference, user decision, native Grant are distinct. No claim that buttons prevent a hostile same-user program. |
| Separate service identity/offline human key | DEFERRED | Outside the approved trusted-local V1; existing DPAPI/ACL/native capability remain. |
| Native Owner/Grant/atomic idle boundaries | ACCEPTED | Owner/Grant/Run/lifecycle core bytes retained. Project adapter invokes existing APIs. |
| Failed short-code/focus UX | ACCEPTED | Native same-window two-button review; default cancel; Enter/focus never approve; no focus-loss abort. Read-only full details are not the default view. |
| Budget actual facts and automatic reconciliation | PARTIALLY_ACCEPTED | `workflow.Campaign.counts` actually maps scientific states to `budget_rules.counters`; it does not invoke the synthetic oracle from `research/budget.py`. New native acceptance facts are same-DB provenance, not another balance; original outcome settlement is unchanged. |
| Current B one-generation recovery restriction | ACCEPTED | New versioned execution-window table/CAS; original table/limits retained. No execution retry, no HOLD reset; all ancestors require zero B execution and qualified closure. |
| PID reuse | PARTIALLY_ACCEPTED | Old retained exit evidence remains primary; a different creation time/image identifies an unrelated reused PID. No requirement that an exited PID number stay absent forever. |
| Windows testing absent | PARTIALLY_ACCEPTED | True for the cited auto-idle-stop candidate scope, not every prior historical test. This candidate adds isolated native Windows IPC start/stop and TEST_ONLY button/layout tests; no real B pass is claimed. |
| Core/AgentHub only README | REJECTED AS GENERAL CLAIM | `src/aegiscae/research/main_runtime.py` contains MainRuntime. Absence of a class named AgentHub is not absence of research/runtime code. |
| M0/current architecture doc drift | ACCEPTED | Short M0 scope note plus current local trust supplement; M0 design retained, README not rewritten. |
| Frozen artifacts outside maintainable source | ACCEPTED | Repository overlay source, baseline commit/dirty-state record, exact diff and deterministic rebuild recipe; no auto Git commit. |
| Timing/token/portability debt | DEFERRED BEYOND LOCAL PROFILE | No general workflow, lifecycle platform, new installer or second executor. |

Actual site limitation: the original B Owner crossed a confirmed OS boot and has
no normal stopped marker/retained-exit conclusion for that event. Offline
implementation does not supply that missing terminal qualification. No actual
new B Plan, Grant, Run or Solver is created by this work.
