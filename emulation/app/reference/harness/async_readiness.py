"""Minimal fresh async correlation; completed producer/consumer detail retired.

This retains listener target/entry/return, exact result+completion fields and the
main zero-countdown path/selected progress-call return. No file tracing, store
hooks, request detail, downstream popup callees, packet or input hooks. A passed
correlation is neither a popup-removal nor full-startup assertion.
"""
import struct

PRODUCER_POINTS=(0x33c280,0x25dfc4,0x25dfd8,0x33c284)
CONSUMER_POINTS=(0x25f000,0x25f04c,0x25f05c,0x25f108,
                 0x25f13c,0x25ec44,0x25eca8,0x25f140,0x25f040)

def word(q,a):return struct.unpack('<I',bytes(q.mem.read(a,4)))[0]
def state(q,owner):
    raw=bytes(q.mem.read(owner+0x12c,8))
    return dict(owner=owner,submitted=raw[0],completed=raw[1],result=struct.unpack_from('<I',raw,4)[0],raw=raw.hex())

class SparseProducer:
    def __init__(self,emit,discovery,run=None):
        self.emit,self.discovery=emit,discovery
        self.hooks,self.frames={},{}
        self.records=[];self.receipt=None;self.retired=False
    def validate(self,q,a,n=4):
        raw=b''.join(self.discovery.expected(a+i) for i in range(0,n,4))
        self.require(bytes(q.mem.read(a,n))==raw,'original producer bytes '+hex(a))
        return raw
    def require(self,ok,why):
        if not ok:self.emit('lifecycle_mismatch',reason='async '+why);raise RuntimeError('Async '+why)
    def record(self,kind,**row):
        value=dict(kind=kind,**row);self.records.append(value);self.emit('async_'+kind,**row)
    def install(self,q):
        self.validate(q,0x25dfc4,24)
        for a in PRODUCER_POINTS:
            self.validate(q,a);self.hooks[a]=q.hook_address(lambda g,a=a:self.visit(g,a),a)
        self.record('producer_hooks_validated',points=[hex(a) for a in PRODUCER_POINTS],read_only=True)
    def visit(self,q,a):
        if self.retired:return
        tid=q.os.thread_management.cur_thread.id;r=q.arch.regs
        self.validate(q,a)
        if a==0x33c280:
            self.require(tid not in self.frames,'overlapping listener call')
            target=r.r3
            self.require(target==0x25dfc4 and word(q,word(q,r.r0)+12)==target,'listener vtable target')
            self.frames[tid]=dict(thread=tid,sp=r.sp,listener=r.r0,owner=r.r0-0x124,manager=r.r1,result=r.r2,entry=False,bx=False)
        f=self.frames.get(tid)
        if f is None:return
        if a==0x25dfc4:
            self.require((r.sp,r.lr,r.r0,r.r1,r.r2)==(f['sp'],0x33c284,f['listener'],f['manager'],f['result']),'listener actual entry thread/SP/LR/arguments')
            f['entry']=True
        elif a==0x25dfd8:
            self.require(f['entry'] and (r.sp,r.lr,r.r0)==(f['sp'],0x33c284,f['owner']),'listener terminal BX thread/SP/LR/owner')
            f['after']=state(q,f['owner'])
            self.require(f['after']['completed']==1 and f['after']['result']==f['result'],'listener result/completion fields')
            f['bx']=True
        elif a==0x33c284:
            self.require(f['entry'] and f['bx'] and r.sp==f['sp'],'listener matched return')
            self.require(state(q,f['owner'])==f['after'],'listener post-return fields')
            self.receipt=dict(frame=f,matched_thread_sp_arguments_lr=True,original_result_and_completion_fields=True,result_is_not_success_predicate=True)
            self.record('producer_completion',evidence=self.receipt)
            self.frames.pop(tid)
            for h in self.hooks.values():q.hook_del(h)
            self.hooks.clear();self.retired=True
    # Preserve compose() call sites without retaining completed resume-file hooks.
    def path_enter(self,name):return lambda *args:None
    def path_exit(self,name):return lambda *args:None
    def summary(self):return dict(receipt=self.receipt,pending=self.frames,retired=self.retired,read_only=True,detail_hooks_enabled=False)

