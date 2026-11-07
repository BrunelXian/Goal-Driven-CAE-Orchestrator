"""Exact original AF incident archive. Never starts/stops/executes or changes GD DB."""
import argparse,json,sys,re
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'runtime')]
import continuation as c
from r3_bridge import trusted_af

def proposal_digest(value):
    """Only the original bare SHA256 or the exact native algorithm tag."""
    c.require(type(value) is str,'PROPOSAL_DIGEST_FORMAT')
    if re.fullmatch(r'[0-9a-f]{64}',value):return 'sha256:'+value
    c.require(re.fullmatch(r'sha256:[0-9a-f]{64}',value) is not None,'PROPOSAL_DIGEST_FORMAT')
    return value

def load_proposal(path,expected,digest):
    outer=json.loads(c.local(path).read_bytes());value=outer.get('proposal',outer)
    actual=digest(value)
    c.require(actual==proposal_digest(expected),'PROPOSAL_CHANGED')
    if 'proposal' in outer:
        c.require(proposal_digest(outer['proposal_digest'])==actual,'PROPOSAL_ENVELOPE_CHANGED')
    return value,actual

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('proposal','check','commit','reconcile'))
    for n in ('project','package-pin','python-exe'):p.add_argument('--'+n,required=True)
    p.add_argument('--identities');p.add_argument('--review');p.add_argument('--review-sha256');p.add_argument('--operation-id')
    p.add_argument('--proposal');p.add_argument('--proposal-digest');p.add_argument('--authorization');p.add_argument('--authorization-sha256')
    a=p.parse_args()
    from main import verify
    verify(Path(__file__).parent,a);trusted_af()
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager
    from abqjobpilot.cross_boot_terminal import read_terminal,INTENT
    from abqjobpilot.execution.models import digest
    m=ServiceLifecycleManager(c.local(a.project))
    if a.action=='proposal':
        identities=json.loads(c.local(a.identities).read_bytes())
        value=m.cross_boot_proposal(identities,[dict(path=a.review,sha256=a.review_sha256)],a.operation_id)
        result=dict(proposal=value,proposal_digest=digest(value),status='UNAPPROVED_PROPOSAL_ONLY')
    elif a.action=='check':
        value,pin=load_proposal(a.proposal,a.proposal_digest,digest)
        fresh=m.cross_boot_proposal(value['scope']['identities'],value['evidence_references'],value['operation_id'])
        c.require(fresh==value,'PROPOSAL_CHANGED');result=dict(status='EXACT_READONLY_CHECK',proposal_digest=pin,execution_authorized=False)
    elif a.action=='commit':
        value,pin=load_proposal(a.proposal,a.proposal_digest,digest)
        result=m.record_cross_boot_terminal(value,proposal_digest=pin,
            authorization_reference=dict(path=a.authorization,sha256=a.authorization_sha256))
    else:
        terminal=read_terminal(m);current=m._current()
        result=dict(terminal=terminal,intent_exists=bool(current and m._path(current['start_id']+'/'+INTENT).exists()),
            instruction='READ_ONLY_RECONCILIATION_NO_AUTOMATIC_RETRY')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
