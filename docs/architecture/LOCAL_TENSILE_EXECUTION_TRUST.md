# Local tensile execution profile — current implementation boundary

This local profile uses Codex Main for research decisions, GD campaign records for
the frozen scientific request/HOLD/results, and AbqJobPilot for native
Plan/Grant/Run/Receipt, capability checks and atomic lifecycle operations. The
Milestone 0 solver-neutral Runtime architecture is a separate design scope.

The threat model is a trusted researcher and trusted Agent on the same Windows
account. DPAPI and ACLs protect cross-user/machine access; they do **not** isolate
arbitrary programs under that same user. A task reference or capability-key HMAC
records provenance/integrity, not an independent human signature.

An actual user mouse decision on the current exact Plan is distinct from the
subsequent native Grant. Enter, focus, UI initialization, a research agreement or
generated model text cannot approve execution. The frozen contract still requires
separate exact approval and zero automatic retries. UI machine tests are explicitly
TEST_ONLY and never represent a real researcher approval.

Normal idle cleanup can be explicitly delegated for an exact local operation.
The delegation reference constrains that operation; the existing AF lifecycle
capability and native atomic idle transaction remain the authority. Unknown
state, active work, reboot without a normal-stop receipt, or a missing exit proof
does not become an orderly stop. No force-kill fallback is added.

Execution-window records share the campaign's existing workflow database. They
version only the execution binding, retain every earlier Plan and the same B
request/HOLD, and use durable intent/CAS plus same-operation reconciliation.
Pending bindings cannot authorize. Native accepted-consumption facts are recorded
separately from scientific outcomes; the frozen workflow's terminal settlement
timing is retained, with no Grant-only charge or duplicate charge on feedback replay.

Product source/rebuild input: `plugins/gdcae-tensile-usability/`. Frozen artifacts
and test evidence remain external to the installable runtime. The current real B
site is blocked by its cross-boot lifecycle evidence; this profile does not repair
or replace those records.
