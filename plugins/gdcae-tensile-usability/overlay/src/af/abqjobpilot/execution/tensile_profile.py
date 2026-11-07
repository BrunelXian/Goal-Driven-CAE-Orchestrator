"""One registered tensile family in the existing managed product Standard lifecycle."""
from decimal import Decimal
import hashlib
import json
import re
import sys
from pathlib import Path
from .models import bytes_digest, digest, now, require
from .paths import confined, no_reparse
from ..local_credentials import protected_project, private_value, read_private

PROFILE = "tensile-bilinear-3d-r3"
POLICY = "tensile-terminal-artifact-manifest-v1"
BASE = "614588c14a7ea24e23a7561b261d5fa0f0147805f74405a0953da30670911efa"
TARGET = "0b3fab4ac5682001c6428122e1dee3084cbb9875567cfce170d2ab23b3bbfe11"
FREEZE = "c08f77ab2b23524a3beee3e73a1114dba54e1e3d4aa2a36015c060d9c3fe317d"
JOB = r"Tensile_[AB]_[0-9a-f]{16}"
TTL = 600
VALIDATOR="tensile-artifact-collector"
VALIDATION_SCOPE="tensile_artifact_identity_only"

def registered(plan):
    return plan.get("model_profile")==PROFILE

def spec_config():
    from .standard_contract import StandardConfig
    from .tensile_catalog import AF_ROOT
    require(Path(__file__).resolve().parents[2]==Path(AF_ROOT),"AF_INSTALLATION_CHANGED","Registered AF installation required")
    config=StandardConfig.fixed([r"D:\ABAQUS2024\product\win_b64\code\bin\SMAPython.exe",r"D:\ABAQUS2024\product\win_b64\code\bin\odbAccess.pyd",str(Path(__file__).with_name("standard_profiles.py")),str(Path(__file__)),str(Path(__file__).with_name("tensile_catalog.py")),
        str(Path(__file__).with_name("standard_backend.py")),str(Path(__file__).with_name("standard_contract.py"))],managed=True)

    value=config.value()
    root=Path(AF_ROOT)
    files={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted((root/"abqjobpilot").rglob("*")) if p.is_file() and not "__pycache__" in p.parts}
    value["installed_af_tree"]=digest(files)
    from .models import canonical_json
    return StandardConfig(canonical_json(value))

def registration_path(ctx):
    require(protected_project(ctx),"TENSILE_PRODUCT_REQUIRED","Protected product project required")
    return confined(ctx.test_root,Path(ctx.test_root)/"private"/"tensile-registration.json")

