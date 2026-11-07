"""Actual workflow SQLite + DPAPI seal, substituted completed ODB source only."""
import sys,json,uuid,hashlib,sqlite3
from pathlib import Path
from unittest.mock import patch
z=Path(__file__).resolve().parents[1];sys.path[:0]=[str(z/'gd'),str(z/'gd/runtime')]
import workflow,tensile,native_feedback as nf,terminal_materialization as tm,native_accounting as accounting
from r3_bridge import trusted_af
trusted_af()
from abqjobpilot.product_project import create_project
from abqjobpilot.service_lifecycle import ServiceLifecycleManager
import abqjobpilot.service_lifecycle as lifecycle
from abqjobpilot.local_credentials import read_private
root=z/'evidence'/('OFFLINE_MATERIALIZATION_'+uuid.uuid4().hex);root.mkdir();checks=[]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,v=True):assert v,name;checks.append(name)
def reject(name,fn):
    try:fn()
    except Exception:checks.append(name)
    else:raise AssertionError(name)
model=Path(r'D:\Projects\GDCAETEST\TENSILE-V1-R3-ADMISSION-20261105-dev-93a1ef42\model')
target=Path(r'D:\Projects\GDCAETEST\TENSILE-V1-PUBLIC-TARGET-20261104-69d2a041ef\target_force_displacement.csv')
package=sha(z/'gd/package-manifest.json');work=root/'research'
init=workflow.initialize(work,model,target,sha(target),'PREPARE_ONLY',package,'OFFLINE_TEST_ONLY')
camp=workflow.Campaign(work,init['contract_sha256'],package);A=camp.prepare('A');frames=tensile.fixture_curve(A['request']['parameters'])
feedback=dict(classification='NATIVE_ODB',binding={'run_id':'OFFLINE_A'},frames=frames,assessment=tensile.compare(camp.target,frames,A['request']['parameters']))
real_verify=nf.verify
def verify(c,row):return json.loads(row['result']) if row['phase']=='A' else real_verify(c,row)
with patch.object(nf,'source',lambda *a:None),patch.object(nf,'extract',lambda *a:feedback),patch.object(nf,'verify',verify):
    camp.observe('A',A['request_sha256'],'NATIVE');B=camp.prepare('B')
req=B['request'];row=camp.db.execute("SELECT * FROM stages WHERE phase='B'").fetchone();raw_request=row['request']
create_project(root/'native','OFFLINE_TEST_ONLY_MATERIALIZATION');manager=ServiceLifecycleManager(root/'native')
reader=z/'gd/odb_reader.py';binding=dict(project_id=manager.context.project_id,plan_id='OFFLINE_PLAN',run_id='OFFLINE_RUN',receipt_id='OFFLINE_RECEIPT',output_key=req['output_key'],phase='B',request_digest=B['request_sha256'],sha256={'inp':req['inp_sha256'],'odb':'OFFLINE_SYNTHETIC'},reader_sha256=sha(reader))
ex=dict(schema='tensile-odb-extraction-v1',binding_sha256=tensile.hashbytes(tensile.pack(binding)),lineage={k:binding[k] for k in ('project_id','plan_id','run_id','receipt_id','output_key','phase','request_digest')},source_hashes=binding['sha256'],reader_sha256=binding['reader_sha256'],odb_read_only=True,analysis_complete=True,review_required=False,analysis_errors=0,analysis_warnings=0,diagnostic_line_count=0,end_forces_balanced=True,frames=tensile.fixture_curve(req['parameters']))
calls=[]
def source(c,r):return req,reader,binding,manager
def read(*args):calls.append('read');return ex
def a_verify(c,r):return json.loads(r['result']) if r['phase']=='A' else real_verify(c,r)
with patch.object(nf,'source',source),patch.object(nf,'read_extraction',read),patch.object(nf,'verify',a_verify),patch.object(accounting,'record_acceptance',lambda *a:{'native_consumed':1,'classification':'SUBSTITUTED_NATIVE_ACCEPTED_FACT'}):
    with patch.object(lifecycle,'write_new',side_effect=OSError('OFFLINE_CRASH_BEFORE_SEAL')):
        reject('crash_result_cached_before_seal',lambda:accounting.feedback_once(camp,B['request_sha256']))
    check('scientific_INTENT_not_charged',camp.db.execute("SELECT state FROM stages WHERE phase='B'").fetchone()[0]=='INTENT' and camp.counts(camp.verified_rows())['held']==1)
    check('cache_durable_unsealed',camp.db.execute('SELECT count(*) FROM '+tm.TABLE).fetchone()[0]==1 and not manager._path('tensile-feedback.json').exists())
    altered=dict(ex,analysis_errors=1)
    with patch.object(nf,'read_extraction',lambda *a:altered):reject('unsealed_cache_needs_actual_reader_equivalence',lambda:accounting.feedback_once(camp,B['request_sha256']))
    check('invalid_reread_not_sealed',not manager._path('tensile-feedback.json').exists())
    r=camp.db.execute("SELECT * FROM stages WHERE phase='B'").fetchone();result=tm.extract_once(camp,r)
    check('cache_reproduced_before_sealing',len(calls)==2 and manager._path('tensile-feedback.json').is_file())
    # Exact next crash seam: native seal exists, scientific INTENT is still open.
    with patch.object(nf,'read_extraction',side_effect=AssertionError('SEALED_CACHE_MUST_NOT_REEXTRACT')):
        completed=accounting.feedback_once(camp,B['request_sha256'])
    check('sealed_INTENT_recovers_without_reextract',completed['status']=='SAME_NATIVE_INTENT_COMMITTED')
    check('exact_once_final_budget',completed['budget']==dict(limit=2,held=0,charged=2,available=0))
    with patch.object(nf,'read_extraction',side_effect=AssertionError('COMMITTED_MUST_NOT_EXTRACT')):
        replay=accounting.feedback_once(camp,B['request_sha256'])
    check('committed_reopen_replay',replay['replayed'] and replay['budget']['charged']==2)
    check('one_scientific_NATIVE',camp.db.execute("SELECT count(*) FROM history WHERE phase='B' AND event='NATIVE'").fetchone()[0]==1)
camp.db.close()
result=dict(classification='OFFLINE_REAL_WORKFLOW_SQLITE_AND_DPAPI_SUBSTITUTED_ODB_SOURCE_NO_SOLVER',passed=len(checks),checks=checks,root=str(root),solver_calls=0,owner_calls=0)
(root/'RESULTS.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
