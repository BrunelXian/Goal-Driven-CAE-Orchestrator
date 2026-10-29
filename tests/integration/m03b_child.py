"""Explicit test child, one coordinator advancement; no owner creation."""

import os
import sys
import time
from pathlib import Path

from m03b_support import load_af, read, reopen, write_new


def main():
    load_af()
    from abqjobpilot.execution.ownership import current_process_identity
    from aegiscae.research import workflow
    root, control, stage = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    check_deadline = time.monotonic() + 30
    write_new(control / "identity.pending", current_process_identity())
    (control / "identity.pending").replace(control / "identity.json")
    while not (control / "go.json").exists():
        if time.monotonic() >= check_deadline:
            raise TimeoutError("PARENT_HANDSHAKE_EXPIRED")
        time.sleep(0.01)
    coordinator = reopen(root)
    if stage == "exit_after_accept":
        coordinator.execution_port.fault = stage
    elif stage != "none":
        def fault(value):
            if value == stage:
                os._exit(73)
        workflow._fault = fault
    revision = read(control / "go.json")["revision"]
    try:
        result = coordinator.advance(revision)
        value = {"state": result["state"]}
    except Exception as exc:
        value = {"error": getattr(exc, "code", type(exc).__name__)}
    write_new(control / "result.json", value)


if __name__ == "__main__":
    main()
