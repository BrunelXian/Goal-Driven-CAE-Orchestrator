# Expired, unconsumed B Grant — offline candidate .13

Status: DEVELOPMENT CANDIDATE; no site recovery authorization. This card never stops an Owner, creates a Plan, issues a Grant or submits a Job.

The actual historical Owner is still CONNECTED. **SITE_READY=false: a legally verified terminal and retained process-exit evidence are missing.** The existing Grant remains expired and immutable. An expired Grant is not a consumed attempt; A remains charged once and B holds the same remaining attempt (2/1/1/0). Do not run archive against the historical workspace in this stage.

## Preparation and authority

Use the candidate's actual `gd/expired_grant.py`, package-manifest SHA and absolute Python 3.12.10. Every command uses `-I -B -S`. No development-source fallback. Verify FREEZE before use. The CLI is local trusted-user machinery, not a permission issuer: an authorization reference or its hash cannot grant permission. Future site qualification append requires its own applicable authorization; the present GO permits isolated offline projects only.

A proposal requires: the exact original authorization journal/installation, the same scientific B/request/contract/HOLD, exactly one matching expired Grant and native authorization receipt/control record, zero Run/Receipt/consumption/unknown execution, a native normal idle-stop receipt plus retained handle exits, and unchanged full ancestry. Missing or contradictory evidence refuses. Old zero-Grant qualifications keep their original strict behavior.

## Exact existing CLI shapes (future approved, isolated paths only)

Set PY to `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`, GD to this candidate's installed `gd`, and PACKAGE to SHA256 of its package-manifest.json. WORK/CONTRACT/OP/JOURNAL/CLOSURE/CLOSURE_SHA must identify one approved project and operation, never default Recent. OP is a unique 32-lowercase-hex qualification ID. CLOSURE is the existing protected normal-stop reference JSON; CLOSURE_SHA is its raw file SHA256.

```powershell
& $PY -I -B -S "$GD\expired_grant.py" propose --workspace $WORK --contract-pin $CONTRACT --package-pin $PACKAGE --python-exe $PY --operation-id $OP --journal $JOURNAL --closure $CLOSURE --closure-pin $CLOSURE_SHA
```

`propose` is read-only and does not start a Plan TTL. Persist stdout only to a new external evidence file. It returns a canonical-object bare 64-hex `proposal_digest`; do not substitute file SHA256 or prefix it. The proposal file can be the full returned object or its `proposal` member.

```powershell
& $PY -I -B -S "$GD\expired_grant.py" archive --workspace $WORK --contract-pin $CONTRACT --package-pin $PACKAGE --python-exe $PY --operation-id $OP --proposal $PROPOSAL_FILE --proposal-pin $PROPOSAL_DIGEST
& $PY -I -B -S "$GD\expired_grant.py" read --workspace $WORK --contract-pin $CONTRACT --package-pin $PACKAGE --python-exe $PY --operation-id $OP
```

`archive` performs one CAS transaction and creates/appends only `tensile_expired_unconsumed_grants` in the existing workflow DB. It never changes native Grant/Plan, stages/history, balances or results. Identical replay returns the original reference after fresh native checks; conflicting/duplicate grant or parent refuses. After an uncertain response, use `read` for the same OP; do not create another OP. The new row is an evidence qualification, not an execution or renewal permission and not Core project revision.

The returned reference has exactly schema=`expired-unconsumed-grant-reference-v1`, operation_id, body_digest, workspace. This reference feeds the existing .13 operator_entry static/review scope. Static does not prepare a Plan. Only a separately permitted new review window may prepare a new unique Plan; its actual button approval must independently authorize its exact Plan and native Grant. The old button, old Grant and old decision are never reusable. Zero automatic Solver retry remains unchanged.

## Write/stop boundaries

Read-only open never creates the new table. Archive writes no AF database or lifecycle file. New-window preparation retains its existing cross-database INTENT/COMMITTED process: pending/unknown can only reconcile the same operation. Every native strict admission rereads the archived old native Grant, normal stop and protected exits, rather than trusting a JSON reference alone. Actual B terminal later consumes only the original HOLD according to the existing scientific outcome transaction: expected 2/0/2/0, independent of MATCH/MISS.

No user GUI or actual B execution was tested in this development stage. Machine-generated test decisions are not human B approval. Old and new UI bytes are identical. A normal native stop receipt and retained tracked exits prove only their actual tracked process identities, not arbitrary descendants.
