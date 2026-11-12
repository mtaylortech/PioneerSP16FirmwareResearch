"""Sparse read-only main startup stages and matched wider caller returns.

Historical parent/allocation hot hooks are deliberately absent. Caller hooks are
permanent and byte-validated when first learned; no hook is deleted in callbacks.
"""
from pathlib import Path
import collections, hashlib, struct, time
from elftools.elf.elffile import ELFFile
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_SP

WAIT_NAMES=('futex','nanosleep','clock_nanosleep','poll','select','_newselect','epoll_wait','read','readv','ioctl','sched_yield')
POINTS={
 0x1bc8d4:'wider_constructor_entry',0x1bc910:'enclosing_caller_continuation',
 0x1bc974:'following_153e98_return',0x1bcc48:'following_33d900_call',
 0x1bcc4c:'following_33d900_return',0x1bceb4:'following_51e2c0_call',
 0x1bceb8:'following_51e2c0_return',0x1bf8ac:'wider_constructor_before_pop',
 0x183504:'subsequent_constructor_entry',0x18381c:'subsequent_parent_continuation',
 0x1839c4:'subsequent_4f782c_call',0x1839c8:'subsequent_4f782c_return',
 0x183c08:'subsequent_second_4f782c_call',0x183c0c:'subsequent_second_4f782c_return',
 0x185e10:'subsequent_constructor_before_pop',
}
FRAMES={0x1bc8d4:('wider_constructor',0x1bf8ac),0x183504:('subsequent_constructor',0x185e10)}

class NextPhaseObserver:
 def __init__(self,emit,started,app_path):
  self.emit=emit;self.started=started;self.app_path=Path(app_path)
  self.app_sha256=hashlib.sha256(self.app_path.read_bytes()).hexdigest()
  if self.app_sha256!='3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464':raise RuntimeError('Sparse observer app identity mismatch')
  with self.app_path.open('rb') as f:
   elf=ELFFile(f);self.segments=[(s['p_vaddr'],s.data()) for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
  self.main_tid=None;self.main_thread=None;self.active=False;self.sequence=0
  self.counts=collections.Counter();self.frames={};self.completed=[];self.installed={};self.last_context=None;self.last_progress=time.monotonic()
 def expected(self,a):
  for start,data in self.segments:
   if start<=a and a+4<=start+len(data):return data[a-start:a-start+4]
  raise RuntimeError('Sparse observer checkpoint outside original app '+hex(a))
 def install_point(self,q,a,name):
  if a in self.installed:return
  expected=self.expected(a)
  if bytes(q.mem.read(a,4))!=expected:raise RuntimeError('Sparse observer loaded checkpoint bytes differ '+hex(a))
  self.installed[a]={'name':name,'bytes':expected.hex()};q.hook_address(self.checkpoint(a,name),a)
 def install(self,q):
  for a,name in POINTS.items():self.install_point(q,a,name)
  self.emit('next_phase_hooks_installed',read_only=True,permanent=True,app_sha256=self.app_sha256,checkpoints={hex(a):v for a,v in self.installed.items()},retired_hooks='all parent/allocation/matrix hot hooks')
 def identify_main(self,q):
  self.main_thread=q.os.thread_management.cur_thread;self.main_tid=self.main_thread.id
  self.emit('next_phase_main_identified',thread=self.main_tid,pc=hex(q.arch.regs.arch_pc))
 def context(self,q,stage):
  return {'stage':stage,'sequence':self.sequence,'host_elapsed':round(time.monotonic()-self.started,6),'thread':q.os.thread_management.cur_thread.id,'pc':hex(q.arch.regs.arch_pc),'lr':hex(q.arch.regs.lr),'sp':hex(q.arch.regs.sp),'registers':{n:hex(q.arch.regs.read(n)) for n in ('r0','r1','r2','r3','r4','r7','r8')}}
 def checkpoint(self,a,name):
  def cb(q):
   if self.main_tid is None or q.os.thread_management.cur_thread.id!=self.main_tid:return
   if a in FRAMES:
    key,pop=FRAMES[a];lr=q.arch.regs.lr;self.frames[key]={'entry':hex(a),'entry_sp':q.arch.regs.sp,'caller':lr,'object':hex(q.arch.regs.r0),'before_pop':pop,'ready':False}
    if not lr&3:
     self.install_point(q,lr,key+'_caller_return')
     self.emit('next_phase_learned_caller',frame=dict(self.frames[key]),checkpoint=self.installed[lr])
   if a in (0x1bc910,0x18381c):self.active=True
   if not self.active and a not in FRAMES:return
   self.sequence+=1;self.counts[name]+=1;row=self.context(q,name)
   for key,f in list(self.frames.items()):
    if a==f['before_pop']:
     try:
      saved=struct.unpack('<I',bytes(q.mem.read(q.arch.regs.sp+32,4)))[0]
      f['ready']=q.arch.regs.sp==f['entry_sp']-36 and saved==f['caller'];f['saved_caller']=hex(saved)
      row.update(frame=key,matched_before_pop=f['ready'],saved_caller=hex(saved),expected_caller=hex(f['caller']))
     except Exception as ex:row['saved_caller_error']=str(ex)[:200]
    if a==f['caller']:
     result={**f,'caller':hex(f['caller']),'entry_sp':hex(f['entry_sp']),'before_pop':hex(f['before_pop']),'matched_return':bool(f['ready'] and q.arch.regs.sp==f['entry_sp']),'return_context':row}
     self.completed.append(result);self.completed=self.completed[-8:];self.frames.pop(key)
     self.emit('next_phase_constructor_return',frame=key,result=result)
   self.last_context=row
   if self.counts[name]<=2:self.emit('next_phase_checkpoint',checkpoint=row,counters=dict(self.counts))
   now=time.monotonic()
   if now-self.last_progress>=5:self.last_progress=now;self.emit('next_phase_progress',**self.summary(q))
  return cb
 def main_state(self,q):
  if self.main_thread is None:return None
  try:
   current=q.os.thread_management.cur_thread
   if current is self.main_thread:return {'thread':self.main_tid,'source':'currently_loaded_main','pc':hex(q.arch.regs.arch_pc),'lr':hex(q.arch.regs.lr),'sp':hex(q.arch.regs.sp)}
   ctx=self.main_thread.saved_context
   return {'thread':self.main_tid,'source':'saved_main_context_read_only','pc':hex(ctx.reg_read(UC_ARM_REG_PC)),'lr':hex(ctx.reg_read(UC_ARM_REG_LR)),'sp':hex(ctx.reg_read(UC_ARM_REG_SP)),'scheduled_current_thread':getattr(current,'id',None),'thread_status':str(getattr(self.main_thread,'status',None))}
  except Exception as ex:return {'thread':self.main_tid,'source':'unavailable','error':str(ex)[:200]}
 def summary(self,q=None):
  return {'runtime_main_tid':self.main_tid,'post_parent_boundary_observed':self.active,'sequence':self.sequence,'counters':dict(self.counts),'pending_constructor_frames':self.frames,'completed_constructor_returns':self.completed,'last_main_context':self.last_context,'sampled_main_state':self.main_state(q) if q is not None else None,'read_only':True,'scope':'15 sparse application boundary/call/return hooks plus validated learned caller returns; no parent/allocation hot hooks'}
