"""Portable Windows entry point for the public historical SP comparison."""
import argparse
import csv
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType

VERSION = "0.2.0-preview.6"
CORE_VERSION = "sp-history-1.0.0"
CORE_SHA = "df8e330150d4959eb55f6add60b92eba41395d68c4794f68dd558834b67ef535"
FILES = {"plugin.json", "skills/research/SKILL.md", "scripts/main.py",
         "scripts/launch.ps1", "core/sp_history.py", "references/sanity-model-protocol.md",
         "scripts/agreement_main.py", "runtime/agreement-core.zip","references/research-agreement.md",
         "LICENSE", "assets/mesh.png", "skills/setup/SKILL.md", "scripts/runtime.ps1",
         "scripts/runtime-checks.ps1", "runtime/cpython-windows.json", "references/runtime-options.md"}
COMPAT = ".codex-plugin/plugin.json"

def require(condition, error):
    if not condition:
        raise ValueError(error)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def metadata_digest(data):
    def unique(pairs):
        obj = dict(pairs)
        require(len(obj) == len(pairs), "DUPLICATE_METADATA_KEY")
        return obj

    require(len(data) <= 65536, "METADATA_SIZE_LIMIT")
    obj = json.loads(data.decode("utf-8"), object_pairs_hook=unique)
    require(isinstance(obj, dict), "INVALID_METADATA_OBJECT")
    return sha(json.dumps(obj, ensure_ascii=True, allow_nan=False, sort_keys=True,
                          separators=(",", ":")).encode("ascii"))

def checked(path):
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "ABSOLUTE_LOCAL_PATH_REQUIRED")
    for entry in (path, *path.parents):
        require(not entry.is_symlink() and not entry.is_junction(), "REPARSE_POINT_DENIED")
    return path.resolve()

def core_bytes(plugin, manifest_pin):
    data = (checked(plugin/"package-manifest.json")).read_bytes()
    require(sha(data) == manifest_pin, "PACKAGE_MANIFEST_MISMATCH")
    manifest = json.loads(data)
    require(manifest["version"] == VERSION and set(manifest["files"]) == FILES, "PACKAGE_FILESET_MISMATCH")
    actual = set()
    for folder, dirs, files in os.walk(plugin, followlinks=False):
        for name in [*dirs, *files]:
            checked(Path(folder)/name)
        for name in files:
            actual.add((Path(folder)/name).relative_to(plugin).as_posix())
    expected = FILES | {"package-manifest.json"}
    require(actual == expected or actual == expected | {COMPAT}, "PACKAGE_FILESET_MISMATCH")
    if COMPAT in actual:
        compat = checked(plugin/COMPAT)
        require(compat.stat().st_size <= 65536 and
                metadata_digest(compat.read_bytes()) == manifest["metadata_sha256"][COMPAT],
                "HOST_METADATA_MISMATCH")
    for name in sorted(FILES):
        content = checked(plugin/name).read_bytes()
        if name == "plugin.json" and sha(content) != manifest["files"][name]:
            require(metadata_digest(content) == manifest["metadata_sha256"][name],
                    "HOST_METADATA_MISMATCH")
        else:
            require(sha(content) == manifest["files"][name], "PACKAGE_IDENTITY_MISMATCH:"+name)
        if name == "core/sp_history.py":
            require(sha(content) == CORE_SHA, "WORKFLOW_CODE_CHANGED")
            module_bytes = content
    return module_bytes

