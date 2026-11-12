"""Sparse original timer, queue gate, manager callback and paint receipts."""
import collections
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from wait_correlation import WaitCorrelation
POINTS={0x69f9bc:'worker_entry',0x69fa20:'worker_clock_return',0x69fa58:'countdown_store',0x69fa84:'countdown_gate',0x69fa9c:'worker_wait_call',0x69faa0:'worker_wait_return',0x69faf8:'one_ms_wait_return',0x69fb34:'message_queue_gate',0x69fc74:'message_post_call',0x69fc7c:'message_post_return',0x69fc88:'retry_post_call',0x69fc90:'retry_post_return',0x644e1c:'timedwait_call',0x644e20:'timedwait_caller_return',0x806840:'manager_callback',0x806890:'manager_drain_tail',0x805e38:'dirty_collection_drain',0x805e60:'drain_collection_copy_return',0x806640:'manager_transfer',0x783bb8:'alternate_transfer'}
class TimerObserver:
    def __init__(self,emit,names,discovery,base):
        self.emit,self.names,self.discovery,self.base=emit,names,discovery,Path(base)
        self.correlation=WaitCorrelation();self.handles={};self.parent_frames={};self.dynamic_points={};self.timer_retired=False
        self.counts=collections.Counter();self.latest={};self.frames={};self.completed={};self.waits={};self.worker={};self.callback=None;self.dynamic={}
    def install(self,q):
        rows=[]
        for a,label in POINTS.items():
            expected=self.discovery.expected(a);actual=bytes(q.mem.read(a,4))
            if expected!=actual:raise RuntimeError('Timer boundary bytes differ '+hex(a))
            self.handles[a]=q.hook_address(lambda guest,a=a:self.visit(guest,a),a)
            rows.append(dict(address=hex(a),boundary=label,expected=expected.hex(),actual=actual.hex(),matches=True))
        self.add_point(q,0x644d8c,'waitable_entry')
        self.emit('timer_boundaries_installed',points=rows,read_only=True)
    def install_library(self,q,base,source):
        with Path(source).open('rb') as f:
            elf=ELFFile(f);segments=[(s['p_vaddr'],s.data()) for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
        def expected(a):return next(d[a-base-s:a-base-s+4] for s,d in segments if s<=a-base<a-base+len(d))
        self.library_expected=expected
        for offset in (0xb4f8,0xb654):
            a=base+offset;raw=expected(a)
            if bytes(q.mem.read(a,4))!=raw:raise RuntimeError('Timedwait observation bytes differ')
            q.hook_address(lambda guest,a=a,offset=offset:self.library_visit(guest,a,offset),a)
    def library_visit(self,q,a,offset):
        tid=q.os.thread_management.cur_thread.id;name=self.names.get(tid)
        if name not in ('Juce Timer','ProjectManager'):return
        if offset==0xb4f8:
            sp=q.arch.regs.sp;caller=q.arch.regs.lr
            from resource_application_observer import caller_transfer
            instruction=self.discovery.expected(caller-4);kind,target=caller_transfer(caller-4,instruction)
            if kind!='arm_bl' or target!=0x1138c or bytes(q.mem.read(caller-4,4))!=instruction:raise RuntimeError('Selected original timedwait caller bytes differ')
            frame=self.correlation.enter(tid,sp,caller)
            self.frames[tid]=dict(thread=tid,thread_name=name,**frame,condition=hex(q.arch.regs.r0),mutex=hex(q.arch.regs.r1),absolute_timeout=bytes(q.mem.read(q.arch.regs.r2,8)).hex())
            self.add_point(q,caller,'timedwait_caller_return')
            self.receipt('selected_original_timedwait_entry',**self.frames[tid])
        else:
            consumed=self.correlation.resume(tid,q.arch.regs.sp,q.arch.regs.r0)
            if consumed:
                consumed['syscall_sp']=consumed.pop('sp')
                self.receipt('selected_original_syscall_resumed',thread=tid,thread_name=name,pc=hex(a),sp=hex(q.arch.regs.sp),r0=hex(q.arch.regs.r0),matched_frame=True,**consumed)
    def call_begin(self,q,sequence):
        tid=q.os.thread_management.cur_thread.id
        row=self.correlation.begin(tid,q.arch.regs.sp,sequence)
        return {k:row[k] for k in ('frame_generation','syscall_generation')}
    def call_immediate(self,q,identity,result):
        tid=q.os.thread_management.cur_thread.id
        self.correlation.immediate(tid,identity['syscall_generation'],result)
        self.receipt('selected_futex_immediate',thread=tid,thread_name=self.names.get(tid),result=result,**identity)
    def wait_entry(self,q,row):self.waits[row['tid']]={k:v for k,v in row.items() if k not in ('thread','event')}
    def wait_completed(self,row,completed):
        self.correlation.complete(row['tid'],row['syscall_generation'],completed)
        self.completed[row['tid']]=completed
    def add_point(self,q,a,label):
        if a in self.dynamic_points:return
        expected=self.discovery.expected(a);actual=bytes(q.mem.read(a,4))
        if expected!=actual:raise RuntimeError('Selected dynamic boundary bytes differ '+hex(a))
        self.dynamic_points[a]=label
        if a not in self.handles:self.handles[a]=q.hook_address(lambda guest,a=a:self.dynamic_visit(guest,a),a)
        self.emit('project_boundary_validated',address=hex(a),boundary=label,expected=expected.hex(),actual=actual.hex(),matches=True)
    def dynamic_visit(self,q,a):
        tid=q.os.thread_management.cur_thread.id;name=self.names.get(tid)
        if name!='ProjectManager':return
        label=self.dynamic_points[a]
        row=dict(thread=tid,thread_name=name,pc=hex(a),sp=hex(q.arch.regs.sp),registers={n:hex(q.arch.regs.read(n)) for n in ('r0','r1','r2','r3','r4','r5','r6','r7','lr')})
        if label=='waitable_entry':
            caller=q.arch.regs.lr
            from resource_application_observer import caller_transfer
            raw=self.discovery.expected(caller-4);kind,target=caller_transfer(caller-4,raw)
            if kind!='arm_bl' or target not in (0x644d8c,0x644ec0) or bytes(q.mem.read(caller-4,4))!=raw:raise RuntimeError('ProjectManager live waitable caller differs')
            self.parent_frames[tid]=dict(sp=q.arch.regs.sp,caller=caller,object=q.arch.regs.r0,timeout_ms=q.arch.regs.r1)
            row.update(parent=self.parent_frames[tid],stack64=bytes(q.mem.read(q.arch.regs.sp,64)).hex(),object80=bytes(q.mem.read(q.arch.regs.r0,80)).hex())
            self.add_point(q,caller,'worker_wait_return')
            # Capture adjacent original calls/branches, without changing their execution.
            if caller not in getattr(self,'discovered_callers',set()):
                if not hasattr(self,'discovered_callers'):self.discovered_callers=set()
                self.discovered_callers.add(caller)
                raw=b''.join(self.discovery.expected(caller+i) for i in range(-128,384,4))
                dis=list(q.arch.disassembler.disasm(raw,caller-128))
                self.emit('project_original_caller_disassembly',caller=hex(caller),instructions=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str,bytes=i.bytes.hex()) for i in dis])
                points=[i for i in dis if i.address>caller and (i.mnemonic in ('bl','blx') or i.mnemonic.startswith('b'))][:10]
                for i in points:
                    self.add_point(q,i.address,'downstream_'+i.mnemonic)
                    if i.mnemonic in ('bl','blx'):self.add_point(q,i.address+4,'downstream_call_return')
        elif label=='worker_wait_return':
            parent=self.parent_frames.pop(tid,None)
            if parent is None:return
            if parent['sp']!=q.arch.regs.sp or parent['caller']!=a:raise RuntimeError('ProjectManager outer wait frame differs')
            row.update(parent=parent,matched_thread_sp=True,result=q.arch.regs.r0,object80=bytes(q.mem.read(parent['object'],80)).hex())
        elif label=='timedwait_caller_return':
            self.timedwait_return(q,a,tid,name);return
        elif label=='downstream_blx':
            instruction=next(q.arch.disassembler.disasm(bytes(q.mem.read(a,4)),a))
            if instruction.op_str.startswith('r'):
                target=q.arch.regs.read(instruction.op_str);row['target']=hex(target)
                if 0x10000<=target<0x870000:self.add_point(q,target,'downstream_virtual_target')
        self.counts['project:'+label]+=1;self.latest['project:'+label]=row
        if self.counts['project:'+label]<=6:self.emit('project_original_boundary',boundary=label,**row)
    def timedwait_return(self,q,a,tid,name):
        frame=self.frames.pop(tid,None)
        if frame is None:return
        if frame['sp']!=q.arch.regs.sp or frame['caller']!=a:raise RuntimeError('Original timedwait caller frame differs')
        call=self.correlation.calls.get(tid)
        if call and call['frame_generation']==frame['frame_generation'] and not call['consumed']:raise RuntimeError('Caller returned without consuming selected completion')
        self.receipt('selected_original_timedwait_return',thread=tid,thread_name=name,pc=hex(a),sp=hex(q.arch.regs.sp),result=q.arch.regs.r0,frame=frame,matched_thread_sp=True,syscall=call)
    def retire_timer(self,q):
        if self.timer_retired or not self.counts.get('dirty_collection_drain'):return
        for a in list(self.handles):
            if a in POINTS and a not in (0x644e20,0x806640,0x783bb8):q.hook_del(self.handles.pop(a))
        self.timer_retired=True
        self.emit('detailed_timer_chain_retired',reason='retained timer/callback/drain and original paint confirmed',paint_sites_retained=True)
    def receipt(self,kind,**values):
        key=kind+':'+str(values.get('thread_name',''))
        self.counts[key]+=1;self.latest[key]=values
        if self.counts[key]<=4:self.emit(kind,**values)
    def u32(self,q,p):return struct.unpack('<I',bytes(q.mem.read(p,4)))[0]
    def visit(self,q,a):
        tid=q.os.thread_management.cur_thread.id;name=self.names.get(tid);label=POINTS[a]
        if a==0x644e20:
            if name in ('Juce Timer','ProjectManager'):self.timedwait_return(q,a,tid,name)
            return
        if a<0x780000 and name!='Juce Timer':return
        self.counts[label]+=1
        row=dict(thread=tid,thread_name=name,pc=hex(a),sp=hex(q.arch.regs.sp),r0=hex(q.arch.regs.r0),r1=hex(q.arch.regs.r1),r2=hex(q.arch.regs.r2),r3=hex(q.arch.regs.r3),r4=hex(q.arch.regs.r4),r5=hex(q.arch.regs.r5),r6=hex(q.arch.regs.r6),lr=hex(q.arch.regs.lr))
        if label=='worker_entry':self.worker[tid]=q.arch.regs.r0
        if label=='timedwait_caller_return':
            frame=self.frames.pop(tid,None)
            row.update(frame=frame,matched_thread_sp=bool(frame and frame['sp']==q.arch.regs.sp and frame['caller']==a),completion=self.completed.get(tid))
            if not row['matched_thread_sp']:raise RuntimeError('Original timedwait caller frame differs')
        worker=self.worker.get(tid)
        if worker and a in range(0x69f9bc,0x69fce8):
            head=self.u32(q,worker+0xe0);items=[];p=head
            for _ in range(4):
                if not p:break
                items.append(dict(pointer=hex(p),raw20=bytes(q.mem.read(p,20)).hex(),countdown=struct.unpack('<i',bytes(q.mem.read(p+4,4)))[0]));p=self.u32(q,p+16)
            row.update(worker=hex(worker),list_head=hex(head),timer_items=items,queue_e4=self.u32(q,worker+0xe4),stop_d0=bytes(q.mem.read(worker+0xd0,1)).hex())
        if label=='manager_callback':
            manager=q.arch.regs.r0;vtable=self.u32(q,manager)
            target=self.u32(q,vtable+8)
            if target!=a:raise RuntimeError('Live manager vtable target differs')
            row.update(manager=hex(manager),vtable=hex(vtable),callback_target=hex(target),dirty_count=self.u32(q,manager+0x28),raw44=bytes(q.mem.read(manager,44)).hex())
            self.callback=dict(thread=tid,sp=q.arch.regs.sp,manager=manager,caller=q.arch.regs.lr)
        if label in ('manager_drain_tail','dirty_collection_drain'):
            manager=q.arch.regs.r0;c=self.callback
            row.update(manager=hex(manager),callback=c,matched_callback_frame=bool(c and c['thread']==tid and c['sp']==q.arch.regs.sp and c['manager']==manager))
            if label=='dirty_collection_drain' and c and not row['matched_callback_frame']:raise RuntimeError('Manager callback/drain frame differs')
        self.latest[label]=row
        if self.counts[label]<=4:self.emit('timer_original_boundary',boundary=label,**row)
    def summary(self):return dict(counts=dict(self.counts),latest=self.latest,pending_timedwait_frames=self.frames,correlation_consumed=self.correlation.consumed,parent_frames=self.parent_frames,timer_details_retired=self.timer_retired,worker_objects={str(k):hex(v) for k,v in self.worker.items()})