def enroll(service,root,job,expires,purpose):
    """Initial lease held. Derive identity from installed GD and its replayed records."""
    from .tensile_catalog import GD_FILES,GD_ROOT
    from ..service_lifecycle import write_new
    from .standard_contract import RESOURCES
    ctx=service.context
    loc=Path(ctx.test_root)
    require(re.fullmatch(JOB,job) and (loc.name=="af-"+job.split("_")[1] or (job.split("_")[1]=="A" and re.fullmatch(r"af-A-(?:cont|readmit)-[a-f0-9]{32}",loc.name)) or (job.split("_")[1]=="B" and re.fullmatch(r"af-B-(?:readmit|window)-[a-f0-9]{32}",loc.name))) and root==loc/"engineering"
            and purpose in ("OFFLINE_TEST_ONLY","JIT_HUMAN_REVIEW") and now()<expires<=now()+TTL,
            "TENSILE_SCOPE","Fixed campaign layout, job and bounded preparation window required")
    import subprocess
    from .standard_contract import PYTHON
    cache=Path(GD_ROOT)
    no_reparse(cache)
    for name,pin in GD_FILES.items():
        path=cache/name
        no_reparse(path)
        require(hashlib.sha256(path.read_bytes()).hexdigest()==pin,"TENSILE_SOURCE_CHANGED","Registered GD code differs")
    require({p.relative_to(cache).as_posix() for p in cache.rglob("*.py")}==set(GD_FILES)
            and not any(p.suffix.lower() in (".pyd",".pyc",".dll",".zip") for p in cache.rglob("*")),
            "TENSILE_SOURCE_CHANGED","Unexpected executable file in registered GD cache")
    work=loc.parent
    proc=subprocess.run([PYTHON,"-I","-B","-S",str(cache/"admission_snapshot.py"),str(work),*(['b-window:'+loc.name.removeprefix('af-B-window-')] if loc.name.startswith('af-B-window-') else ['b-readmit:'+loc.name.removeprefix('af-B-readmit-')] if loc.name.startswith('af-B-readmit-') else ['phase:B'] if loc.name=='af-B' else (["readmit:"+loc.name.removeprefix("af-A-readmit-")] if loc.name.startswith("af-A-readmit-") else ([loc.name[10:]] if loc.name.startswith("af-A-cont-") else [])))],
                        stdin=subprocess.DEVNULL,capture_output=True,timeout=60,check=True,cwd=cache)
    snap=json.loads(proc.stdout)
    handoff=snap["req"]
    require(purpose==snap["purpose"] and job==handoff["job"] and handoff["expected_work_dir"]==str(root)
            and handoff["resource_review"]==RESOURCES and handoff["phase"]==job.split("_")[1]
            and handoff["project"]==snap["project"] and handoff["profile"]==PROFILE
            and handoff["action"]=="STANDARD_FULL_ANALYSIS" and handoff["contract_sha256"]==snap["contract"]
            and handoff["campaign_mode"]=="PREPARE_ONLY" and handoff["target_sha256"]==TARGET
            and handoff["model_freeze_sha256"]==FREEZE,"TENSILE_SOURCE_MISMATCH","Exact replayed campaign request required")
    value={"schema":PROFILE,"purpose":purpose,"gd_package":snap["package"],"project_id":ctx.project_id,
           "project_instance_id":ctx.project_instance_id,"context_digest":ctx.context_digest,
           "research_project":handoff["project"],"candidate":handoff["candidate_id"],"phase":handoff["phase"],
           "contract":snap["contract"],"request":snap["request"],"output":handoff["output_key"],
           "prior":handoff["prior_feedback_sha256"],"parameters":handoff["parameters"],"baseline":BASE,
           "model_freeze":FREEZE,"target":TARGET,"input_digest":"sha256:"+handoff["inp_sha256"],
           "job":job,"engineering":str(root),"resources":dict(RESOURCES),"expires_at":expires,"retry":0}
    if "continuation" in snap:
        require(expires==snap["continuation"]["expires_at"],"CONTINUATION_EXPIRY_CHANGED","Exact intent expiry required")
        value["continuation"]=snap["continuation"]
    if "readmission" in snap:
        require(expires==snap["readmission"]["expires_at"],"READMISSION_EXPIRY_CHANGED","Exact readmission expiry required")
        value["readmission"]=snap["readmission"]
    if 'b_admission' in snap:
        require(handoff['phase']=='B' and expires==snap['b_admission']['expires_at'],'B_EXPIRY_CHANGED','Exact B intent expiry required')
        value['b_admission']=snap['b_admission']
    if 'b_readmission' in snap:
        require(handoff['phase']=='B' and expires==snap['b_readmission']['expires_at'],'B_READMISSION_EXPIRY_CHANGED','Exact B re-admission intent expiry required')
        value['b_readmission']=snap['b_readmission']
    if 'execution_window' in snap:
        require(handoff['phase']=='B' and expires==snap['execution_window']['expires_at'],'WINDOW_EXPIRY_CHANGED','Exact current execution window required')
        value['execution_window']=snap['execution_window']
    validate_input(root,value)
    write_new(registration_path(ctx),private_value(ctx,value))
    return value

