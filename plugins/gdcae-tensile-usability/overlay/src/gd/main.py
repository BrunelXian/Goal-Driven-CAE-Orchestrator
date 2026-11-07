"""Installed tensile V1 workflow entry. No AF imports or job launcher."""
import argparse,hashlib,json,os,sys
from pathlib import Path

def check(v,code):
    if not v:raise ValueError(code)

def safe(path):
    path=Path(path).absolute()
    for p in (path,*path.parents):
        check(not p.is_symlink() and not p.is_junction(),"REPARSE_DENIED")
    return path.resolve()

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(root,a):
    check(sys.version_info[:3]==(3,12,10) and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,"ISOLATED_3_12_10_REQUIRED")
    check(Path(a.python_exe).is_absolute() and safe(a.python_exe)==safe(sys.executable),"EXPLICIT_INTERPRETER_REQUIRED")
    manifest=safe(root/"package-manifest.json")
    check(digest(manifest)==a.package_pin,"PACKAGE_PIN_MISMATCH")
    files=json.loads(manifest.read_bytes())["files"]
    observed=set()
    for folder,dirs,names in os.walk(root,followlinks=False):
        for name in dirs+names:safe(Path(folder)/name)
        for name in names:observed.add((Path(folder)/name).relative_to(root).as_posix())
    check(observed==set(files)|{"package-manifest.json"},"PACKAGE_FILESET")
    for rel,want in files.items():check(digest(root/rel)==want,"PACKAGE_FILE_MISMATCH:"+rel)