class SparseConsumer:
    def __init__(self,emit,discovery,producer):
        self.emit,self.discovery,self.producer=emit,discovery,producer
        self.hooks,self.frames={},{}
        self.records=[];self.acceptance=None;self.retired=False;self.skipped=0
    def require(self,ok,why):
        if not ok:self.emit('lifecycle_mismatch',reason='async '+why);raise RuntimeError('Async '+why)
    def validate(self,q,a,n=4):
        raw=b''.join(self.discovery.expected(a+i) for i in range(0,n,4))
        self.require(bytes(q.mem.read(a,n))==raw,'original consumer bytes '+hex(a))
    def hook(self,q,a):
        if a not in self.hooks:
            self.validate(q,a);self.hooks[a]=q.hook_address(lambda g,a=a:self.visit(g,a),a)
    def record(self,kind,**row):
        self.records.append(dict(kind=kind,**row));self.emit('async_'+kind,**row)
    def install(self,q):
        # Retain original-byte verification of both bodies, omit detailed hooks.
        self.validate(q,0x25eff8,428);self.validate(q,0x25ec44,408)
        for a in CONSUMER_POINTS:self.hook(q,a)
        self.record('consumer_hooks_validated',points=[hex(a) for a in CONSUMER_POINTS],read_only=True)
    def visit(self,q,a):
        if self.retired:return
        tid=q.os.thread_management.cur_thread.id;r=q.arch.regs
        if tid!=self.discovery.main_tid:return
        self.validate(q,a)
        if a==0x25f000:
            if r.r1!=2:return
            receipt=self.producer.receipt
            if receipt is None or r.r0!=receipt['frame']['owner']:
                self.skipped+=1;return
            self.require(tid not in self.frames,'overlapping main consumer frame')
            before=state(q,r.r0)
            self.require(before['completed']==1 and before['result']==receipt['frame']['result'],'main state differs from fresh listener fields')
            f=dict(thread=tid,sp=r.sp,caller=r.lr,owner=r.r0,before=before,selected=False,pop=False,popup_entry=False,popup_pop=False,popup_return=False)
            self.frames[tid]=f;self.hook(q,r.lr)
            return
        f=self.frames.get(tid)
        if f is None:return
        if a==f['caller']:
            self.require(f['pop'] and r.sp==f['sp'],'main consumer saved LR/restored SP')
            self.frames.pop(tid)
            if f['selected']:
                self.require(f['popup_entry'] and f['popup_pop'] and f['popup_return'],'selected call lacked matched target/return')
                self.acceptance=dict(passed=True,frame=f,producer=self.producer.receipt,
                    matched_main_thread_saved_lr_restored_sp=True,original_completion_state_evidence=True,
                    interpretation='Fresh original listener fields and selected main zero-countdown path returned.',
                    popup_removed_proved=False,completed_startup_proved=False)
                self.record('readiness_correlation',evidence=self.acceptance)
                for h in self.hooks.values():q.hook_del(h)
                self.hooks.clear();self.retired=True
            return
        if a==0x25ec44:
            self.require(f.get('selected_call') and (r.sp,r.lr,r.r0,r.r1)==(f['sp']-40,0x25f140,f['owner'],0),'progress actual entry thread/SP/LR/arguments')
            f['popup_entry']=True;return
        if a==0x25eca8:
            self.require(f['popup_entry'] and r.sp==f['sp']-60 and word(q,r.sp+16)==0x25f140,'progress saved LR/SP')
            f['popup_pop']=True;return
        if a==0x25f040:
            self.require(r.sp==f['sp']-16 and word(q,r.sp+12)==f['caller'],'consumer saved LR/SP')
            f['pop']=True;return
        self.require(r.sp==f['sp']-40 and r.r4==f['owner'],'consumer body SP/owner')
        if a==0x25f04c:
            self.require(r.r3==1 and not r.cpsr&(1<<30),'completion flag branch')
            f['flag_matched']=True
        elif a==0x25f05c:
            p=struct.unpack('<I',self.discovery.expected(0x25f1a4))[0]
            count=word(q,p+4)
            self.require(r.r0==p and r.r5==count and bool(r.cpsr&(1<<30))==(count==0),'countdown pointer/value/flag')
            f['zero_countdown']=count==0
        elif a==0x25f108:
            self.require(f.get('flag_matched') and f.get('zero_countdown'),'selected path without flag/countdown gates')
            f['selected']=True
        elif a==0x25f13c:
            self.require(f['selected'] and (r.r0,r.r1)==(f['owner'],0),'progress selected call owner/false argument')
            f['selected_call']=True
        elif a==0x25f140:
            self.require(f['popup_entry'] and f['popup_pop'],'progress matched return')
            f['popup_return']=True
    def summary(self):return dict(acceptance=self.acceptance,pending_frames=self.frames,retired=self.retired,skipped_unattributed_callbacks=self.skipped,read_only=True,detail_hooks_enabled=False,input_sent=False)
