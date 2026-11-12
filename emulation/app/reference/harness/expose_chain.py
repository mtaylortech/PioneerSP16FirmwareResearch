"""Read-only receipts for one exact original main-drawable Expose frame."""
import collections, hashlib, time
from natural_dispatch import decode

POINTS={0x817d58:'context_call',0x817d5c:'context_return',
        0x817d68:'context_success_gate',0x817d84:'window_registry_gate',
        0x817dc8:'registry_match',0x817dcc:'dispatch_gate',
        0x817de4:'window_call',0x817564:'window_entry',0x817de8:'window_return',
        0x81785c:'expose_branch',0x7f9814:'helper_entry',0x817860:'helper_return',
        0x7f98a0:'virtual_call',0x7f98a4:'virtual_return'}
KNOWN={0x817d58:'d3e2dfeb',0x817d5c:'00509de5',0x817564:'f0472de9',
       0x81785c:'ec87ffeb',0x7f9814:'f0402de9',0x7f98a0:'33ff2fe1'}

class ExposeChain:
    def __init__(self,emit,started,discovery):
        self.emit=emit;self.started=started;self.discovery=discovery
        self.selected=None;self.receipts=[];self.pending={};self.counts=collections.Counter()
        self.handles={};self.target=None;self.completed=False;self.redraw=None
    def point(self,q,a,name):
        expected=self.discovery.expected(a)
        if a in KNOWN and expected.hex()!=KNOWN[a]:raise RuntimeError('Expose static bytes differ '+hex(a))
        actual=bytes(q.mem.read(a,4))
        if actual!=expected:raise RuntimeError('Expose loaded bytes differ '+hex(a))
        self.handles[a]=q.hook_address(lambda guest,a=a:self.visit(guest,a),a)
        return dict(address=hex(a),name=name,expected=expected.hex(),actual=actual.hex(),matches=True)
    def install(self,q):
        self.emit('expose_chain_installed',points=[self.point(q,a,n) for a,n in POINTS.items()],read_only=True,selected_window='0x200009',max_selected_events=1)
    def select(self,q,call):
        if self.selected is not None:return
        e=decode(bytes.fromhex(call['argument60']))
        if e['type']!=12 or e['window']!='0x200009' or e['send_event']:return
        if call['target']!='0x817cf0' or call['target_matches_original_app'] is not True:raise RuntimeError('Selected Expose callback identity differs')
        self.selected=dict(event=e,event_pointer=call['argument'],thread=call['thread'],outer_sp=call['sp'],outer_return=hex(int(call['pc'],16)+4),event_sha256=hashlib.sha256(bytes.fromhex(e['raw60'])).hexdigest())
        self.emit('selected_expose_frame',**self.selected,read_only=True)
    def record(self,name,base,**extra):
        row=dict(boundary=name,elapsed=time.monotonic()-self.started,event_sha256=self.selected['event_sha256'],**base,**extra)
        self.receipts.append(row);self.emit('expose_chain_boundary',**row)
    def visit(self,q,a):
        s=self.selected
        if s is None or self.completed or q.os.thread_management.cur_thread.id!=s['thread']:return
        name='virtual_target_entry' if a==self.target else POINTS[a]
        tid=s['thread'];sp=q.arch.regs.sp
        self.counts[name]+=1
        base=dict(thread=tid,pc=hex(a),sp=hex(sp),lr=hex(q.arch.regs.lr),read_only=True)
        return_names={'context_return','window_return','helper_return','virtual_return'}
        if name in return_names:
            f=self.pending.pop((tid,a,sp),None)
            if not f:return
            extra=dict(call=f,result=hex(q.arch.regs.r0),matched_thread_sp=True)
            if name=='context_return':extra.update(output_pointer=f['output_pointer'],output_value=hex(q.mem.read_ptr(int(f['output_pointer'],16))))
            self.record(name,base,**extra);return
        ptr=q.arch.regs.r1 if name in ('window_call','window_entry','helper_entry') else (q.arch.regs.r6 if name in ('virtual_call','virtual_target_entry') else q.arch.regs.r4)
        raw=bytes(q.mem.read(ptr,60))
        if raw.hex()!=s['event']['raw60']:raise RuntimeError('Selected Expose bytes differ at '+name)
        base.update(event_pointer=hex(ptr),matched_event_bytes=True,matched_event_pointer=hex(ptr)==s['event_pointer'])
        if name=='context_call':
            extra=dict(display=hex(q.arch.regs.r0),drawable=hex(q.arch.regs.r1),context=hex(q.arch.regs.r2),output_pointer=hex(q.arch.regs.r3),output_before=hex(q.mem.read_ptr(q.arch.regs.r3)))
            self.pending[(tid,0x817d5c,sp)]={**base,**extra};self.record(name,base,**extra)
        elif name=='window_call':
            f=dict(base,object=hex(q.arch.regs.r0));self.pending[(tid,0x817de8,sp)]=f;self.record(name,base,object=f['object'])
        elif name=='expose_branch':
            f=dict(base,object=hex(q.arch.regs.r0));self.pending[(tid,0x817860,sp)]=f;self.record(name,base,object=f['object'])
        elif name=='virtual_call':
            target=q.arch.regs.r3
            if target&3:raise RuntimeError('Selected virtual target is not ARM aligned')
            self.target=target
            validation=self.point(q,target,'virtual_target_entry')
            extra=dict(target=hex(target),target_validation=validation,object=hex(q.arch.regs.r0),rectangle_pointer=hex(q.arch.regs.r1),rectangle16=bytes(q.mem.read(q.arch.regs.r1,16)).hex())
            if self.redraw:self.redraw.activate(q,extra,self.selected)
            self.pending[(tid,0x7f98a4,sp)]={**base,**extra};self.record(name,base,**extra)
        else:
            self.record(name,base,registers={n:hex(q.arch.regs.read(n)) for n in ('r0','r1','r2','r3','r4','r5','r6')})
    def complete(self,q,call):
        s=self.selected
        if s is None or self.completed:return False
        if call['argument60']!=s['event']['raw60'] or call['thread']!=s['thread'] or call['sp']!=s['outer_sp']:return False
        self.completed=True
        if self.redraw:self.redraw.retire(q)
        for h in self.handles.values():q.hook_del(h)
        self.handles={}
        self.emit('selected_expose_completed',selected=s,pending=list(self.pending.values()),receipts=len(self.receipts),matched_outer_thread_sp=True,chain_hooks_retired=True,read_only=True)
        return True
    def summary(self):return dict(selected=self.selected,receipts=self.receipts,pending=list(self.pending.values()),counts=dict(self.counts),completed=self.completed,read_only=True)