def validate_input(root,reg):
    from .standard_contract import identity
    job=reg["job"]
    require(re.fullmatch(JOB,job) and root==Path(reg["engineering"]),"TENSILE_SCOPE","Fixed job and output required")
    path=root/(job+".inp")
    no_reparse(path)
    info=identity(path,65536)
    require(path.stat().st_nlink==1 and info["digest"]==reg["input_digest"],"PLAN_STALE","Input identity changed")
    raw=path.read_bytes()
    require(bytes_digest(raw)==info["digest"],"PLAN_STALE","Candidate changed during verification")
    p=reg["parameters"]
    require(set(p)=={"sigma_y_MPa","H_MPa"} and all(type(v) is str and re.fullmatch(r"[0-9]{1,4}(?:\.[0-9]{1,8})?",v) for v in p.values()),
            "TENSILE_MATERIAL","Invalid registered decimal parameters")
    sy,h=Decimal(p["sigma_y_MPa"]),Decimal(p["H_MPa"])
    require(150<=sy<=450 and 500<=h<=5000,"TENSILE_MATERIAL","Out of bounds")
    lines=raw.splitlines(keepends=True)
    idx=[i for i,l in enumerate(lines) if l.strip().lower()==b"*plastic"]
    require(len(idx)==1,"TENSILE_MODEL","Expected one plastic table")
    i=idx[0]+1
    require(hashlib.sha256(b"".join(lines[:i]+lines[i+2:])).hexdigest()=="05de8731e7369ad54e9ce5e057168f562ce0607f502800f1b42f41f7f2c28ddb",
            "TENSILE_MODEL","Frozen nonmaterial bytes differ")
    values=[[Decimal(x.strip().decode("ascii")) for x in line.split(b",")] for line in lines[i:i+2]]
    require(values==[[sy,0],[sy+h*Decimal(".05"),Decimal(".05")]] and
            (reg["phase"]!="A" or (info["digest"]=="sha256:"+BASE and (sy,h)==(250,2000))),
            "TENSILE_MODEL","Frozen A or two-row constitutive law differs")
    return info

def read(ctx,root,job,config,expires,*,terminal_evidence=False):
    value=read_private(ctx,registration_path(ctx))
    require(value["schema"]==PROFILE and value["job"]==job and value["expires_at"]==expires
            and (value["project_id"],value["project_instance_id"],value["context_digest"])==
            (ctx.project_id,ctx.project_instance_id,ctx.context_digest) and root==Path(ctx.test_root)/"engineering"
            and config.value()==spec_config().value(),"TENSILE_REGISTRATION_MISMATCH","Registered context or runtime differs")
    if "continuation" in value or "readmission" in value or 'b_admission' in value or 'b_readmission' in value or 'execution_window' in value:
        # Initial creation has no persisted Plan. Any later preflight/authorization
        # requires the same committed GD binding. No change to Grant/Owner core.
        import sqlite3,subprocess
        from .standard_contract import PYTHON
        from .tensile_catalog import GD_ROOT,GD_FILES
        cache=Path(GD_ROOT)
        require({p.relative_to(cache).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in cache.rglob("*.py")}==GD_FILES,
                "TENSILE_SOURCE_CHANGED","Registered GD code differs")
        db=sqlite3.connect((Path(ctx.root)/"execution.sqlite3").as_uri()+"?mode=ro",uri=True)
        try:
            persisted=db.execute("SELECT body FROM plans").fetchmany(2)
            require(len(persisted)<=1,"CONTINUATION_BINDING_CHANGED","One original native Plan required")
            committed=bool(persisted)
            native_plan=json.loads(persisted[0][0]) if committed else None
        finally:db.close()
        kind='execution_window' if 'execution_window' in value else 'b_readmission' if 'b_readmission' in value else 'b_admission' if 'b_admission' in value else ("readmission" if "readmission" in value else "continuation")
        op=('b-window:'+value[kind]['operation_id']) if kind=='execution_window' else ('b-readmit:'+value[kind]['operation_id']) if kind=='b_readmission' else 'phase:B' if kind=='b_admission' else (("readmit:" if kind=="readmission" else "")+value[kind]["operation_id"])
        # Only tensile_terminal's trusted read-only evidence call supplies True.
        # Plan/registration/request data never selects this branch. All native
        # prepare/preflight/Grant/dispatch callers use the strict default.
        mode=['--terminal'] if terminal_evidence else (["--committed"] if committed else [])
        proc=subprocess.run([PYTHON,"-I","-B","-S",str(cache/"admission_snapshot.py"),str(Path(ctx.test_root).parent),op,
                             *mode],stdin=subprocess.DEVNULL,capture_output=True,timeout=60,check=False,cwd=cache)
        require(proc.returncode==0,"CONTINUATION_NOT_COMMITTED","Exact committed research binding required after Plan persistence")
        snap=json.loads(proc.stdout)
        require(snap[kind]==value[kind] and snap["request"]==value["request"],"CONTINUATION_BINDING_CHANGED","Continuation lineage differs")
        if committed:
            result=snap["result"]
            from .product_standard import scope
            unsigned=dict(native_plan)
            require(unsigned.pop('plan_digest')==digest(unsigned),"PLAN_STALE","Native Plan digest differs")
            require(result["new"]["project_id"]==ctx.project_id and result["new"]["project_instance_id"]==ctx.project_instance_id
                    and result["new"]["af_project"]==str(Path(ctx.test_root))
                    and result["new"]["plan"]==native_plan
                    and result["new"]["scope_digest"]==digest(scope(native_plan))
                    and native_plan["registration"]==value,"CONTINUATION_BINDING_CHANGED","Complete committed native Plan and scope differ")
    return value,validate_input(root,value)

