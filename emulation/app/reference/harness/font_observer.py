"""Read-only main-thread font file progress; sparse syscall metadata only."""
import collections, time

FONT_NAMES=('open','openat','read','lseek','_llseek','close')

class FontObserver:
 def __init__(self,emit,started,gate=lambda:True):
  self.emit=emit;self.started=started;self.gate=gate;self.main_tid=None
  self.pending={};self.files={};self.counts=collections.Counter();self.last_emit={}
 def identify_main(self,q):self.main_tid=q.os.thread_management.cur_thread.id
 def main(self,q):return self.main_tid is not None and q.os.thread_management.cur_thread.id==self.main_tid and self.gate()
 def fd_info(self,q,fd):
  row={'descriptor':fd}
  try:
   obj=q.os.fd[fd];row.update(object_type=type(obj).__name__,name=str(getattr(obj,'name',None)))
   for label,method in (('offset','tell'),('size','fstat')):
    try:
     v=getattr(obj,method)();row[label]=v.st_size if label=='size' else v
    except Exception as ex:row[label+'_error']=str(ex)[:120]
  except Exception as ex:row['error']=str(ex)[:160]
  return row
 def context(self,q):
  return {'thread':q.os.thread_management.cur_thread.id,'pc':hex(q.arch.regs.arch_pc),'lr':hex(q.arch.regs.lr),'sp':hex(q.arch.regs.sp)}
 def mappings(self,q):
  result=[]
  for a,b,perm,label,*other in q.mem.map_info:
   if a<=0x901fca20<b or a<=q.arch.regs.arch_pc<b:
    result.append({'start':hex(a),'end':hex(b),'permissions':str(perm),'label':str(label)})
  return result
 def syscall_enter(self,name):
  def cb(q,*values):
   if not self.main(q):return
   now=time.monotonic()-self.started
   if name in ('open','openat'):
    try:path=q.mem.string(values[1] if name=='openat' else values[0])
    except Exception:return
    if '/fonts/' not in path and not path.endswith('.bdf'):return
    row={'name':name,'entered_elapsed':now,'path':path,'arguments':list(values),**self.context(q)}
   else:
    if not values:return
    fd=values[0];info=self.fd_info(q,fd)
    if '/fonts/' not in info.get('name','') and '.bdf' not in info.get('name',''):return
    row={'name':name,'entered_elapsed':now,'file_before':info,'arguments':list(values),**self.context(q)}
   self.pending[name]=row
  return cb
 def syscall_exit(self,name):
  def cb(q,*values):
   if not self.main(q):return
   row=self.pending.pop(name,None)
   if row is None:return
   result=values[-1] if values else None;now=time.monotonic()-self.started
   row.update(result=result,duration_seconds=round(now-row['entered_elapsed'],6))
   if name in ('open','openat'):
    if isinstance(result,int) and result>=0:
     row['file_after']=self.fd_info(q,result);self.files[result]={'path':row['path'],'reads':0,'bytes_read':0,'last_read':None,'last_seek':None}
    self.emit('font_open',**row);return
   fd=row['file_before']['descriptor'];row['file_after']=self.fd_info(q,fd)
   state=self.files.setdefault(fd,{'path':row['file_before'].get('name'),'reads':0,'bytes_read':0,'last_read':None,'last_seek':None})
   if name=='read':
    state['reads']+=1
    if isinstance(result,int) and result>0:state['bytes_read']+=result
    state['last_read']=row
   elif name in ('lseek','_llseek'):state['last_seek']=row
   self.counts[name]+=1;key=(name,fd);count=self.counts[name]
   if count<=3 or now-self.last_emit.get(key,-10)>=5 or (name=='read' and result==0):
    self.last_emit[key]=now
    self.emit('font_file_progress',operation=name,reads=state['reads'],bytes_read=state['bytes_read'],file=row,selected_library_mappings=self.mappings(q) if count<=3 else None)
  return cb
 def summary(self):return {'main_tid':self.main_tid,'files':self.files,'counts':dict(self.counts),'pending':self.pending,'read_only':True}
