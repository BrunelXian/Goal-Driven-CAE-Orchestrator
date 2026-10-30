"""Bounded G2 canary inspection; never reads real credentials or changes ACLs."""

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

PYTHON = Path("D:/XianLab/envs/LangChainEnv/Scripts/python.exe")


def token_projection(salt):
    """Compare actual process user tokens without returning a user/SID to tools."""
    if os.name != "nt":
        raise ValueError("WINDOWS_REQUIRED")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    advapi.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                       ctypes.POINTER(wintypes.HANDLE)]
    advapi.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                          ctypes.c_void_p, wintypes.DWORD,
                                          ctypes.POINTER(wintypes.DWORD)]
    advapi.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p,
                                           ctypes.POINTER(wintypes.LPWSTR)]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
        raise ValueError("TOKEN_QUERY_FAILED")
    try:
        length = wintypes.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(length))
        if not 0 < length.value < 65536:
            raise ValueError("TOKEN_QUERY_FAILED")
        buffer = ctypes.create_string_buffer(length.value)
        if not advapi.GetTokenInformation(token, 1, buffer, length, ctypes.byref(length)):
            raise ValueError("TOKEN_QUERY_FAILED")
        sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        text = wintypes.LPWSTR()
        if not advapi.ConvertSidToStringSidW(sid, ctypes.byref(text)):
            raise ValueError("TOKEN_QUERY_FAILED")
        try:
            key = hashlib.sha256((salt + text.value).encode("utf-8")).hexdigest()
        finally:
            kernel.LocalFree(ctypes.cast(text, ctypes.c_void_p))
        elevation = wintypes.DWORD()
        if not advapi.GetTokenInformation(token, 20, ctypes.byref(elevation),
                                         ctypes.sizeof(elevation), ctypes.byref(length)):
            raise ValueError("TOKEN_QUERY_FAILED")
        return {"token_key": key, "elevated": bool(elevation.value)}
    finally:
        kernel.CloseHandle(token)


def _child(root, salt):
    result = token_projection(salt)
    secret = (root / "capability.canary").read_bytes()
    result["capability_read"] = len(secret) == 32
    target = root / "operator-code.canary"
    result["code_read"] = target.read_bytes() == b"CANARY_ONLY_ORIGINAL"
    target.write_bytes(b"CANARY_ONLY_CHILD_WRITE")
    result["code_write"] = target.read_bytes() == b"CANARY_ONLY_CHILD_WRITE"
    return result


def run(task_root):
    if not task_root.is_absolute() or not task_root.is_dir():
        raise ValueError("TASK_ROOT_INVALID")
    if not task_root.name.startswith("gdcae-m03f1p1-g2long-"):
        raise ValueError("TASK_ROOT_INVALID")
    if any(p.is_symlink() or p.is_junction() for p in (task_root, *task_root.parents)):
        raise ValueError("TASK_ROOT_INVALID")
    root = task_root / "hil-canary"
    root.mkdir()  # exclusive, no old canary/credential reuse
    (root / "capability.canary").write_bytes(secrets.token_bytes(32))
    (root / "operator-code.canary").write_bytes(b"CANARY_ONLY_ORIGINAL")
    salt = secrets.token_hex(16)
    parent = token_projection(salt)
    started = time.time_ns()
    child = subprocess.Popen([str(PYTHON), "-B", str(Path(__file__).resolve()),
                              "--child", str(root)], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    timed_out = False
    try:
        output, error = child.communicate(salt.encode("ascii"), timeout=20)
    except subprocess.TimeoutExpired:
        timed_out = True
        child.kill()  # only this owned handle
        output, error = child.communicate(timeout=10)
    finally:
        child.stdin.close()
        child.stdout.close()
        child.stderr.close()
    if timed_out or child.returncode != 0 or error or len(output) > 2048:
        raise ValueError("CANARY_CHILD_FAILED")
    observed = json.loads(output)
    expected = {"token_key", "elevated", "capability_read", "code_read", "code_write"}
    if set(observed) != expected:
        raise ValueError("CANARY_CHILD_FAILED")
    result = {"schema": "g2-canary-inspection-v1", "status": "OBSERVED",
              "same_process_user": parent["token_key"] == observed["token_key"],
              "parent_elevated": parent["elevated"],
              "child_elevated": observed["elevated"],
              "canary_capability_read": observed["capability_read"],
              "canary_operator_code_read": observed["code_read"],
              "canary_operator_code_write": observed["code_write"],
              "owned_pid": child.pid, "created_at_ns": started,
              "exit_code": child.returncode, "process_exited": True,
              "real_credentials_accessed": False, "acl_modified": False,
              "actual_operator_identity": "NOT_DEPLOYED_OR_VERIFIED",
              "mcp_service_identity": "NOT_INSPECTED",
              "network_or_elevation_path": "NOT_TESTED",
              "hil_enforcement": "NOT_VERIFIED"}
    (root / "result.safe.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--child":
            print(json.dumps(_child(Path(sys.argv[2]), sys.stdin.buffer.read(64).decode("ascii"))))
        elif len(sys.argv) == 2:
            print(json.dumps(run(Path(sys.argv[1]))))
        else:
            raise ValueError("INVALID_ARGUMENTS")
    except (ValueError, OSError, KeyError, subprocess.SubprocessError):
        print('{"status":"BLOCKED","code":"CANARY_INSPECTION_FAILED"}')
        raise SystemExit(2)
