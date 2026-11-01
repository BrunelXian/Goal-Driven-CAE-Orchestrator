"""Explicit isolated-home auth check only. No model, thread or App Server start.

One owned invocation; writes only a new private test HOME and sanitized outcome.
Never imports or copies authentication state from the user's existing HOME.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def probe(executable, root):
    root, executable = Path(root), Path(executable)
    if (not root.is_absolute() or root.parent != Path(tempfile.gettempdir()).resolve()
            or not root.name.startswith("gdcae-m03f1-") or root.resolve() != root
            or not executable.is_absolute() or executable.name != "codex.exe"):
        raise ValueError("INVALID_OWNED_PROBE")
    marker = root / "auth-probe-intent.json"
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"attempt_limit": 1, "operation": "isolated-home-login-status"}, stream)
    home = root / "isolated-codex-home"
    home.mkdir()
    # Whitelist basic process environment; no inherited tokens, parent thread IDs,
    # CODEX_HOME, session metadata, provider overrides or SQLite state root.
    allowed = {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "TEMP", "TMP", "USERPROFILE",
               "APPDATA", "LOCALAPPDATA", "COMSPEC"}
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    env.update(CODEX_HOME=str(home), CODEX_SQLITE_HOME=str(home / "sqlite"))
    outcome = {"schema": "m03f1-auth-probe-v1", "fresh_home": True, "credential_copy": False,
        "global_config_changed": False, "thread_calls": 0, "turn_calls": 0,
        "raw_output_saved": False, "authenticated": False}
    try:
        result = subprocess.run([str(executable), "login", "status"], cwd=root / "empty-work",
            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        outcome.update(exit_code=result.returncode, stdout_bytes=len(result.stdout),
                       stderr_bytes=len(result.stderr), process_exited=True)
        # Exit zero is only an auth-status observation, never full capability permission.
        outcome["authenticated"] = result.returncode == 0
        outcome["status"] = "AUTH_STATUS_AVAILABLE" if result.returncode == 0 else "BLOCKED_TEST_AUTH"
    except subprocess.TimeoutExpired:
        outcome.update(status="AUTH_PROBE_TIMEOUT", process_exited=True)
    with (root / "auth-probe-result.json").open("x", encoding="utf-8") as stream:
        json.dump(outcome, stream, indent=2)
    return outcome


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("EXPLICIT_EXE_AND_TEST_ROOT_REQUIRED")
    print(json.dumps(probe(sys.argv[1], sys.argv[2])))
