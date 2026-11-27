# Research agenda · Verifiable agentic simulation

**Under what conditions can a CAE research agent choose its next experiment, and what evidence should make it stop?** VeriCAE makes that question testable. A researcher specifies a quantity of interest, units, admissible model changes, evidence requirements and a stopping condition. Four persistent research roles interpret that contract. AbqJobPilot records which experiment an operator authorized, which process ran and which result bytes it produced.

## Preliminary result

For one linear-elastic T3D2 axial bar, the analytical displacement and the historical Abaqus DAT agreed at −0.010 mm. Independent review also corrected a field attribution. The diagnostic JSON contained the node, increment, step time and value. The named step came from the approved selector, checked against the input and DAT. The original extraction Receipt recorded a failure and the historical output lacked an Owner-bound digest. Agreement justified the displacement finding for this load case, while the evidence chain received a **PARTIAL** verdict. A separate TEST_ONLY bridge study demonstrated bounded submission, idempotent replay, reconnect and result-byte binding with a fake backend. [Historical case](INT-001.md) · [Offline numerical replay](demo/README.md) · [Execution platform](https://github.com/BrunelXian/AbqJobPilot/tree/dev/0.5.3)

## Proposed experiments

| Question | Experiment | Measure |
| --- | --- | --- |
| Can the agent qualify a model for a stated use? | Start with analytical axial and bending cases. Introduce one tagged change at a time in units, constraints, load sign or result selector. Ask the roles to specify which claims survive each change. | False acceptance of invalid cases, false rejection of valid cases and agreement on the affected observable. |
| Does independent review improve the decision? | Compare a single review with a review in which the validator first derives an expectation without seeing the other roles' answers. Include cases with the right number attributed to the wrong step or artifact. | Attribution errors found, unsupported claims accepted and review time. |
| Can an agent choose informative experiments within a budget? | Give a fixed parameter sweep and a goal-driven planner the same qualified model, permitted parameter range, evaluation budget and held-out target. Record each proposed experiment and stopping decision. | Target residual versus evaluations consumed, budget compliance, and stops caused by missing or contradictory evidence. |
| What transfers across solvers or coupled physics? | First map one observable across two single-physics solvers using matched units, locations and loading histories. Then introduce a coupled benchmark with an independent conservation check. | Selector mismatches, agreement within declared discretization error, conservation residual and provenance gaps. |

The proposed deliverables are a benchmark with labeled failure cases, reproducible comparison protocols and decision records that connect each next experiment to a measured residual. A fresh real-solver experiment requires an execution environment bound to its Plan, explicit authorization and reviewable outputs. General real-solver execution and multi-physics or multi-solver studies remain research milestones.
