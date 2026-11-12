"""Read-only shipped-library entry hooks and validated Display buffer snapshots."""
from pathlib import Path
import collections,json,struct,time
BASE=Path(__file__).resolve().parent
class DisplayDiagnostics:
 def __init__(self,emit,started,fixture):
  self.emit=emit;self.started=started;self.fixture=fixture;self.layout=json.loads((BASE/'xlib-layout.json').read_text());self.display=None;self.created_id=None;self.installed=False;self.near_stop=False;self.counts=collections.Counter()
 def install(self,q):
  if self.installed:return
  libraries=[('libX11',self.layout['entry_points']),('libxcb.so',self.layout['xcb']['entry_points'])]
  pending=[];mapped=[]
  for fragment,symbols in libraries:
   candidates=[a for a,b,perm,label,*other in q.mem.map_info if fragment in label and bytes(q.mem.read(a,4))==b'\x7fELF']
   if len(candidates)!=1:raise RuntimeError('Cannot derive unique ELF load base for '+fragment)
   base=candidates[0];mapped.append({'library':fragment,'base':hex(base)})
   for name,row in symbols.items():
    address=base+row['elf_vaddr'];expected=bytes.fromhex(row['entry_bytes'])
    if bytes(q.mem.read(address,len(expected)))!=expected:raise RuntimeError('Loaded entry bytes differ: '+name)
    pending.append((name,address))
  for name,address in pending:q.hook_address(self.trace(name),address)
  xbase=mapped[0]['base']
  for name,row in self.layout['checkpoints'].items():
   address=int(xbase,16)+row['elf_vaddr']
   if bytes(q.mem.read(address,4))!=bytes.fromhex(row['entry_bytes']):raise RuntimeError('Checkpoint bytes differ')
   q.hook_address(self.checkpoint(name),address)
  self.installed=True
  self.emit('display_library_hooks',maps=mapped,entries={n:hex(a) for n,a in pending},entry_bytes_verified=True)
 def trace(self,name):
  def callback(q):
   tid=q.os.thread_management.cur_thread.id;self.counts[name]+=1
   if self.counts[name]<=20:
    self.emit('display_library_entry',name=name,count=self.counts[name],thread=tid,pc=hex(q.arch.regs.arch_pc),lr=hex(q.arch.regs.lr),arguments=[hex(q.arch.regs.read('r'+str(i))) for i in range(4)])
   if name=='XCreateWindow':self.display=q.arch.regs.r0
   self.maybe_near_stop(q)
  return callback
 def checkpoint(self,name):
  def callback(q):
   self.created_id=q.arch.regs.r5 if name=='XCreateWindow_before_unlock' else q.arch.regs.r0
   self.snapshot(q,name)
  return callback
 def maybe_near_stop(self,q):
  if self.display and not self.near_stop and time.monotonic()-self.started>=170:
   self.near_stop=True;self.snapshot(q,'near_stop_170s')
 def snapshot(self,q,reason):
  if not self.display:return
  try:
   fields={n:struct.unpack('<I',bytes(q.mem.read(self.display+offset,4)))[0] for n,offset in self.layout['layout'].items()}
   start,end,maximum=(fields[n] for n in ['buffer','bufptr','bufmax'])
   if not 0<start<=end<=maximum or maximum-start>1048576:raise ValueError('Invalid binary-derived buffer bounds')
   if not self.fixture.owns(q,fields['fd']):raise ValueError('Display fd does not match tracked scoped socket')
   if end-start>65536:raise ValueError('Snapshot exceeds bounded 64KiB diagnostic limit')
   raw=bytes(q.mem.read(start,end-start));requests=[];pos=0
   # Buffer contains protocol requests, never authentication setup/cookies.
   while pos<len(raw):
    if pos+4>len(raw):raise ValueError('Truncated request header')
    opcode,detail,units=struct.unpack_from('<BBH',raw,pos);length=units*4
    if length<4 or pos+length>len(raw):raise ValueError('Request length outside buffered bounds')
    row={'offset':pos,'opcode':opcode,'detail':detail,'units':units,'bytes':length}
    if opcode==1 and length>=32:
     wid,parent=struct.unpack_from('<II',raw,pos+4);x,y,w,h,border,cl=struct.unpack_from('<hhHHHH',raw,pos+12);visual,mask=struct.unpack_from('<II',raw,pos+24)
     row.update(name='CreateWindow',window=hex(wid),parent=hex(parent),x=x,y=y,width=w,height=h,border=border,window_class=cl,visual=hex(visual),value_mask=hex(mask),matches_returned_id=wid==self.created_id)
    elif opcode==8 and length>=8:row.update(name='MapWindow',window=hex(struct.unpack_from('<I',raw,pos+4)[0]))
    requests.append(row);pos+=length
   private=fields['xcb_private'];c=struct.unpack('<I',bytes(q.mem.read(private+8,4)))[0]
   xfields={n:struct.unpack('<I',bytes(q.mem.read(c+off,4)))[0] for n,off in self.layout['xcb']['layout'].items() if n!='output_buffer'}
   xfields['error']=struct.unpack('<I',bytes(q.mem.read(c,4)))[0]
   if xfields['fd']!=fields['fd'] or not 0<=xfields['output_length']<=4096:raise ValueError('XCB fd/length validation failed')
   xraw=bytes(q.mem.read(c+self.layout['xcb']['layout']['output_buffer'],xfields['output_length']))
   xrequests=[];xpos=0
   while xpos<len(xraw):
    if xpos+4>len(xraw):raise ValueError('Truncated XCB request')
    op,detail,units=struct.unpack_from('<BBH',xraw,xpos);size=units*4
    if size<4 or xpos+size>len(xraw):raise ValueError('Invalid XCB request length')
    xr={'offset':xpos,'opcode':op,'detail':detail,'units':units,'bytes':size}
    if op==1 and size>=32:
     wid,parent=struct.unpack_from('<II',xraw,xpos+4);x,y,w,h,border,cl=struct.unpack_from('<hhHHHH',xraw,xpos+12);visual,mask=struct.unpack_from('<II',xraw,xpos+24)
     xr.update(name='CreateWindow',window=hex(wid),parent=hex(parent),x=x,y=y,width=w,height=h,border=border,window_class=cl,visual=hex(visual),value_mask=hex(mask),matches_returned_id=wid==self.created_id)
    elif op==8 and size>=8:xr.update(name='MapWindow',window=hex(struct.unpack_from('<I',xraw,xpos+4)[0]))
    xrequests.append(xr);xpos+=size
   self.emit('display_buffer_snapshot',reason=reason,display=hex(self.display),returned_window=hex(self.created_id) if self.created_id is not None else None,fields={n:hex(v) if n!='fd' else v for n,v in fields.items()},pending_bytes=len(raw),buffer_hex=raw.hex(),requests=requests,xcb={'connection':hex(c),'fields':xfields,'pending_bytes':len(xraw),'buffer_hex':xraw.hex(),'requests':xrequests},pc=hex(q.arch.regs.arch_pc),lr=hex(q.arch.regs.lr),thread=q.os.thread_management.cur_thread.id,library_counts=dict(self.counts),read_only=True)
  except Exception as exc:self.emit('display_snapshot_error',reason=reason,error=str(exc),pc=hex(q.arch.regs.arch_pc))
