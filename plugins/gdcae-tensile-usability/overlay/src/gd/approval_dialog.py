"""Local Win32 review surface. A mouse decision is not a native AF Grant.

No Solver, Owner or authorization API is imported here. The orchestration caller
revalidates the exact packet and calls the existing native issuer once.
"""
import ctypes
from ctypes import wintypes as w
from datetime import datetime, timedelta, timezone
import hashlib
import json
import queue
import threading
import time


def require(ok, reason):
    if not ok: raise ValueError(reason)


def packet_bytes(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')


def packet_digest(value): return hashlib.sha256(packet_bytes(value)).hexdigest()


class DecisionState:
    """One start and one approve; focus and keyboard events cannot grant either."""
    def __init__(self,wall=time.time,clock=time.monotonic):
        self.wall,self.clock=wall,clock
        self.lock=threading.Lock();self.event=threading.Event()
        self.mode='INITIAL';self.cancelled=False;self.choice=None
        self.expires=None;self.deadline=None;self.used=set()
    def arm(self,mode,*,expires=None,deadline=None):
        with self.lock:
            require(not self.cancelled and mode not in self.used,'DIALOG_STAGE_UNAVAILABLE')
            self.mode=mode;self.choice=None;self.expires=expires;self.deadline=deadline;self.event.clear()
    def expired(self):
        return ((self.expires is not None and self.wall()>=self.expires)
                or (self.deadline is not None and self.clock()>=self.deadline))
    def click(self,action,*,mouse):
        with self.lock:
            if action=='cancel':
                self.cancelled=True;self.choice='cancel';self.mode='CANCELLED';self.event.set();return True
            if not mouse or self.cancelled or self.choice is not None or self.mode not in ('START','APPROVE') or self.mode in self.used:return False
            if self.expired():
                self.mode='EXPIRED';self.choice='expired';self.event.set();return False
            if action!=self.mode.lower():return False
            self.used.add(self.mode);self.choice=action;self.mode='BUSY';self.event.set();return True
    def tick(self):
        with self.lock:
            if self.mode=='APPROVE' and self.expired():
                self.mode='EXPIRED';self.choice='expired';self.event.set()
            return self.mode
    def wait(self):
        while not self.event.wait(.05): self.tick()
        require(not self.cancelled,'HUMAN_CANCELLED_NO_RETRY')
        require(self.choice not in (None,'expired'),'APPROVAL_EXPIRED_NO_GRANT')
        return self.choice
    def check(self):
        require(not self.cancelled,'HUMAN_CANCELLED_NO_RETRY')
        require(not self.expired(),'APPROVAL_EXPIRED_NO_GRANT')


class Win32Window:
    """One modeless window, two buttons, read-only full details; no focus policy."""
    def __init__(self,state,*,test_only=False):
        self.state=state;self.test_only=test_only;self.commands=queue.Queue()
        self.created=threading.Event();self.failure=None;self.hwnd=None
        self.thread=threading.Thread(target=self._run,name='gdcae-native-review',daemon=True)
        self.thread.start()
        require(self.created.wait(10),'APPROVAL_WINDOW_CREATION_TIMEOUT')
        if self.failure:raise RuntimeError('APPROVAL_WINDOW_UNAVAILABLE') from self.failure
    def update(self,status,details='',button=None,enabled=False,summary=''):
        require(self.thread.is_alive(),'APPROVAL_WINDOW_CLOSED')
        self.commands.put(('update',status,details,button,enabled,summary))
    def close(self):
        if self.thread.is_alive():self.commands.put(('close',))
        self.thread.join(2)
    def _run(self):
        try:self._windows()
        except BaseException as exc:
            self.failure=exc;self.state.click('cancel',mouse=False);self.created.set()
    def _windows(self):
        u=ctypes.WinDLL('user32',use_last_error=True);k=ctypes.WinDLL('kernel32',use_last_error=True)
        LRESULT=ctypes.c_ssize_t;WNDPROC=ctypes.WINFUNCTYPE(LRESULT,w.HWND,w.UINT,w.WPARAM,w.LPARAM)
        class WNDCLASS(ctypes.Structure):
            _fields_=[('style',w.UINT),('lpfnWndProc',WNDPROC),('cbClsExtra',ctypes.c_int),('cbWndExtra',ctypes.c_int),
                      ('hInstance',w.HINSTANCE),('hIcon',w.HICON),('hCursor',w.HANDLE),('hbrBackground',w.HBRUSH),
                      ('lpszMenuName',w.LPCWSTR),('lpszClassName',w.LPCWSTR)]
        k.GetModuleHandleW.argtypes=[w.LPCWSTR];k.GetModuleHandleW.restype=w.HMODULE
        u.RegisterClassW.argtypes=[ctypes.POINTER(WNDCLASS)];u.RegisterClassW.restype=w.ATOM
        u.CreateWindowExW.argtypes=[w.DWORD,w.LPCWSTR,w.LPCWSTR,w.DWORD,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,w.HWND,w.HMENU,w.HINSTANCE,ctypes.c_void_p];u.CreateWindowExW.restype=w.HWND
        u.DefWindowProcW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.DefWindowProcW.restype=LRESULT
        u.CallWindowProcW.argtypes=[ctypes.c_void_p,w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.CallWindowProcW.restype=LRESULT
        u.SetWindowLongPtrW.argtypes=[w.HWND,ctypes.c_int,ctypes.c_void_p];u.SetWindowLongPtrW.restype=ctypes.c_void_p
        u.SetWindowTextW.argtypes=[w.HWND,w.LPCWSTR];u.EnableWindow.argtypes=[w.HWND,w.BOOL]
        u.ShowWindow.argtypes=[w.HWND,ctypes.c_int];u.DestroyWindow.argtypes=[w.HWND]
        u.SetFocus.argtypes=[w.HWND];u.SetFocus.restype=w.HWND
        u.GetMessageW.argtypes=[ctypes.POINTER(w.MSG),w.HWND,w.UINT,w.UINT];u.GetMessageW.restype=w.BOOL
        u.TranslateMessage.argtypes=[ctypes.POINTER(w.MSG)];u.DispatchMessageW.argtypes=[ctypes.POINTER(w.MSG)];u.DispatchMessageW.restype=LRESULT
        u.SetTimer.argtypes=[w.HWND,ctypes.c_size_t,w.UINT,ctypes.c_void_p];u.SetTimer.restype=ctypes.c_size_t
        u.KillTimer.argtypes=[w.HWND,ctypes.c_size_t]
        controls={};mouse_release=[False];held=[False];original_proc=[None];expanded=[False]
        @WNDPROC
        def button_proc(hwnd,msg,wp,lp):
            # No Enter/Space/default-button or BM_CLICK approval. A real button
            # mouse up must follow its mouse down. TEST_ONLY automation is not
            # represented as human approval evidence.
            if msg in (0x100,0x101,0x104,0x105,0x102,0xF5):return 0
            if msg==0x201:held[0]=True
            if msg==0x202:
                mouse_release[0]=held[0];held[0]=False
                try:return u.CallWindowProcW(original_proc[0],hwnd,msg,wp,lp)
                finally:mouse_release[0]=False
            return u.CallWindowProcW(original_proc[0],hwnd,msg,wp,lp)
        def refresh():
            self.state.tick()
            while True:
                try:item=self.commands.get_nowait()
                except queue.Empty:break
                if item[0]=='close':u.DestroyWindow(self.hwnd);return
                _,status,details,button,enabled,summary=item
                u.SetWindowTextW(controls['status'],status)
                if details:u.SetWindowTextW(controls['details'],details)
                if summary:u.SetWindowTextW(controls['summary'],summary)
                if button:u.SetWindowTextW(controls['approve'],button)
                u.EnableWindow(controls['approve'],enabled)
            if self.state.mode=='APPROVE':
                seconds=max(0,int(min(self.state.expires-self.state.wall(),self.state.deadline-self.state.clock())))
                u.SetWindowTextW(controls['countdown'],'剩余 %d 秒；Enter 不批准。失焦或最小化不延长有效期。'%seconds)
            elif self.state.mode=='EXPIRED':
                u.EnableWindow(controls['approve'],False)
                u.SetWindowTextW(controls['countdown'],'已过期：未批准，不会创建 Grant 或启动求解。保留证据，停止。')
            if self.state.mode in ('BUSY','CANCELLED'):u.EnableWindow(controls['approve'],False)
        @WNDPROC
        def wndproc(hwnd,msg,wp,lp):
            try:
                if msg==0x111:
                    ident=wp&0xffff
                    if ident==102:
                        self.state.click('cancel',mouse=False);u.DestroyWindow(hwnd)
                    elif ident==101 and mouse_release[0]:
                        mode=self.state.mode
                        if self.state.click(mode.lower(),mouse=True):
                            u.EnableWindow(controls['approve'],False)
                            u.SetWindowTextW(controls['status'],'已收到点击，正在核验。尚未获得原生 Grant。')
                    elif ident==204:
                        expanded[0]=not expanded[0]
                        u.ShowWindow(controls['details'],5 if expanded[0] else 0)
                        u.ShowWindow(controls['summary'],0 if expanded[0] else 5)
                        u.SetWindowTextW(controls['details_toggle'],'返回科研摘要 ▲' if expanded[0] else '查看完整身份与证据详情 ▼')
                    return 0
                if msg==0x10:
                    self.state.click('cancel',mouse=False);u.DestroyWindow(hwnd);return 0
                if msg==2:u.PostQuitMessage(0);return 0
                if msg==0x113:refresh();return 0
                # No dialog manager/IsDialogMessage, no default Enter action.
                if msg==0x100 and wp==27:self.state.click('cancel',mouse=False);return 0
                return u.DefWindowProcW(hwnd,msg,wp,lp)
            except BaseException as exc:
                self.failure=exc;self.state.click('cancel',mouse=False);return 0
        instance=k.GetModuleHandleW(None);name='GDCAEReview_'+str(id(self))
        cls=WNDCLASS();cls.lpfnWndProc=wndproc;cls.hInstance=instance;cls.hbrBackground=6;cls.lpszClassName=name
        require(u.RegisterClassW(ctypes.byref(cls)),'REGISTER_WINDOW_FAILED')
        title=('TEST_ONLY — ' if self.test_only else '')+'GD-CAE 本机执行审查'
        self.hwnd=u.CreateWindowExW(0,name,title,0x00CF0000,100,80,980,780,None,None,instance,None)
        require(self.hwnd,'CREATE_WINDOW_FAILED')
        def child(kind,text,style,x,y,width,height,ident):
            h=u.CreateWindowExW(0,kind,text,0x50000000|style,x,y,width,height,self.hwnd,w.HMENU(ident),instance,None)
            require(h,'CREATE_CONTROL_FAILED');return h
        controls['status']=child('STATIC','正在静态检查。尚未创建新 Plan，尚未批准执行。',0,20,15,925,65,201)
        controls['countdown']=child('STATIC','默认取消。点击“发起审查”才创建 JIT Plan；不会自动批准。',0,20,82,925,38,202)
        controls['summary']=child('STATIC','请等待静态检查；检查通过后可点击“发起审查”。',0,20,140,925,460,205)
        controls['details']=child('EDIT','',0x00200000|0x0040|0x0004|0x0800,20,140,925,460,203)
        controls['details_toggle']=child('STATIC','查看完整身份与证据详情 ▼',0x100,20,620,925,30,204)
        controls['approve']=child('BUTTON','发起审查',0,520,683,200,40,101)
        controls['cancel']=child('BUTTON','取消',0,745,683,200,40,102)
        original_proc[0]=u.SetWindowLongPtrW(controls['approve'],-4,ctypes.cast(button_proc,ctypes.c_void_p))
        require(original_proc[0],'BUTTON_SUBCLASS_FAILED')
        u.EnableWindow(controls['approve'],False)
        u.ShowWindow(controls['details'],0)
        u.SetTimer(self.hwnd,1,100,None);u.ShowWindow(self.hwnd,5);u.SetFocus(controls['cancel'])
        self.controls=controls;self.created.set()
        msg=w.MSG()
        while True:
            result=u.GetMessageW(ctypes.byref(msg),None,0,0)
            if result<=0:break
            u.TranslateMessage(ctypes.byref(msg));u.DispatchMessageW(ctypes.byref(msg))
        u.KillTimer(self.hwnd,1)
        require(result!=-1,'WINDOW_MESSAGE_LOOP_FAILED')


class ApprovalDialog:
    def __init__(self,*,wall=time.time,clock=time.monotonic,window_factory=Win32Window):
        self.state=DecisionState(wall,clock);self.wall,self.clock=wall,clock
        self.window=window_factory(self.state)
        self.packet_pin=None;self.operation=None;self.grant_received=False
    def ready(self,static,operation):
        self.operation=operation;self.state.arm('START')
        details=json.dumps(dict(operation_id=operation,static=static,execution_authorized=False),indent=2,ensure_ascii=False)
        self.window.update('静态准备完成。点击“发起审查”才创建 JIT Plan；这不是计算批准。',details,'发起审查',True,
            '下一步：发起 Candidate B 的本机执行审查。\r\n\r\n'
            '研究目的：用真实 B 力–位移响应检验基于 A 反馈提出的两参数调整。\r\n\r\n'
            '本阶段尚无新 Plan，也没有新 Solver Grant。\r\n'
            'B 的实际参数、资源、已预留次数和到期时间将在 Plan 核验后显示。\r\n\r\n'
            '不重算 A，不自动重试，不执行 C。\r\n'
            '取消将停止后续流程；窗口不会自行终止任何进程。')
        require(self.state.wait()=='start','REVIEW_START_REQUIRED')
        return dict(status='READY_RECEIVED_NO_EXECUTION_AUTHORITY',operation_id=operation,proposal_digest=static['proposal_digest'],received_at=self.wall(),input_method='local_win32_mouse')
    def authorize(self,packet,*,monotonic_deadline):
        require(self.operation==packet['operation_id'] and 'START' in self.state.used,'REVIEW_NOT_STARTED')
        require(self.packet_pin is None,'APPROVAL_ALREADY_ATTEMPTED')
        raw=packet_bytes(packet);value=json.loads(raw);self.packet_pin=hashlib.sha256(raw).hexdigest()
        plan=value['plan'];expires=plan['expires_at']
        require(value['owner']['state']=='CONNECTED','OWNER_NOT_CONNECTED')
        require(min(expires-self.wall(),monotonic_deadline-self.clock())>=15,'INSUFFICIENT_REVIEW_WINDOW')
        summary={k:value[k] for k in ('project','candidate','parameters','budget','job_id','job_revision','input_manifest','engineering','scratch','expected_outputs','resources','owner')}
        summary.update(plan_id=plan['plan_id'],plan_digest=plan['plan_digest'],scope_digest=value['scope_digest'],
                       expires_beijing=datetime.fromtimestamp(expires,timezone(timedelta(hours=8))).isoformat(),expires_epoch=expires,
                       immutable_packet_sha256=self.packet_pin,installation=value['installation'])
        self.state.arm('APPROVE',expires=expires,deadline=monotonic_deadline)
        parameters=value['parameters'];resources=value['resources'];budget=value['budget']
        readable=('项目：'+str(value['project'])+'\r\n候选：'+str(value['candidate'])+'（Candidate B）\r\n\r\n'
            '研究目的：验证 A 反馈产生的两参数调整对真实力–位移曲线的影响。\r\n'
            'sigma_y = '+str(parameters['sigma_y_MPa'])+' MPa；H = '+str(parameters['H_MPa'])+' MPa\r\n\r\n'
            '资源：'+str(resources['cpus'])+' CPU / '+str(resources['gpus'])+' GPU / '+str(resources['memory_mb'])+' MB\r\n'
            '次数：使用原 B 已预留的 1 次；本次最多启动 1 次。\r\n'
            '科研预算：总量 '+str(budget['limit'])+' / 已用 '+str(budget['charged'])+' / 已预留 '+str(budget['held'])+' / 可用 '+str(budget['available'])+'\r\n\r\n'
            'Plan 到期（北京时间）：'+summary['expires_beijing']+'\r\n\r\n'
            '不重算 A；零自动重试；不执行 C。\r\n'
            '点击批准后会重新核验，只有原生 Grant 返回成功才算批准成功。')
        self.window.update('Owner 已连接。仅审查下方精确 B Plan。尚未获得 Solver Grant。',
                           json.dumps(dict(summary=summary,complete_packet=value),indent=2,ensure_ascii=False),'批准本次计算',True,readable)
        require(self.state.wait()=='approve','APPROVAL_REQUIRED')
        require(packet_bytes(packet)==raw,'CONFIRMATION_PACKET_CHANGED')
        return dict(status='USER_DECISION_CAPTURED',packet_sha256=self.packet_pin,operation_id=self.operation,
                    received_at=self.wall(),input_method='local_win32_mouse')
    def before_native_authorize(self,*,expires,monotonic_deadline):
        require(self.packet_pin and 'APPROVE' in self.state.used,'HUMAN_APPROVAL_REQUIRED')
        self.state.check()
        require(self.wall()<expires and self.clock()<monotonic_deadline,'APPROVAL_EXPIRED_NO_GRANT')
    def status(self,text):
        if self.window.thread.is_alive():self.window.update(text)
    def check_cancelled(self):require(not self.state.cancelled,'HUMAN_CANCELLED_NO_RETRY')
    def native_granted(self,grant):
        require(grant['receipt']['grant_id'] and grant['replayed'] is False,'NATIVE_GRANT_REQUIRED')
        self.grant_received=True
        self.status('原生批准成功：'+grant['receipt']['grant_id']+'。正在按已批准范围单次提交。取消不会撤销已有 Grant 或终止 Solver。')
    def close(self):self.window.close()
    def finish(self):
        # Keep the final outcome visible. Closing only closes this review UI.
        while self.window.thread.is_alive():time.sleep(.1)