def interpreter_identity(plugin):
    import platform
    import struct
    import sqlite3
    import zipimport
    spec = json.loads((plugin/"runtime/cpython-windows.json").read_bytes())
    version = platform.python_version()
    require(sys.platform == "win32" and sys.implementation.name == "cpython"
            and version in spec["supported_versions"], "UNSUPPORTED_CPYTHON_VERSION")
    require(struct.calcsize("P") == 8 and platform.machine().upper() in ("AMD64", "X86_64"),
            "WINDOWS_X64_REQUIRED")
    require(sqlite3.sqlite_version and zipimport.zipimporter, "CORE_DEPENDENCIES_REQUIRED")
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
            "ISOLATED_NO_SITE_NO_BYTECODE_REQUIRED")
    executable = checked(sys.executable)
    base = checked(sys._base_executable)
    get_filename = ctypes.windll.kernel32.GetModuleFileNameW
    get_filename.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    get_filename.restype = wintypes.DWORD
    buffer = ctypes.create_unicode_buffer(32768)
    length = get_filename(sys.dllhandle, buffer, len(buffer))
    require(0 < length < len(buffer), "PYTHON_DLL_IDENTITY_REQUIRED")
    dll = checked(buffer.value)
    paths = {executable, base, dll}
    import _ctypes
    import _sqlite3
    import _hashlib
    for module in (_ctypes, _sqlite3, _hashlib):
        paths.add(checked(module.__file__))
    for directory in (executable.parent, dll.parent):
        for name in ("python312.zip", "python312._pth", "python._pth"):
            if (directory/name).exists():
                paths.add(checked(directory/name))
    with executable.open("rb") as stream:
        stream.seek(0x3c)
        stream.seek(int.from_bytes(stream.read(4), "little"))
        require(stream.read(6) == b"PE\x00\x00\x64\x86", "WINDOWS_X64_REQUIRED")
    for folder in (executable.parent, executable.parent.parent):
        cfg = folder/"pyvenv.cfg"
        if cfg.is_file():
            paths.add(checked(cfg))
    return {"interpreter": str(executable), "python_version": version,
            "runtime_files": {str(path): sha(path.read_bytes()) for path in sorted(paths)}}

def binding_path():
    return checked(Path(os.environ["LOCALAPPDATA"])/"GDCAE"/"gdcae-research"/VERSION/"binding.json")

def write_once(path, document):
    require(not path.exists(), "BINDING_ALREADY_EXISTS")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(document, sort_keys=True, indent=2)+"\n").encode()
    # Windows rename refuses an existing destination, also with concurrent binders.
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            stream.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.rename(path)
    finally:
        temporary.unlink(missing_ok=True)
    return sha(data)

def identity(args, plugin):
    pin = args.manifest_sha256
    path = binding_path()
    if args.action == "bind":
        require(args.selected_python and checked(args.selected_python) == checked(sys.executable),
                "EXPLICIT_INTERPRETER_REQUIRED")
    if args.action != "bind":
        data = path.read_bytes()
        require(sha(data) == args.binding_sha256, "BINDING_RECEIPT_MISMATCH")
        bound = json.loads(data)
        require(bound["schema"] == "gdcae-sp-user-binding-v1" and bound["plugin"] == str(plugin)
                and bound["version"] == VERSION, "INSTALLATION_IDENTITY_MISMATCH")
        pin = bound["package_manifest_sha256"]
    source = core_bytes(plugin, pin)
    current = interpreter_identity(plugin)
    if args.action != "bind":
        require(bound["runtime"] == current, "WORKSPACE_RUNTIME_MISMATCH")
    if args.action == "bind":
        receipt = write_once(path, {"schema":"gdcae-sp-user-binding-v1","version":VERSION,
            "plugin":str(plugin),"package_manifest_sha256":pin,"runtime":current})
        return None, {"status":"BOUND","binding_sha256":receipt,"binding_file":str(path)}
    runtime = {"plugin":str(plugin),"plugin_version":VERSION,"core_version":CORE_VERSION,
        "core_sha256":CORE_SHA,"package_manifest_sha256":pin,
        "binding_sha256":args.binding_sha256,"interpreter":str(sys.executable),
        "python_version":current["python_version"],"host_skill_activation":"NOT_ESTABLISHED_BY_DRIVER"}
    module = ModuleType("gdcae_sp_history")
    exec(compile(source, str(plugin/"core/sp_history.py"), "exec"), module.__dict__)
    return module, runtime

