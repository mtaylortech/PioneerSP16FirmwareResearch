"""Optional one-interaction helper for an owned private original X11 drawable.

Inert without --execute. Uses only one explicit AF_UNIX X16 connection. It is to
be spawned by the existing watchdog, and retains its leader until that watchdog
stops the guest. Original guest launches, physical input and TCP are absent.
Protocol offsets follow the retained XQuartz X11/Xproto.h, not a host ABI.
"""
import argparse, hashlib, json, math, os, pathlib, signal, socket, stat, struct, time
from live_prerequisite import validate_for_send
HOST_ENDPOINT='/private/tmp/.X11-unix/X16'
BUTTON_PRESS_MASK=1<<2;BUTTON_RELEASE_MASK=1<<3;POINTER_MOTION_MASK=1<<6
MAX_MESSAGE=8388608

def read(path):return json.loads(path.read_text())
def cookie(path):
 data=path.read_bytes();pos=0
 while pos<len(data):
  family=struct.unpack_from('>H',data,pos)[0];pos+=2;fields=[]
  for unused in range(4):
   length=struct.unpack_from('>H',data,pos)[0];pos+=2;fields.append(data[pos:pos+length]);pos+=length
  address,number,name,value=fields
  if family==65535 and number==b'16' and name==b'MIT-MAGIC-COOKIE-1' and len(value)==16:return name,value
 raise ValueError('Scoped MIT-MAGIC-COOKIE-1 X16 credential missing')

def guest_evidence(run,xid):
 path=run/'supervision/guest.stdout.txt'
 if path.stat().st_size>33554432:raise ValueError('Guest stdout exceeds bounded evidence scan')
 created=None;continuation=None;pending={}
 for line in path.read_text(errors='replace').splitlines():
  if not line.startswith('PROBE '):continue
  try:e=json.loads(line[6:])
  except ValueError:continue
  kind=e.get('kind')
  if kind=='display_buffer_snapshot':
   for r in e.get('requests',[])+e.get('xcb',{}).get('requests',[]):
    if r.get('name')=='CreateWindow' and r.get('matches_returned_id') and r.get('window')==hex(xid)==e.get('returned_window'):
     created={'source':'byte_validated_original_XCreateWindow_returned_XID_and_request','probe_sequence':e.get('probe_sequence'),'host_monotonic':e.get('host_monotonic'),'request':r,'descriptor':e.get('fields',{}).get('fd')}
  elif kind=='api_call' and e.get('name')=='XCreateWindow':pending[e.get('thread')]=e
  elif kind=='api_return' and e.get('name')=='XCreateWindow':
   p=pending.pop(e.get('thread'),None)
   if p and e.get('result')==xid and created is None:created={'source':'original_application_XCreateWindow_same_thread_call_and_return','entry_sequence':p.get('probe_sequence'),'return_sequence':e.get('probe_sequence'),'thread':e.get('thread')}
  elif kind=='active_enclosing_subsequent_execution':
   r=e.get('result',{})
   if r.get('matched_return') and r.get('entry')=='0x40d6e8' and r.get('caller')=='0x322b40' and r.get('subsequent')=='0x322b44':continuation={k:e.get(k) for k in ('probe_sequence','host_monotonic','elapsed','result')}
 if not created:raise ValueError('Current original returned XID missing')
 return {'original_window':hex(xid),'created':created,'prerequisite':'current original returned XID plus ownership/private credential and live attributes checks'}

