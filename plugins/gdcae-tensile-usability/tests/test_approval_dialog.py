"""No Solver/Owner: in-memory substitutes and an explicit TEST_ONLY Win32 smoke."""
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
import struct
import zlib
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/gd'))
import approval_dialog as ui
import operator_entry as entry


class Clock:
    def __init__(self):self.t=1000.;self.offset=0
    def wall(self):return self.t+self.offset
    def clock(self):return self.t
    def sleep(self,seconds):self.t+=seconds


class FakeWindow:
    def __init__(self,state,actions=('start','approve')):
        self.state=state;self.actions=list(actions);self.events=[];self.thread=self
    def is_alive(self):return True
    def update(self,status,details='',button=None,enabled=False,summary=''):
        self.events.append((status,details,button,enabled,summary))
        if enabled and self.actions:self.state.click(self.actions.pop(0),mouse=True)
    def close(self):pass


class Native:
    def __init__(self,clock,fail=None):
        self.clock=clock;self.fail=fail;self.calls=[];self.queries=0
        self.plan=dict(plan_id='TEST_plan',plan_digest='TEST_digest',project_instance_id='TEST_pi',job_id='TEST_job',job_revision=1,
            job_name='TEST_B',engineering='TEST_OUTPUT',scratch='TEST_SCRATCH',output_key='test_out',expires_at=1600,
            resources=entry.RESOURCES,input_manifest=[{'digest':'TEST_INPUT'}],
            registration=dict(project_id='TEST_project',purpose='JIT_HUMAN_REVIEW',phase='B',parameters={'sigma_y_MPa':'288','H_MPa':'3003'}))
        self.checked=dict(status='DYNAMIC_READONLY_PASS',operation_id='op',project='TEST_rp',candidate='TEST_B',original_request='TEST_request_B',
            budget=dict(limit=2,held=1,charged=1,available=0),execution_authorized=False,plan_id=self.plan['plan_id'],plan_digest=self.plan['plan_digest'],
            scope_digest='TEST_scope',new={'plan':self.plan,'scope_digest':'TEST_scope','af_project':'TEST_AF'})
        self.receipt={'state':'STOP_COMMITTED','owner_id':'TEST_owner','start_id':'TEST_start'}
    def hit(self,name):
        self.calls.append(name)
        if self.fail==name:raise RuntimeError('LOST_RESPONSE_'+name)
    def static(self,op):self.hit('static');return dict(status='STATIC_READONLY_READY',plan_created=False,proposal_digest='TEST_proposal',proposal={'purpose':'JIT_HUMAN_REVIEW'})
    def prepare(self,*args):self.hit('prepare');return {'new':self.checked['new']}
    def dynamic(self,path):return self.checked
    def review_binding(self):return self.checked
    def installation(self):return {'gd_installed':'TEST_GD','gd_package_sha256':'TEST_PIN','af_installed':'TEST_AF','af_identity':'TEST_AF_PIN'}
    def digest(self,value):return 'TEST_scope'
    def scope(self,plan):return {}
    def attach(self,path):pass
    def inspect(self,path):return dict(plan=self.plan,counts=dict(plans=1,grants=0,runs=0,receipts=0,consumption=0),gate={'state':'PAUSED','owner_id':'TEST_owner'},supervisor_started='1' if 'start' in self.calls else '0')
    def start(self):self.hit('start');return dict(state='CONNECTED',created=True,owner_id='TEST_owner',start_id='TEST_start')
    def connect(self,owner):return {'project_instance_id':'TEST_pi','owner_id':'TEST_owner','start_id':'TEST_start'}
    def project_view(self):return dict(project_id='TEST_project',project_instance_id='TEST_pi',gate={'state':'PAUSED','owner_id':'TEST_owner'},slot_run_id=None,runs=[])
    def sid(self):return 'TEST_SID'
    def authorize(self,args,key,owner):self.hit('authorize');return dict(replayed=False,receipt={'grant_id':'TEST_grant','scope_digest':'TEST_scope','expires_at':1600})
    def submit(self,request):self.hit('submit');return {'request_status':'ACCEPTED','receipt':{'run_id':'TEST_run'}}
    def record_acceptance(self):self.hit('acceptance_fact');return {'TEST_ONLY':True,'scientific_charge_policy':'UNCHANGED_FROZEN_OUTCOME_SETTLEMENT'}
    def cleanup_preflight(self,plan,owner):
        self.hit('cleanup_preflight')
        return dict(plan_id=plan['plan_id'],owner=self.connect(owner),counts={'grants':0,'runs':0,'receipts':0,'consumption':0,'events':0},
                    gate=self.gate(),slot_run_id=None)
    def cleanup_records(self,plan):return dict(TEST_ONLY=True,process_exit='NOT_INDEPENDENTLY_VERIFIED')
    def completion_exits(self,owner,stop):
        self.hit('completion_exits')
        return dict(classification='TEST_ONLY_RETAINED_EXITS',unexecuted_readmission_qualification=False)
    def closure(self,plan,owner,stop,journal_root):
        self.hit('closure')
        return dict(schema='execution-window-stop-reference-v1',path=str(Path(journal_root)/'TEST_ONLY_closure.json'),sha256='a'*64)
    def run(self,run):
        self.queries+=1
        return dict(plan_id=self.plan['plan_id'],plan_digest=self.plan['plan_digest'],grant_id='TEST_grant',revision=1,
            execution='PLANNED' if self.queries==1 else 'FINISHED',queue_state='PENDING',launch_state='NOT_CALLED',reconciliation='NONE',managed_completion='COMMITTED_EMPTY_SCOPE')
    def gate(self):return {'state':'PAUSED','owner_id':'TEST_owner','version':2}
    def dispatch(self,args,key,owner):self.hit('dispatch');return {'receipt':{'run_id':'TEST_run','grant_id':'TEST_grant'}}
    def stop(self,owner,key):self.hit('stop');return {'receipt':self.receipt}
    def stopped(self):return {'receipt':self.receipt}
    def observe(self,request):self.hit('observe');return {'phase':'B','TEST_ONLY':'NO_REAL_ODB'}


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='ui-test-',dir=ROOT);self.root=Path(self.tmp.name);self.clock=Clock()
    def tearDown(self):self.tmp.cleanup()
    def dialog(self,actions=('start','approve')):
        return ui.ApprovalDialog(wall=self.clock.wall,clock=self.clock.clock,window_factory=lambda s:FakeWindow(s,actions))
    def flow(self,dialog,native=None,delegation=None):
        native=native or Native(self.clock)
        result=entry.execute(native,entry.Journal(self.root/'op'),'op',confirmation=dialog,wall=self.clock.wall,
            clock=self.clock.clock,sleep=self.clock.sleep,emit=lambda s:None,artifacts=lambda p:{'TEST_ONLY':True},cleanup_delegation=delegation)
        return result,native
    def test_full_substitute_path_two_clicks_native_grant_once(self):
        dialog=self.dialog();result,native=self.flow(dialog)
        self.assertEqual(native.calls.count('authorize'),1);self.assertEqual(native.calls.count('submit'),1)
        self.assertEqual(native.calls.count('dispatch'),1);self.assertTrue(dialog.grant_received)
        self.assertEqual(result['independent_acceptance'],'NOT_PERFORMED')
        detail=next(e[1] for e in dialog.window.events if e[2]=='批准本次计算')
        for field in ('TEST_job','TEST_INPUT','TEST_OUTPUT','TEST_SCRATCH','TEST_PIN','+08:00','288','3003','2048'):self.assertIn(field,detail)
        self.assertFalse(any('RUN ' in e[0] for e in dialog.window.events))
    def test_cancel_before_jit_no_plan(self):
        native=Native(self.clock)
        with self.assertRaisesRegex(ValueError,'CANCELLED'):self.flow(self.dialog(('cancel',)),native)
        self.assertEqual(native.calls,['static'])
    def test_cancel_after_connected_no_grant_no_cleanup(self):
        native=Native(self.clock)
        with self.assertRaisesRegex(ValueError,'CANCELLED'):self.flow(self.dialog(('start','cancel')),native)
        self.assertIn('start',native.calls);self.assertNotIn('authorize',native.calls);self.assertNotIn('stop',native.calls)
    def test_enter_space_focus_not_approval(self):
        state=ui.DecisionState(self.clock.wall,self.clock.clock);state.arm('APPROVE',expires=1600,deadline=1600)
        for event in ('enter','space','focus','minimize','approve'):
            self.assertFalse(state.click(event,mouse=False));self.assertIsNone(state.choice)
        self.assertTrue(state.click('approve',mouse=True))
    def test_double_click_and_concurrent_one_decision(self):
        state=ui.DecisionState(self.clock.wall,self.clock.clock);state.arm('APPROVE',expires=1600,deadline=1600)
        results=[];threads=[threading.Thread(target=lambda:results.append(state.click('approve',mouse=True))) for _ in range(12)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(results.count(True),1)
    def test_expiry_monotonic_and_wallclock_never_extended(self):
        for rollback in (False,True):
            state=ui.DecisionState(self.clock.wall,self.clock.clock);state.arm('APPROVE',expires=1600,deadline=1600)
            self.clock.t=1601;self.clock.offset=-1000 if rollback else 0
            self.assertEqual(state.tick(),'EXPIRED');self.assertFalse(state.click('approve',mouse=True))
    def test_expired_during_click_preflight_no_native_authorize(self):
        dialog=self.dialog();native=Native(self.clock);old=native.review_binding
        def expired():self.clock.t=1601;return old()
        native.review_binding=expired
        with self.assertRaisesRegex(ValueError,'EXPIRED'):self.flow(dialog,native)
        self.assertNotIn('authorize',native.calls)
    def test_budget_changed_after_click_refused(self):
        native=Native(self.clock);native.review_binding=lambda:dict(native.checked,budget=dict(limit=2,held=0,charged=2,available=0))
        with self.assertRaisesRegex(ValueError,'BINDING_OR_BUDGET'):self.flow(self.dialog(),native)
        self.assertNotIn('authorize',native.calls)
    def test_owner_changed_after_click_refused(self):
        native=Native(self.clock);calls=[];old=native.connect
        def changed(owner):
            calls.append(1);result=old(owner)
            if len(calls)>1:result['start_id']='OTHER'
            return result
        native.connect=changed
        with self.assertRaisesRegex(ValueError,'OWNER_CHANGED'):self.flow(self.dialog(),native)
        self.assertNotIn('authorize',native.calls)
    def test_slot_changed_after_click_refused(self):
        native=Native(self.clock);old=native.project_view;native.project_view=lambda:dict(old(),slot_run_id='OTHER')
        with self.assertRaisesRegex(ValueError,'SLOT_OR_RUN'):self.flow(self.dialog(),native)
        self.assertNotIn('authorize',native.calls)
    def test_counts_changed_after_click_refused(self):
        native=Native(self.clock);old=native.inspect
        def changed(path):
            result=old(path)
            if 'start' in native.calls:result['counts']['grants']=1
            return result
        native.inspect=changed
        with self.assertRaisesRegex(ValueError,'NATIVE_STATE_CHANGED'):self.flow(self.dialog(),native)
        self.assertNotIn('authorize',native.calls)
    def test_cancel_during_preflight_refuses(self):
        dialog=self.dialog();native=Native(self.clock);old=native.review_binding
        def cancelled():dialog.state.click('cancel',mouse=False);return old()
        native.review_binding=cancelled
        with self.assertRaisesRegex(ValueError,'CANCELLED'):self.flow(dialog,native)
        self.assertNotIn('authorize',native.calls)
    def test_installation_changed_after_click_refused(self):
        native=Native(self.clock);calls=[];old=native.installation
        def changed():calls.append(1);return dict(old(),af_identity='OTHER' if len(calls)>1 else 'TEST_AF_PIN')
        native.installation=changed
        with self.assertRaisesRegex(ValueError,'INSTALLATION_CHANGED'):self.flow(self.dialog(),native)
        self.assertNotIn('authorize',native.calls)
    def test_packet_file_changed_after_click_refused(self):
        dialog=self.dialog();old=dialog.authorize
        def changed(packet,**kwargs):
            proof=old(packet,**kwargs);p=self.root/'op'/'confirmation-packet.json';data=json.loads(p.read_bytes());data['job_id']='OTHER';p.write_text(json.dumps(data));return proof
        dialog.authorize=changed;native=Native(self.clock)
        with self.assertRaisesRegex(ValueError,'PERSISTED_CONFIRMATION'):self.flow(dialog,native)
        self.assertNotIn('authorize',native.calls)
    def test_native_grant_loss_no_success_or_submit(self):
        dialog=self.dialog();native=Native(self.clock,fail='authorize')
        with self.assertRaisesRegex(RuntimeError,'LOST_RESPONSE'):self.flow(dialog,native)
        self.assertFalse(dialog.grant_received);self.assertNotIn('submit',native.calls);self.assertNotIn('stop',native.calls)
    def test_nonconnected_owner_cannot_show_approval(self):
        native=Native(self.clock);native.start=lambda:dict(state='STARTING',created=True)
        with self.assertRaisesRegex(ValueError,'OWNER_START_UNKNOWN'):self.flow(self.dialog(),native)
        self.assertNotIn('authorize',native.calls)
    def test_delegated_cancel_once_idle_stop(self):
        native=Native(self.clock)
        with self.assertRaisesRegex(ValueError,'CANCELLED'):
            self.flow(self.dialog(('start','cancel')),native,{'permitted_actions':['normal_idle_stop_unexecuted'],'TEST_ONLY':True})
        self.assertEqual(native.calls.count('stop'),1);self.assertNotIn('authorize',native.calls)
        result=json.loads((self.root/'op'/'cancel-idle-result.json').read_bytes())
        self.assertEqual(result['process_exit'],'RETAINED_HANDLE_FACTS_RECORDED')
        self.assertEqual(result['independent_acceptance'],'NOT_PERFORMED')
        self.assertEqual(native.calls.count('closure'),1)
        self.assertTrue((self.root/'op'/'cancel-idle-qualification.json').exists())
        self.assertTrue((self.root/'op'/'cancel-idle-stop-request.json').exists())
    def test_delegated_expired_once_idle_stop(self):
        native=Native(self.clock);dialog=self.dialog()
        def expired(packet,**kwargs):self.clock.t=1601;raise ValueError('APPROVAL_EXPIRED_NO_GRANT')
        dialog.authorize=expired
        with self.assertRaisesRegex(ValueError,'EXPIRED'):
            self.flow(dialog,native,{'permitted_actions':['normal_idle_stop_unexecuted']})
        self.assertEqual(native.calls.count('stop'),1);self.assertNotIn('authorize',native.calls)
    def test_unknown_never_auto_cleanup_even_delegated(self):
        native=Native(self.clock,fail='authorize')
        with self.assertRaises(RuntimeError):self.flow(self.dialog(),native,{'permitted_actions':['normal_idle_stop_unexecuted']})
        self.assertNotIn('stop',native.calls);self.assertNotIn('cleanup_preflight',native.calls)
    def test_cancel_after_grant_never_cleanup(self):
        native=Native(self.clock);dialog=self.dialog();old=dialog.native_granted
        def cancelled(grant):old(grant);dialog.state.click('cancel',mouse=False)
        dialog.native_granted=cancelled
        with self.assertRaisesRegex(ValueError,'CANCELLED'):
            self.flow(dialog,native,{'permitted_actions':['normal_idle_stop_unexecuted']})
        self.assertNotIn('cleanup_preflight',native.calls);self.assertNotIn('stop',native.calls);self.assertNotIn('submit',native.calls)
    def test_cleanup_not_idle_refuses_without_stop(self):
        native=Native(self.clock);old=native.cleanup_preflight
        def changed(plan,owner):value=old(plan,owner);value['counts']['grants']=1;return value
        native.cleanup_preflight=changed
        with self.assertRaisesRegex(ValueError,'CANCELLED'):
            self.flow(self.dialog(('start','cancel')),native,{'permitted_actions':['normal_idle_stop_unexecuted']})
        self.assertNotIn('stop',native.calls)
    def test_cleanup_lost_response_no_retry(self):
        native=Native(self.clock,fail='stop')
        with self.assertRaisesRegex(ValueError,'CANCELLED'):
            self.flow(self.dialog(('start','cancel')),native,{'permitted_actions':['normal_idle_stop_unexecuted']})
        self.assertEqual(native.calls.count('stop'),1)
        self.assertTrue((self.root/'op'/'cancel-idle-blocked.json').exists())
    def test_delegation_exact_reference_and_no_solver_grant(self):
        package='a'*64;p=self.root/'delegation.json'
        data=dict(schema='local-operation-delegation-v1',operation_id='op',workspace=str(self.root),package_pin=package,
                  permitted_actions=['normal_idle_stop_unexecuted'],solver_grant=False,source_reference='TEST_ONLY explicit task delegation')
        p.write_text(json.dumps(data));ref={'permitted_actions':data['permitted_actions'],'reference':{'path':str(p),'sha256':entry.sha(p)}}
        entry.check_cleanup_delegation(ref,operation='op',work=self.root,package=package)
        data['solver_grant']=True;p.write_text(json.dumps(data));ref['reference']['sha256']=entry.sha(p)
        with self.assertRaisesRegex(ValueError,'BINDING_MISMATCH'):entry.check_cleanup_delegation(ref,operation='op',work=self.root,package=package)
    def test_window_stop_reference_exact_fields(self):
        ref=dict(schema='execution-window-stop-reference-v1',path=str(self.root/'closure.json'),sha256='a'*64)
        entry.check_qualification(ref)
        with self.assertRaisesRegex(ValueError,'EXACT_WINDOW'):entry.check_qualification(dict(ref,approval=True))
        with self.assertRaises(ValueError):entry.check_qualification(dict(ref,sha256='bad'))


def capture_test_client(hwnd,target):
    """PrintWindow client only, never a desktop screenshot or other HWND."""
    u=ctypes.WinDLL('user32',use_last_error=True);g=ctypes.WinDLL('gdi32',use_last_error=True)
    u.GetDC.argtypes=[w.HWND];u.GetDC.restype=w.HDC;u.ReleaseDC.argtypes=[w.HWND,w.HDC]
    u.GetClientRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)];u.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
    u.PrintWindow.argtypes=[w.HWND,w.HDC,w.UINT];u.PrintWindow.restype=w.BOOL
    g.CreateCompatibleDC.argtypes=[w.HDC];g.CreateCompatibleDC.restype=w.HDC
    g.CreateCompatibleBitmap.argtypes=[w.HDC,ctypes.c_int,ctypes.c_int];g.CreateCompatibleBitmap.restype=w.HBITMAP
    g.SelectObject.argtypes=[w.HDC,w.HGDIOBJ];g.SelectObject.restype=w.HGDIOBJ
    g.DeleteObject.argtypes=[w.HGDIOBJ];g.DeleteDC.argtypes=[w.HDC]
    g.GetDIBits.argtypes=[w.HDC,w.HBITMAP,w.UINT,w.UINT,ctypes.c_void_p,ctypes.c_void_p,w.UINT];g.GetDIBits.restype=ctypes.c_int
    client=w.RECT();outer=w.RECT();assert u.GetClientRect(hwnd,ctypes.byref(client));assert u.GetWindowRect(hwnd,ctypes.byref(outer))
    width,height=client.right,client.bottom;dc=u.GetDC(hwnd);memory=g.CreateCompatibleDC(dc);bitmap=g.CreateCompatibleBitmap(dc,width,height);prior=g.SelectObject(memory,bitmap)
    try:
        assert u.PrintWindow(hwnd,memory,1),'PrintWindow failed'
        g.SelectObject(memory,prior)
        info=struct.pack('<IiiHHIIiiII',40,width,-height,1,32,0,width*height*4,0,0,0,0)
        buffer=ctypes.create_string_buffer(width*height*4);header=ctypes.create_string_buffer(info)
        assert g.GetDIBits(memory,bitmap,0,height,buffer,header,0)==height
        pixels=buffer.raw;rows=[]
        for row in range(height):
            source=pixels[row*width*4:(row+1)*width*4];rgb=bytearray(width*3)
            rgb[0::3]=source[2::4];rgb[1::3]=source[1::4];rgb[2::3]=source[0::4];rows.append(b'\0'+rgb)
        def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)
        png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')
        with target.open('xb') as f:f.write(png)
        return dict(window_rect=[outer.left,outer.top,outer.right,outer.bottom],client_rect=[0,0,width,height],capture='PrintWindow_PW_CLIENTONLY',other_desktop_content_captured=False)
    finally:g.DeleteObject(bitmap);g.DeleteDC(memory);u.ReleaseDC(hwnd,dc)


