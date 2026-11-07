"""Bounded collector classification substitutes; no Owner or project writes."""
import sys,json,subprocess,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
z=Path(__file__).resolve().parents[1];sys.path[:0]=[str(z/'gd'),str(z/'gd/runtime')]
from r3_bridge import trusted_af
trusted_af()
from abqjobpilot import cross_boot_terminal as cb
from abqjobpilot.execution.ownership import current_process_identity
own=current_process_identity();boot=cb.boot_observation();project=r'D:\OFFLINE_TEST_ONLY\no-project';entry=str(z/'gd/cross_boot_archive.py')
manager=SimpleNamespace(context=SimpleNamespace(root=project,test_root=project),_current=lambda:dict(start_id='start_OFFLINE'))
tail=['-I','-B','-S',entry,'proposal','--project',project]
rows=[dict(ProcessId=own['pid'],ExecutablePath=own['image_path'],CommandLine=subprocess.list2cmdline([own['image_path']]+tail)),
      dict(ProcessId=own['parent_pid'],ExecutablePath=sys.executable,CommandLine=subprocess.list2cmdline([sys.executable]+tail))]
identities=[dict(image_path=own['image_path']),dict(image_path=sys.executable)]
checks=[]
def call(data):
    with patch.object(subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(data))):
        return cb.no_replacement(manager,identities,boot=boot)
def reject(name,data):
    try:call(data)
    except Exception:checks.append(name)
    else:raise AssertionError(name)
assert call(rows).startswith('SUPPORTED_NATIVE');checks.append('exact_current_archive_worker_transport')
bad=[dict(v) for v in rows];bad[1]['CommandLine']=subprocess.list2cmdline([sys.executable]+tail+['--different']);reject('parent_different_argv_rejected',bad)
bad=[dict(v) for v in rows];bad[1]['CommandLine']=None;reject('related_unreadable_rejected',bad)
bad=rows+[dict(ProcessId=2147483647,ExecutablePath=sys.executable,CommandLine=subprocess.list2cmdline([sys.executable,'service_owner.py','--project',project]))];reject('actual_owner_shaped_other_process_rejected',bad)
bad=[dict(v) for v in rows];bad[1]['ExecutablePath']=own['image_path'];reject('transport_wrong_image_rejected',bad)
out=dict(classification='COLLECTOR_ENUMERATION_SUBSTITUTES_WITH_ACTUAL_CURRENT_PARENT_HANDLE_IDENTITY',passed=len(checks),checks=checks,real_site_changed=False)
path=z/'evidence'/('COLLECTOR_'+uuid.uuid4().hex+'.json');path.write_text(json.dumps(out,indent=2));print(json.dumps(out))
