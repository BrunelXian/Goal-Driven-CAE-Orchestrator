"""Developer bounded coordinator tests; recovery/native facts explicitly substituted."""
import sys,time,tempfile,json,hashlib
from pathlib import Path
from unittest.mock import patch
z=Path(__file__).resolve().parents[1];sys.path[:0]=[str(z/'gd'),str(z/'gd/runtime')]
import grant_response as r
from operator_entry import Journal
out=z/'evidence'/('COORDINATOR_'+str(time.time_ns()));out.mkdir();checks=[]
def case(name,fn):fn();checks.append(name)
class Native:
    def __init__(self,fail):self.calls=0;self.fail=fail
    def authorize(self,args,key,owner):
        self.calls+=1
        if self.fail:raise TimeoutError('test post-send lost response')
        return dict(replayed=False,receipt={'grant_id':'fixture'})
def run(name,fail,states,expired=False):
    j=Journal(out/name);n=Native(fail);args={'expires_at':int(time.time())+100}
    with patch.object(r,'recover',side_effect=states):
        try:v=r.authorize_once(n,j,args,'fixtureowner',deadline=time.monotonic()-1 if expired else time.monotonic()+100)
        except ValueError as e:v=str(e)
    return j,n,v
good=dict(confirmed_committed=True,executable_now=True,receipt={'grant_id':'fixture'},state='COMMITTED_RESPONSE_RECOVERED')
j,n,v=run('success',False,[good]);assert n.calls==1 and (j.root/'authorize-result.json').exists();checks.append('one_send_response_verified')
j,n,v=run('lost',True,[good,good]);assert n.calls==1 and v['receipt']==good['receipt'];checks.append('lost_response_only_readonly_recovery_no_second_authorize')
j,n,v=run('pending',True,[dict(confirmed_committed=False,executable_now=False)]);assert n.calls==1 and v=='AUTHORIZATION_UNKNOWN_READONLY_RECONCILE_ONLY' and not (j.root/'authorize-result.json').exists();checks.append('unknown_no_fabricated_response')
j,n,v=run('expired',True,[dict(confirmed_committed=True,executable_now=False)]);assert n.calls==1 and v=='AUTHORIZATION_COMMITTED_NOT_EXECUTABLE';checks.append('committed_expired_no_progress')
j,n,v=run('before_send',False,[],True);assert n.calls==0 and not (j.root/'authorize-send-intent.json').exists();checks.append('expired_before_send_not_transmitted')
try:r.authorize_once(n,j,{'expires_at':int(time.time())+100},'fixtureowner',deadline=time.monotonic()+100)
except FileExistsError:pass
else:raise AssertionError('duplicate key path accepted')
assert n.calls==0;checks.append('duplicate_journal_no_transmission')
empty=out/'empty';empty.mkdir();view=r.recover(empty);assert view['state']=='REQUEST_NOT_PERSISTED' and not view['executable_now'];checks.append('no_request_no_authority')
(empty/'authorize-send-intent.json').write_text('{}')
try:r.recover(empty)
except ValueError as e:assert str(e)=='RECOVERY_REQUEST_MISSING'
else:raise AssertionError('missing request accepted')
checks.append('incomplete_request_refused')
for n in (-1,61,'60'):
 try:r.recover(empty,wait_seconds=n)
 except ValueError:pass
 else:raise AssertionError('unbounded wait')
checks.append('wait_bound_enforced')
# Static boundary: neither recovery nor this CLI may exercise an execution API.
source=(z/'gd/grant_response.py').read_text(encoding='utf8');import ast
tree=ast.parse(source)
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='recover')
attrs=[n.func.attr for n in ast.walk(f) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
assert not set(attrs)&{'authorize','request','submit','dispatch','stop','start','prepare','commit'};checks.append('readonly_recovery_has_no_mutation_call')
from r3_bridge import trusted_af
trusted_af()
from types import SimpleNamespace
import abqjobpilot.service_lifecycle as lifecycle
late=out/'late';late.mkdir();(late/'authorize-request.json').write_text('{}')
ctx=dict(owner=dict(owner_id='o',start_id='s'),packet=dict(af_project=str(out)),request=dict(operation_key='k'),old=z/'gd')
receipt={'operation_key':'k'};view=dict(receipt=receipt,ready=dict(process={'pid':1}))
client=SimpleNamespace(endpoint={'owner_id':'o'},management_receipt=lambda *a:receipt)
manager=SimpleNamespace(connect=lambda:(client,None,dict(lifecycle_start_id='s',process={'pid':1})))
with patch.object(r,'packet_context',return_value=ctx),patch.object(r,'scientific_context',side_effect=[{'budget':'held'},{'budget':'changed'}]),patch.object(r,'durable',return_value=view),patch.object(lifecycle,'ServiceLifecycleManager',return_value=manager):
 try:r.recover(late)
 except ValueError as e:assert str(e)=='RECOVERY_SCIENTIFIC_STATE_CHANGED_DURING_WAIT'
 else:raise AssertionError('late scientific mutation accepted')
checks.append('scientific_state_rechecked_before_executable_result')
result=dict(classification='COORDINATOR_TEST_SUBSTITUTED_NATIVE_RECOVERY',checks=checks,pass_count=len(checks),actual_native_ipc=False)
(out/'RESULTS.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
