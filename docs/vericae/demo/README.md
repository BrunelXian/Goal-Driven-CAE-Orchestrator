# Recheck the INT-001 axial bar

VeriCAE's four research roles reviewed the displacement of a two-node truss from a historical Abaqus analysis. Follow their comparison from the frozen model to the printed node table, then inspect the diagnostic file whose provenance limited the final verdict.

| Historical observation | Result |
| --- | --- |
| Axial solution · node 2, global U2 | **−0.010 mm** |
| Abaqus DAT · last increment, TIP set | **−0.010000000 mm** |
| ODB diagnostic minus DAT | **+2.235174179 × 10⁻¹⁰ mm** |
| Historical evidence qualification | **PARTIAL** |

## Replay the comparison

From the checkout root, run this command in PowerShell 5.1 or later. The script reads three local files, verifies their SHA-256 digests and prints the numerical comparison. A solver, license and MCP connection are unnecessary.

```powershell
./docs/vericae/demo/replay.ps1
```

The last two lines should read `Analytical / DAT comparison     PASS` and `Historical evidence verdict     PARTIAL`. The first is calculated during the replay. The second quotes the study's recorded verdict.

## Trace one displacement

1. In the [frozen input](axial_bar.inp), one T3D2 element connects nodes at Y = 0 and 10 mm. Node 1 is fixed. At node 2, only U2 is free. With E = 1000 N/mm² and A = 1 mm², the axial stiffness EA/L is 100 N/mm. The applied −1 N gives U2 = FL/(EA) = −0.010 mm.
2. In the [historical DAT excerpt](tip-table.txt), find step 1, increment 1, step time 1.00, node set TIP. Read the U2 column for node 2. The negative sign denotes displacement toward the fixed end. The frozen input maps step 1 to `LOAD`.
3. In the [historical diagnostic JSON](u2.json), read `measurement.value_mm` as a decimal. The file supplies the node, increment, step time and value. The approved selector and the INP/DAT establish the step name and component. The numerical agreement has a narrower scope than the execution evidence.

## What the files preserve

The 399-byte INP and the 100-byte diagnostic JSON are byte-identical copies of the study inputs to this comparison. The DAT excerpt retains lines 126, 182, 186, 196, 198 and 201 of the archived DAT, with only surrounding whitespace removed and LF line endings. The full DAT's archived SHA-256 is `aa2e86e6315a2f1fe123d1a41265a6a77e856cc841e72bb0b5ef9e8f398b66dd`. The public excerpt has its own digest in the [replay script](replay.ps1). The `TEST_ONLY` string in the deck heading is a fixture label retained verbatim in the historical real solver output.

The historical extraction Receipt recorded **FAILED**. Both execution and extraction qualification remained **REVIEW_REQUIRED**, and historical result-data integrity remained **INSUFFICIENT**. A local checksum identifies the published file. The missing link is the historical Owner's attestation that this extraction produced those bytes. [Full case findings](../INT-001.md)
