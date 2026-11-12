"""Sparse original FxMasterLofiView frame matching; read-only boundaries."""
import collections,struct,time
from resource_application_observer import caller_transfer
ENTRY=0x4007a4;POP=0x4013ac;CALLER=0x324388
POINTS={ENTRY:'f04f2de9',0x4007b4:'b4d04de2',0x4013a8:'b4d08de2',POP:'f08fbde8',CALLER-4:'067103eb',CALLER:'000054e3'}
class ConstructorObserver:
 def __init__(self,emit,started,discovery):
  self.emit=emit;self.started=started;self.discovery=discovery;self.frames=[];self.completed=[];self.counts=collections.Counter();self.installed={}
 def install(self,q):
  for a,h in POINTS.items():
   if self.discovery.expected(a).hex()!=h or bytes(q.mem.read(a,4)).hex()!=h:raise RuntimeError('Constructor original bytes differ '+hex(a))
  kind,target=caller_transfer(CALLER-4,bytes.fromhex(POINTS[CALLER-4]))
  if kind!='arm_bl' or target!=ENTRY:raise RuntimeError('Constructor caller transfer differs')
  for a in (ENTRY,POP,CALLER):
   q.hook_address(lambda guest,a=a:self.checkpoint(guest,a),a);self.installed[hex(a)]=POINTS[a]
  self.emit('constructor_hooks_installed',points={hex(a):h for a,h in POINTS.items()},caller_transfer=kind,caller_target=hex(target),read_only=True,main_only=True)
 def context(self,q):return dict(host_elapsed=round(time.monotonic()-self.started,6),thread=q.os.thread_management.cur_thread.id,pc=hex(q.arch.regs.arch_pc),sp=hex(q.arch.regs.sp),lr=hex(q.arch.regs.lr))
 def checkpoint(self,q,a):
  if self.discovery.main_tid is None or q.os.thread_management.cur_thread.id!=self.discovery.main_tid:return
  c=self.context(q)
  if a==ENTRY:
   if q.arch.regs.lr!=CALLER:raise RuntimeError('Unexpected constructor caller')
   if self.frames and self.frames[-1]['entry_sp']==q.arch.regs.sp:
    self.counts['duplicate_entries']+=1;return
   f=dict(entry=hex(ENTRY),caller=CALLER,entry_sp=q.arch.regs.sp,entry_context=c,ready=False,pop_observed=False)
   self.frames.append(f);self.counts['entries']+=1;self.emit('constructor_entry',frame=dict(f))
  elif a==POP:
   if not self.frames:self.counts['pop_without_frame']+=1;return
   f=self.frames[-1];saved=struct.unpack('<I',bytes(q.mem.read(q.arch.regs.sp+32,4)))[0]
   f.update(pop_observed=True,saved_caller=hex(saved),ready=q.arch.regs.sp==f['entry_sp']-36 and saved==CALLER,pop_context=c)
   self.counts['pops']+=1;self.emit('constructor_before_pop',frame=dict(f))
  elif a==CALLER and self.frames:
   f=self.frames[-1]
   if not f['pop_observed']:self.counts['caller_without_pop']+=1;return
   self.frames.pop();f.update(restored_sp_matches=q.arch.regs.sp==f['entry_sp'],matched_return=bool(f['ready'] and q.arch.regs.sp==f['entry_sp']),return_context=c)
   self.completed.append(f);self.counts['matched_returns' if f['matched_return'] else 'unmatched_returns']+=1;self.emit('constructor_return',result=f)
 def summary(self):return dict(counts=dict(self.counts),installed=self.installed,pending_frames=self.frames,completed_returns=self.completed,read_only=True)
