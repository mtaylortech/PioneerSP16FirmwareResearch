"""Original resume results, selected branches and actual listener state receipts."""
import collections,json,time
from pathlib import Path
POINTS=(0x33c048,0x33c078,0x33c07c,0x33c1c8,0x33c1f0,0x33c1f4,0x33c1fc,0x33c200,0x33c204,0x33c208,0x33c254,0x33c258,0x33c260,0x33c268,0x33c280,0x33c284,0x33c290,0x33c294,0x33c298,0x33c2a4,0x33c2a8,0x33c2c0,0x33c2c4,0x33c2e0)
class CompletionObserver:
 def __init__(self,emit,discovery,run):
  self.emit,self.discovery,self.run=emit,discovery,Path(run);self.frames={};self.listener={};self.hooks={};self.counts=collections.Counter();self.records=[];self.paths={};self.pending_paths={};self.stores={};self.callback_calls={};self.hook_callbacks={};self.listener_completed=False;self.installed_targets=set()
 def validate(self,q,a,n=4):
  raw=b''.join(self.discovery.expected(a+i) for i in range(0,n,4))
  if bytes(q.mem.read(a,n))!=raw:raise RuntimeError('Completion original bytes differ '+hex(a))
  return raw
 def hook(self,q,a,fn):
  if a not in self.hooks:
   self.hook_callbacks[a]=[]
   self.hooks[a]=q.hook_address(lambda guest,a=a:self.dispatch_hook(guest,a),a)
  self.hook_callbacks[a].append(fn)
 def dispatch_hook(self,q,a):
  for callback in list(self.hook_callbacks[a]):callback(q)
 def install(self,q):
  rows={}
  for a in POINTS:
   rows[hex(a)]=self.validate(q,a).hex();self.hook(q,a,lambda guest,a=a:self.visit(guest,a))
  self.emit('completion_hooks_validated',points=rows,read_only=True)
 def record(self,kind,**row):
  self.records.append(dict(kind=kind,**row));self.emit(kind,**row)
 def context(self,q):return dict(thread=q.os.thread_management.cur_thread.id,sp=hex(q.arch.regs.sp),pc=hex(q.arch.regs.arch_pc),registers={n:hex(q.arch.regs.read(n)) for n in ('r0','r1','r2','r3','r4','r5','r6','r7','lr')})
 def visit(self,q,a):
  tid=q.os.thread_management.cur_thread.id;r=q.arch.regs
  if a==0x33c048:
   if tid in self.frames:raise RuntimeError('Overlapping original resume frame')
   self.frames[tid]=dict(thread=tid,sp=r.sp,caller=r.lr,manager=r.r0,listener=r.r1)
   self.validate(q,r.lr);self.hook(q,r.lr,self.resume_return)
  if tid not in self.frames:return
  self.counts[hex(a)]+=1;row=self.context(q)
  if a in (0x33c1f0,0x33c200,0x33c290):
   try:row['file_object_path']=q.mem.string(q.mem.read_ptr(r.r0))
   except Exception:row['file_object_raw16']=bytes(q.mem.read(r.r0,16)).hex()
  if a==0x33c280:
   target=r.r3;vtable=q.mem.read_ptr(r.r0)
   if target!=q.mem.read_ptr(vtable+12) or target&3:raise RuntimeError('Listener virtual target mismatch')
   raw=self.validate(q,target,768);ins=list(q.arch.disassembler.disasm(raw,target));body=[]
   for i in ins:
    body.append(dict(address=hex(i.address),bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str))
    if i.mnemonic in ('pop','bx') and ('pc' in i.op_str or i.op_str=='lr'):break
   frame=dict(thread=tid,sp=r.sp,target=target,listener=r.r0,manager=r.r1,result_argument=r.r2,before64=bytes(q.mem.read(r.r0,64)).hex(),manager_before64=bytes(q.mem.read(r.r1,64)).hex(),entry_observed=False)
   self.listener[tid]=frame;row['listener_frame']=frame
   self.record('original_completion_listener_target',target=hex(target),instructions=body,frame=frame)
   self.hook(q,target,lambda guest:self.target_entry(guest)) if target not in self.installed_targets else None
   for i in ([] if target in self.installed_targets else body):
    addr=int(i['address'],16)
    if i['mnemonic'].startswith('str'):
     self.hook(q,addr,lambda guest,a=addr:self.store_before(guest,a));self.validate(q,addr+4);self.hook(q,addr+4,lambda guest,a=addr:self.store_after(guest,a))
    elif i['mnemonic'] in ('bl','blx'):
     self.hook(q,addr,lambda guest,a=addr:self.callback_call(guest,a));self.validate(q,addr+4);self.hook(q,addr+4,lambda guest,a=addr:self.callback_return(guest,a))
  if a==0x33c280:self.installed_targets.add(r.r3)
  if a==0x33c284 and tid in self.listener:
   f=self.listener.pop(tid)
   if r.sp!=f['sp']:raise RuntimeError('Original listener return SP mismatch')
   if not f.get('entry_observed'):raise RuntimeError('Listener return without validated actual target entry')
   self.listener_completed=True
   self.record('original_completion_listener_return',frame=f,matched_thread_sp=True,after64=bytes(q.mem.read(f['listener'],64)).hex(),manager_after64=bytes(q.mem.read(f['manager'],64)).hex(),**row)
  self.record('original_resume_boundary',**row)
 def target_entry(self,q):
  tid=q.os.thread_management.cur_thread.id;f=self.listener.get(tid);r=q.arch.regs
  if not f:return
  if (r.sp,r.r0,r.r1,r.lr)!=(f['sp'],f['listener'],f['manager'],0x33c284):raise RuntimeError('Original listener entry frame mismatch')
  f['entry_observed']=True
  self.record('original_completion_listener_entry',frame=f,matched_thread_sp_arguments_lr=True)
 def store_before(self,q,a):
  tid=q.os.thread_management.cur_thread.id
  if tid not in self.listener:return
  i=next(q.arch.disassembler.disasm(bytes(q.mem.read(a,4)),a))
  import re
  m=re.fullmatch(r'(\w+), \[(\w+)(?:, #(-?(?:0x[0-9a-f]+|\d+)))?\]',i.op_str)
  if not m:return
  src,base,off=m.groups();p=q.arch.regs.read(base)+int(off or '0',0);n=1 if i.mnemonic.startswith('strb') else 2 if i.mnemonic.startswith('strh') else 4
  self.stores[(tid,a,q.arch.regs.sp)]=dict(address=hex(p),size=n,before=bytes(q.mem.read(p,n)).hex(),source=hex(q.arch.regs.read(src)),instruction=i.op_str,pc=hex(a))
 def store_after(self,q,a):
  tid=q.os.thread_management.cur_thread.id;row=self.stores.pop((tid,a,q.arch.regs.sp),None)
  if row:self.record('original_listener_state_store',after=bytes(q.mem.read(int(row['address'],16),row['size'])).hex(),thread=tid,**row)
 def callback_call(self,q,a):
  tid=q.os.thread_management.cur_thread.id
  if tid not in self.listener:return
  i=next(q.arch.disassembler.disasm(bytes(q.mem.read(a,4)),a));target=int(i.op_str.lstrip('#'),0) if i.mnemonic=='bl' else q.arch.regs.read(i.op_str)
  row=dict(target=hex(target),pc=hex(a),sp=q.arch.regs.sp,thread=tid,arguments=[hex(q.arch.regs.read('r'+str(n))) for n in range(4)])
  if 0x10000<=target<0x870000:
   row['target_bytes']=self.validate(q,target,16).hex()
   # Retain original callee instructions to interpret the state change without changing execution.
   raw=self.validate(q,target,256);row['target_instructions']=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str) for i in q.arch.disassembler.disasm(raw,target)]
  self.callback_calls[(tid,a,q.arch.regs.sp)]=row;self.record('original_listener_adjacent_call',**row)
 def callback_return(self,q,a):
  row=self.callback_calls.pop((q.os.thread_management.cur_thread.id,a,q.arch.regs.sp),None)
  if row:self.record('original_listener_adjacent_return',call=row,result=hex(q.arch.regs.r0),matched_thread_sp=True)
 def resume_return(self,q):
  tid=q.os.thread_management.cur_thread.id;f=self.frames.get(tid)
  if not f or q.arch.regs.arch_pc!=f['caller']:return
  if q.arch.regs.sp!=f['sp']:raise RuntimeError('Original resume return SP mismatch')
  self.record('original_resume_return',frame=f,result=hex(q.arch.regs.r0),matched_thread_sp=True);self.frames.pop(tid)
  if not self.listener_completed:
   self.emit('completion_observation_retained',reason='resume returned without matched listener completion; asynchronous work remains unobserved',frame=f)
   return
  if self.frames:return
  for a,h in list(self.hooks.items()):q.hook_del(h)
  self.hooks.clear();self.hook_callbacks.clear();self.emit('completion_details_retired',reason='matched original listener and enclosing resume returned; receipts retained, no success inference')
 def path_enter(self,name):
  def cb(q,*values):
   tid=q.os.thread_management.cur_thread.id
   if tid not in self.frames:return
   p=q.mem.string(values[1] if name=='openat' else values[0])
   if 'System/resuming' in p or 'System/data.rsm' in p:self.pending_paths[(tid,name)]=dict(path=p,thread=tid,sp=q.arch.regs.sp,syscall=name,pc=hex(q.arch.regs.arch_pc))
  return cb
 def path_exit(self,name):
  def cb(q,*values):
   row=self.pending_paths.pop((q.os.thread_management.cur_thread.id,name),None)
   if row:
    if row['sp']!=q.arch.regs.sp:raise RuntimeError('Resume path syscall frame mismatch')
    self.record('original_resume_file_result',result=values[-1],matched_thread_sp=True,**row)
  return cb
 def summary(self):return dict(counts=dict(self.counts),pending=self.frames,listener_pending=self.listener,records=self.records,retired=not bool(self.hooks))
