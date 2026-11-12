"""Finite local scheduling comparison; original app/fonts remain unchanged.

Default font_scan preserves the established phase-only fixture. main_startup
uses finite timed slices for identified main throughout the bounded run; workers
and explicit nondefault counts are unchanged. Syscall stops remain effective.
"""
import collections, time

DEFAULT_COUNT = 31337
MULTIPLIER = 100
SCAN_EPILOGUE = 0x706d04

class FontScanQuantum:
 def __init__(self,emit,started,discovery,multiplier=MULTIPLIER,mode="instruction_count",time_budget_us=20000,scope="font_scan",post_count=DEFAULT_COUNT):
  if not isinstance(multiplier,int) or not 1<multiplier<=100:raise ValueError('Finite multiplier must be 2..100')
  if mode not in ('instruction_count','time_budget'):raise ValueError('Unknown font quantum mode')
  if scope not in ('font_scan','main_startup','startup_through_font'):raise ValueError('Unknown scheduling scope')
  if scope!='font_scan' and mode!='time_budget':raise ValueError('Startup scopes require finite timed slices')
  if not isinstance(time_budget_us,int) or not 1<=time_budget_us<=20000:raise ValueError('Time budget must be finite 1..20000us')
  if post_count not in (31337,313370):raise ValueError('Post-font count must be finite selected arm')
  self.post_count=post_count;self.post_active=False
  self.emit=emit;self.started=started;self.discovery=discovery;self.multiplier=multiplier
  self.mode=mode;self.time_budget_us=time_budget_us;self.last_count_mode=None
  self.scope=scope;self.slice_metrics={};self.font_scan_completed=False
  self.startup_scope_completed=False
  self.counts=collections.Counter();self.active=False;self.current_boosted=False
  self.suppressed_frame=None;self.original=None;self.q=None;self.installed=False
 def main(self,q):
  try:return self.discovery.main_tid is not None and q.os.thread_management.cur_thread.id==self.discovery.main_tid
  except AttributeError:return False
 def install(self,q):
  if self.installed:raise RuntimeError('Font scan quantum already installed')
  expected=self.discovery.expected(SCAN_EPILOGUE);actual=bytes(q.mem.read(SCAN_EPILOGUE,4))
  if expected!=actual:raise RuntimeError('Font scan quantum epilogue bytes differ')
  if self.mode=='time_budget' and not callable(getattr(q.uc,'ctl_flush_tb',None)):raise RuntimeError('Timed mode requires native translation-cache flush')
  self.q=q;self.original=q.emu_start
  if self.scope!='main_startup':q.hook_address(self.finish_boosted_phase,SCAN_EPILOGUE)
  q.emu_start=self.emu_start;self.installed=True
  self.emit('font_scan_quantum_installed',original_count=DEFAULT_COUNT,multiplier=self.multiplier,
            finite_boosted_count=DEFAULT_COUNT*self.multiplier,mode=self.mode,finite_time_budget_us=self.time_budget_us,phase_end_address=hex(SCAN_EPILOGUE),
            phase_end_bytes=expected.hex(),original_app_sha256=self.discovery.app_sha256,
            scope=self.scope,condition='identified main + count exactly31337'+(' + pending original_font_scan frame' if self.scope=='font_scan' else ' until validated original font-scan epilogue' if self.scope=='startup_through_font' else ' throughout bounded startup'),
            original_syscall_stops_retained=True,requires_independent_watchdog=True)
 def emu_start(self,begin,end,timeout=0,count=0):
  q=self.q;frame=self.discovery.frames.get('original_font_scan')
  if any(r.get('entry')=='0x706948' and r.get('matched_return') for r in getattr(self.discovery,'completed',())):self.font_scan_completed=True
  phase='font' if frame is not None else 'post_font' if self.font_scan_completed else 'pre_font'
  if frame is None:
   self.suppressed_frame=None
   if self.active and self.scope=='font_scan':
    self.active=False;self.emit('font_scan_quantum_reverted',host_elapsed=round(time.monotonic()-self.started,6),reason='font scan frame completed')
  phase_allowed=(self.scope=='main_startup' or (self.scope=='startup_through_font' and not self.startup_scope_completed) or (self.scope=='font_scan' and frame is not None and frame is not self.suppressed_frame))
  post_selected=(self.startup_scope_completed and self.main(q) and count==DEFAULT_COUNT and timeout==0)
  boost=(count==DEFAULT_COUNT and timeout==0 and self.main(q) and phase_allowed)
  self.counts['calls']+=1
  if boost:
   if self.mode=='time_budget':
    count=0;timeout=min(timeout,self.time_budget_us) if timeout>0 else self.time_budget_us
   else:count*=self.multiplier
   self.counts['boosted_main_slices']+=1
   if not self.active:
    self.active=True;self.emit('font_scan_quantum_active',host_elapsed=round(time.monotonic()-self.started,6),
       thread=self.discovery.main_tid,begin=hex(begin),original_count=DEFAULT_COUNT,effective_count=count,effective_timeout_us=timeout,mode=self.mode,frame=frame)
  else:
   if post_selected:
    count=self.post_count;self.counts['post_font_selected_slices']+=1
    if not self.post_active:
     self.post_active=True;self.emit('post_font_count_active',host_elapsed=round(time.monotonic()-self.started,6),thread=self.discovery.main_tid,effective_count=count,timeout=timeout,validated_epilogue_observed=True)
   else:self.counts['unchanged_slices']+=1
  # Unicorn's internal count hook needs freshly translated blocks on EVERY
  # count-enabled/disabled transition, including interleaved worker slices.
  if self.mode=='time_budget':
   count_mode=count>0
   if self.last_count_mode is None or count_mode!=self.last_count_mode:
    q.uc.ctl_flush_tb();self.counts['translation_cache_flushes']+=1
   self.last_count_mode=count_mode
  self.current_boosted=boost
  tid=getattr(q.os.thread_management.cur_thread,'id',None)
  key=phase+':'+str(tid);metric=self.slice_metrics.setdefault(key,{'phase':phase,'thread':tid,'slices':0,'boosted_slices':0,'emu_start_seconds':0.0})
  metric['slices']+=1;metric['boosted_slices']+=int(boost);slice_started=time.monotonic()
  try:return self.original(begin,end,timeout=timeout,count=count)
  finally:
   metric['emu_start_seconds']+=time.monotonic()-slice_started
   self.current_boosted=False
 def finish_boosted_phase(self,q):
  if self.scope=='main_startup':return
  frame=self.discovery.frames.get('original_font_scan')
  if not self.current_boosted or not self.main(q) or frame is None or frame is self.suppressed_frame:return
  self.suppressed_frame=frame;self.active=False;self.counts['epilogue_slice_stops']+=1
  if self.scope=='startup_through_font':self.startup_scope_completed=True
  self.emit('font_scan_quantum_reverted',host_elapsed=round(time.monotonic()-self.started,6),
            reason='validated original scan epilogue; remaining enlarged slice ends here',pc=hex(q.arch.regs.arch_pc),
            following_slices_use_original_count=True)
  q.emu_stop()
 def summary(self):
  return {'fixture':'main_font_scan_instruction_quantum','scope':self.scope,'mode':self.mode,'finite_time_budget_us':self.time_budget_us,'last_count_mode':self.last_count_mode,'multiplier':self.multiplier,'original_count':DEFAULT_COUNT,
          'startup_scope_completed':self.startup_scope_completed,'post_font_count':self.post_count,'post_font_active':self.post_active,
          'slice_metrics':{key:{**row,'emu_start_seconds':round(row['emu_start_seconds'],6)} for key,row in self.slice_metrics.items()},'slice_metric_basis':'Host elapsed inside original emu_start, excluding translation-cache flush and outer scheduler; phase sampled at slice entry; not guest CPU time',
          'finite_boosted_count':DEFAULT_COUNT*self.multiplier,'counts':dict(self.counts),'active':self.active,
          'current_boosted':self.current_boosted,'epilogue_suppressed':self.suppressed_frame is not None,
          'app_fonts_and_libraries_unchanged':True,'original_syscall_stops_retained':True,'installed_runtime_unchanged':True}
