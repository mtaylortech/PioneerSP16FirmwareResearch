"""Read-only original worker queue and live virtual request execution receipts."""
import collections, struct
POINTS={0x504480:'request_flag',0x504498:'queue_access',0x5044f4:'queue_before_swap',0x50452c:'queue_after_swap',0x504564:'dispatch_count',0x504578:'request_gate',0x504598:'request_virtual_call',0x50459c:'request_virtual_return'}
class ProjectRequests:
    def __init__(self,emit,names,discovery):
        self.emit,self.names,self.discovery=emit,names,discovery
        self.counts=collections.Counter();self.latest={};self.frames={};self.targets={};self.hooks={};self.states={};self.subcalls={}
    def u32(self,q,p):return struct.unpack('<I',bytes(q.mem.read(p,4)))[0]
    def validate(self,q,a,size=4):
        expected=b''.join(self.discovery.expected(a+i) for i in range(0,size,4));actual=bytes(q.mem.read(a,size))
        if expected!=actual:raise RuntimeError('Project request loaded bytes differ '+hex(a))
        return actual.hex()
    def hook(self,q,a,callback):
        if a not in self.hooks:self.hooks[a]=q.hook_address(callback,a)
    def install(self,q):
        rows=[]
        for a,label in POINTS.items():
            rows.append(dict(address=hex(a),boundary=label,bytes=self.validate(q,a)))
            self.hook(q,a,lambda guest,a=a:self.visit(guest,a))
        self.emit('project_request_hooks_validated',points=rows,read_only=True)
    def queue(self,q,p):
        if not p:return None
        words={hex(o):self.u32(q,p+o) for o in (0x1c,0x20,0x24,0x28,0x2c,0x30,0x34)}
        lists={}
        for po,co in ((0x1c,0x24),(0x28,0x30)):
            ptr,count=words[hex(po)],words[hex(co)]
            if count>4096:raise RuntimeError('Project queue count exceeds observation bound')
            lists[hex(po)]=[hex(self.u32(q,ptr+i*4)) for i in range(min(count,8))] if ptr else []
        return dict(pointer=hex(p),words=words,request_pointers=lists)
    def record(self,label,row):
        self.counts[label]+=1;self.latest[label]=row
        state={k:v for k,v in row.items() if k not in ('sp','registers')}
        if self.counts[label]<=4 or (state!=self.states.get(label) and self.counts[label]<=64):self.emit('project_request_boundary',boundary=label,**row)
        self.states[label]=state
    def visit(self,q,a):
        tid=q.os.thread_management.cur_thread.id
        if self.names.get(tid)!='ProjectManager':return
        label=POINTS[a];r=q.arch.regs;worker=r.r8
        row=dict(thread=tid,pc=hex(a),sp=hex(r.sp),worker=hex(worker),request_flag=bytes(q.mem.read(worker+0xfc,1)).hex(),stop_flag=bytes(q.mem.read(worker+0xe0,1)).hex(),queue=self.queue(q,self.u32(q,worker+0xe4)),registers={n:hex(r.read(n)) for n in ('r0','r3','r4','r5','r7','r8','lr')})
        if a==0x504598:
            target=r.r3;request=r.r0;vtable=self.u32(q,request)
            if target!=self.u32(q,vtable+8) or target&3:raise RuntimeError('Original request virtual target differs')
            raw=self.validate(q,target,32)
            frame=dict(thread=tid,sp=r.sp,request=hex(request),target=hex(target),vtable=hex(vtable),request48=bytes(q.mem.read(request,48)).hex(),target_bytes=raw)
            if tid in self.frames:raise RuntimeError('Unexpected overlapping project request frame')
            self.frames[tid]=frame;row['call']=frame
            if target not in self.targets:
                raw=b''.join(self.discovery.expected(target+i) for i in range(0,512,4));instructions=list(q.arch.disassembler.disasm(raw,target))
                self.targets[target]=dict(bytes=raw.hex(),instructions=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str,bytes=i.bytes.hex()) for i in instructions])
                self.emit('project_request_target_original',target=hex(target),**self.targets[target])
                self.hook(q,target,lambda guest,target=target:self.target_entry(guest,target))
                # Observe adjacent calls in the request's first basic function body.
                for i in instructions:
                    if i.mnemonic in ('pop','bx') and ('pc' in i.op_str or i.op_str=='lr'):break
                    if i.mnemonic in ('bl','blx'):
                        self.validate(q,i.address);self.validate(q,i.address+4)
                        self.hook(q,i.address,lambda guest,a=i.address:self.adjacent(guest,a,False))
                        self.hook(q,i.address+4,lambda guest,a=i.address:self.adjacent(guest,a,True))
        elif a==0x50459c:
            frame=self.frames.pop(tid,None)
            if frame:
                if frame['sp']!=r.sp:raise RuntimeError('Project virtual request return SP differs')
                row.update(call=frame,result=hex(r.r0),matched_thread_sp=True)
        elif a==0x504578:row['request48']=bytes(q.mem.read(r.r0,48)).hex()
        self.record(label,row)
    def target_entry(self,q,target):
        tid=q.os.thread_management.cur_thread.id;frame=self.frames.get(tid)
        if not frame or frame['target']!=hex(target):return
        if frame['sp']!=q.arch.regs.sp or frame['request']!=hex(q.arch.regs.r0) or q.arch.regs.lr!=0x50459c:raise RuntimeError('Project actual virtual entry frame differs')
        self.record('request_target_entry',dict(call=frame,matched_thread_sp_argument_lr=True))
    def adjacent(self,q,a,returned):
        tid=q.os.thread_management.cur_thread.id
        if tid not in self.frames:return
        r=q.arch.regs;key=(tid,a,r.sp)
        if returned:
            call=self.subcalls.pop(key,None)
            if call:self.record('request_adjacent_return',dict(call=call,result=hex(r.r0),matched_thread_sp=True))
            return
        i=next(q.arch.disassembler.disasm(bytes(q.mem.read(a,4)),a))
        target=int(i.op_str.lstrip('#'),0) if i.mnemonic=='bl' else r.read(i.op_str)
        row=dict(thread=tid,pc=hex(a),sp=hex(r.sp),target=hex(target),request=self.frames[tid]['request'],registers={n:hex(r.read(n)) for n in ('r0','r1','r2','r3')})
        if 0x10000<=target<0x870000:row['target_original_bytes']=self.validate(q,target,16)
        self.subcalls[key]=row;self.record('request_adjacent_call',row)
    def summary(self):return dict(counts=dict(self.counts),latest=self.latest,pending_requests=self.frames,pending_adjacent_calls=list(self.subcalls.values()),targets=[hex(a) for a in self.targets])