def ownership(run,stop_at):
 owner=run/'supervision/attempt-owned';launcher=read(owner/'launcher.json');state=read(owner/'state.json');display=read(run/'display-process.json');now=time.monotonic()
 if state.get('phase')!='running' or state.get('closed') or now-state['monotonic']>2:raise ValueError('Owned supervision is not fresh/running')
 if state['watchdog_pid']!=launcher['pid'] or state['owner_pid']!=launcher['owner_pid']:raise ValueError('Watchdog identities contradict launcher')
 if not math.isfinite(stop_at) or stop_at>state['deadlines']['term_at'] or now+12>=stop_at:raise ValueError('At least 12 seconds inside unchanged finite TERM deadline required')
 groups={g['role']:g for g in state['groups']}
 if any(groups.get(role,{}).get('exit_code') is not None or not groups.get(role) for role in ('guest','display')):raise ValueError('Owned guest/display leaders are not live')
 dg=groups['display']
 if display['wrapper_pid']!=dg['pid'] or display['wrapper_pgid']!=dg['pgid'] or display['server_pgid']!=dg['pgid']:raise ValueError('Private display process-group identities contradict')
 if not any(m['pid']==display['server_pid'] and m['ppid']==display['wrapper_pid'] and m['pgid']==dg['pgid'] for m in dg['live_members']):raise ValueError('Exact private Xvfb server is not in owned live group')
 if os.getppid()!=state['watchdog_pid']:raise ValueError('Helper must be a direct child of this existing watchdog')
 if not any(g['pid']==os.getpid() for g in state['groups']):raise ValueError('Helper is not yet recorded in current watchdog state')
 for pid in (state['owner_pid'],state['watchdog_pid'],groups['guest']['pid'],display['server_pid']):os.kill(pid,0)
 path=pathlib.Path(HOST_ENDPOINT);info=path.lstat()
 if not stat.S_ISSOCK(info.st_mode) or info.st_uid!=os.getuid():raise ValueError('X16 Unix socket owner/type differs')
 lock=pathlib.Path('/private/tmp/.X16-lock')
 if int(lock.read_text().strip())!=display['server_pid']:raise ValueError('X16 lock does not identify exact owned server')
 auth=run/'display.xauth'
 if stat.S_IMODE(auth.stat().st_mode)!=0o600 or auth.read_bytes()!=(run/'rootfs/root/display.xauth').read_bytes():raise ValueError('Fresh mapped private display credentials differ')
 if not display.get('authentication',{}).get('actual_mapped_equal'):raise ValueError('Original authenticated fixture record differs')
 return {'watchdog_pid':state['watchdog_pid'],'owner_pid':state['owner_pid'],'guest_pid':groups['guest']['pid'],'display_server_pid':display['server_pid'],'display_pgid':dg['pgid'],'helper_pid':os.getpid(),'term_at':state['deadlines']['term_at'],'socket_inode':info.st_ino,'authentication':'MIT-MAGIC-COOKIE-1','cookie_disclosed':False}

def visible_region(width,height,root_x,root_y,root_width,root_height):
 x,y=max(0,-root_x),max(0,-root_y)
 right,bottom=min(width,root_width-root_x),min(height,root_height-root_y)
 if right<=x or bottom<=y:raise ValueError('Original drawable has no visible root intersection')
 return [x,y,right-x,bottom-y]

