"""Sparse, byte-validated dispatch and direct painting boundaries; read only."""
import collections, struct, time, json
from pathlib import Path
CALLBACKS = (0x69b048,0x69b564,0x69b584,0x69b73c,0x69bc54,0x69bc90,0x69bce4,0x7f9918)
FILTERS = {0x69b038:0x88,0x69b554:0xe8,0x69b72c:0x88,0x69bc44:0xe8}
PAINT = {0x783bb8:bytes.fromhex('1736e2eb'),0x806640:bytes.fromhex('752be0eb')}

def decode(raw):
    vals=struct.unpack('<15I',raw)
    kind=struct.unpack_from('<i',raw)[0]
    e=dict(type=kind,serial=vals[1],send_event=bool(vals[2]),display=hex(vals[3]),
           offset16=hex(vals[4]),window=hex(vals[5] if kind in (16,17,18,19,20,21,22,23,24,26,27) else vals[4]),raw60=raw.hex())
    if kind==12:e.update(x=vals[5],y=vals[6],width=vals[7],height=vals[8],count=vals[9])
    if kind==22:e.update(event=hex(vals[4]),x=vals[6],y=vals[7],width=vals[8],height=vals[9])
    return e

class NaturalDispatch:
    def __init__(self,emit,started,discovery):
        self.emit=emit;self.started=started;self.discovery=discovery
        self.counts=collections.Counter();self.pending={};self.records=[];self.points={}
        self.handles={};self.retired=False;self.expose=None;self.retire_events=None
    def install(self,q):
        self.q=q
        from resource_application_observer import caller_transfer
        for a in CALLBACKS:
            if self.discovery.expected(a)!=bytes.fromhex('33ff2fe1'):raise RuntimeError('Callback BLX differs '+hex(a))
        for a,b in PAINT.items():
            kind,target=caller_transfer(a,b)
            if kind!='arm_bl' or target!=0x1141c:raise RuntimeError('Painting BL differs')
        for a in (*PAINT,*(a+4 for a in PAINT)):
            b=self.discovery.expected(a)
            if bytes(q.mem.read(a,4))!=b:raise RuntimeError('Dispatch loaded instruction differs '+hex(a))
            self.points[a]=b.hex();self.handles[a]=q.hook_address(lambda guest,a=a:self.visit(guest,a),a)
        self.emit('natural_dispatch_installed',points={hex(a):b for a,b in self.points.items()},read_only=True,max_records=64)
    def record(self,kind,**row):
        if len(self.records)<128 or kind=='original_dispatch_or_paint_return':
            row=dict(kind=kind,elapsed=time.monotonic()-self.started,**row)
            self.records.append(row);self.emit(kind,**{k:v for k,v in row.items() if k!='kind'})
            if kind=='original_dispatch_or_paint_return' and row.get('call',{}).get('pc') in ('0x783bb8','0x806640'):
                if getattr(self,'paint_confirmed',None):self.paint_confirmed(self.q)
                marker=Path(__file__).with_name('paint-capture-request.json')
                temp=marker.with_suffix('.tmp');temp.write_text(json.dumps(dict(monotonic=time.monotonic(),receipt=row))+'\n');temp.replace(marker)
    def visit(self,q,a):
        tid=q.os.thread_management.cur_thread.id;sp=q.arch.regs.sp
        if a not in PAINT and a-4 not in PAINT and tid!=self.discovery.main_tid:return
        self.counts[hex(a)]+=1
        # A shared loop address may be visited indefinitely. Only admitted calls
        # consume the cap; their matching returns must always be processed.
        is_return=a in {v+4 for v in (*CALLBACKS,*PAINT)}
        if not is_return and self.counts[hex(a)]>16:return
        base=dict(thread=tid,pc=hex(a),sp=hex(sp),read_only=True)
        try:
            if a in FILTERS:
                raw=bytes(q.mem.read(sp+FILTERS[a],60));r5=q.arch.regs.r5
                base.update(event=decode(raw),excluded_window=hex(q.mem.read_ptr(r5+0x58)),
                            callback=hex(q.mem.read_ptr(r5+0x68)))
                self.record('original_event_filter',**base)
            elif a in CALLBACKS:
                target=q.arch.regs.r3;arg=q.arch.regs.r0
                base.update(target=hex(target),argument=hex(arg),argument60=bytes(q.mem.read(arg,60)).hex(),
                            target_bytes=bytes(q.mem.read(target&~1,8)).hex())
                try:base['target_matches_original_app']=bytes(q.mem.read(target,4))==self.discovery.expected(target)
                except RuntimeError:base['target_matches_original_app']=None
                self.pending[(tid,a+4,sp)]=base
                self.record('original_dispatch_callback_call',**base)
                if self.expose:self.expose.select(q,base)
            elif a in PAINT:
                args=[q.arch.regs.read('r'+str(i)) for i in range(4)]
                base.update(arguments=[hex(v) for v in args],stack40=bytes(q.mem.read(sp,40)).hex())
                self.pending[(tid,a+4,sp)]=base
                self.record('original_paint_callsite',**base)
            else:
                call=self.pending.pop((tid,a,sp),None)
                if call:
                    self.record('original_dispatch_or_paint_return',call=call,result=hex(q.arch.regs.r0),matched_thread_sp=True,**base)
                    if self.expose and self.expose.complete(q,call):
                        self.retire(q)
                        if self.retire_events:self.retire_events(q)
        except Exception as e:self.record('natural_dispatch_read_error',error=repr(e),**base)
    def retire(self,q):
        for a in list(self.handles):
            if a not in PAINT and a-4 not in PAINT:q.hook_del(self.handles.pop(a))
        self.retired=True
        self.emit('broad_dispatch_hooks_retired',reason='selected Expose callback matched return',remaining_points=[hex(a) for a in self.handles],pending=list(self.pending.values()),read_only=True)
    def summary(self):
        return dict(counts=dict(self.counts),records=self.records,pending=list(self.pending.values()),read_only=True,broad_hooks_retired=self.retired)
