"""Frozen A02 binding of the unchanged E4G wiring. No automatic execution."""
import hashlib
import json
import os
from pathlib import Path
import sys
import types

A01_SHA = "6f28256b6126349e46785aa1e67de0019c67de750b1df82f1a634cd5c8164c2a"
source = Path(__file__).with_name("d7_e4g_lifecycle.py")
raw = source.read_bytes()
if hashlib.sha256(raw).hexdigest() != A01_SHA:
    raise RuntimeError("E4G_A01_SOURCE_DRIFT")
wire = types.ModuleType("e4g_a02_frozen_wire")
wire.__file__ = str(source)
exec(compile(raw, str(source), "exec"), wire.__dict__)
# Only two fixed task bindings change. No arbitrary path/attempt selection API.
wire.TASK = wire.E2.parent / "GDCAE-D7-E4G-20261102-A02"
wire.PROJECT = wire.TASK / "af-test-only"
PREFERENCES = wire.TASK.with_name(wire.TASK.name + ".ui.json")


def preflight():
    """Files/imports only; must run before GUI creates its preference file."""
    wire.verify_runtime()
    wire.no_links(PREFERENCES)
    wire.need(not wire.TASK.exists() and not PREFERENCES.exists())


def main():
    if sys.argv[1:] == ["--preflight-only"]:
        try:
            preflight()
        except BaseException:
            print(json.dumps({"status": "E4G_A02_PREFLIGHT_BLOCKED", "owner_started": False, "retry": False}))
            return 2
        print(json.dumps({"status": "E4G_A02_PREFLIGHT_PASS", "owner_started": False, "retry": False}))
        return 0
    if sys.argv[1:] == ["--execute-approved-single-attempt"]:
        # GUI and acceptance must use the same explicit process-local preference binding.
        # Its file may now exist from GUI saving; never delete it or rerun preflight.
        if os.environ.get("ABQJOBPILOT_UI_PREFS") != str(PREFERENCES):
            print(json.dumps({"status": "E4G_A02_PREFERENCES_BINDING_BLOCKED", "owner_started": False, "retry": False}))
            return 2
    return wire.main()  # Original confirmation, reservation, start/stop and UNKNOWN rules.


if __name__ == "__main__":
    sys.exit(main())
