"""Bounded, read-only, runtime-main-thread checkpoints after CreateWindow.

Permanent address hooks avoid mutable one-shot hook-list collisions. No guest
memory/register writes; no per-basic-block or application-wide tracing.
"""
from pathlib import Path
import collections,json,struct,time
from elftools.elf.elffile import ELFFile
BASE=Path(__file__).resolve().parent
POINTS={0x6980f4:'original_CreateWindow_return',0x698100:'post_create_cleanup_return',
 0x698104:'post_create_function_return',0x6982ec:'caller_return_6982ec',
 0x698378:'caller_return_698378',0x698454:'caller_return_698454',
 0x698500:'caller_return_698500',0x69861c:'caller_return_69861c',
 0x69984c:'caller_return_69984c',0x699b50:'caller_return_699b50',
 0x354604:'matrix_initializer_entry',0x354640:'matrix_element_callsite',
 0x354658:'matrix_element_return',0x354674:'matrix_loop_complete',
 0x3546d4:'matrix_initializer_return',0x350010:'element_initializer_entry',
 0x353c80:'allocation_element_return',0x353d04:'allocation_initializer_return'}

OMITTED_HOT_POINTS={a:POINTS.pop(a) for a in list(POINTS) if a!=0x6980f4}
WAIT_NAMES=('futex','nanosleep','clock_nanosleep','poll','select','_newselect',
 'epoll_wait','read','readv','ioctl','sched_yield','write','writev','clock_gettime')
class StartupTrace:
 def __init__(self,emit,started,diagnostics):
  self.emit=emit;self.started=started;self.diagnostics=diagnostics;self.main_tid=None;self.active=False
  self.counts=collections.Counter();self.last={};self.syscounts=collections.Counter();self.pending={};self.installed={};self.first_boundary=None;self.last_main=None
  self.progress_gate=lambda:True
  self.expected={}
  with (BASE/'rootfs/root/pdj/EP085_Main_R').open('rb') as f:
   elf=ELFFile(f)
   for a in POINTS:
    seg=next(s for s in elf.iter_segments() if s['p_type']=='PT_LOAD' and s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz'])
    self.expected[a]=seg.data()[a-seg['p_vaddr']:a-seg['p_vaddr']+4]
 def context(self,q):
  return {'thread':q.os.thread_management.cur_thread.id,'pc':hex(q.arch.regs.arch_pc),'lr':hex(q.arch.regs.lr),'registers':{n:hex(q.arch.regs.read(n)) for n in ['r0','r1','r2','r3','r4','r5','r6','r7','r8','r9','r10','r11','sp']}}
 def is_main(self,q):return q.os.thread_management.cur_thread.id==self.main_tid
 def identify_main(self,q):
  self.main_tid=q.os.thread_management.cur_thread.id
  self.emit('startup_main_identified',**self.context(q),source='runtime original main entry')
 def install(self,q):
  for a,n in POINTS.items():
   if bytes(q.mem.read(a,4))!=self.expected[a]:raise RuntimeError('Original main checkpoint bytes differ '+hex(a))
   self.installed[a]=n;q.hook_address(self.checkpoint(a,n),a)
  self.emit('startup_hooks_installed',checkpoints={hex(a):{'name':n,'bytes':self.expected[a].hex()} for a,n in POINTS.items()},read_only=True,permanent=True,main_only_after_return=True,omitted_per_element_checkpoints={hex(a):n for a,n in OMITTED_HOT_POINTS.items()})
 def checkpoint(self,a,name):
  def cb(q):
   if not self.is_main(q):return
   if a==0x6980f4 and not self.active:
    self.active=True;self.emit('startup_after_create_begin',**self.context(q),original_window=hex(q.arch.regs.r0));self.diagnostics.snapshot(q,'startup_original_return')
   if not self.active:return
   self.counts[name]+=1;count=self.counts[name];now=time.monotonic()-self.started
   self.last_main={'checkpoint':name,'elapsed':round(now,6),**self.context(q)}
   if count<=3 or (now-self.last.get(name,0)>=5 and count>3 and self.progress_gate()):
    self.last[name]=now;extra={}
    if a in (0x354640,0x354658,0x354674,0x3546d4):
     base=q.arch.regs.r6
     try:extra['matrix']={'base':hex(base),'header_hex':bytes(q.mem.read(base,40)).hex(),'outer_index_r8':q.arch.regs.r8,'inner_index_r5':q.arch.regs.r5,'stride_offset_r4':q.arch.regs.r4}
     except Exception as ex:extra['matrix_read_error']=str(ex)
    if a==0x698104:extra['saved_caller_pc']=hex(q.mem.read_ptr(q.arch.regs.sp+12))
    if a in (0x354604,):
     try:extra['matrix_input_header_hex']=bytes(q.mem.read(q.arch.regs.r0,40)).hex()
     except Exception as ex:extra['matrix_read_error']=str(ex)
    self.emit('startup_checkpoint',name=name,count=count,**self.context(q),**extra)
    if now>=10:self.diagnostics.snapshot(q,'startup_progress_'+name)
  return cb
 def syscall_enter(self,name):
  def cb(q,*values):
   if not self.active or not self.is_main(q):return
   self.syscounts[name]+=1;count=self.syscounts[name];now=time.monotonic()-self.started
   key=('enter',name)
   log=count<=3 or now-self.last.get(key,0)>=5
   self.pending[name]={'entered_elapsed':round(now,6),'arguments':[hex(v) if isinstance(v,int) else str(v) for v in values],'count':count,'logged':log,**self.context(q)}
   if self.first_boundary is None:self.first_boundary=dict(name=name,**self.pending[name])
   if log:
    self.last[key]=now;self.emit('startup_syscall_enter',name=name,**self.pending[name])
  return cb
 def syscall_exit(self,name):
  def cb(q,*values):
   if not self.active or not self.is_main(q):return
   row=self.pending.pop(name,None)
   if row and row['logged']:
    self.emit('startup_syscall_return',name=name,result=values[-1] if values else None,entered_elapsed=row['entered_elapsed'],duration_seconds=round(time.monotonic()-self.started-row['entered_elapsed'],6),**self.context(q))
  return cb
 def summary(self):
  return {'runtime_main_tid':self.main_tid,'after_return_observed':self.active,'checkpoint_counts':dict(self.counts),'syscall_counts':dict(self.syscounts),'first_syscall_boundary':self.first_boundary,'pending_main_syscalls':self.pending,'last_main_checkpoint':self.last_main,'read_only':True,'omitted_per_element_checkpoints':{hex(a):n for a,n in OMITTED_HOT_POINTS.items()},'trace_scope':'10 byte-validated permanent display caller addresses and selected syscall boundaries; main only after original return; output first3/every5s'}