class X11:
 def __init__(self,auth,deadline):self.auth=auth;self.deadline=deadline;self.conn=None;self.sequence=0;self.formats={};self.visuals={};self.root=None;self.image_order=None
 def timeout(self):
  remaining=self.deadline-time.monotonic()
  if remaining<=0:raise TimeoutError('Bounded input observation deadline')
  self.conn.settimeout(min(2,remaining))
 def recv(self,length):
  if length>MAX_MESSAGE:raise ValueError('X11 response exceeds bounded 8MiB')
  data=bytearray()
  while len(data)<length:
   self.timeout();part=self.conn.recv(length-len(data))
   if not part:raise EOFError('Private X server closed')
   data.extend(part)
  return bytes(data)
 def send(self,payload):self.timeout();self.conn.sendall(payload)
 def connect(self):
  name,value=cookie(self.auth);pad=lambda x:x+b'\0'*(-len(x)%4)
  self.conn=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.timeout();self.conn.connect(HOST_ENDPOINT)
  self.send(struct.pack('<BBHHHHH',ord('l'),0,11,0,len(name),len(value),0)+pad(name)+pad(value))
  prefix=self.recv(8);body=self.recv(struct.unpack_from('<H',prefix,6)[0]*4)
  if prefix[0]!=1:raise ValueError('Private X11 authentication/setup rejected')
  self.parse_setup(body)
 def parse_setup(self,body):
  if len(body)<32 or body[20]!=1:raise ValueError('Expected exactly one private X11 screen')
  vendor_length=struct.unpack_from('<H',body,16)[0];self.image_order=body[22];pos=32+(vendor_length+3)//4*4
  for i in range(body[21]):
   depth,bpp,pad=struct.unpack_from('<BBB',body,pos);self.formats[depth]=(bpp,pad);pos+=8
  if pos+40>len(body):raise ValueError('Truncated private screen metadata')
  self.root_width,self.root_height=struct.unpack_from('<HH',body,pos+20)
  self.root=struct.unpack_from('<I',body,pos)[0];ndepths=body[pos+39];pos+=40
  for i in range(ndepths):
   depth=body[pos];nvisuals=struct.unpack_from('<H',body,pos+2)[0];pos+=8
   for unused in range(nvisuals):
    visual,cl,bits,entries,red,green,blue=struct.unpack_from('<IBBHIII',body,pos);pos+=24;self.visuals[visual]={'depth':depth,'class':cl,'red':red,'green':green,'blue':blue}
 def request(self,opcode,body=b'',detail=0,reply=True):
  payload=struct.pack('<BBH',opcode,detail,(4+len(body))//4)+body
  if len(payload)%4:raise ValueError('Unaligned X11 request')
  self.sequence+=1;expected=self.sequence&0xffff;self.send(payload)
  if not reply:return expected
  for unused in range(64):
   header=self.recv(32);kind=header[0]
   if kind==0:raise RuntimeError('Private X11 error code=%d sequence=%d major=%d'%(header[1],struct.unpack_from('<H',header,2)[0],header[10]))
   if kind==1:
    extra=self.recv(struct.unpack_from('<I',header,4)[0]*4)
    if struct.unpack_from('<H',header,2)[0]!=expected:raise ValueError('X11 reply sequence differs')
    return header+extra
   # This connection selects no input. Unrelated server events are bounded.
  raise RuntimeError('Too many unsolicited X11 frames')
 def attributes(self,xid):
  r=self.request(3,struct.pack('<I',xid));g=self.request(14,struct.pack('<I',xid));tree=self.request(15,struct.pack('<I',xid))
  visual=struct.unpack_from('<I',r,8)[0];root=struct.unpack_from('<I',g,8)[0];width,height=struct.unpack_from('<HH',g,16)
  a={'window':hex(xid),'visual':visual,'window_class':struct.unpack_from('<H',r,12)[0],'map_state':r[26],'all_event_masks':struct.unpack_from('<I',r,32)[0],'root':root,'width':width,'height':height,'depth':g[1],'tree_root':struct.unpack_from('<I',tree,8)[0],'parent':struct.unpack_from('<I',tree,12)[0]}
  if not a['window_class']==1 or not a['map_state']==2 or root!=self.root or a['tree_root']!=self.root or not 0<width<=self.root_width+2 or not 0<height<=self.root_height+2:raise ValueError('Exact original window is not viewable InputOutput on owned 800x480 root')
  translation=self.request(40,struct.pack('<IIhh',xid,self.root,0,0))
  if translation[1]!=1:raise ValueError('Drawable/root geometry crossed screens')
  root_x,root_y=struct.unpack_from('<hh',translation,12)
  a['visible_region']=visible_region(width,height,root_x,root_y,self.root_width,self.root_height)
  a['root_origin']=[root_x,root_y];a['root_dimensions']=[self.root_width,self.root_height]
  return a
 def image(self,xid,attributes,path):
  x,y,width,height=attributes['visible_region'];r=self.request(73,struct.pack('<IhhHHI',xid,x,y,width,height,0xffffffff),detail=2);depth=r[1];visual=struct.unpack_from('<I',r,8)[0];pixels=r[32:]
  bpp,pad=self.formats[depth];v=self.visuals[visual];stride=((width*bpp+pad-1)//pad)*(pad//8)
  if bpp not in (16,24,32) or v['class']!=4 or len(pixels)!=height*stride or depth!=attributes['depth'] or visual!=attributes['visual']:raise ValueError('Captured original drawable TrueColor layout differs')
  n=bpp//8;mask=v['red']|v['green']|v['blue'];order='little' if self.image_order==0 else 'big';nonblack=sum(bool(int.from_bytes(pixels[y*stride+x*n:y*stride+(x+1)*n],order)&mask) for y in range(height) for x in range(width))
  with path.open('xb') as f:f.write(pixels)
  return {'path':str(path),'host_monotonic':time.monotonic(),'window':hex(xid),'capture_region':[x,y,width,height],'width':width,'height':height,'depth':depth,'bpp':bpp,'stride':stride,'image_order':self.image_order,'visual':v,'nonblack_pixels':nonblack,'pixel_sha256':hashlib.sha256(pixels).hexdigest()}
 def send_interaction(self,xid,x,y,stamp,interaction):
  translation=self.request(40,struct.pack('<IIhh',xid,self.root,x,y))
  if translation[1]!=1:raise ValueError('Original drawable coordinate translation crossed screens')
  root_x,root_y=struct.unpack_from('<hh',translation,12)
  events=[(6,0,POINTER_MOTION_MASK,0)] if interaction=='motion' else [(4,1,BUTTON_PRESS_MASK,0),(5,1,BUTTON_RELEASE_MASK,1<<8)]
  rows=[]
  for kind,detail,mask,state in events:
   event=struct.pack('<BBHIIIIhhhhHBB',kind,detail,0,stamp,self.root,xid,0,root_x,root_y,x,y,state,1,0)
   sequence=self.request(25,struct.pack('<II',xid,mask)+event,reply=False)
   rows.append({'type':kind,'detail':detail,'event_mask':mask,'state':state,'window':hex(xid),'time':stamp,'event_x':x,'event_y':y,'root_x':root_x,'root_y':root_y,'request_sequence':sequence,'propagate':False})
  self.request(43) # Server processes all requests/errors preceding this reply.
  return rows
 def close(self):
  if self.conn:self.conn.close();self.conn=None

def event_receipts(run,xid,stamp,sent):
 receipts=[];types={e['type']:e for e in sent}
 for line in (run/'supervision/guest.stdout.txt').read_text(errors='replace').splitlines():
  if not line.startswith('PROBE '):continue
  try:e=json.loads(line[6:])
  except ValueError:continue
  r=e.get('event',{})
  if e.get('kind')=='original_x11_event_return' and e.get('matched_return') and r.get('window')==hex(xid) and r.get('time')==stamp and r.get('type') in types and r.get('send_event') and r.get('detail')==types[r['type']]['detail'] and r.get('x')==types[r['type']]['event_x'] and r.get('y')==types[r['type']]['event_y']:
   receipts.append(e)
 return receipts

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=pathlib.Path,required=True);p.add_argument('--xid',type=lambda s:int(s,0),required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--stop-at',type=float,required=True);p.add_argument('--execute',action='store_true');p.add_argument('--interaction',choices=['click','motion'],default='click');p.add_argument('--x',type=int);p.add_argument('--y',type=int);a=p.parse_args()
 run=a.run.resolve();output=a.output.resolve();output.relative_to(run);output.mkdir(exist_ok=False)
 report={'started_monotonic':time.monotonic(),'execute_requested':a.execute,'interaction':a.interaction,'input_sent':False,'original_event_received':False,'visual_change_after_input':False,'input_response_confirmed':False,'limitations':'Server acceptance is separate from original guest consumption or attributable UI handling. Synthetic SendEvent may be ignored.','phase_deadline':min(time.monotonic()+15,a.stop_at-3)};stopping=False;connection=None
 def stop(*unused):
  nonlocal stopping
  stopping=True
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 def save():(output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 try:
  report['guest_evidence']=guest_evidence(run,a.xid)
  # Spawn starts before the watchdog can save its group; wait only for that registration.
  until=min(time.monotonic()+1,report['phase_deadline'])
  while time.monotonic()<until:
   state=read(run/'supervision/attempt-owned/state.json')
   if any(g['pid']==os.getpid() for g in state.get('groups',[])):break
   if state.get('phase')!='running':break
   time.sleep(.025)
  report['ownership']=ownership(run,a.stop_at)
  connection=X11(run/'display.xauth',report['phase_deadline']);connection.connect();attrs=connection.attributes(a.xid);report['attributes']=attrs
  x=a.x if a.x is not None else attrs['width']//2;y=a.y if a.y is not None else attrs['height']//2
  vx,vy,vw,vh=attrs['visible_region']
  if not vx<=x<vx+vw or not vy<=y<vy+vh:raise ValueError('Coordinates outside visible original drawable')
  report['valid_visible_region']=attrs['visible_region'];report['coordinates']=[x,y]
  required=POINTER_MOTION_MASK if a.interaction=='motion' else BUTTON_PRESS_MASK|BUTTON_RELEASE_MASK
  if attrs['all_event_masks']&required!=required:raise ValueError('Original drawable does not select requested input event masks')
  report['before']=[connection.image(a.xid,attrs,output/'before-0.ximage')];time.sleep(.2);report['before'].append(connection.image(a.xid,attrs,output/'before-1.ximage'));save()
  if not all(i['nonblack_pixels'] for i in report['before']):raise ValueError('Original drawable captures are black; no input sent')
  if report['before'][0]['pixel_sha256']!=report['before'][1]['pixel_sha256']:raise ValueError('Original pixels changed in pre-input control; no attributable response test')
  if a.execute:
   if a.interaction!='click' or [x,y]!=[250,350]:raise ValueError('Only one reversible Track 2 selection is prepared')
   if attrs['visible_region'][2:]!=[800,480] or attrs['root_dimensions']!=[800,480]:raise ValueError('Live exact 800x480 geometry required')
   prerequisite=validate_for_send(run,a.xid)
   if any(i['pixel_sha256']!=prerequisite['owned_pixel_evidence']['pixel_sha256'] for i in report['before']):raise ValueError('Live pixels differ from bound stable HOME')
   report['completion_prerequisite']=prerequisite
   if stopping:raise ValueError('Owned helper received stop before input')
   report['ownership_before_send']=ownership(run,a.stop_at);fresh=connection.attributes(a.xid)
   if fresh!=attrs:raise ValueError('Original drawable attributes changed before input')
   if stopping:raise ValueError('Owned helper received stop before input')
   report['prerequisite_before_send']=validate_for_send(run,a.xid)
   stamp=int(time.monotonic()*1000)&0xffffffff;record={'output':str(output),'interaction':a.interaction,'window':hex(a.xid),'time':stamp,'host_monotonic':time.monotonic(),'at_most_one_interaction':True,'event_x':x,'event_y':y,'root_x':attrs['root_origin'][0]+x,'root_y':attrs['root_origin'][1]+y}
   # A failed/uncertain send consumes this arm's one-input allowance too.
   with (run/'drawable-input-consumed.json').open('x') as f:f.write(json.dumps(record)+'\n')
   report['input_attempt']=record;save();report['events']=connection.send_interaction(a.xid,x,y,stamp,a.interaction);report['input_sent']=True;report['server_processed_send_without_X_error']=True;save()
   report['after']=[]
   for index,delay in enumerate((.25,1.0)):
    time.sleep(delay)
    if stopping:break
    report['after'].append(connection.image(a.xid,attrs,output/('after-'+str(index)+'.ximage')));save()
   report['visual_change_after_input']=any(i['pixel_sha256']!=report['before'][-1]['pixel_sha256'] for i in report['after'])
   report['guest_event_receipts']=event_receipts(run,a.xid,stamp,report['events'])
   report['original_event_received']=bool(report['guest_event_receipts'])
   report['handler_receipts']=[json.loads(l[6:]) for l in (run/'supervision/guest.stdout.txt').read_text(errors='replace').splitlines() if l.startswith('PROBE ') and json.loads(l[6:]).get('kind') in ('original_input_handler_call','original_input_handler_return')]
   report['original_event_and_subsequent_pixel_change_observed']=bool(report['original_event_received'] and report['visual_change_after_input'])
   report['input_response_confidence']='matched original event receipt and subsequent visual change; causal UI handler not isolated' if report['original_event_and_subsequent_pixel_change_observed'] else 'not established'
  else:report['outcome']='read_only_ready_no_input'
 except Exception as e:report['exception']={'type':type(e).__name__,'message':str(e),'host_monotonic':time.monotonic()}
 finally:
  if connection:connection.close()
  report['interaction_finished_monotonic']=time.monotonic();save();print(json.dumps(report),flush=True)
 # Existing launcher interprets early non-guest leader exit as a stop. Keep this
 # owned leader until the already-configured watchdog stops it; never extend it.
 while not stopping and time.monotonic()<a.stop_at-.1:
  state=read(run/'supervision/attempt-owned/state.json')
  if state.get('phase')!='running':break
  time.sleep(min(.05,max(0,a.stop_at-.1-time.monotonic())))
 report['helper_finished_monotonic']=time.monotonic();report['stopped']=stopping;save()
if __name__=='__main__':main()