def guard(output):
    def audit(event, args):
        if event in ('subprocess.Popen','os.system','os.startfile','sqlite3.connect') or event.startswith(('socket.','ctypes.dlopen')):
            raise PermissionError('EXECUTION_OR_NETWORK_DENIED:'+event)
        if event == 'open':
            path, mode, flags = args
            write = (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if write and (not isinstance(path,(str,bytes,os.PathLike)) or not Path(path).resolve().is_relative_to(output)):
                raise PermissionError('WRITE_OUTSIDE_OUTPUT_DENIED')
        if event in ('os.remove','os.rename','os.rmdir','os.mkdir','os.chmod','os.truncate','os.link','os.symlink'):
            if not Path(args[0]).resolve().is_relative_to(output):
                raise PermissionError('MUTATION_OUTSIDE_OUTPUT_DENIED')
    sys.addaudithook(audit)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['preflight','bind','doctor','main','agreement'])
    parser.add_argument('--operation', choices=['new','freeze','propose','confirm','attribute','overview','detail','diff','hint'])
    parser.add_argument('--input-file', type=Path)
    parser.add_argument('--selector')
    parser.add_argument('--agreement-root', type=Path)
    parser.add_argument('--project-root', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--selected-python')
    parser.add_argument('--binding-sha256')
    args = parser.parse_args()
    try:
        if sys.version_info[:2] < (3, 12):
            raise ValueError("UNSUPPORTED_CPYTHON_VERSION")
        plugin = checked(Path(__file__).parent.parent)
        if args.action == 'preflight':
            core_bytes(plugin, args.manifest_sha256)
            interpreter_identity(plugin)
            print(json.dumps({"status":"RUNTIME_PREFLIGHT_OK"}))
            return 0
        module, runtime = identity(args, plugin)
        if args.action == 'bind':
            print(json.dumps(runtime, indent=2))
            return 0
        if args.action == 'doctor':
            print(json.dumps({'status':'PACKAGE_AND_CORE_VERIFIED','runtime':runtime},indent=2))
            return 0
        sys.path.insert(0,str(plugin/"scripts"))
        import agreement_main
        agreement_main.load_core(plugin)
        if args.action == 'agreement':
            require(args.project_root and args.operation, "PROJECT_AND_OPERATION_REQUIRED")
            result = agreement_main.run(args,plugin,checked)
            print(json.dumps(result,ensure_ascii=True,indent=2))
            return 0
        require(not args.operation and not args.selector and not args.input_file, "INVALID_MAIN_ARGUMENTS")
        hint = agreement_main.query(checked(args.agreement_root)) if args.agreement_root else {
            "status":"NO_RESEARCH_PROJECT_ATTACHED","markdown":"未关联 ResearchProject。可用 agreement overview 查询已有科研约定。"}
        if args.project_root is None or args.output is None:
            raise ValueError('PROJECT_AND_FRESH_OUTPUT_REQUIRED')
        project, output = checked(args.project_root), checked(args.output)
        if output.exists() or output.is_relative_to(project) or output.is_relative_to(plugin) or project.is_relative_to(output) or output.is_relative_to(binding_path().parent):
            raise ValueError('FRESH_EXTERNAL_OUTPUT_REQUIRED')
        guard(output)
        # output parent must already exist; creates only this distinct result directory.
        output.mkdir()
        try:
            report, differences = module.analyze(project)
            report['runtime'] = runtime
            report['research_agreement_hint'] = hint
            report['external_project_root'] = str(project)
            with (output/'curve_difference.csv').open('w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(['displacement_model_length','candidate_force_model','baseline_interpolated_force_model','difference_model_force'])
                writer.writerows(differences)
            (output/'report.md').write_text(module.markdown(report)+'\n\n'+hint['markdown']+'\n',encoding='utf-8')
            (output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
            print(json.dumps({'status':report['status'],'output':str(output),'runtime':runtime,'research_agreement_hint':hint},indent=2))
            return 0
        except Exception as exc:
            failure = {'status':'BLOCKED','error':str(exc),'metrics':None,'runtime':runtime}
            (output/'failure.json').write_text(json.dumps(failure,indent=2),encoding='utf-8')
            raise
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc),'metrics':None}))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
