"""Owned private-server observations and original-XID correlated drawable captures.

All helpers inherit this owned group and retain the existing two-second command
bound. No input, guest execution, firmware modification or extra connection is
introduced. Root pixels remain separate from exact original drawable pixels.
"""
import argparse,datetime,hashlib,json,pathlib,re,signal,struct,subprocess,time
from display_owned import environment
BASE=pathlib.Path(__file__).resolve().parent
MAX_ORIGINAL_WINDOWS=16
MAX_DETAIL_QUERIES_PER_TREE=4
MAX_CHANGED_DRAWABLE_CAPTURES=4

class OriginalWindows:
 def __init__(self):
  self.windows={};self.pending_create={};self.offset=0;self.partial='';self.matched_enclosing_continuation=None;self.read_errors=[];self.limit_reached=False
 def observe(self,e):
  kind=e.get('kind')
  if kind=='active_enclosing_subsequent_execution' and e.get('result',{}).get('matched_return'):
   self.matched_enclosing_continuation={k:e.get(k) for k in ('probe_sequence','host_monotonic','elapsed','result')}
  elif kind=='api_call' and e.get('name') in ('XCreateWindow','XCreateSimpleWindow'):
   self.pending_create[(e.get('thread'),e['name'])]={k:e.get(k) for k in ('probe_sequence','host_monotonic','elapsed','thread','name')}
  elif kind=='api_return' and e.get('name') in ('XCreateWindow','XCreateSimpleWindow'):
   pending=self.pending_create.pop((e.get('thread'),e['name']),None)
   if pending and isinstance(e.get('result'),int) and 0<e['result']<=0xffffffff:
    self.add(hex(e['result']),{'source':'original_application_API_call_and_return','entry':pending,'return':{k:e.get(k) for k in ('probe_sequence','host_monotonic','elapsed','thread','name','result')}})
  elif kind=='display_buffer_snapshot':
   for request in e.get('requests',[])+e.get('xcb',{}).get('requests',[]):
    if request.get('name')=='CreateWindow' and request.get('matches_returned_id') and request.get('window')==e.get('returned_window'):
     self.add(request['window'],{'source':'byte_validated_original_XCreateWindow_returned_XID_and_request','probe_sequence':e.get('probe_sequence'),'host_monotonic':e.get('host_monotonic'),'elapsed':e.get('elapsed'),'thread':e.get('thread'),'request':request,'display':e.get('display'),'descriptor':e.get('fields',{}).get('fd')},strong=True)
 def add(self,xid,evidence,strong=False):
  if not re.fullmatch(r'0x[0-9a-fA-F]{1,8}',xid):return
  if xid not in self.windows:
   if len(self.windows)>=MAX_ORIGINAL_WINDOWS:self.limit_reached=True;return
   self.windows[xid]={'window':xid,'ownership':evidence,'capture_count':0,'capture_attempts':0}
  elif strong:self.windows[xid]['ownership']=evidence
 def refresh(self,path):
  if not path.exists():return
  with path.open('r',errors='replace') as f:
   f.seek(self.offset);chunk=f.read(1048576);self.offset=f.tell()
  lines=(self.partial+chunk).split('\n');self.partial=lines.pop()
  # A huge final record is not required to identify windows; bounded carry.
  if len(self.partial)>2097152:self.partial='';self.read_errors.append('Oversized partial stdout record dropped')
  for line in lines:
   if not line.startswith('PROBE '):continue
   try:self.observe(json.loads(line[6:]))
   except (ValueError,TypeError,KeyError) as e:
    if len(self.read_errors)<8:self.read_errors.append(type(e).__name__+': '+str(e))
 def in_tree(self,text):
  # Match actual tree lines, never an XID merely mentioned in root/parent headers.
  ids=set(re.findall(r'^\s*(0x[0-9a-fA-F]+)\s+.*:\s+.*\d+x\d+',text,re.M))
  return [w for xid,w in self.windows.items() if xid in ids]
 def summary(self):
  return {'original_windows':list(self.windows.values()),'matched_enclosing_continuation':self.matched_enclosing_continuation,'stdout_bytes_consumed':self.offset,'read_errors':self.read_errors,'candidate_limit_reached':self.limit_reached,'input_sent':False,'capture_prerequisite':'original guest returned XID in current tree; exact InputOutput/IsViewable attributes','input_prerequisite':'current original returned XID plus owned private credentials and stable pixels; this observer sends no input'}

def window_attributes(text,xid):
 def field(name):
  m=re.search(r'^\s*'+re.escape(name)+r':\s*(.+)$',text,re.M);return m.group(1).strip() if m else None
 found=re.search(r'xwininfo: Window id:\s*(0x[0-9a-fA-F]+)',text)
 number=lambda name:int(field(name)) if field(name) and field(name).isdigit() else None
 return {'window':found.group(1) if found else None,'expected_window':xid,'exact_id_matches':bool(found and int(found.group(1),16)==int(xid,16)),'class':field('Class'),'map_state':field('Map State'),'width':number('Width'),'height':number('Height'),'depth':number('Depth'),'all_event_masks':field('All Event Masks')}

