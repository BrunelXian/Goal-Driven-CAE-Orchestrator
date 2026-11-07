"""One read-only extraction from a released, original AF run. No supplied frames or bindings."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from odb_reader import digest,local,check_step_times
import tensile as case
from r3_bridge import trusted_af

def source(camp,r):
    trusted_af()
    from abqjobpilot.execution.tensile_terminal import bind_compatible,bind
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager
    from abqjobpilot.execution.terminal_feedback_compat import effective
    if r['phase']=='A':
        req,request_pin,product=effective(camp,r)
        binding_reader=bind_compatible
    else:
        import execution_windows
        req,request_pin,product=execution_windows.effective(camp,r);binding_reader=bind
    reader=local(Path(__file__).with_name("odb_reader.py"))
    b=binding_reader(product,req,request_pin,digest(reader))
    return req,reader,b,ServiceLifecycleManager(product)

def evaluate(camp,req,b,ex):
    case.check(ex["schema"]=="tensile-odb-extraction-v1" and ex["binding_sha256"]==case.hashbytes(case.pack(b)) and
               ex["lineage"]=={k:b[k] for k in ("project_id","plan_id","run_id","receipt_id","output_key","phase","request_digest")} and
               ex["source_hashes"]==b["sha256"] and ex["reader_sha256"]==b["reader_sha256"] and
               ex["odb_read_only"] is True and ex["analysis_complete"] is True and ex["review_required"] is False and
               ex["analysis_errors"]==ex["analysis_warnings"]==ex["diagnostic_line_count"]==0 and ex["end_forces_balanced"] is True,
               "NATIVE_EVIDENCE_INCOMPLETE")
    frames=ex["frames"]
    check_step_times(frames)
    return {"classification":"NATIVE_ODB","binding":b,"extraction_sha256":case.hashbytes(case.pack(ex)),
            "frames":frames,"assessment":case.compare(camp.target,frames,req["parameters"])}

def extract(camp,r):
    if r['phase']=='B':
        from terminal_materialization import extract_once
        return extract_once(camp,r)
    from abqjobpilot.local_credentials import private_value
    from abqjobpilot.service_lifecycle import write_new
    req,reader,b,m=source(camp,r)
    ex=read_extraction(camp,req,reader,b)
    case.check(source(camp,r)[2]==b,"TERMINAL_SOURCE_CHANGED")
    result=evaluate(camp,req,b,ex)
    write_new(m._path("tensile-feedback.json"),private_value(m.context,{"result_digest":case.hashbytes(case.pack(result)),
              "binding_digest":case.hashbytes(case.pack(b))}))
    return result

def read_extraction(camp,req,reader,b):
    from abqjobpilot.execution.standard_contract import CMD,ENTRY
    # Only the fixed 'python' reader action. No solver subcommand or arbitrary script.
    with tempfile.TemporaryDirectory(dir=camp.root,prefix="native-read-") as tmp:
        tmp=local(tmp)
        binding=tmp/"source.json"; binding.write_bytes(case.pack(b))
        out=tmp/"extraction.json"
        argv=[ENTRY,"python",str(reader),"read","--binding",str(binding),"--binding-sha256",digest(binding),
              "--handoff",str(camp.root/req["job"]/"handoff.json"),"--handoff-sha256",b["request_digest"],"--output",str(out)]
        case.check(all(re.fullmatch(r"[A-Za-z0-9_ .:/\\-]+",v) for v in argv),"UNSAFE_READER_ARGUMENT")
        command='"'+CMD+'" /d /s /c "'+" ".join('"'+s+'"' for s in argv)+'"'
        env={k:os.environ[k] for k in ("SYSTEMROOT","WINDIR","ProgramData","ProgramFiles","SystemDrive","COMSPEC") if k in os.environ}
        env.update(PATH=r"C:\Windows\System32;C:\Windows",TEMP=str(tmp),TMP=str(tmp),HOME=str(tmp),USERPROFILE=str(tmp),
                   PYTHONNOUSERSITE="1",PYTHONDONTWRITEBYTECODE="1")
        subprocess.run(command,executable=CMD,shell=False,env=env,cwd=tmp,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,timeout=120,check=True)
        case.check(local(out).is_file() and out.stat().st_size<=64<<20,"EXTRACTION_LIMIT")
        ex=json.loads(out.read_bytes())
    return ex

def verify(camp,r):
    from abqjobpilot.local_credentials import read_private
    req,reader,b,m=source(camp,r)
    raw=r["result"]; result=json.loads(raw)
    seal=read_private(m.context,m._path("tensile-feedback.json"))
    case.check(seal=={"result_digest":case.hashbytes(raw),"binding_digest":case.hashbytes(case.pack(b))} and
               b==result["binding"] and result["classification"]=="NATIVE_ODB" and
               result["assessment"]==case.compare(camp.target,result["frames"],req["parameters"]),"NATIVE_FEEDBACK_CHANGED")
    return result

