"""Optional sparse, read-only original XNextEvent return/payload observer.

Copy/integrate only between original guests. Uses ARM32 Xlib event offsets from
the retained Xlib.h and original ELF's 32-bit ABI, with byte-validated PLT/caller
and same-thread/SP matching. It changes no instructions, registers or scheduling.
"""
import collections,json,pathlib,struct,time
from natural_dispatch import decode
from event_pump_observer import exact_event
PLT=0x10f78
CALLERS=(0x69b014,0x69b530,0x69b704,0x69bc1c,0x7f98e0)
class OriginalX11Events:
 def __init__(self,emit,started,discovery,run_directory):
  self.emit=emit;self.started=started;self.discovery=discovery;self.run=pathlib.Path(run_directory);self.counts=collections.Counter();self.pending={};self.callers={};self.receipts=[];self.max_callers=len(CALLERS);self.max_receipts=128
  self.handles=[];self.retired=False;self.active_input=None;self.handler_frames={};self.handler_hooks={}
 def expected(self,address,size=4):return b''.join(self.discovery.expected(address+i) for i in range(0,size,4))
 def install(self,q):
  expected=self.expected(PLT,12)
  if bytes(q.mem.read(PLT,12))!=expected:raise RuntimeError('Original XNextEvent PLT bytes differ')
  from resource_application_observer import caller_transfer
  for caller in CALLERS:
   instruction=self.expected(caller-4);kind,target=caller_transfer(caller-4,instruction)
   if kind!='arm_bl' or target!=PLT or bytes(q.mem.read(caller-4,4))!=instruction or bytes(q.mem.read(caller,4))!=self.expected(caller):raise RuntimeError('Original XNextEvent direct BL/caller bytes differ '+hex(caller))
   self.callers[caller]=self.expected(caller).hex()
  self.handles.append(q.hook_address(self.enter,PLT))
  for caller in CALLERS:self.handles.append(q.hook_address(lambda guest,a=caller:self.returned(guest,a),caller))
  from natural_dispatch import CALLBACKS
  for a in CALLBACKS:
   raw=self.expected(a)
   if bytes(q.mem.read(a,4))!=raw:raise RuntimeError('Original input dispatch bytes differ')
   self.handles.append(q.hook_address(lambda guest,a=a:self.input_dispatch(guest,a),a))
  self.emit('original_x11_event_hooks_installed',plt=hex(PLT),bytes=expected.hex(),callers={hex(a):b for a,b in self.callers.items()},read_only=True,main_only=True,permanent=True,event_abi='ELF ARM32; Xlib.h 32-bit fields; first60 bytes for key/button/motion',max_callers=self.max_callers,max_receipts=self.max_receipts)
 def enter(self,q):
  tid=q.os.thread_management.cur_thread.id
  # Observe validated callers across all live threads.
  self.counts['entries']+=1;caller=q.arch.regs.lr;sp=q.arch.regs.sp
  from resource_application_observer import caller_transfer
  try:
   instruction=self.expected(caller-4);kind,target=caller_transfer(caller-4,instruction)
   if kind!='arm_bl' or target!=PLT or bytes(q.mem.read(caller-4,4))!=instruction or bytes(q.mem.read(caller,4))!=self.expected(caller):raise ValueError('Original direct BL/caller bytes differ')
   if caller not in self.callers:raise ValueError('Original event caller is outside byte-validated fixed caller set')
   key=(tid,caller,sp)
   if key in self.pending:self.counts['duplicate_entries']+=1;return
   self.pending[key]={'thread':tid,'caller':hex(caller),'entry_sp':hex(sp),'event_pointer':q.arch.regs.r1,'display':hex(q.arch.regs.r0),'entry_elapsed':time.monotonic()-self.started}
  except Exception as e:
   self.counts['unverified_entries']+=1
   if self.counts['unverified_entries']<=3:self.emit('original_x11_event_entry_unverified',error=type(e).__name__+': '+str(e),thread=tid,caller=hex(caller),sp=hex(sp))
 def returned(self,q,caller):
  tid=q.os.thread_management.cur_thread.id;key=(tid,caller,q.arch.regs.sp);frame=self.pending.pop(key,None)
  if not frame:return
  self.counts['matched_returns']+=1
  try:
   raw=bytes(q.mem.read(frame['event_pointer'],60));event_type=struct.unpack_from('<i',raw)[0]
   if event_type not in (2,3,4,5,6):
    event=decode(raw)
    if event['display']!=frame['display']:raise ValueError('Returned original event Display differs')
    self.counts['natural_returns']+=1
    return
   event=dict(type=event_type,serial=struct.unpack_from('<I',raw,4)[0],send_event=bool(struct.unpack_from('<I',raw,8)[0]),display=hex(struct.unpack_from('<I',raw,12)[0]),window=hex(struct.unpack_from('<I',raw,16)[0]),root=hex(struct.unpack_from('<I',raw,20)[0]),subwindow=hex(struct.unpack_from('<I',raw,24)[0]),time=struct.unpack_from('<I',raw,28)[0],x=struct.unpack_from('<i',raw,32)[0],y=struct.unpack_from('<i',raw,36)[0],x_root=struct.unpack_from('<i',raw,40)[0],y_root=struct.unpack_from('<i',raw,44)[0],state=struct.unpack_from('<I',raw,48)[0],detail=struct.unpack_from('<I',raw,52)[0],same_screen=bool(struct.unpack_from('<I',raw,56)[0]))
   if event['display']!=frame['display']:raise ValueError('Returned original event Display differs')
   self.counts['input_returns']+=1;selected=event['send_event'] and (self.run/'drawable-input-consumed.json').exists()
   if selected:
    requested=json.loads((self.run/'drawable-input-consumed.json').read_text())
    selected=exact_event(event,requested)
   if selected and len(self.receipts)<self.max_receipts:
    row=dict(raw60=raw.hex(),matched_return=True,frame=frame,event=event,return_elapsed=time.monotonic()-self.started,thread=tid,pc=hex(q.arch.regs.arch_pc),sp=hex(q.arch.regs.sp),read_only=True);self.receipts.append(row);self.emit('original_x11_event_return',**row);self.active_input=row
  except Exception as e:
   self.counts['payload_errors']+=1
   if self.counts['payload_errors']<=3:self.emit('original_x11_event_payload_error',error=type(e).__name__+': '+str(e),frame=frame)
 def input_dispatch(self,q,a):
  active=self.active_input
  if not active or active['thread']!=q.os.thread_management.cur_thread.id:return
  raw=bytes(q.mem.read(q.arch.regs.r0,60));event=active['event']
  if raw!=bytes.fromhex(active['raw60']):return
  target=q.arch.regs.r3;expected=self.discovery.expected(target)
  if bytes(q.mem.read(target,4))!=expected:raise RuntimeError('Original input target bytes differ')
  tid=active['thread'];sp=q.arch.regs.sp;key=(tid,a+4,sp)
  self.handler_frames[key]=dict(event=event,thread=tid,call=hex(a),target=hex(target),target_bytes=expected.hex(),sp=hex(sp),argument60=raw.hex(),matched_original_input=True)
  self.emit('original_input_handler_call',**self.handler_frames[key])
  if a+4 not in self.handler_hooks:
   expected=self.discovery.expected(a+4)
   if bytes(q.mem.read(a+4,4))!=expected:raise RuntimeError('Original input return bytes differ')
   self.handler_hooks[a+4]=q.hook_address(lambda guest,addr=a+4:self.handler_return(guest,addr),a+4)
  self.active_input=None
 def handler_return(self,q,a):
  key=(q.os.thread_management.cur_thread.id,a,q.arch.regs.sp);frame=self.handler_frames.pop(key,None)
  if frame:self.emit('original_input_handler_return',frame=frame,result=hex(q.arch.regs.r0),pc=hex(a),matched_thread_sp=True)
 def retire(self,q):
  for h in self.handles:q.hook_del(h)
  self.handles=[];self.retired=True
  self.emit('broad_event_hooks_retired',reason='selected Expose callback matched return',pending=list(self.pending.values()),read_only=True)
 def summary(self):return dict(counts=dict(self.counts),pending_frames=list(self.pending.values()),caller_hooks={hex(a):b for a,b in self.callers.items()},receipts=self.receipts,read_only=True,hooks_retired=self.retired)