def drawable_eligible(attributes):
 return attributes['exact_id_matches'] and attributes['class']=='InputOutput' and attributes['map_state']=='IsViewable' and bool(attributes['width']) and bool(attributes['height']) and bool(attributes['depth'])

def pixel_summary(path):
 if path.stat().st_size>33554432:raise ValueError('XWD exceeds bounded 32MiB decode size')
 data=path.read_bytes();h=struct.unpack_from('>25I',data)
 size,version,fmt,depth,width,height,xoffset,order,unit,bitorder,pad,bpp,stride,vclass,red,green,blue,bits,cmap,ncolors,*_=h
 if version!=7 or fmt!=2 or bpp not in (8,16,24,32) or xoffset!=0:raise ValueError('Unsupported XWD pixel layout')
 pixels=data[size+ncolors*12:]
 if len(pixels)!=height*stride or width*bpp//8>stride or width*height>4194304:raise ValueError('Invalid or oversized XWD pixel payload')
 n=bpp//8;mask=red|green|blue
 nonblack=sum(bool(int.from_bytes(pixels[y*stride+x*n:y*stride+(x+1)*n],'little' if order==0 else 'big')&mask) for y in range(height) for x in range(width))
 return {'pixel_sha256':hashlib.sha256(pixels).hexdigest(),'nonblack_pixels':nonblack,'width':width,'height':height,'root_capture':False}