def outputs(plan):
    root=Path(plan["engineering"])
    return [p for p in root.glob(plan["job_name"]+".*") if not registered(plan) or p.name!=plan["job_name"]+".inp"]

def input_name(plan):
    if registered(plan):
        require(re.fullmatch(JOB,plan["job_name"]),"TENSILE_SCOPE","Registered tensile job required")
        return plan["job_name"]+".inp"
    return "axial_bar.inp"

def collect(ctx,plan,run,intent,process):
    """Only structural validation here. Numerical judgment requires the qualified ODB reader."""
    root=Path(plan["engineering"])
    reg=read_private(ctx,registration_path(ctx))
    require(reg==plan["registration"] and intent["plan_digest"]==plan["plan_digest"]
            and intent["run_id"]==run["run_id"] and intent["phase_attempt_id"]==run["phase_attempt_id"]
            and intent["output_key"]==plan["output_key"] and intent["project_instance_id"]==ctx.project_instance_id,
            "TENSILE_SOURCE_MISMATCH","Launch intent lineage differs")
    inp=validate_input(root,reg)
    artifacts=[{"logical_ref":"input:inp","digest":inp["digest"],"size":inp["size"]}]
    require(process.get("all_observed_exited") and not (root/(reg["job"]+".lck")).exists(),
            "TENSILE_SOURCE_INCOMPLETE","Exited process and closed ODB required")
    logs={}
    from .standard_contract import identity
    for ext,limit in (("odb",128<<20),("sta",16<<20),("msg",32<<20)):
        path=confined(ctx.test_root,root/(reg["job"]+"."+ext),exists=True)
        stat=path.stat()
        require(stat.st_nlink==1 and stat.st_size>0 and min(stat.st_ctime_ns,stat.st_mtime_ns)>=intent["intent_at_ns"],
                "TENSILE_SOURCE_STALE","Missing or pre-existing job output")
        info=identity(path,limit)
        artifacts.append({"logical_ref":"output:"+ext,"digest":info["digest"],"size":info["size"],
                         "device":stat.st_dev,"inode":stat.st_ino,"mtime_ns":stat.st_mtime_ns})
        if ext!="odb":
            data=path.read_bytes()
            require(bytes_digest(data)==info["digest"],"EVIDENCE_CHANGED","Log changed")
            logs[ext]=data.upper()
    require(b"THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in logs["sta"] and b"THE ANALYSIS HAS BEEN COMPLETED" in logs["msg"]
            and all(b"***ERROR" not in data for data in logs.values()),"TENSILE_SOURCE_INCOMPLETE","Missing successful terminal logs")
    return {"solver":"COMPLETED_TEXT_EVIDENCE","numerical":"NOT_RUN","odb_content_validation":"NOT_RUN",
            "artifacts":artifacts,"structural":"COMPLETE_HASHED","source":"native_tensile_artifacts","validation_policy":POLICY}

