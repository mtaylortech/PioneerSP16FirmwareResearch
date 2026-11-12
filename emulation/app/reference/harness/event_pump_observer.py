"""Sparse original XPending gates and credential-free X11 incoming packet assembly."""
import collections,json,struct,select
from pathlib import Path
POINTS=(0x69affc,0x69b000,0x69b008,0x69b010,0x69b214)
def exact_event(event,tag):
 return bool(event.get('send_event') and event.get('window')==tag['window'] and event.get('time')==tag['time'] and event.get('type') in (4,5) and event.get('detail')==1 and event.get('x')==tag['event_x'] and event.get('y')==tag['event_y'] and event.get('x_root')==tag['root_x'] and event.get('y_root')==tag['root_y'] and event.get('state')==(0 if event['type']==4 else 256) and event.get('same_screen'))
def decode_packet(p):
 t,detail,seq,stamp,root,window,sub,rx,ry,x,y,state,same,pad=struct.unpack('<BBHIIIIhhhhHBB',p)
 return dict(type=t&127,send_event=bool(t&128),detail=detail,sequence=seq,time=stamp,root=hex(root),window=hex(window),subwindow=hex(sub),x_root=rx,y_root=ry,x=x,y=y,state=state,same_screen=bool(same))
class PacketStream:
 def __init__(self):self.data=b'';self.setup=True;self.packets=0
 def feed(self,data):
  self.data+=data;out=[]
  while True:
   if self.setup:
    if len(self.data)<8:break
    size=8+struct.unpack_from('<H',self.data,6)[0]*4
    if len(self.data)<size:break
    if self.data[0]!=1:raise RuntimeError('Observed guest X11 setup rejected')
    self.data=self.data[size:];self.setup=False;continue
   if len(self.data)<32:break
   t=self.data[0]&127;size=32
   if t in (1,35):size+=struct.unpack_from('<I',self.data,4)[0]*4
   if size>16777216:raise RuntimeError('X11 packet observation length exceeds bound')
   if len(self.data)<size:break
   p=self.data[:size];self.data=self.data[size:];self.packets+=1
   if t in (4,5):out.append(decode_packet(p[:32]))
  return out
class EventPump:
 def __init__(self,emit,discovery,fixture,run):
  self.emit,self.discovery,self.fixture,self.run=emit,discovery,fixture,Path(run);self.frames={};self.gates={};self.counts=collections.Counter();self.latest={};self.streams={};self.tagged=[];self.samples={}
 def tag(self):
  p=self.run/'drawable-input-consumed.json'
  return json.loads(p.read_text()) if p.exists() else None
 def install(self,q):
  rows={}
  from resource_application_observer import caller_transfer
  k,t=caller_transfer(0x69affc,self.discovery.expected(0x69affc))
  if (k,t)!=('arm_bl',0x113f8):raise RuntimeError('XPending original call differs')
  for a in POINTS:
   raw=self.discovery.expected(a)
   if bytes(q.mem.read(a,4))!=raw:raise RuntimeError('Event pump bytes differ '+hex(a))
   rows[hex(a)]=raw.hex();q.hook_address(lambda guest,a=a:self.visit(guest,a),a)
  self.emit('original_event_pump_hooks_validated',points=rows,read_only=True)
 def sparse(self,key,row):
  self.counts[key]+=1;prior=self.latest.get(key);self.latest[key]=row
  # Only state/result transitions plus one sample per ~128 calls are emitted.
  signature=(row.get('result'),row.get('selected_gate'),row.get('thread'),bool(self.tag()))
  if self.counts[key]<=3 or self.samples.get(key)!=signature or self.counts[key]%128==0:
   self.samples[key]=signature;self.emit(key,count=self.counts[key],**row)
 def visit(self,q,a):
  tid=q.os.thread_management.cur_thread.id;r=q.arch.regs;key=(tid,r.sp)
  if a==0x69affc:
   if key in self.frames:raise RuntimeError('Overlapping XPending call frame')
   self.frames[key]=dict(thread=tid,sp=hex(r.sp),display=hex(r.r0));return
  if a==0x69b000:
   f=self.frames.pop(key,None)
   if not f:raise RuntimeError('XPending return lacks matched live frame')
   row=dict(frame=f,result=r.r0,thread=tid,matched_thread_sp=True);self.gates[key]=row;self.sparse('original_xpending_return',row);return
  row=self.gates.get(key)
  if not row:return
  if a==0x69b008:
   expected=bool(row['result']==0);z=bool(r.cpsr&(1<<30))
   if z!=expected:raise RuntimeError('Original XPending cmp/gate Z differs')
   self.sparse('original_xpending_gate',dict(**row,selected_gate='skip_empty' if z else 'next_event',zero_flag=z));return
  if a in (0x69b010,0x69b214):
   expected=0x69b214 if row['result']==0 else 0x69b010
   if a!=expected:raise RuntimeError('Original XPending selected destination differs')
   self.sparse('original_xpending_destination',dict(**row,selected_gate=hex(a)));self.gates.pop(key)
 def before_read(self,q,fd,name,requested):
  if not self.fixture.owns(q,fd):return None
  ready=bool(select.select([q.os.fd[fd].fileno()],[],[],0)[0])
  return dict(thread=q.os.thread_management.cur_thread.id,descriptor=fd,operation=name,requested=requested,ready_before=ready,pc=hex(q.arch.regs.arch_pc),lr=hex(q.arch.regs.lr))
 def after_read(self,q,row,result,data=b''):
  if row is None:return
  self.sparse('owned_xlib_read_result',dict(**row,result=result))
  if result<=0:return
  stream=self.streams.setdefault(row['descriptor'],PacketStream());tag=self.tag()
  for event in stream.feed(data):
   if tag and exact_event(event,tag):
    receipt=dict(read=row,result=result,event=event,exact_tagged_packet=True);self.tagged.append(receipt);self.emit('owned_xlib_tagged_packet',**receipt)
 def summary(self):return dict(counts=dict(self.counts),latest=self.latest,pending=list(self.frames.values()),gates=list(self.gates.values()),tagged_packets=self.tagged,streams={fd:dict(setup=s.setup,buffered_bytes=len(s.data),packets=s.packets) for fd,s in self.streams.items()})
