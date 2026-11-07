"""Actual archive SQLite transaction/CAS; native proof and lease are TEST substitutes.
No native Owner, Grant, Plan, Run or Solver API is called. Crash workers use
os._exit only on their own isolated test process, never a retained site process.
"""
import argparse,contextlib,json,os,sqlite3,subprocess,sys,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'gd'),str(ROOT/'gd/runtime'),str(ROOT/'tests')]
import expired_grant as eg
import native_grant_response_ipc as ipc

class CrashConnection:
    def __init__(self,db,point):self.db=db;self.point=point;self.inserted=False
    def execute(self,sql,args=()):
        value=self.db.execute(sql,args)
        if sql.startswith('INSERT INTO '+eg.TABLE):
            self.inserted=True
            if self.point=='before_commit':os._exit(71)
        return value
    def commit(self):
        self.db.commit()
        if self.inserted and self.point=='after_commit':os._exit(72)
    def rollback(self):return self.db.rollback()

def proposal(folder,op):
    return dict(schema=eg.SCHEMA,operation_id=op,workspace=str(folder),project='MACHINE_TEST_RP',candidate='MACHINE_TEST_B',contract='MACHINE_TEST_CONTRACT',original_request='MACHINE_TEST_REQUEST',
        parent=dict(operation_id='MACHINE_TEST_PARENT',identity={'MACHINE_TEST':True}),history='MACHINE_TEST_HISTORY',budget=dict(limit=2,held=1,charged=1,available=0),
        proof=dict(journal='MACHINE_TEST_NOT_A_REAL_JOURNAL',closure={'MACHINE_TEST':True},native=dict(grant=dict(grant_id='g_MACHINE_TEST_UNIQUE'))),
        package='MACHINE_TEST_NOT_SITE',execution_authorized=False,budget_changed=False,native_grant_modified=False)

def archive(folder,op,point=None):
    folder=Path(folder).resolve();assert folder.parent.parent==ROOT/'evidence' and folder.parent.name.startswith('MACHINE_TEST_ARCHIVE_TX_')
    db=sqlite3.connect(folder/'workflow.sqlite',timeout=10,isolation_level=None);db.row_factory=sqlite3.Row
    camp=SimpleNamespace(root=folder,db=CrashConnection(db,point) if point else db);p=proposal(folder,op)
    try:
        return eg.archive(camp,p,eg.c.pin(p))
    finally:db.close()

def persisted(folder):
    db=sqlite3.connect(Path(folder)/'workflow.sqlite');db.row_factory=sqlite3.Row
    try:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(eg.TABLE,)).fetchone():return []
        return [dict(r) for r in db.execute('SELECT * FROM '+eg.TABLE)]
    finally:db.close()

def main():
    p=argparse.ArgumentParser();p.add_argument('--package-pin',required=True);p.add_argument('--worker');p.add_argument('--operation');p.add_argument('--point');a=p.parse_args();ipc.installed(a.package_pin)
    boundaries=contextlib.ExitStack()
    boundaries.enter_context(patch.object(eg,'native_proof',lambda *a:({},object(),{})))
    boundaries.enter_context(patch.object(eg,'proposal',lambda camp,op,*a:proposal(camp.root,op)))
    boundaries.enter_context(patch.object(eg,'verify_reference',lambda *a:({},None)))
    boundaries.enter_context(patch.object(eg.c,'leases',lambda *a:contextlib.nullcontext()))
    if a.worker:archive(a.worker,a.operation,a.point);return
    root=ROOT/'evidence'/('MACHINE_TEST_ARCHIVE_TX_'+uuid.uuid4().hex);root.mkdir();checks=[]
    def check(name,value=True):assert value,name;checks.append(name)
    folder=root/'concurrent';folder.mkdir();ops=[uuid.uuid4().hex,uuid.uuid4().hex]
    def compete(op):
        try:return ('PASS',archive(folder,op))
        except Exception as exc:return ('REFUSED',repr(exc))
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(compete,ops))
    ipc.write(root/'CONCURRENT_RESULTS.json',results)
    check('different_operations_same_parent_grant_one_winner',sorted(x[0] for x in results)==['PASS','REFUSED'])
    rs=persisted(folder);check('one_complete_row',len(rs)==1 and rs[0]['state']=='COMMITTED')
    winner=rs[0]['operation_id'];again=archive(folder,winner);check('concurrent_winner_replay_no_append',again['replayed'] and len(persisted(folder))==1)
    for point,exit_code in [('before_commit',71),('after_commit',72)]:
        folder=root/point;folder.mkdir();op=uuid.uuid4().hex
        run=subprocess.run([sys.executable,'-I','-B','-S',str(Path(__file__).resolve()),'--package-pin',a.package_pin,'--worker',str(folder),'--operation',op,'--point',point],stdin=subprocess.DEVNULL,capture_output=True,timeout=25,creationflags=subprocess.CREATE_NO_WINDOW)
        check(point+'_controlled_test_process_exit',run.returncode==exit_code)
        rows=persisted(folder)
        if point=='before_commit':
            check('uncommitted_insert_no_partial_row',rows==[])
            result=archive(folder,op);check('same_operation_can_finish_after_rollback',not result['replayed'] and len(persisted(folder))==1)
        else:
            check('committed_row_survives_process_exit',len(rows)==1 and rows[0]['operation_id']==op and rows[0]['state']=='COMMITTED')
            result=archive(folder,op);check('post_commit_reopen_same_result_no_append',result['replayed'] and len(persisted(folder))==1)
    output=dict(classification='ACTUAL_ARCHIVE_SQLITE_TX_WITH_NATIVE_PROOF_PROPOSAL_LEASE_TEST_BOUNDARIES',passed=len(checks),checks=checks,native_calls=0,solver_calls=0)
    ipc.write(root/'RESULTS.json',output);print(json.dumps(dict(passed=len(checks),evidence=str(root/'RESULTS.json'))))

if __name__=='__main__':main()
