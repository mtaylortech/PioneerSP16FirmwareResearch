"""Phase-limited cooperative early/font scheduling candidate.

20ms is advisory: CPU-only stretches can run longer. A separate independent
finite watchdog is required. Original syscall dispatch, guard results and
instructions remain unchanged; the validated font epilogue restores counting.
"""
import collections
import time

DEFAULT_COUNT=31337
SCAN_EPILOGUE=0x706d04


class SyscallBoundaryQuantum:
 def __init__(self,emit,started,discovery,advisory_us=20000,clock=time.monotonic,post_count=DEFAULT_COUNT,scope="startup_through_font"):
  if not isinstance(advisory_us,int) or not 1<=advisory_us<=20000:raise ValueError('Advisory must be1..20000us')
  if post_count not in (31337,313370):raise ValueError('Post-font count must be finite selected arm')
  if scope not in ("startup_through_font","main_startup"):raise ValueError("Unknown cooperative scope")
  self.scope=scope
  self.emit=emit;self.started=started;self.discovery=discovery;self.advisory_us=advisory_us;self.clock=clock
  self.counts=collections.Counter();self.installed=False;self.active=False;self.last_count_mode=None;self.slice_started=None
  self.post_count=post_count;self.startup_scope_completed=False;self.post_active=False;self.suppressed_frame=None
  self.slice_metrics={}
  self.max_main_slice_seconds=0.0
 def main(self,q):
  try:return self.discovery.main_tid is not None and q.os.thread_management.cur_thread.id==self.discovery.main_tid
  except AttributeError:return False
 def install(self,q):
  if self.installed:raise RuntimeError('Boundary scheduling already installed')
  if not callable(getattr(q.uc,'ctl_flush_tb',None)):raise RuntimeError('Boundary scheduling requires translation-cache flush')
  expected=self.discovery.expected(SCAN_EPILOGUE);actual=bytes(q.mem.read(SCAN_EPILOGUE,4))
  if expected!=actual:raise RuntimeError('Boundary scheduling font epilogue bytes differ')
  self.q=q;self.original=q.emu_start;self.original_load_syscall=q.os.load_syscall
  if self.scope=="startup_through_font":q.hook_address(self.finish_boosted_phase,SCAN_EPILOGUE)
  q.emu_start=self.emu_start;q.os.load_syscall=self.load_syscall;self.installed=True
  self.emit('syscall_boundary_quantum_installed',advisory_us=self.advisory_us,original_count=DEFAULT_COUNT,
            scope=self.scope,condition='identified main + exact31337count + no explicit timeout; yield only after original syscall dispatcher returns',
            phase_end_address=hex(SCAN_EPILOGUE) if self.scope=="startup_through_font" else None,phase_end_bytes=expected.hex(),original_app_sha256=self.discovery.app_sha256,
            post_font_count=self.post_count,cpu_only_stretches_may_exceed_advisory=True,requires_independent_watchdog=True,
            original_syscall_dispatch_and_guards_retained=True,original_instructions_unchanged=True)
 def load_syscall(self,*args,**kwargs):
  # Complete dispatch, interceptors, return-register writes and deferred
  # scheduler callback setup before requesting a cooperative stop.
  result=self.original_load_syscall(*args,**kwargs)
  self.counts['original_dispatch_returns']+=1
  if self.active and self.main(self.q):
   self.counts['main_dispatch_returns']+=1
   if self.clock()-self.slice_started>=self.advisory_us/1000000:
    self.counts['advisory_syscall_stops']+=1;self.q.emu_stop()
  return result
 def emu_start(self,begin,end,timeout=0,count=0):
  q=self.q;eligible=(count==DEFAULT_COUNT and timeout==0 and self.main(q))
  boost=eligible and not self.startup_scope_completed
  self.counts['slices']+=1;self.counts['uncounted_main_slices' if boost else 'unchanged_slices']+=1
  if boost:count=0
  elif eligible and self.startup_scope_completed:
   count=self.post_count;self.counts['post_font_selected_slices']+=1
   if not self.post_active:
    self.post_active=True;self.emit('post_font_count_active',host_elapsed=round(self.clock()-self.started,6),thread=self.discovery.main_tid,effective_count=count,timeout=timeout,validated_epilogue_observed=True)
  count_mode=count>0
  if self.last_count_mode is None or count_mode!=self.last_count_mode:
   q.uc.ctl_flush_tb();self.counts['translation_cache_flushes']+=1
  self.last_count_mode=count_mode;self.active=boost;self.slice_started=self.clock()
  tid=getattr(q.os.thread_management.cur_thread,'id',None)
  phase='post_font' if self.startup_scope_completed else 'font' if self.discovery.frames.get('original_font_scan') is not None else 'pre_font'
  key=phase+':'+str(tid);metric=self.slice_metrics.setdefault(key,{'phase':phase,'thread':tid,'slices':0,'boosted_slices':0,'emu_start_seconds':0.0,'max_slice_seconds':0.0})
  metric['slices']+=1;metric['boosted_slices']+=int(boost)
  try:return self.original(begin,end,timeout=timeout,count=count)
  except Exception as exc:
   context={'error_type':type(exc).__name__,'error':str(exc),'read_only':True,'thread':tid,
            'begin':hex(begin),'count':count,'timeout':timeout,'capture':'synchronous before scheduler context restore'}
   try:
    context['registers']={n:hex(q.arch.regs.read(n)) for n in ['r'+str(i) for i in range(13)]+['sp','lr','pc','cpsr']}
    context['pointer_cells']={}
    for n in ('r0','r1','r3','r4','r5','sp'):
     address=q.arch.regs.read(n);cell={'address':hex(address),'alignment_mod4':address&3}
     try:cell['bytes']=bytes(q.mem.read(address,64)).hex()
     except Exception as read_error:cell['read_error']=repr(read_error)
     context['pointer_cells'][n]=cell
    context['instruction_bytes']=bytes(q.mem.read(q.arch.regs.arch_pc-8,24)).hex()
    context['memory_maps']=q.mem.get_mapinfo()
   except Exception as diagnostic_error:context['diagnostic_error']=repr(diagnostic_error)
   try:self.emit('synchronous_emulator_exception_context',**context)
   except Exception:pass
   raise
  finally:
   elapsed=self.clock()-self.slice_started
   metric['emu_start_seconds']+=elapsed;metric['max_slice_seconds']=max(metric['max_slice_seconds'],elapsed)
   if boost:self.max_main_slice_seconds=max(self.max_main_slice_seconds,elapsed)
   self.active=False
 def finish_boosted_phase(self,q):
  if self.scope=="main_startup":return
  frame=self.discovery.frames.get('original_font_scan')
  if self.startup_scope_completed or not self.active or not self.main(q) or frame is None:return
  self.suppressed_frame=frame;self.startup_scope_completed=True;self.active=False;self.counts['epilogue_slice_stops']+=1
  self.emit('font_scan_quantum_reverted',host_elapsed=round(self.clock()-self.started,6),reason='validated original scan epilogue; cooperative slice ends here',pc=hex(q.arch.regs.arch_pc),following_slices_use_selected_count=self.post_count)
  q.emu_stop()
 def summary(self):
  return {'fixture':'syscall_boundary_quantum_candidate','advisory_us':self.advisory_us,'counts':dict(self.counts),
          'scope':self.scope,'mode':'syscall_boundary','startup_scope_completed':self.startup_scope_completed,
          'post_font_count':self.post_count,'post_font_active':self.post_active,'last_count_mode':self.last_count_mode,
          'slice_metrics':{key:{**row,'emu_start_seconds':round(row['emu_start_seconds'],6),'max_slice_seconds':round(row['max_slice_seconds'],6)} for key,row in self.slice_metrics.items()},
          'max_main_slice_seconds':self.max_main_slice_seconds,'cpu_only_stretches_may_exceed_advisory':True,
          'requires_independent_watchdog':True,'original_dispatch_and_guards_retained':True,
          'original_instructions_unchanged':True,'firmware_validation':'Not yet established'}
