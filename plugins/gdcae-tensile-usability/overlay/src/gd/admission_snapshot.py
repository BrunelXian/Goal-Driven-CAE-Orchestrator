"""Fresh isolated interpreter. Read a single committed request and its native predecessor."""
import hashlib,json,sys
from pathlib import Path
def main():
    root=Path(__file__).resolve().parent
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):raise ValueError("ISOLATION_REQUIRED")
    sys.path[:0]=[str(root/"runtime"),str(root)]
    from r3_bridge import trusted_af
    trusted_af()
    import workflow
    work=Path(sys.argv[1]);pin=hashlib.sha256((work/"contract.json").read_bytes()).hexdigest()
    pkg=hashlib.sha256((root/"package-manifest.json").read_bytes()).hexdigest()
    is_b=len(sys.argv)>2 and (sys.argv[2]=='phase:B' or sys.argv[2].startswith(('b-readmit:','b-window:')))
    camp=workflow.Campaign(work,pin,pkg,readonly=True,candidate_b_admission=is_b)
    try:
        camp.db.execute("BEGIN")
        if is_b:
            import b_admission
            mode=sys.argv[3] if len(sys.argv)>3 else '--preparation'
            if mode not in ('--preparation','--committed','--terminal'):raise ValueError('SNAPSHOT_MODE_REQUIRED')
            if sys.argv[2].startswith('b-window:'):
                import execution_windows
                return execution_windows.snapshot(camp,mode,sys.argv[2][9:])
            if sys.argv[2].startswith('b-readmit:'):
                import b_readmission
                snap=b_readmission.snapshot(camp,mode)
                if snap['b_readmission']['operation_id']!=sys.argv[2][10:]:raise ValueError('B_READMISSION_OPERATION_MISMATCH')
                return snap
            return b_admission.snapshot(camp,mode)
        if len(sys.argv)>2:
            import continuation
            mode=sys.argv[3] if len(sys.argv)>3 else '--preparation'
            if mode not in ('--preparation','--committed','--terminal'):raise ValueError('SNAPSHOT_MODE_REQUIRED')
            if mode=='--terminal':
                rows=camp.verified_rows(terminal_structure_only=True)
                if not rows or camp.c['mode']!='PREPARE_ONLY':raise ValueError('TERMINAL_LEDGER_REQUIRED')
                events=list(camp.db.execute('SELECT event FROM history WHERE phase=? ORDER BY seq',('A',)))
                if [e[0] for e in events] not in (['PREPARED'],['PREPARED','INTENT'],['PREPARED','INTENT','NATIVE']):raise ValueError('TERMINAL_HISTORY_UNKNOWN')
                if any(r['state']=='UNKNOWN' for r in rows):raise ValueError('TERMINAL_STATE_UNKNOWN')
                budget=camp.counts(rows)
                if budget['limit']!=2 or budget['held']+budget['charged']!=len(rows):raise ValueError('TERMINAL_BUDGET_MISMATCH')
            else:
                # Native admission is independently fail-closed, even if no
                # operator ran the convenience gate. Full ledger + one held A.
                continuation.row(camp)
                if camp.c['mode']!='PREPARE_ONLY':raise ValueError('PREPARED_REQUIRED')
            import readmission
            op=sys.argv[2]
            if op.startswith('readmit:'):
                if mode!='--terminal':
                    record,body=readmission.get(camp,op[8:])
                    readmission.ancestry(camp,body['ancestors'],body['qualification_reference'])
                return readmission.snapshot(camp,op[8:],mode in ('--committed','--terminal'))
            return continuation.snapshot(camp,op,mode in ('--committed','--terminal'))
        rows=camp.verified_rows();r=rows[-1]
        workflow.case.baseline(Path(camp.c["model_source"]))
        if r["state"]!="PREPARED" or camp.c["mode"]!="PREPARE_ONLY":raise ValueError("PREPARED_REQUIRED")
        counts=camp.counts(rows)
        if counts["held"]!=1 or counts["charged"]!=len(rows)-1:raise ValueError("BUDGET_SCOPE")
        return dict(req=camp.check_row(r),project=camp.b.research_project_id,request=workflow.case.hashbytes(r["request"]),
                    package=pkg,contract=pin,purpose=camp.c["af_purpose"])
    finally:camp.db.close()
if __name__=="__main__":print(json.dumps(main(),allow_nan=False))

