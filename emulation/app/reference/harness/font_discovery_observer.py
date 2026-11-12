"""Read-only, byte-validated original-app font discovery and matched returns.

The original app uses its own directory/XML/FreeType enumeration. This observer
makes no fontconfig API/cache assumption and never changes guest registers or
memory. Function entry, saved return PC and restored SP prove caller return.
"""
from pathlib import Path
import collections, hashlib, struct, time
from elftools.elf.elffile import ELFFile

APP_SHA256 = '3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464'
# Entry: (name, final POP instruction, count of pushed 32-bit registers).
FRAMES = {
 0x702c38: ('font_directory_discovery', 0x702ccc, 5),
 0x706948: ('original_font_scan', 0x706d08, 9),
 0x71ce28: ('font_manager_constructor', 0x71cecc, 3),
}
POINTS = {a:v[0]+'_entry' for a,v in FRAMES.items()}
POINTS.update({v[1]:v[0]+'_before_pop' for v in FRAMES.values()})
POINTS.update({0x706ab4:'scan_FT_New_Face_call',0x706ab8:'scan_FT_New_Face_return',
               0x71cb90:'selected_FT_New_Face_call',0x71cb94:'selected_FT_New_Face_return'})

class FontDiscoveryObserver:
 def __init__(self,emit,started,app_path):
  self.emit=emit;self.started=started;self.app_path=Path(app_path)
  self.app_sha256=hashlib.sha256(self.app_path.read_bytes()).hexdigest()
  if self.app_sha256!=APP_SHA256:raise RuntimeError('Font discovery app identity differs')
  with self.app_path.open('rb') as f:
   e=ELFFile(f);self.segments=[(s['p_vaddr'],s.data()) for s in e.iter_segments() if s['p_type']=='PT_LOAD']
  self.main_tid=None;self.installed={};self.frames={};self.completed=[]
  self.counts=collections.Counter();self.ft_pending={};self.ft_results=[];self.continuations=[]
 def expected(self,address):
  for start,data in self.segments:
   if start<=address and address+4<=start+len(data):return data[address-start:address-start+4]
  raise RuntimeError('Font observer point outside original app '+hex(address))
 def install_point(self,q,address,name):
  if address in self.installed:return
  expected=self.expected(address);actual=bytes(q.mem.read(address,4))
  if actual!=expected:raise RuntimeError('Font observer loaded bytes differ '+hex(address))
  self.installed[address]={'name':name,'bytes':expected.hex()}
  q.hook_address(self.checkpoint(address,name),address)
 def install(self,q):
  for address,name in POINTS.items():self.install_point(q,address,name)
  self.emit('font_discovery_hooks_installed',read_only=True,app_sha256=self.app_sha256,
            points={hex(a):v for a,v in self.installed.items()},
            scope='Original app XML directory discovery and direct FreeType scan; no assumed Fc APIs')
 def identify_main(self,q):
  self.main_tid=q.os.thread_management.cur_thread.id
  self.emit('font_discovery_main_identified',thread=self.main_tid,pc=hex(q.arch.regs.arch_pc),source='native original main first entry')
 def context(self,q):
  return {'host_elapsed':round(time.monotonic()-self.started,6),'thread':q.os.thread_management.cur_thread.id,
          'pc':hex(q.arch.regs.arch_pc),'lr':hex(q.arch.regs.lr),'sp':hex(q.arch.regs.sp),'r0':hex(q.arch.regs.r0)}
 def checkpoint(self,address,name):
  def cb(q):
   if self.main_tid is None or q.os.thread_management.cur_thread.id!=self.main_tid:return
   self.counts[name]+=1;row=self.context(q)
   if address in FRAMES:
    key,pop,nregs=FRAMES[address];caller=q.arch.regs.lr
    if key in self.frames:raise RuntimeError('Unexpected reentrant main font frame '+key)
    self.frames[key]={'entry':hex(address),'entry_sp':q.arch.regs.sp,'caller':caller,'before_pop':pop,
                      'pushed_registers':nregs,'object':q.arch.regs.r0,'ready':False,'entry_context':row}
    if caller&3:raise RuntimeError('Unexpected non-ARM font caller '+hex(caller))
    self.install_point(q,caller,key+'_caller_return')
    # A subsequent instruction after the exact caller return is separately
    # observed; it is not inferred from a cache file or a before-POP hook.
    self.install_point(q,caller+4,key+'_caller_subsequent_execution')
    self.emit('font_discovery_function_entry',function=key,frame=self.frames[key])
   for key,frame in list(self.frames.items()):
    if address==frame['before_pop']:
     nregs=frame['pushed_registers'];saved=struct.unpack('<I',bytes(q.mem.read(q.arch.regs.sp+4*(nregs-1),4)))[0]
     frame.update(saved_caller=hex(saved),ready=(q.arch.regs.sp==frame['entry_sp']-4*nregs and saved==frame['caller']))
     self.emit('font_discovery_before_pop',function=key,matched_saved_return=frame['ready'],saved_caller=hex(saved),context=row)
    if address==frame['caller']:
     result={**frame,'matched_return':bool(frame['ready'] and q.arch.regs.sp==frame['entry_sp']),'return_context':row}
     if key=='original_font_scan':
      try:result['font_face_count']=struct.unpack('<I',bytes(q.mem.read(frame['object']+16,4)))[0]
      except Exception as ex:result['font_face_count_error']=str(ex)[:160]
     self.completed.append(result);self.frames.pop(key)
     self.emit('font_discovery_function_return',function=key,result=result)
   for result in self.completed:
    if address==result['caller']+4 and result['matched_return'] and not result.get('subsequent_execution'):
     result['subsequent_execution']=row;self.continuations.append({'function':next((v[0] for a,v in FRAMES.items() if hex(a)==result['entry']),None),'context':row})
     self.emit('font_discovery_subsequent_execution',function_entry=result['entry'],matched_caller_return=result['return_context'],context=row)
   if address in (0x706ab4,0x71cb90):
    key='scan' if address==0x706ab4 else 'selected'
    try:path=q.mem.string(q.arch.regs.r1)
    except Exception as ex:path='unreadable:'+str(ex)[:100]
    self.ft_pending[key]={'path':path,'face_index':q.arch.regs.r2,'face_output_pointer':q.arch.regs.r3,'entry_sp':q.arch.regs.sp,'call_context':row}
    self.emit('font_discovery_face_call',source=key,**self.ft_pending[key])
   if address in (0x706ab8,0x71cb94):
    key='scan' if address==0x706ab8 else 'selected';pending=self.ft_pending.pop(key,None)
    if pending:
     result={**pending,'return_r0':q.arch.regs.r0,'matched_sp':q.arch.regs.sp==pending['entry_sp'],'return_context':row}
     self.ft_results.append(result);self.emit('font_discovery_face_return',source=key,result=result)
  return cb
 def summary(self):
  return {'main_tid':self.main_tid,'app_sha256':self.app_sha256,'pending_frames':self.frames,'completed_returns':self.completed,
          'face_results':self.ft_results,'pending_faces':self.ft_pending,'subsequent_executions':self.continuations,
          'counts':dict(self.counts),'read_only':True}
