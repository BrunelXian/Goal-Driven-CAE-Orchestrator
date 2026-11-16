"""Private worker of the verified installed launcher; no CLI command or executable parameter."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def sdk_directory(executable):
    folder = Path(executable).parent
    prefix = folder.parent if folder.name.lower() == "scripts" else folder
    return prefix/"Lib/site-packages"


async def collect():
    plugin = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(plugin/"scripts"))
    import main as driver

    request = json.loads(sys.stdin.buffer.read(8193))
    driver.require(set(request) == {"root","host","desktop","queue","binding","consent"}, "INVALID_T02_REQUEST")
    data = driver.binding_path().read_bytes()
    driver.require(driver.sha(data) == request["binding"], "BINDING_RECEIPT_MISMATCH")
    bound = json.loads(data)
    driver.require(bound["plugin"] == str(plugin) and bound["runtime"] == driver.interpreter_identity(plugin),
                   "INSTALLATION_IDENTITY_MISMATCH")
    driver.core_bytes(plugin,bound["package_manifest_sha256"])
    import agreement_main
    agreement_main.load_core(plugin)
    from aegiscae.research.project import open_agreement_project
    from aegiscae.research.capability_discovery import local
    from abqjobpilot_readonly import observe
    from t02_service import authorized, scope_for

    project = open_agreement_project(local(request["root"]))
    host, desktop, queue = request["host"], request["desktop"], request["queue"]
    base, profile, policy, card, pair, permit = scope_for(plugin,project,host,desktop,queue)
    authorized(card,pair,permit)
    driver.require(card["execution"] == "IN_PROGRESS" and permit["sha256"] == request["consent"], "T02_READ_CONSENT_REQUIRED")
    sdk = local(sdk_directory(sys.executable))
    driver.require(sdk.is_dir(), "MCP_CLIENT_SDK_UNAVAILABLE")
    # No site initialization, PYTHONPATH, user site, .pth execution or executable from the research request.
    win32 = local(sdk/"win32")
    win32_lib = local(win32/"lib")
    dlls = local(sdk/"pywin32_system32")
    driver.require(all(p.is_dir() for p in (win32,win32_lib,dlls)), "MCP_CLIENT_SDK_UNAVAILABLE")
    sys.path.extend(map(str,(sdk,win32,win32_lib)))
    # Hold the DLL directory handle through the native MCP transport lifetime.
    dll_handle = os.add_dll_directory(str(dlls))
    from importlib.metadata import PackageNotFoundError, version
    try:
        driver.require(version("mcp") == "2.3.0", "MCP_CLIENT_SDK_INCOMPATIBLE")
        from mcp import Client, StdioServerParameters
    except (ImportError, PackageNotFoundError):
        raise ValueError("MCP_CLIENT_SDK_UNAVAILABLE") from None
    archive = local(base/"server.zip").read_bytes()
    driver.require(hashlib.sha256(archive).hexdigest() == policy["source_sha256"], "BACKEND_SOURCE_MISMATCH")
    # Snapshot the validated bytes before starting the fixed vendor module.
    with tempfile.TemporaryDirectory(prefix="gdcae-t02-") as tmp:
        package = Path(tmp)/"server.zip"
        package.write_bytes(archive)
        bootstrap = ("import os,runpy,sys;from pathlib import Path;sys.path.insert(0,sys.argv.pop(1));"
                     "sdk=Path(sys.argv.pop(1));sys.path.extend(map(str,(sdk,sdk/'win32',sdk/'win32/lib')));"
                     "dll_handle=os.add_dll_directory(str(sdk/'pywin32_system32'));"
                     "runpy.run_module('abqjobpilot.mcp.server',run_name='__main__')")
        params = StdioServerParameters(command=sys.executable,cwd=tmp,
            args=["-I","-B","-S","-c",bootstrap,str(package),str(sdk),"--project",profile["backend_root"]])
        async with asyncio.timeout(55):
            async with Client(params,mode="legacy",read_timeout_seconds=15) as client:
                report = await observe(client,project,host,desktop,profile["backend_id"],queue_id=queue)
    dll_handle.close()
    return {"status":"OBSERVED","observation":report,"consent":permit["sha256"]}


def reason(error):
    import re
    if isinstance(error,BaseExceptionGroup):
        codes = {reason(child) for child in error.exceptions}
        return codes.pop() if len(codes)==1 else "MCP_SESSION_FAILED"
    if isinstance(error,TimeoutError):
        return "MCP_TIMEOUT"
    code = str(error)
    return code if re.fullmatch(r"[A-Z_]{3,64}",code) else "MCP_SESSION_FAILED"


if __name__ == "__main__":
    try:
        print(json.dumps(asyncio.run(collect())))
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED","reason":reason(exc)}))
        sys.exit(2)
