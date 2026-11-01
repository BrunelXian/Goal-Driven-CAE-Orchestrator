"""Read-only current-token effective access; never reads capabilities or changes ACLs.

Only security descriptors are read. This does not impersonate another user, grant
privileges, launch a process, validate human approval or qualify HIL enforcement.
"""

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import stat


class AuditBlocked(ValueError):
    pass


def need(value):
    if not value:
        raise AuditBlocked("OPERATOR_AUDIT_UNAVAILABLE")


RIGHTS = {"read_data": 1, "write_data": 2, "append_data": 4,
          "delete": 0x10000, "change_dacl": 0x40000, "change_owner": 0x80000}
RESOURCES = ("code.canary", "config.canary", "capability.canary", "audit.canary")


class CurrentWindowsToken:
    """Query-only handles for this process; no user identity escapes the adapter."""

    def __enter__(self):
        need(os.name == "nt")
        import win32api
        import win32con
        import win32security as security

        self.security = security
        self.token = security.OpenProcessToken(win32api.GetCurrentProcess(),
                                               win32con.TOKEN_QUERY | win32con.TOKEN_DUPLICATE)
        try:
            self.duplicate = security.DuplicateToken(self.token, security.SecurityImpersonation)
        except BaseException:
            self.token.Close()
            raise
        return self

    def __exit__(self, *_args):
        self.duplicate.Close()
        self.token.Close()

    def risk(self):
        s = self.security
        admin = s.CreateWellKnownSid(s.WinBuiltinAdministratorsSid, None)
        groups = s.GetTokenInformation(self.token, s.TokenGroups)
        elevated = bool(s.GetTokenInformation(self.token, s.TokenElevation))
        elevation_type = s.GetTokenInformation(self.token, s.TokenElevationType)
        return {"elevated": elevated,
                "admin_or_linked_admin": any(group == admin for group, _ in groups)
                or elevation_type in (2, 3)}

    def access(self, path, mask):
        s = self.security
        sd = s.GetNamedSecurityInfo(str(path), s.SE_FILE_OBJECT,
                                   s.OWNER_SECURITY_INFORMATION | s.GROUP_SECURITY_INFORMATION
                                   | s.DACL_SECURITY_INFORMATION)
        binary = memoryview(sd).tobytes()
        descriptor = ctypes.create_string_buffer(binary)

        class GenericMapping(ctypes.Structure):
            _fields_ = [(name, wintypes.DWORD) for name in ("read", "write", "execute", "all")]

        mapping = GenericMapping(0x120089, 0x120116, 0x1200A0, 0x1F01FF)
        privileges = ctypes.create_string_buffer(4096)
        length = wintypes.DWORD(len(privileges))
        granted = wintypes.DWORD()
        status = wintypes.BOOL()
        api = ctypes.WinDLL("advapi32", use_last_error=True).AccessCheck
        api.argtypes = [ctypes.c_void_p, wintypes.HANDLE, wintypes.DWORD,
                        ctypes.POINTER(GenericMapping), ctypes.c_void_p,
                        ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
                        ctypes.POINTER(wintypes.BOOL)]
        api.restype = wintypes.BOOL
        need(api(descriptor, int(self.duplicate), mask, ctypes.byref(mapping), privileges,
                 ctypes.byref(length), ctypes.byref(granted), ctypes.byref(status)))
        return "ALLOWED" if status.value and granted.value & mask == mask else "DENIED"


def inspect_fixture(root, backend):
    """Explicit new canary layout only; no arbitrary protected credential paths."""
    root = Path(root)
    need(root.is_absolute() and root.name == "d4-operator-canary" and root.is_dir())
    need(not any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)))
    risk = backend.risk()
    need(type(risk) is dict and set(risk) == {"elevated", "admin_or_linked_admin"}
         and all(type(v) is bool for v in risk.values()))
    access = {}
    for name in RESOURCES:
        path = root / name
        need(path.is_file() and not path.is_symlink() and not path.is_junction())
        rights = {right: backend.access(path, mask) for right, mask in RIGHTS.items()}
        need(all(value in ("ALLOWED", "DENIED") for value in rights.values()))
        access[name.removesuffix(".canary")] = rights
    return {"schema": "gdcae-operator-current-token-audit-v1", "source": "NEW_CANARY_ACL_ONLY",
            "current_token_risk": risk, "effective_rights": access,
            "protected_operator_identity": "NOT_DEPLOYED_OR_VERIFIED",
            "credential_bytes_read": False, "acl_modified": False,
            "HIL_ENFORCEMENT": "BLOCKED", "execution_authorized": False}


def inspect_protected_layout(backend):
    """Prepared post-deployment read-only checks at fixed reviewed paths.

    Not invoked in D4. Run separately under each approved principal after actual
    deployment. A single current-token observation never establishes isolation.
    """
    paths = {
        "code": Path("C:/Program Files/GDCAE Operator/issuer.py"),
        "config": Path("C:/ProgramData/GDCAE Operator/config.json"),
        "capability": Path("C:/ProgramData/GDCAE Operator/capability.dpapi"),
        "audit": Path("C:/ProgramData/GDCAE Operator/approval-audit.jsonl"),
    }
    rows = {}
    for name, path in paths.items():
        presence = _probe_presence(path)
        if presence != "REGULAR_FILE":
            rows[name] = presence
            continue
        need(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)))
        rights = {right: backend.access(path, mask) for right, mask in RIGHTS.items()}
        need(all(value in ("ALLOWED", "DENIED") for value in rights.values()))
        rows[name] = rights
    risk = backend.risk()
    need(type(risk) is dict and set(risk) == {"elevated", "admin_or_linked_admin"}
         and all(type(v) is bool for v in risk.values()))
    return {"schema": "gdcae-operator-protected-layout-observation-v1",
            "source": "CURRENT_TOKEN_ACL_METADATA_ONLY", "effective_rights": rows,
            "current_token_risk": risk, "credential_bytes_read": False,
            "acl_modified": False, "cross_principal_qualification": "NOT_VERIFIED",
            "HIL_ENFORCEMENT": "BLOCKED", "execution_authorized": False}


def _probe_presence(path):
    try:
        value = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return "NOT_DEPLOYED"
    except PermissionError:
        return "NOT_OBSERVED_ACCESS_DENIED"
    except OSError:
        return "NOT_OBSERVED_IO_ERROR"
    return "REGULAR_FILE" if stat.S_ISREG(value.st_mode) else "NOT_REGULAR_FILE"
