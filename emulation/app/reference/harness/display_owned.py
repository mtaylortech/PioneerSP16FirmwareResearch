"""One disposable authenticated Unix X16 fixture; owns/reaps its direct server."""
import argparse,datetime,json,os,pathlib,secrets,shutil,signal,stat,struct,subprocess,time
BASE=pathlib.Path(__file__).resolve().parent
X11=BASE/'xquartz-package/XQuartzComponent.pkg/Payload/opt/X11'
HELPER=pathlib.Path('/private/tmp/p16008x')
def environment():
 return dict(os.environ,DYLD_LIBRARY_PATH=str(X11/'lib'),XAUTHORITY=str(BASE/'display.xauth'),DISPLAY=':16',XKB_CONFIG_ROOT=str(X11/'share/X11/xkb'),LC_ALL='C',LANG='C',PYTHONDONTWRITEBYTECODE='1')
def main():
 p=argparse.ArgumentParser();p.add_argument('--stop-at',type=float,required=True);a=p.parse_args()
 state={'start_monotonic':time.monotonic(),'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wrapper_pid':os.getpid(),'wrapper_pgid':os.getpgrp(),'stop_at':a.stop_at};proc=None;owned_helper=False;stopping=False
 def save():
  (BASE/'display-process.json').write_text(json.dumps(state,indent=2)+'\n')
 def stop(*unused):
  nonlocal stopping
  stopping=True
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 try:
  if time.monotonic()+10>=a.stop_at:raise RuntimeError('No bounded setup time remains')
  d=pathlib.Path('/private/tmp/.X11-unix').lstat()
  if d.st_uid!=0 or stat.S_IMODE(d.st_mode)!=0o1777 or not stat.S_ISDIR(d.st_mode):raise RuntimeError('Shared socket directory prerequisite differs')
  for path in [HELPER,pathlib.Path('/private/tmp/.X11-unix/X16'),pathlib.Path('/private/tmp/.X16-lock')]:
   if os.path.lexists(path):raise RuntimeError('Occupied fixture prerequisite: '+str(path))
  cookie=secrets.token_bytes(16)
  field=lambda x:struct.pack('>H',len(x))+x
  content=b''.join(struct.pack('>H',65535)+field(b'')+field(n)+field(b'MIT-MAGIC-COOKIE-1')+field(cookie) for n in (b'0',b'16'))
  for path in [BASE/'display.xauth',BASE/'rootfs/root/display.xauth']:
   with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(content)
  state['authentication']={'kind':'MIT-MAGIC-COOKIE-1','actual_mapped_equal':(BASE/'display.xauth').read_bytes()==(BASE/'rootfs/root/display.xauth').read_bytes(),'mode':'0600','value_logged':False}
  HELPER.mkdir(mode=0o700);owned_helper=True
  shutil.copy2(BASE/'xkbcomp-wrapper.sh',HELPER/'xkbcomp')
  marker={'owner_pid':os.getpid(),'root':str(BASE),'directory_inode':HELPER.stat().st_ino}
  (HELPER/'owner.json').write_text(json.dumps(marker));state['helper']=marker;save()
  fonts=','.join(str(X11/'share/fonts'/n) for n in ('misc','TTF','OTF','Type1','100dpi','75dpi') if (X11/'share/fonts'/n).is_dir())
  argv=[str(BASE/'display-bin/Xvfb'),':16','-screen','0','800x480x24','-nolisten','tcp','-auth',str(BASE/'display.xauth'),'-noreset','-fp',fonts,'-xkbdir',str(X11/'share/X11/xkb'),'-extension','MIT-SHM']
  state['argv']=argv
  if stopping or time.monotonic()+1>=a.stop_at:raise RuntimeError('Stop/deadline during display preparation; no server launch')
  with (BASE/'logs/xvfb-server.stdout-stderr.txt').open('xb') as log:
   proc=subprocess.Popen(argv,env=environment(),stdout=log,stderr=log)
   state['server_pid']=proc.pid;state['server_pgid']=os.getpgid(proc.pid);save()
   while proc.poll() is None and not stopping and time.monotonic()<a.stop_at:time.sleep(.05)
   state['stopping_condition']='signal/absolute deadline' if proc.poll() is None else 'server exited'
 except BaseException as ex:
  state['exception']={'type':type(ex).__name__,'message':str(ex)}
 finally:
  if proc is not None:
   cleanup_start=time.monotonic()
   if proc.poll() is None:proc.terminate()
   until=min(cleanup_start+2.2,a.stop_at+3)
   while proc.poll() is None and time.monotonic()<until:time.sleep(.025)
   if proc.poll() is None:proc.kill()
   try:proc.wait(timeout=max(.01,min(.3,a.stop_at+5-time.monotonic())))
   except subprocess.TimeoutExpired:state['reap_failed']=True
   state['server_exit_code']=proc.returncode;state['server_reaped']=proc.returncode is not None
  if owned_helper:
   # Only the just-created directory, marker and exact copied wrapper are removed.
   try:
    current=json.loads((HELPER/'owner.json').read_text())
    if current!=state['helper'] or HELPER.stat().st_ino!=current['directory_inode'] or (HELPER/'xkbcomp').read_bytes()!=(BASE/'xkbcomp-wrapper.sh').read_bytes():raise RuntimeError('Helper ownership/content contradiction')
    (HELPER/'xkbcomp').unlink();(HELPER/'owner.json').unlink();HELPER.rmdir();state['helper_removed']=True
   except Exception as ex:state['helper_cleanup_error']=str(ex)
  state['end_monotonic']=time.monotonic();state['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print(json.dumps(state),flush=True)
 return 1 if state.get('exception') or state.get('reap_failed') or state.get('helper_cleanup_error') else 0
if __name__=='__main__':raise SystemExit(main())