def main():
 p=argparse.ArgumentParser();p.add_argument('--stop-at',type=float,required=True);a=p.parse_args();rows=[];captures=[];helpers=[];drawable_rows=[];stopping=False;last_query=0;paint_marker=0;paint_captures=0;index=0;captured_child=False;final=False;last_children=0;change_captures=0;windows=OriginalWindows();changed_drawable_captures=0;detail_index=0;last_periodic=0
 def stop(*unused):
  nonlocal stopping
  stopping=True
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 def deadline():
  f=BASE/'observation-deadline.json'
  if f.exists():return min(a.stop_at,json.loads(f.read_text())['term_at'])
  return a.stop_at
 def save():
  (BASE/'display-observations.json').write_text(json.dumps({'observations':rows,'captures':captures,'drawable_observations':drawable_rows,'drawable_following':windows.summary(),'stopping':stopping,'current_deadline':deadline()},indent=2)+'\n')
 def command(argv,name):
  start=time.monotonic();limit=deadline()
  if stopping or start+2.1>=limit:return None
  row={'argv':argv,'started_monotonic':start,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timeout_seconds':2,'stdout':'logs/'+name+'.stdout.txt','stderr':'logs/'+name+'.stderr.txt'}
  proc=None
  with (BASE/row['stdout']).open('xb') as out,(BASE/row['stderr']).open('xb') as err:
   try:
    proc=subprocess.Popen(argv,env=environment(),stdout=out,stderr=err)
    row.update(pid=proc.pid)
    proc.wait(timeout=min(2,limit-time.monotonic()))
   except subprocess.TimeoutExpired:
    row['timeout']=True;proc.terminate()
    try:proc.wait(timeout=max(.001,min(.2,limit-time.monotonic())))
    except subprocess.TimeoutExpired:
     proc.kill()
     try:proc.wait(timeout=max(.001,min(.2,limit-time.monotonic())))
     except subprocess.TimeoutExpired:row['reap_failed']=True
   finally:
    row['exit_code']=proc.returncode if proc else None;row['finished_monotonic']=time.monotonic();row['reaped']=proc is not None and proc.returncode is not None
  return row
 def query():
  nonlocal index,last_query
  row=command([str(BASE/'display-bin/xwininfo'),'-display',':16','-root','-tree'],'window-tree-%03d'%index)
  if row:
   text=(BASE/row['stdout']).read_text(errors='replace');m=re.search(r'(\d+) child(?:ren)?[.:]',text);row.update(index=index,root_children=int(m.group(1)) if m else None);rows.append(row);last_query=row['finished_monotonic'];index+=1;save()
  return row
 def capture(name):
  target=BASE/'captures'/(name+'-root.xwd');row=command([str(BASE/'display-bin/xwd'),'-display',':16','-root','-silent','-out',str(target)],'capture-'+name)
  if row:row.update(path=str(target.relative_to(BASE)),bytes=target.stat().st_size if target.exists() else 0,scope='server root pixels; original drawable ownership requires correlated tree and guest evidence');captures.append(row);save()
 def capture_drawable(window,attributes,name,tree):
  xid=window['window'];attempt=window['capture_attempts'];window['capture_attempts']+=1;name=name+'-'+str(attempt);target=BASE/'captures'/(name+'-'+xid+'-drawable.xwd')
  row=command([str(BASE/'display-bin/xwd'),'-display',':16','-id',xid,'-silent','-out',str(target)],'capture-'+name+'-'+xid)
  if row:
   row.update(path=str(target.relative_to(BASE)),bytes=target.stat().st_size if target.exists() else 0,window=xid,scope='exact original guest-created InputOutput drawable',ownership=window['ownership'],attributes=attributes,correlated_tree=tree['stdout'],matched_enclosing_continuation=windows.matched_enclosing_continuation)
   if row['exit_code']==0 and target.exists():
    try:
     row.update(pixel_summary(target));row['pixels_changed_since_previous']=None if not window.get('last_pixel_sha256') else row['pixel_sha256']!=window['last_pixel_sha256'];window['last_pixel_sha256']=row['pixel_sha256'];window['capture_count']+=1
    except Exception as e:row['pixel_decode_error']=type(e).__name__+': '+str(e)
   captures.append(row);save()
 def follow_drawables(tree,final_capture=False,periodic=False):
  nonlocal changed_drawable_captures,detail_index
  windows.refresh(BASE/'supervision/guest.stdout.txt')
  if tree is None or tree['exit_code']!=0:return
  text=(BASE/tree['stdout']).read_text(errors='replace')
  eligible=[w for w in windows.in_tree(text) if w.get('last_attributes',{}).get('class')!='InputOnly']
  # Class is fixed at creation; an identified InputOnly window needs no repeat.
  # Rotate ordinary details so newly created candidates cannot starve behind four old ones.
  eligible.sort(key=lambda w:((not bool(w['capture_count'])) if final_capture else w.get('last_detail_index',-1)))
  for window in eligible[:MAX_DETAIL_QUERIES_PER_TREE]:
   xid=window['window'];row=command([str(BASE/'display-bin/xwininfo'),'-display',':16','-id',xid,'-stats','-events'],'original-window-%03d'%detail_index);detail_index+=1
   if not row:continue
   window['last_detail_index']=detail_index
   attributes=window_attributes((BASE/row['stdout']).read_text(errors='replace'),xid);row.update(attributes=attributes,window=xid,ownership=window['ownership'],correlated_tree=tree['stdout']);drawable_rows.append(row)
   previous=window.get('last_attributes');window['last_attributes']=attributes
   if row['exit_code']!=0 or not drawable_eligible(attributes):continue
   if not window['capture_count']:capture_drawable(window,attributes,'original-first',tree)
   elif final_capture or periodic:capture_drawable(window,attributes,'original-final' if final_capture else 'original-periodic',tree)
   elif attributes!=previous and changed_drawable_captures<MAX_CHANGED_DRAWABLE_CAPTURES:
    capture_drawable(window,attributes,'original-state-change-'+str(changed_drawable_captures),tree);changed_drawable_captures+=1
  save()
 try:
  info=command([str(BASE/'display-bin/xdpyinfo'),'-display',':16'],'xdpyinfo')
  if not info or info['exit_code']!=0:raise RuntimeError('xdpyinfo did not pass')
  helpers.append(info)
  row=query();capture('initial');follow_drawables(row);(BASE/'display-observer-ready.json').write_text(json.dumps({'ready_monotonic':time.monotonic(),'xdpyinfo':info})+'\n')
  while not stopping and time.monotonic()<deadline():
   now=time.monotonic()
   if (BASE/'observation-deadline.json').exists() and now>=deadline()-10 and not final:
    capture('final');row=query();follow_drawables(row,final_capture=True);final=True
   marker=BASE/'paint-capture-request.json'
   if marker.exists() and paint_captures<4 and now+2.1<deadline():
    request=json.loads(marker.read_text())
    if request['monotonic']>paint_marker and now>request['monotonic']+1:
     paint_marker=request['monotonic'];row=query();windows.refresh(BASE/'supervision/guest.stdout.txt')
     if row and row['exit_code']==0:
      for window in windows.in_tree((BASE/row['stdout']).read_text(errors='replace')):
       attributes=window.get('last_attributes',{})
       if attributes and drawable_eligible(attributes):capture_drawable(window,attributes,'after-paint-'+str(paint_captures),row)
     paint_captures+=1
   if captured_child and now-last_periodic>=45 and now+12<deadline():
    row=query();follow_drawables(row,periodic=True);last_periodic=now
   if now-last_query>=5 and now+2.1<deadline():
    row=query()
    if row and row['root_children'] and not captured_child:capture('first-children');captured_child=True
    if row and row['root_children'] is not None and row['root_children']!=last_children:
     if row['root_children']>1 and change_captures<4:capture('children-change-'+str(index));change_captures+=1
     last_children=row['root_children']
    follow_drawables(row)
   time.sleep(min(.05,max(0,deadline()-time.monotonic())))
 except BaseException as ex:
  (BASE/'display-observer-error.json').write_text(json.dumps({'type':type(ex).__name__,'message':str(ex),'monotonic':time.monotonic()})+'\n');raise
 finally:
  stopping=True;windows.refresh(BASE/'supervision/guest.stdout.txt');save();(BASE/'display-observer-closure.json').write_text(json.dumps({'end_monotonic':time.monotonic(),'all_recorded_helpers_reaped':all(r['reaped'] for r in rows+captures+helpers+drawable_rows)})+'\n')
if __name__=='__main__':main()
