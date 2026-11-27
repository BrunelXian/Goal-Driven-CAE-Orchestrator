# Engineering case study · VeriCAE × AbqJobPilot

**Research Engineer — Agentic AI for Engineering / Simulation**

An agent reported the correct displacement of an Abaqus truss. Could another engineer establish which node, load step and output file supported that number? This project splits the problem between VeriCAE, which manages the scientific decision, and AbqJobPilot, which manages authority to execute and evidence about what happened.

## One model, two decisions

The reference model is small enough to inspect in full. Its two nodes are 10 mm apart, its axial stiffness is 100 N/mm, and −1 N acts on the free node along global Y. The analytical result is −0.010 mm. The historical Abaqus DAT gives −0.010000000 mm at node 2. The ODB diagnostic differs by only +2.235174179 × 10⁻¹⁰ mm.

Independent Validation derived the result before reviewing the CAE and Results reports. It identified where the step name came from and reconciled that selector with the input and DAT. The displacement check passed. The extraction Receipt was **FAILED**, execution and extraction qualification were **REVIEW_REQUIRED**, and the historical output lacked an Owner-bound digest. The overall evidence verdict was **PARTIAL**. Another engineer can inspect the three published data files and rerun the arithmetic locally. [Reproduce the comparison](demo/README.md) · [Review the historical findings](INT-001.md)

## Engineering decisions

| Design decision | What it made possible to check |
| --- | --- |
| Keep one research-state writer. Main dispatches scoped Task Cards to CAE, Results and Independent Validation in persistent native conversations. | A reviewer can trace a final claim back to its task, the originating role's reply and the independent derivation. |
| Bind the Project, Plan, input identity and budget to the execution Grant. Persist the original acceptance Receipt. | In the TEST_ONLY bridge, replaying a request returned the original Receipt. A second stdio client recovered the same terminal Run after disconnect. |
| Check the generated JSON against its Run, Attempt and SHA-256. Record solver outcome, process containment and evidence qualification separately. | The fake backend demonstrated result binding with `solver_conclusion=NOT_RUN`. Engineers could also preserve the historical extraction failure alongside the correct numerical result. |
| Treat Owner identity as a prerequisite for trusted readback. | During INT-002B, MCP tool discovery still worked after the original Owner disappeared. The failed identity check left the current balance unverified. The team stopped before submitting a new task. |

## Portfolio summary

Designed a four-role CAE research workflow in Codex and a companion Windows execution platform with scoped Grants, durable Run receipts and MCP integration. Cross-verified a historical Abaqus displacement against an analytical solution and traced an unresolved extraction-provenance gap. Demonstrated budget enforcement, idempotency and output binding on a TEST_ONLY backend with 250 targeted regression checks in the original bridge qualification. [VeriCAE research preview](../../README.md) · [AbqJobPilot development source](https://github.com/BrunelXian/AbqJobPilot/tree/dev/0.5.3)
