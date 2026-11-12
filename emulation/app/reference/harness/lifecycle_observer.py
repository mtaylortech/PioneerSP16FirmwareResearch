"""Read-only startup lifecycle boundaries. Pending dispatch never proves return."""
import json,struct
from pathlib import Path
HOOKS=(0xb3ac4,0xb4034,0xb404c,0x56e7bc,0xb4050,0xb405c,
       0x69850c,0x698544,0x571d24,0x57222c,0x698548,0x69854c,
       0x6985a4,0xb4060,0xb4068,0xb4094,0x69afc0,0x69b04c,
       0x69affc,0x69b000,0x69b004,0x6985a8,0x6985b8,0x6985bc,
       0x698690,0x57263c,0x5726fc,0x572714,0x572774)
class LifecycleObserver:
 def __init__(self,emit,discovery,manifest=None):
  self.emit,self.discovery=emit,discovery
  self.map=manifest or json.loads((Path(__file__).parent/'lifecycle-map.json').read_text())
  self.points={int(a,16):bytes.fromhex(b) for a,b in self.map['points'].items()}
  self.handles={};self.main=None;self.frames={};self.receipts=[];self.state='unobserved';self.dispatch=None;self.retired=False
  self.inner_returned=False;self.inner_continued=False;self.branch_success=None;self.terminal_cleanup=[]
 def require(self,condition,message):
  if not condition:
   self.state='mismatch';self.emit('lifecycle_mismatch',reason=message,pending=self.frames)
   raise RuntimeError('Lifecycle '+message)
 def validate(self,q,a):
  self.require(self.discovery.expected(a)==self.points[a] and bytes(q.mem.read(a,4))==self.points[a],'original bytes differ '+hex(a))
 def install(self,q):
  self.require(not self.handles,'already installed')
  for a in self.points:self.validate(q,a)
  for a in HOOKS:self.handles[a]=q.hook_address(lambda g,a=a:self.visit(g,a),a)
  self.emit('lifecycle_hooks_validated',points={hex(a):self.points[a].hex() for a in HOOKS},read_only=True)
 def word(self,q,a):return struct.unpack('<I',bytes(q.mem.read(a,4)))[0]
 def record(self,kind,**row):
  self.receipts.append(dict(kind=kind,**row));self.emit('lifecycle_'+kind,**row)
 def take(self,q,name,caller,obj=None):
  r=q.arch.regs
  self.require(name not in self.frames,'duplicate '+name)
  self.require(r.lr==caller,'LR '+name)
  self.frames[name]=dict(thread=self.main,sp=r.sp,caller=caller,object=obj,pop=False)
  self.record('entry',function=name,frame=dict(self.frames[name]))
 def pop(self,q,name,pushed):
  f=self.frames.get(name);self.require(f is not None,'missing entry '+name)
  self.require(q.arch.regs.sp==f['sp']-4*pushed,'epilogue SP '+name)
  self.require(self.word(q,q.arch.regs.sp+4*(pushed-1))==f['caller'],'saved LR '+name)
  f['pop']=True;self.record('before_pop',function=name,frame=dict(f))
 def returned(self,q,name):
  f=self.frames.get(name);self.require(f is not None and f['pop'],'return without validated epilogue '+name)
  self.require(q.arch.regs.sp==f['sp'],'restored SP '+name)
  self.frames.pop(name);self.record('return',function=name,frame=f,matched_thread_sp=True,result=q.arch.regs.r0)
  return f
 def visit(self,q,a):
  if self.retired:return
  r=q.arch.regs;tid=q.os.thread_management.cur_thread.id
  if a==0xb3ac4:self.validate(q,a)
  if a==0xb3ac4:
   self.require(self.main is None,'duplicate main');self.main=tid;self.state='main_entered';self.record('main',thread=tid,sp=r.sp);return
  if tid!=self.main:return
  self.validate(q,a)
  if a in (0x698690,0x57263c,0x5726fc,0x572714,0x572774):
   name='wrapper_initializer' if a==0x698690 else 'application_initializer'
   self.require(name in self.frames,'cleanup without owned initializer frame')
   row=dict(function=name,pc=hex(a),target='0x1111c',symbol='__cxa_end_cleanup',thread=tid,sp=r.sp,pending=dict(self.frames))
   self.terminal_cleanup.append(row);self.record('exception_cleanup_continuation',**row)
   self.state='exception_cleanup_observed';return
  if a==0xb4034:
   self.require(self.state=='main_entered','main wrapper order');self.wrapper_sp=r.sp-24;self.state='wrapper_entered'
  elif a==0xb404c:
   self.require(r.sp==self.wrapper_sp and r.r3==0x56e7bc,'factory call target/SP');self.factory_sp=r.sp
  elif a==0x56e7bc:
   self.require(r.sp==self.factory_sp and r.lr==0xb4050,'factory entry frame')
  elif a==0xb4050:
   self.require(r.sp==self.factory_sp,'factory return SP');self.obj=r.r0
   self.require(self.word(q,self.obj)==0x9327f0,'constructed application vtable');self.record('factory_return',object=self.obj,vtable='0x9327f0')
  elif a==0xb405c:
   self.require(r.sp==self.wrapper_sp and r.r3==0x7552b0 and r.r0==self.obj,'initializer virtual call target/object/SP');self.state='initializer_pending'
  elif a==0x69850c:
   self.require(self.state=='initializer_pending' and r.r0==self.obj,'initializer wrapper entry');self.take(q,'wrapper_initializer',0xb4060,self.obj)
  elif a==0x698544:
   f=self.frames.get('wrapper_initializer');self.require(f is not None and r.sp==f['sp']-40 and r.r5==0x571d24 and r.r0==self.obj,'application initialize call target/object/SP')
   self.inner_sp=r.sp
  elif a==0x571d24:
   self.require(r.sp==self.inner_sp and r.r0==self.obj,'application initialize entry SP/object');self.take(q,'application_initializer',0x698548,self.obj)
  elif a==0x57222c:self.pop(q,'application_initializer',9)
  elif a==0x698548:
   self.returned(q,'application_initializer');self.inner_returned=True;self.state='application_initializer_returned'
  elif a==0x69854c:
   self.require(self.state=='application_initializer_returned' and r.sp==self.inner_sp,'application subsequent continuation');self.inner_continued=True;self.record('initializer_continuation',pc=hex(a))
  elif a in (0x6985a8,0x6985b8,0x6985bc):
   f=self.frames.get('wrapper_initializer');self.require(f is not None and r.sp==f['sp']-40,'wrapper pre-initializer branch SP')
   self.record('pre_initializer_check',pc=hex(a),result=r.r0,z=bool(r.cpsr&(1<<30)))
  elif a==0x6985a4:self.pop(q,'wrapper_initializer',5)
  elif a==0xb4060:
   self.returned(q,'wrapper_initializer');self.result=r.r0
   self.require(not self.result or self.inner_returned and self.inner_continued,'success wrapper return without matched application return/continuation')
   self.state='initializer_returned' if self.result else 'initializer_rejected'
   if not self.result:self.record('initializer_rejected',application_initializer_observed=self.inner_returned)
  elif a==0xb4068:
   self.require(self.state in ('initializer_returned','initializer_rejected') and r.sp==self.wrapper_sp,'post-init branch SP/order')
   self.require(bool(r.cpsr&(1<<30))==(self.result==0),'post-init comparison Z')
   self.branch_success=self.result!=0
   self.record('post_init_branch',result=self.result,success_branch=self.result!=0)
  elif a==0xb4094:
   self.require(self.state=='initializer_returned' and self.result!=0 and self.branch_success is True and r.sp==self.wrapper_sp,'steady dispatch call order/SP');self.manager=r.r0;self.state='dispatch_called'
  elif a==0x69afc0:
   # The same loop can be called recursively during initialization. Observe
   # it sparsely without claiming that any pending initializer returned.
   if self.state!='dispatch_called':
    if not getattr(self,'nested_seen',False):
     self.record('dispatch_with_pending_initialization',lr=r.lr,sp=r.sp,pending=dict(self.frames));self.nested_seen=True
    return
   self.require(r.lr==0xb4098 and r.sp==self.wrapper_sp and r.r0==self.manager,'dispatch entry LR/SP/object')
   self.dispatch=dict(sp=r.sp-400,caller=r.lr,manager=r.r0);self.state='dispatch_entered';self.record('dispatch_entry',frame=self.dispatch)
  elif a in (0x69b04c,0x69affc,0x69b000,0x69b004):
   if self.dispatch is None:return
   self.require(r.sp==self.dispatch['sp'] and r.r9==self.manager,'dispatch body SP/object')
   self.require(self.word(q,r.sp+396)==0xb4098,'dispatch saved caller')
   if a==0x69b04c:
    if not getattr(self,'loop_seen',False):self.record('dispatch_loop',pc=hex(a));self.loop_seen=True
   elif a==0x69affc:
    self.require(not getattr(self,'xp',None),'overlapping XPending');self.xp=dict(thread=tid,sp=r.sp)
   elif a==0x69b000:
    self.require(getattr(self,'xp',None)==dict(thread=tid,sp=r.sp),'XPending return frame');self.xp=None;self.xp_return=r.r0
    self.record('dispatch_xpending_return',result=r.r0,thread=tid,sp=r.sp,matched_thread_sp=True)
   else:
    self.require(hasattr(self,'xp_return'),'dispatch continuation without XPending return')
    self.require(bool(r.cpsr&(1<<30))==(self.xp_return==0),'dispatch XPending CMP Z')
    self.state='mapped_initializer_returned_and_dispatch_observed'
    self.record('boundary_complete',full_startup_requires_fresh_async_readiness_and_owned_HOME=True)
    for h in self.handles.values():q.hook_del(h)
    self.handles.clear();self.retired=True
 def summary(self):
  missing=('application initializer return 0x698548' if 'application_initializer' in self.frames else 'initializer wrapper return 0xb4060' if 'wrapper_initializer' in self.frames else 'application initialize entry 0x571d24' if self.state=='initializer_pending' else 'attributed dispatch entry 0x69afc0' if self.state=='initializer_returned' else 'matched dispatch XPending and subsequent CMP' if self.dispatch and not self.retired else None)
  if self.state=='unobserved':missing='original main entry 0xb3ac4'
  if self.state=='wrapper_entered':missing='factory return and initialization wrapper entry'
  return dict(state=self.state,pending=self.frames,first_missing_boundary=missing,dispatch=self.dispatch,receipts=self.receipts,terminal_cleanup=self.terminal_cleanup,initializer_rejected=self.state=='initializer_rejected',retired=self.retired,read_only=True,full_startup_proved=False)

class DisabledEventPump:
 """No packet/event detail hooks for the no-input lifecycle question."""
 def install(self,q):pass
 def before_read(self,*args):return None
 def after_read(self,*args):pass
 def summary(self):return dict(enabled=False,reason='completed input discovery; no-input lifecycle scope')
