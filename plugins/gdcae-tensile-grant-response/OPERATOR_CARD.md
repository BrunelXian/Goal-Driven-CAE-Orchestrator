# Grant response recovery — offline candidate, no actual continuation

This version does not authorize a new Plan, Grant, Submit, Dispatch, Owner stop or Solver. The original B Plan and Grant have expired. A confirmed historical Grant does not regain execution validity.

The frozen installed read-only CLI is:

```powershell
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -I -B -S 'D:\Projects\GDCAETEST\TENSILE-GRANT-RESPONSE-20261107-dev-4d9e7c1b20\gd\grant_response.py' --journal 'D:\Projects\GDCAETEST\TENSILE-R4-JIT-A-20261105-MAIN-8fb1ad880d\research\operator-39379097202a4eb68fc3190c6e951bf4' --package-pin '7174ae94e46617d4934ac0ec36a92c86691cb2b26b51e7b9bf6e07ba781ec798' --python-exe 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe'
```

Run only after independent candidate verification, saving stdout/stderr in a fresh independent evidence directory. Do not redirect into the old operation directory. The CLI itself writes nothing. It does not retry authorization and accepts no mutation/action option.

Expected for the actual original expired request: original key `authorize_589b90728a5f429a9d0acecf3e6942f9`, same Grant `grant_b5d117a4d02f48239ffca6f0f95f1f8f`, same Plan `plan_9e12e6ddae214fe19e0d12364210ba34`; `confirmed_committed=true`, `executable_now=false`, `historical_runtime_readonly=true`, `runtime_compatible_for_execution=false`, `expired=true`, `automatic_resume=false`. A mismatch or unqueryable Owner is BLOCKED/UNKNOWN, not permission to retry. No receipt means unknown acceptance, never permission to issue another Grant. No original journal/ledger backfill is allowed by this card.

The new reader validates original .11.1 freeze, source/installed files and runtime identities, then uses its original qualified scientific snapshot reader. It does not substitute .12 identity into the old Plan. New-version automatic response recovery applies only inside a future separately authorized .12 operation: its single send may be followed by read-only same-key acknowledgement checks; only complete fresh checks and remaining original validity permit the already authorized flow to continue. This card does not start that flow.

`automatic_resume=false` describes the read-only CLI/report; it is not a claim that the new inline call cannot continue. The inline function can continue its same call after verified acknowledgement, without another authorize, key, human approval or new Grant. It still rechecks before Submit and uses native execution gates. UI files and native AF authorization/transport implementation are unchanged. This is not a general retry or timeout increase.

States: REQUEST_NOT_PERSISTED; REQUEST_PERSISTED_NOT_SENT (new explicit journal sequence only); SENT_ACCEPTANCE_UNKNOWN; COMMITTED_RESPONSE_RECOVERED; RECEIPT_RECEIVED. Every state independently reports execution validity. Legacy missing send-intent is conservative unknown; it is never taken as proof that nothing was sent.

Main remains the only actual-site operator. Testing may execute the read-only CLI under this task's explicit read-only scope. This phase ends after independent evidence review.