def run():
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("doctor","init","prepare","observe-fixture","status","af-admission","review-extraction","observe-native","continue-propose","continue-prepare","continue-reconcile","continue-finalize","continue-static","continue-gate","readmit-static","readmit-propose","readmit-prepare","readmit-reconcile","readmit-finalize","readmit-gate","window-static","window-reconcile","window-finalize","window-gate","window-feedback"))
    parser.add_argument("--package-pin",required=True);parser.add_argument("--python-exe",required=True)
    for arg in ("workspace","source","target","target-pin","contract-pin","request-pin","extraction","extraction-pin","binding","binding-pin","operation-id","proposal","proposal-pin","result","qualification","qualification-pin"):
        parser.add_argument("--"+arg)
    parser.add_argument("--mode",choices=("FIXTURE","PREPARE_ONLY"))
    parser.add_argument("--af-purpose",choices=("OFFLINE_TEST_ONLY","JIT_HUMAN_REVIEW"),default="OFFLINE_TEST_ONLY")
    parser.add_argument("--expires-at",type=int)
    parser.add_argument("--phase",choices=("A","B"))
    parser.add_argument("--outcome",choices=("SURROGATE","UNKNOWN","FAILED"),default="SURROGATE")
    a=parser.parse_args()
    root=safe(Path(__file__).parent)
    verify(root,a)
    sys.path[:0]=[str(root/"runtime"),str(root)]
    import workflow
    if a.action=="doctor":
        return {"status":"PACKAGE_VERIFIED","interpreter":sys.executable,"python":sys.version.split()[0],"plugin":str(root),
                "package_pin":a.package_pin,"activation":"NOT_ESTABLISHED_BY_DRIVER"}
    check(a.workspace and Path(a.workspace).is_absolute(),"ABSOLUTE_WORKSPACE_REQUIRED")
    if a.action=="init":
        check(a.mode and a.source and a.target and a.target_pin,"EXPLICIT_CONTRACT_INPUTS_REQUIRED")
        return workflow.initialize(a.workspace,a.source,a.target,a.target_pin,a.mode,a.package_pin,a.af_purpose)
    camp=workflow.Campaign(a.workspace,a.contract_pin,a.package_pin,readonly=a.action in ('status','continue-static','continue-propose','continue-reconcile','continue-gate','readmit-static','readmit-propose','readmit-reconcile','readmit-gate','window-static','window-reconcile','window-gate'),candidate_b_admission=a.action.startswith('window-'))
    try:
        if a.action.startswith('window-'):
            import execution_windows as ew
            if a.action=='window-static':
                check(a.qualification and a.qualification_pin,'EXACT_WINDOW_QUALIFICATION_REQUIRED')
                with safe(a.qualification).open('rb') as stream:raw=stream.read((2<<20)+1)
                check(len(raw)<=2<<20 and hashlib.sha256(raw).hexdigest()==a.qualification_pin,'QUALIFICATION_CHANGED')
                return ew.static(camp,a.operation_id,json.loads(raw))
            if a.action=='window-reconcile':return ew.reconcile(camp,a.operation_id)
            if a.action=='window-finalize':return ew.finalize(camp,a.operation_id)
            if a.action=='window-gate':return ew.dynamic(camp,safe(a.result))
            from native_accounting import feedback_once
            return feedback_once(camp,a.request_pin)
        if a.action=="status":return camp.inspect()
        if a.action.startswith("readmit-"):
            import readmission as rm
            if a.action in ('readmit-static','readmit-propose'):
                check(a.qualification and a.qualification_pin,'EXPLICIT_RETAINED_EXIT_REVIEW_REQUIRED')
                with safe(a.qualification).open('rb') as f:raw=f.read((2<<20)+1)
                check(len(raw)<=2<<20 and hashlib.sha256(raw).hexdigest()==a.qualification_pin,'QUALIFICATION_FILE_CHANGED')
                camp.readmission_qualification=json.loads(raw)
            if a.action=='readmit-static':return rm.static(camp,a.operation_id)
            if a.action=='readmit-propose':return rm.propose(camp,a.operation_id)
            if a.action=='readmit-reconcile':return rm.reconcile(camp,a.operation_id)
            if a.action=='readmit-finalize':return rm.finalize(camp,a.operation_id)
            if a.action=='readmit-gate':return rm.dynamic(camp,safe(a.result))
            return rm.prepare(camp,json.loads(safe(a.proposal).read_bytes()),a.proposal_pin,a.expires_at)
        if a.action.startswith("continue-"):
            import continuation as c
            if a.action=='continue-static':
                from readiness import static
                return static(camp,a.operation_id)
            if a.action=='continue-gate':
                from readiness import dynamic
                return dynamic(camp,safe(a.result))
            if a.action=="continue-propose":return c.propose(camp,a.operation_id)
            if a.action=="continue-reconcile":return c.reconcile(camp,a.operation_id)
            if a.action=="continue-finalize":return c.finalize(camp,a.operation_id)
            proposal=json.loads(safe(a.proposal).read_bytes())
            return c.prepare(camp,proposal,a.proposal_pin,a.expires_at)
        check(a.phase in ("A","B"),"EXPLICIT_PHASE_REQUIRED")
        if a.action=="prepare":return camp.prepare(a.phase)
        if a.action=="observe-fixture":return camp.observe(a.phase,a.request_pin,a.outcome)
        if a.action=="observe-native":return camp.observe(a.phase,a.request_pin,"NATIVE")
        camp.db.execute("BEGIN")
        row=next((r for r in camp.verified_rows() if r["phase"]==a.phase),None)
        check(row is not None,"PREPARED_PHASE_REQUIRED")
        req=camp.check_row(row)
        check(workflow.case.hashbytes(row["request"])==a.request_pin,"EXACT_PHASE_REQUEST_REQUIRED")
        if a.action=="af-admission":
            from r3_bridge import admit
            return admit(camp,row,a.expires_at)
        import odb_reader
        source=odb_reader.local(a.extraction);binding=odb_reader.local(a.binding)
        check(digest(source)==a.extraction_pin and digest(binding)==a.binding_pin,"EXTRACTION_PIN_MISMATCH")
        ex=json.loads(source.read_bytes());sub=json.loads(binding.read_bytes())
        check(ex["schema"]=="tensile-odb-extraction-v1" and ex["binding_sha256"]==a.binding_pin and
              sub["request_digest"]==a.request_pin and ex["lineage"]["request_digest"]==a.request_pin and
              ex["lineage"]=={k:sub[k] for k in ("project_id","plan_id","run_id","receipt_id","output_key","phase","request_digest")} and
              sub["research_project_id"]==req["project"] and sub["job_name"]==req["job"] and sub["phase"]==req["phase"] and
              sub["output_key"]==req["output_key"] and ex["source_hashes"]==sub["sha256"] and
              sub["sha256"]["inp"]==req["inp_sha256"] and ex["reader_sha256"]==sub["reader_sha256"]==digest(root/"odb_reader.py"),
              "SOURCE_CHAIN_MISMATCH")
        check(ex["odb_read_only"] is True and ex["analysis_complete"] is True and ex["review_required"] is False,"WARNING_OR_UNKNOWN_STOP")
        rows=[]
        odb_reader.check_step_times(ex["frames"])
        for item in ex["frames"]:
            right=item["right_nodes"];left=item["left_nodes"];ip=item["integration_points"]
            check(len(right)==len(left)==9 and len(ip)==80 and all(p[1]==1 for p in ip),"SOURCE_COVERAGE")
            r=odb_reader.frame_summary({v[0]:v[1] for v in right},{v[0]:v[2] for v in right},{v[0]:v[2] for v in left},
                {v[0]:v[2] for v in ip},item["time_s"],{v[0]:v[1] for v in left},{v[0]:v[3] for v in ip},{v[0]:v[4] for v in ip})
            check(r==item,"EXTRACTION_ROW_INCONSISTENT")
            rows.append(r)
        return {"status":"DIAGNOSTIC_ONLY_CALLER_SUPPLIED","phase":a.phase,"scoring":workflow.case.compare(camp.target,rows,req["parameters"]),
                "production_feedback_accepted":False,"new_authority":None}
    finally:camp.db.close()

if __name__=="__main__":
    try: print(json.dumps(run(),indent=2,allow_nan=False))
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED","error":str(exc),"af_action":None}));sys.exit(2)