def window_smoke():
    """Only this newly created TEST_ONLY HWND; never an actual operator window."""
    state=ui.DecisionState();window=ui.Win32Window(state,test_only=True)
    u=ctypes.WinDLL('user32',use_last_error=True)
    u.SendMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.SendMessageW.restype=ctypes.c_ssize_t
    u.ShowWindow.argtypes=[w.HWND,ctypes.c_int]
    u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    title=ctypes.create_unicode_buffer(256);u.GetWindowTextW(window.hwnd,title,256)
    assert title.value.startswith('TEST_ONLY'),title.value
    try:
        state.arm('START');window.update('TEST_ONLY 无 Solver/Owner/Grant。机器点击不代表真人验收。','TEST_ONLY exact synthetic packet','发起审查',True);time.sleep(.25)
        button=window.controls['approve']
        for msg,wp in ((0x100,13),(0x101,13),(0x100,32),(0x101,32),(0xF5,0)):u.SendMessageW(button,msg,wp,0)
        assert state.choice is None
        u.SendMessageW(button,0x201,1,10|(10<<16));u.SendMessageW(button,0x202,0,10|(10<<16))
        assert state.choice=='start'
        deadline=time.monotonic()+120;expires=time.time()+120
        dialog=object.__new__(ui.ApprovalDialog);dialog.state=state;dialog.window=window;dialog.wall=time.time;dialog.clock=time.monotonic
        dialog.packet_pin=None;dialog.operation='op';dialog.grant_received=False
        native=Native(Clock());plan=dict(native.plan,expires_at=expires)
        value=dict(operation_id='op',project='TEST_ONLY 科研项目',candidate='TEST_ONLY B',parameters=plan['registration']['parameters'],
            budget=native.checked['budget'],resources=plan['resources'],job_id=plan['job_id'],job_revision=1,input_manifest=plan['input_manifest'],
            engineering=plan['engineering'],scratch=plan['scratch'],expected_outputs={'odb':'TEST_ONLY_NEW_B.odb'},owner=dict(state='CONNECTED',owner_id='TEST_ONLY_OWNER',start_id='TEST_ONLY_START'),
            plan=plan,scope_digest='TEST_ONLY_SCOPE',installation=native.installation())
        decisions=[];errors=[]
        def approve_wait():
            try:decisions.append(dialog.authorize(value,monotonic_deadline=deadline))
            except BaseException as exc:errors.append(str(exc))
        waiter=threading.Thread(target=approve_wait);waiter.start();time.sleep(.3)
        evidence=ROOT/'evidence'/('ui-machine-'+uuid.uuid4().hex[:10]);evidence.mkdir(parents=True)
        rect=capture_test_client(window.hwnd,evidence/'summary-client.png')
        u.SendMessageW(window.hwnd,0x111,204,window.controls['details_toggle']);time.sleep(.15)
        capture_test_client(window.hwnd,evidence/'details-client.png')
        u.SendMessageW(window.hwnd,0x111,204,window.controls['details_toggle']);time.sleep(.15)
        u.ShowWindow(window.hwnd,6);time.sleep(.1);u.ShowWindow(window.hwnd,9)
        assert state.choice is None and state.deadline==deadline
        for msg,wp in ((0x100,13),(0x101,13),(0xF5,0)):u.SendMessageW(button,msg,wp,0)
        assert state.choice is None
        u.SendMessageW(button,0x201,1,10|(10<<16));u.SendMessageW(button,0x202,0,10|(10<<16))
        waiter.join(2);assert not errors and len(decisions)==1 and decisions[0]['status']=='USER_DECISION_CAPTURED',errors
        assert state.choice=='approve' and state.used=={'START','APPROVE'}
        u.SendMessageW(button,0x201,1,10|(10<<16));u.SendMessageW(button,0x202,0,10|(10<<16))
        assert state.used=={'START','APPROVE'}
        u.SendMessageW(window.hwnd,0x10,0,0);time.sleep(.1);assert state.cancelled
        result=dict(status='PASS_TEST_ONLY_NATIVE_WINDOW',enter_did_not_approve=True,bm_click_rejected=True,
            minimize_did_not_approve_or_extend=True,mouse_stages=2,close_cancels=True,real_human_acceptance='NOT_TESTED',
            native_owner_grant_solver_called=False,evidence=str(evidence),screenshot_rect=rect)
        (evidence/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8')
        print(json.dumps(result,indent=2))
    finally:window.close()


if __name__=='__main__':
    if '--window-smoke' in sys.argv:window_smoke()
    else:unittest.main(verbosity=2)
