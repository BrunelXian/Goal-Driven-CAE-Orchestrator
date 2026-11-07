"""Spawned installed expired_grant.main CLI with declared synthetic science boundary.
Only stopped MACHINE_TEST fixture accepted. No Owner/Grant/Plan/Solver calls.
"""
import argparse,json,sys,subprocess,uuid
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'gd'),str(ROOT/'gd/runtime'),str(ROOT/'tests')]
import native_grant_response_ipc as ipc,build_grant_fixture as bf

def main():
    p=argparse.ArgumentParser();p.add_argument('--fixture',required=True);p.add_argument('--package-pin',required=True);p.add_argument('--child',choices=('read','archive'));a=p.parse_args();root=ipc.fixture_path(a.fixture)
    ipc.installed(a.package_pin);first=root/'first';work=first/'research';data=json.loads((first/'FIXTURE.json').read_bytes());ref=json.loads((first/'ARCHIVE_RESULT.json').read_bytes())['reference']
    if a.child:
        import expired_grant as eg
        argv=['expired_grant.py',a.child,'--workspace',str(work),'--contract-pin',data['contract'],'--package-pin',a.package_pin,'--python-exe',sys.executable,'--operation-id',ref['operation_id']]
        if a.child=='archive':
            proposal=first/'ARCHIVE_PROPOSAL.json';value=json.loads(proposal.read_bytes())
            argv+=['--proposal',str(proposal),'--proposal-pin',value['proposal_digest']]
        with bf.science(work,a.package_pin,data['contract']),patch.object(sys,'argv',argv):eg.main()
        return
    out=root/('cli-process-'+uuid.uuid4().hex);out.mkdir();checks=[]
    def check(n,v=True):assert v,n;checks.append(n)
    before=ipc.sha(work/'workflow.sqlite')
    for action in ('read','archive'):
        result=subprocess.run([sys.executable,'-I','-B','-S',str(Path(__file__).resolve()),'--fixture',str(root),'--package-pin',a.package_pin,'--child',action],stdin=subprocess.DEVNULL,capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
        (out/(action+'.stdout.json')).write_bytes(result.stdout);(out/(action+'.stderr.txt')).write_bytes(result.stderr)
        check(action+'_spawned_process_exit_zero',result.returncode==0)
        value=json.loads(result.stdout)
        check(action+'_exact_archive_reference',value['reference']==ref)
        if action=='archive':check('spawned_archive_same_key_replayed',value['replayed'] and not value['budget_changed'] and not value['native_grant_modified'])
        else:check('spawned_read_exact_persisted_operation',value['record']['operation_id']==ref['operation_id'])
        check(action+'_workflow_bytes_unchanged',ipc.sha(work/'workflow.sqlite')==before)
    ipc.write(out/'RESULTS.json',dict(passed=len(checks),checks=checks,classification='SPAWNED_INSTALLED_MAIN_ARGUMENTS_AND_QUALIFICATION_WITH_SCIENTIFIC_BOUNDARY_SUBSTITUTES',native_calls=0,new_plan_owner_grant_run_solver=0))
    print(json.dumps(dict(passed=len(checks),evidence=str(out/'RESULTS.json'))))

if __name__=='__main__':main()
