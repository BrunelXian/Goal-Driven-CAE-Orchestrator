"""Read-only own-token/explicit-path probe. No other processes, secrets or ACL writes."""

import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import winreg


def host_digest():
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography",
                        0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
        guid = winreg.QueryValueEx(key, "MachineGuid")[0]
    return hashlib.sha256(str(guid).encode("utf-8")).hexdigest()


def current_identity():
    import win32api
    import win32con
    import win32security as security

    token = security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    try:
        user = security.GetTokenInformation(token, security.TokenUser)
        sid = security.ConvertSidToStringSid(user[0] if isinstance(user, tuple) else user)
        name, domain, _kind = security.LookupAccountSid(None, user[0] if isinstance(user, tuple) else user)
        groups = security.GetTokenInformation(token, security.TokenGroups)
        administrator = any(security.ConvertSidToStringSid(s) == "S-1-5-32-544" for s, _ in groups)
        elevated = bool(security.GetTokenInformation(token, security.TokenElevation))
        elevation_type = security.GetTokenInformation(token, security.TokenElevationType)
        privileges = security.GetTokenInformation(token, security.TokenPrivileges)
        enabled = [security.LookupPrivilegeName(None, luid) for luid, flags in privileges if flags & 2]
        try:
            thread_token = security.OpenThreadToken(win32api.GetCurrentThread(), win32con.TOKEN_QUERY, True)
        except Exception as exc:
            if getattr(exc, "winerror", None) != 1008:
                raise ValueError("THREAD_IDENTITY_UNKNOWN") from None
            impersonating = False
        else:
            thread_token.Close()
            impersonating = True
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
        kernel.IsProcessInJob.restype = wintypes.BOOL
        in_job = wintypes.BOOL()
        if not kernel.IsProcessInJob(kernel.GetCurrentProcess(), None, ctypes.byref(in_job)):
            raise ValueError("JOB_MEMBERSHIP_UNKNOWN")
        accounts = {}
        for proposed in ("GDCAEResearch", "GDCAEIssuer"):
            try:
                other, _domain, kind = security.LookupAccountName(None, ".\\" + proposed)
            except Exception as exc:
                accounts[proposed] = {"status": "ABSENT" if getattr(exc, "winerror", None) == 1332 else "UNKNOWN"}
            else:
                accounts[proposed] = {"status": "NAME_CONFLICT", "sid": security.ConvertSidToStringSid(other),
                                      "kind": kind, "same_as_current": other == (user[0] if isinstance(user, tuple) else user)}
        return {"schema": "gdcae-current-token-probe-v1", "scope": "THIS_TOOL_PROCESS_NOT_DESKTOP_PROCESS",
                "host_sha256": host_digest(), "windows_version": platform.version(),
                "sid": sid, "account": domain + "\\" + name,
                "elevated": elevated, "admin_or_linked_admin": administrator or elevation_type in (2, 3),
                "impersonating": impersonating, "in_job": bool(in_job.value),
                "enabled_privileges": sorted(enabled), "accounts": accounts}
    finally:
        token.Close()


def public_summary(value):
    return {key: value[key] for key in ("schema", "scope", "windows_version", "elevated",
            "admin_or_linked_admin", "impersonating", "in_job", "enabled_privileges")} | {
        "identity_sha256": hashlib.sha256(value["sid"].encode()).hexdigest(),
        "accounts": {name: item["status"] for name, item in value["accounts"].items()}}


def inspect_access():
    """Own-token AccessCheck, metadata only, fixed future A layout; no test writes.

    The exact live AF DB path must later come from a frozen ProjectContext. A
    parent-directory denial here is not a replacement for that final-file test.
    """
    spec = importlib.util.spec_from_file_location("operator_readonly_audit", Path(__file__).with_name("audit.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    paths = {
        "code": "C:/Program Files/GDCAE Operator",
        "rules": "C:/Program Files/GDCAE Operator/code/abqjobpilot/execution/rod_authority.py",
        "config": "C:/ProgramData/GDCAE Operator/config",
        "projects_parent": "C:/ProgramData/GDCAE Operator/projects",
        "future_A_capability": "C:/ProgramData/GDCAE Operator/projects/A/private/standard-operator.json",
    }
    result = {}
    with module.CurrentWindowsToken() as token:
        for label, location in paths.items():
            path = Path(location)
            if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
                result[label] = {"status": "BLOCKED_REPARSE"}
            elif not path.exists():
                result[label] = {"status": "NOT_PROVISIONED"}
            else:
                result[label] = {"status": "CURRENT_TOKEN_CHECKED", "rights": {
                    name: token.access(path, mask) for name, mask in module.RIGHTS.items()}}
    return {"source": "CURRENT_TOOL_TOKEN_ACCESSCHECK", "resources": result,
            "final_grant_store": "AF_CONTEXT_FILE_BINDING_REQUIRED",
            "execution_authorized": False, "mutation_performed": False}


if __name__ == "__main__":
    # No raw identity or hostname is emitted by the ordinary command line.
    if sys.argv[1:] not in ([], ["--access"]):
        raise SystemExit("READ_ONLY_FIXED_ACCESS_PROBE_ONLY")
    try:
        result = public_summary(current_identity())
        if sys.argv[1:]:
            result["access"] = inspect_access()
        print(json.dumps(result))
    except Exception:
        print('{"status":"BLOCKED","code":"IDENTITY_PROBE_UNAVAILABLE"}')
        raise SystemExit(1) from None
