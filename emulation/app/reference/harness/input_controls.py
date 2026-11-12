"""Mock-only scoped X11 packet, input gate and original event return controls."""
import ast,collections,importlib.util,json,pathlib,os,stat,struct,sys,tempfile,time,types
B=pathlib.Path(__file__).resolve().parent
PROJECT=next(p for p in B.parents if (p/'README.md').exists() and (p/'experiments').is_dir())
M=B if (B/'resource_application_observer.py').exists() else PROJECT/'experiments/milestone-following-20261008/common'
sys.path.insert(0,str(M))
def load(name):
 spec=importlib.util.spec_from_file_location(name,B/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
m=load('drawable_input');o=load('x11_event_observer');rows=[]

def reply(seq,extra=0):
 r=bytearray(32+extra);r[0]=1;struct.pack_into('<HI',r,2,seq,extra//4);return r

def setup():
 body=bytearray(32);body[20]=1;body[21]=1;body[22]=0;struct.pack_into('<H',body,18,65535)
 body+=bytes([24,32,32,0])+b'\0'*4
 screen=bytearray(40);struct.pack_into('<I',screen,0,0x42);struct.pack_into('<HH',screen,20,800,480);struct.pack_into('<I',screen,32,0x21);screen[38]=24;screen[39]=1;body+=screen
 body+=struct.pack('<BBHI',24,0,1,0);body+=struct.pack('<IBBHIIII',0x21,4,8,256,0xff0000,0xff00,0xff,0)
 return bytes(body)

class MockSocket:
 def __init__(self):self.queue=bytearray();self.seq=0;self.requests=[];self.connected=None;self.closed=False;self.class_value=1;self.map_state=2;self.server_error=False
 def settimeout(self,timeout):assert 0<timeout<=2
 def connect(self,path):assert path==m.HOST_ENDPOINT;self.connected=path
 def sendall(self,payload):
  if self.connected is None:raise AssertionError('send before scoped connect')
  if payload[0]==ord('l') and self.seq==0 and not self.requests:
   body=setup();self.queue+=struct.pack('<BBHHH',1,0,11,0,len(body)//4)+body;self.requests.append({'setup':True});return
  opcode,detail,units=struct.unpack_from('<BBH',payload);assert units*4==len(payload);self.seq+=1;self.requests.append({'opcode':opcode,'detail':detail,'payload':payload})
  r=reply(self.seq,12 if opcode==3 else 8 if opcode==73 else 0)
  if opcode==3:
   struct.pack_into('<IH',r,8,0x21,self.class_value);r[26]=self.map_state;struct.pack_into('<I',r,32,4|8|64)
  elif opcode==14:
   r[1]=24;struct.pack_into('<IhhHH',r,8,0x42,10,20,2,1)
  elif opcode==15:struct.pack_into('<II',r,8,0x42,0x42)
  elif opcode==73:
   r[1]=24;struct.pack_into('<I',r,8,0x21);r[32:]=b'\0\0\0\xff'+b'\0\xff\0\0'
  elif opcode==40:
   r[1]=1;src_x,src_y=struct.unpack_from('<hh',payload,12);struct.pack_into('<hh',r,12,src_x+10,src_y+20)
  elif opcode==25:return
  elif opcode==43:
   if self.server_error:r[0]=0;r[1]=3;r[10]=25
  else:raise AssertionError('Unexpected opcode '+str(opcode))
  self.queue+=r
 def recv(self,length):
  # Deliberately fragmented protocol headers and payloads.
  part=bytes(self.queue[:min(length,7)]);del self.queue[:len(part)];return part
 def close(self):self.closed=True

with tempfile.TemporaryDirectory(prefix='input-control-',dir=B) as td:
 d=pathlib.Path(td);auth=d/'auth';field=lambda x:struct.pack('>H',len(x))+x
 auth.write_bytes(struct.pack('>H',65535)+field(b'')+field(b'16')+field(b'MIT-MAGIC-COOKIE-1')+field(bytes(range(16))))
 s=MockSocket();original=m.socket.socket;calls=[]
 def factory(family,kind):assert family==m.socket.AF_UNIX and kind==m.socket.SOCK_STREAM;calls.append((family,kind));return s
 m.socket.socket=factory
 try:x=m.X11(auth,time.monotonic()+10);x.connect();attrs=x.attributes(0x200002);image=x.image(0x200002,attrs,d/'image.ximage');assert image['nonblack_pixels']==1 and x.root==0x42
 finally:m.socket.socket=original
 sent=x.send_interaction(0x200002,1,0,12345,'click');packets=[r['payload'] for r in s.requests if r.get('opcode')==25]
 assert len(packets)==2 and [struct.unpack_from('<I',p,4)[0] for p in packets]==[0x200002]*2
 assert [(p[12],p[13]) for p in packets]==[(4,1),(5,1)]
 assert [struct.unpack_from('<H',p,40)[0] for p in packets]==[0,256]
 assert all(struct.unpack_from('<IIIIhhhh',p,16)==(12345,0x42,0x200002,0,11,20,1,0) for p in packets)
 assert sent[0]['root_x']==11 and sent[0]['root_y']==20 and len(calls)==1
 x.close();assert s.closed
 rows.append({'control':'one_AF_UNIX_authenticated_connection_fragmented_replies_original_geometry_image_and_exact_two_event_click','passed':True,'network_or_server_used':False})
 for cl,mapstate in [(2,2),(1,0)]:
  s=MockSocket();s.connected=m.HOST_ENDPOINT;s.class_value=cl;s.map_state=mapstate;x=m.X11(auth,time.monotonic()+5);x.conn=s;x.parse_setup(setup())
  try:x.attributes(0x200002);raise AssertionError('InputOnly/unmapped accepted')
  except ValueError:pass
  assert not any(r.get('opcode')==25 for r in s.requests)
 rows.append({'control':'InputOnly_and_unmapped_metadata_rejected_before_SendEvent','passed':True})
 s=MockSocket();s.connected=m.HOST_ENDPOINT;s.server_error=True;x=m.X11(auth,time.monotonic()+5);x.conn=s;x.parse_setup(setup())
 try:x.send_interaction(0x200002,1,0,12345,'motion');raise AssertionError('Server X error ignored')
 except RuntimeError:pass
 assert len([r for r in s.requests if r.get('opcode')==25])==1
 rows.append({'control':'single_motion_option_and_sync_server_error_retained','passed':True})
 (d/'supervision').mkdir();stdout=d/'supervision/guest.stdout.txt'
 creation={'kind':'display_buffer_snapshot','returned_window':'0x200002','requests':[{'name':'CreateWindow','matches_returned_id':True,'window':'0x200002','window_class':1}]}
 continuation={'kind':'active_enclosing_subsequent_execution','result':{'matched_return':True,'entry':'0x40d6e8','caller':'0x322b40','subsequent':'0x322b44'}}
 stdout.write_text('PROBE '+json.dumps(creation)+'\n')
 try:m.guest_evidence(d,0x200002);raise AssertionError('Missing continuation accepted')
 except ValueError:pass
 with stdout.open('a') as f:f.write('PROBE '+json.dumps(continuation)+'\n')
 assert m.guest_evidence(d,0x200002)['matched_enclosing_continuation']
 try:m.guest_evidence(d,0x300002);raise AssertionError('Wrong original window accepted')
 except ValueError:pass
 with (d/'drawable-input-consumed.json').open('x') as f:f.write('{}')
 try:(d/'drawable-input-consumed.json').open('x');raise AssertionError('One-input record overwritten')
 except FileExistsError:pass
 rows.append({'control':'matched_exact_guest_creation_and_enclosing_continuation_gate_and_exclusive_one_input_record','passed':True})

# Use actual original app bytes to identify direct XNextEvent callsite/caller.
from font_discovery_observer import FontDiscoveryObserver
from resource_application_observer import caller_transfer
app=PROJECT/'experiments/post-font-counted-quantum-20261008-repeat/control/rootfs/root/pdj/EP085_Main_R'
disc=FontDiscoveryObserver(lambda *a,**k:None,time.monotonic(),app);disc.main_tid=2000
callers=[]
for base,data in disc.segments:
 for off in range(0,len(data)-4,4):
  a=base+off;kind,target=caller_transfer(a,data[off:off+4])
  if kind=='arm_bl' and target==o.PLT:callers.append(a+4)
assert callers
caller=callers[0];event_ptr=0x15000000;display=0x17de000
payload=struct.pack('<IIIIIIIIiiiiIII',4,99,1,display,0x200002,0x42,0,12345,1,0,11,20,0,1,1)
class Mem:
 def read(self,a,n):
  if a==event_ptr:return payload[:n]
  return b''.join(disc.expected(a+i) for i in range(0,n,4))
class Guest:
 def __init__(self):self.mem=Mem();self.arch=types.SimpleNamespace(regs=types.SimpleNamespace(lr=caller,sp=0x7ff3c800,r0=display,r1=event_ptr,arch_pc=o.PLT));self.os=types.SimpleNamespace(thread_management=types.SimpleNamespace(cur_thread=types.SimpleNamespace(id=2000)));self.hooks={}
 def hook_address(self,cb,a):self.hooks[a]=cb
q=Guest();events=[];observer=o.OriginalX11Events(lambda kind,**r:events.append(dict(kind=kind,**r)),time.monotonic(),disc,B);observer.install(q);observer.enter(q)
q.arch.regs.arch_pc=caller;q.arch.regs.sp+=4;observer.returned(q,caller);assert not observer.receipts
q.arch.regs.sp-=4;q.os.thread_management.cur_thread.id=2001;observer.returned(q,caller);assert not observer.receipts
q.os.thread_management.cur_thread.id=2000;observer.returned(q,caller);assert len(observer.receipts)==1 and observer.receipts[0]['event']['time']==12345 and observer.receipts[0]['event']['window']=='0x200002'
rows.append({'control':'actual_original_XNextEvent_PLT_and_BL_bytes_same_thread_SP_return_plus_ARM32_event_fields','passed':True,'original_app_sha256':disc.app_sha256,'verified_direct_callers':[hex(a) for a in callers],'isolated_mock_guest_only':True})
probe=(B/'probe.py').read_text()
assert 'if name=="XNextEvent": return' in probe and 'input_events.install(q);' in probe and 'original_x11_events=input_events.summary()' in probe and '"original_x11_events":input_events.summary(),' in probe
compile(probe,str(B/'probe.py'),'exec')
# Execute only the extracted API observer callback against an inert mock.
api_node=next(n for n in ast.parse(probe).body if isinstance(n,ast.FunctionDef) and n.name=='api_trace')
api_events=[];api_hooks=[]
q.arch.regs.read=lambda name:getattr(q.arch.regs,name,0)
q.hook_address=lambda cb,address:api_hooks.append((cb,address))
namespace={'args':types.SimpleNamespace(local_display=False),'api_counts':collections.Counter(),'event':lambda kind,**r:api_events.append(dict(kind=kind,**r))}
exec(compile(ast.Module(body=[api_node],type_ignores=[]),str(B/'probe.py'),'exec'),namespace)
namespace['api_trace']('XNextEvent')(q);assert api_events[-1]['name']=='XNextEvent' and not api_hooks
namespace['api_trace']('XPutImage')(q);assert api_events[-1]['name']=='XPutImage' and len(api_hooks)==1
rows.append({'control':'conditional_install_sample_final_integration_XNextEvent_entry_retained_one_shot_return_retired_other_API_return_preserved','passed':True})
spawn=load('spawn_input_request')
with tempfile.TemporaryDirectory(prefix='spawn-control-',dir=B) as td, tempfile.TemporaryDirectory(prefix='p16wd-',dir='/private/tmp') as private:
 d=pathlib.Path(td);owned=d/'supervision/attempt-owned';owned.mkdir(parents=True);private=pathlib.Path(private);private.chmod(0o700);control=private/'control.sock';control.touch();original_lstat=pathlib.Path.lstat
 def mocked_lstat(path,*args,**kwargs):
  if path==control:return types.SimpleNamespace(st_uid=os.getuid(),st_mode=stat.S_IFSOCK|0o600)
  return original_lstat(path,*args,**kwargs)
 pathlib.Path.lstat=mocked_lstat
 try:
  launcher={'control_socket':str(control),'private_socket_directory':str(private),'pid':12345,'owner_pid':12346};state={'phase':'running','closed':False,'monotonic':time.monotonic(),'watchdog_pid':12345,'owner_pid':12346,'deadlines':{'term_at':time.monotonic()+60},'groups':[]}
  (owned/'launcher.json').write_text(json.dumps(launcher));(owned/'state.json').write_text(json.dumps(state))
  root,endpoint,request,deadline=spawn.prepare(d,pathlib.Path('/mock/python'),xid=0x200002)
  assert root==owned and endpoint==control and request['attempt'] is False and request['role']=='drawable-input' and '--execute' not in request['argv']
  state['groups']=[{'role':'drawable-input'}];(owned/'state.json').write_text(json.dumps(state))
  try:spawn.prepare(d,pathlib.Path('/mock/python'),xid=0x200002);raise AssertionError('Duplicate helper role accepted')
  except ValueError:pass
  state['groups']=[];state['phase']='term';(owned/'state.json').write_text(json.dumps(state))
  try:spawn.prepare(d,pathlib.Path('/mock/python'),xid=0x200002);raise AssertionError('Stopped watchdog accepted')
  except ValueError:pass
 finally:pathlib.Path.lstat=original_lstat
rows.append({'control':'inert_existing_watchdog_spawn_request_false_attempt_unused_role_finite_deadline_private_owned_socket_and_stopped_role_rejection','passed':True,'guest_or_helper_spawned':False,'control_socket_type_mocked_no_socket_bound_or_requests_sent':True})
result={'passed':True,'original_application_guests_launched':0,'server_or_network_used':False,'physical_input_sent':False,'controls':rows}
(B/'input-controls.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
