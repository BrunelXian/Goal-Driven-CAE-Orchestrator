# Bind native scoped sessions without adding a runtime

AOO-V1-01 keeps scientific reasoning in the native Main and execution authority
in existing AF. SessionHub adds a bounded Project-owned session mapping using
the existing ResearchProject transaction lock and an atomic sidecar file. It
does not extend scientific events, create another database, run models or own
a scheduler. Persist intent before host calls; UNKNOWN never triggers blind
recreation. This trades automatic recovery for unambiguous side-effect history.

Native roles are preferred. The currently exposed native-agent IDs have no
verified Desktop thread/title/interactive-session mapping; the Desktop creation
tool has no enforced native role/tool binding. The production adapter therefore
blocks that creation path, while independently testable policy and mappings are
implemented. A task prompt or title cannot compensate for the missing bridge.
This preserves required scoped interaction without inventing new authorization
or weakening the existing four specialist feature restrictions.

This is a new candidate. Its whole Core digest differs from frozen D7 and from
the separately retained Recovery candidate. Neither is migrated by this change.
