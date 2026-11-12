"""Single authorized launch gate and observer client; watchdog owns every runtime group."""
import datetime,hashlib,json,os,pathlib,signal,stat,sys,time,traceback
from supervision.supervisor import WatchdogClient
from supervision.runtime_limits import ObservationLimits, verify_tested_supervision
from local_display import verify_endpoint
from stop_policy import decisive_event
from outcome_policy import launch_failed
BASE=pathlib.Path(__file__).resolve().parent;PROJECT=BASE.parents[2]
PYTHON=PROJECT/'experiments/emulation-20261007/tools/venv/bin/python'
LABEL=BASE.parent.name+'-'+BASE.name
REUSED=PROJECT/'experiments/full-font-cache-20261008-1614-next-20261008-1712'
FLAGS=['--library-aliases','--high-loader','--null-audio','--trace-startup','--trace-affinity','--local-ipc','--epoll-fixture','--fast','--correct-arm-tls','--local-display','--font-scan-quantum','--startup-through-font','--startup-lifecycle']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def stamp():return {'monotonic':time.monotonic(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def main():
 import argparse
 parser=argparse.ArgumentParser()
 parser.add_argument('--seconds',type=int,required=True)
 parser.add_argument('--cooperative-font',action='store_true')
 parser.add_argument('--cooperative-main',action='store_true')
 parser.add_argument("--main-startup-quantum",action="store_true")
 parser.add_argument("--post-font-count",type=int,choices=(31337,313370),required=True)
 options=parser.parse_args()
 if options.seconds!=600 or not options.cooperative_main or options.post_font_count!=313370:raise RuntimeError('Lifecycle plan requires 600s cooperative-main/count313370')
 timing=ObservationLimits(options.seconds)
 flags=[f for f in FLAGS if f!="--startup-through-font"]+["--main-startup-quantum" if options.main_startup_quantum else "--startup-through-font"]
 flags += ['--seconds',str(timing.observation_seconds)]
 if options.cooperative_font:flags += ['--cooperative-font']
 if options.cooperative_main:flags += ['--cooperative-main']
 flags += ["--post-font-count",str(options.post_font_count)]
 clock=json.loads((BASE/'session-clock.json').read_text());stop_at=clock['process_stop_monotonic'];launch_at=clock['launch_latest_monotonic'];client=None;report={'start':stamp(),'guest_processes_created':0,'label':LABEL,'authorization':clock.get('authorization'),'controls':str(REUSED/'supervision/controls-02/control-results.json')}
 def save():
  (BASE/'attempt-supervision.json').write_text(json.dumps(report,indent=2)+'\n')
 def interrupted(*unused):raise KeyboardInterrupt('observer client interrupted')
 signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
 try:
  if clock.get('authorized_guest_attempts')!=1:raise RuntimeError('Fresh single-attempt authorization missing')
  if clock.get('observation_seconds')!=timing.observation_seconds:raise RuntimeError('Selected observation differs from authorized session configuration')
  if clock.get('authorized_input_interactions',0)!=0 or clock.get('input_authorized',False) or clock.get('max_conditional_tagged_interactions',0)!=0:raise RuntimeError('Lifecycle experiment has no input scope')
  if clock.get('total_budget_seconds')!=1200:raise RuntimeError('Lifecycle plan requires a fresh 1200s session ceiling')
  lifecycle_ready=json.loads((BASE/'lifecycle-validation.json').read_text())
  if not lifecycle_ready['passed']:raise RuntimeError('Lifecycle controls did not pass')
  for row in lifecycle_ready['code_identities']:
   if sha(BASE/row['path'])!=row['sha256']:raise RuntimeError('Lifecycle validated identity changed '+row['path'])
  timing.require_budget(time.monotonic(),stop_at,before_setup=True)
  if time.monotonic()>=launch_at:raise RuntimeError('Launch window closed')
  report['duration_configuration']=timing.configuration()
  if not json.loads((REUSED/'supervision/controls-02/control-results.json').read_text())['passed']:raise RuntimeError('Reused supervisor controls did not pass')
  ready=json.loads((BASE/'observer-validation.json').read_text())
  if not ready['passed']:raise RuntimeError('Layout observer controls did not pass')
  for row in ready['code_identities']:
   if sha(BASE/row['path'])!=row['sha256']:raise RuntimeError('Validated code identity changed '+row['path'])
  report['supervision_validation']=str(BASE.parent/'supervision-validation.json')
  verify_tested_supervision(BASE/'supervision',report['supervision_validation'])
  if not json.loads((REUSED/'fresh-launch-checks.json').read_text())['cleanup_permission_controls']['passed']:raise RuntimeError('Focused cleanup PermissionError controls did not pass')
  if not json.loads((BASE/'endpoint-preflight-initial.json').read_text())['passed']:raise RuntimeError('Fresh native preflight did not pass')
  if any(p.exists() for p in (BASE/'display.xauth',BASE/'rootfs/root/display.xauth')):raise RuntimeError('Fresh private credential paths occupied')
  versions=json.loads((BASE/'runtime-versions.stdout.json').read_text())
  if not versions['python'].startswith('3.10.1 ') or versions['qiling']!='1.4.6' or versions['unicorn']!='2.1.4':raise RuntimeError('Runtime version contradiction')
  if sha(PYTHON)!=json.loads((BASE/'runtime-identity.json').read_text())['python_sha256']:raise RuntimeError('Interpreter identity differs')
  report['identity_checks']=[]
  app=BASE/'rootfs/root/pdj/EP085_Main_R';actual=sha(app)
  report['identity_checks'].append({'path':str(app),'sha256':actual,'matches':actual=='3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464'})
  if not report['identity_checks'][-1]['matches']:raise RuntimeError('Original app identity differs')
  baseline=json.loads((PROJECT/'experiments/emulation-startup-20261008-105916/integrity-verification.json').read_text())
  for row in baseline['elf_identity']:
   if not any(k in row['guest_path'] for k in ('EP085_Main_R','libc.so','libpthread.so')):continue
   f=BASE/'rootfs'/row['guest_path'];actual=sha(f)
   if actual!=row['sha256']:raise RuntimeError('Original ELF identity differs '+str(f))
   report['identity_checks'].append({'path':str(f),'sha256':actual,'matches':True})
  d=pathlib.Path('/private/tmp/.X11-unix').lstat()
  if d.st_uid!=0 or stat.S_IMODE(d.st_mode)!=0o1777 or not stat.S_ISDIR(d.st_mode):raise RuntimeError('Shared directory contradiction')
  for p in ['/private/tmp/.X11-unix/X16','/private/tmp/.X16-lock','/private/tmp/p16008x']:
   if os.path.lexists(p):raise RuntimeError('Occupied launch prerequisite '+p)
  # Build an explicit nonsecret host environment. The guest's Linux env/profile
  # remain the held harness dictionaries below; no external endpoint is added.
  host_env={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','HOME':str(pathlib.Path.home()),'TMPDIR':os.environ.get('TMPDIR','/private/tmp'),'LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}
  report['host_child_environment']=host_env
  report['guest_environment']={'LD_LIBRARY_PATH':'/lib:/usr/lib','HOME':'/root','DISPLAY':':0','XAUTHORITY':'/root/display.xauth'}
  report['guest_profile']={'KERNEL':{'uid':'0','gid':'0'},'MISC':{'current_path':'/root/pdj'},'OS32':{'interp_address':'0x70000000'}}
  report['code_identities']=[{'path':str(p.relative_to(BASE)),'sha256':sha(p)} for p in list(BASE.glob('*.py'))+list((BASE/'static').glob('*.py'))+list((BASE/'supervision').glob('*.py'))+list((BASE/'review').glob('*.py'))]
  save()
  client=WatchdogClient.start(BASE/'supervision/attempt-owned',session_stop_at=stop_at,python=PYTHON,ready_deadline=min(time.monotonic()+3,launch_at),observation_seconds=timing.observation_seconds)
  def spawn(role,script):
   return client.spawn(role,[str(PYTHON),'-B','-u',str(BASE/script),'--stop-at',str(stop_at-5)],cwd=PROJECT,stdout=BASE/'supervision'/f'{role}.stdout.txt',stderr=BASE/'supervision'/f'{role}.stderr.txt',env=host_env,deadline=min(time.monotonic()+2,launch_at))
  report['display']=spawn('display','display_owned.py');save()
  ready=min(time.monotonic()+10,launch_at)
  while time.monotonic()+2<ready:
   try:report['authenticated_endpoint']=verify_endpoint(BASE/'display.xauth');break
   except (OSError,ValueError,RuntimeError):
    state=client.read_state()
    if state.get('failure') or any(g['exit_code'] is not None for g in state['groups']):raise RuntimeError('Display/watchdog exited during setup')
    time.sleep(.05)
  else:raise RuntimeError('Authenticated display setup deadline')
  report['display_observer']=spawn('display-observer','display_observer.py');save()
  ready=min(time.monotonic()+5,launch_at)
  while not (BASE/'display-observer-ready.json').exists():
   if time.monotonic()>=ready:raise RuntimeError('Server observation setup deadline')
   if (BASE/'display-observer-error.json').exists():raise RuntimeError('Server observation setup failed')
   time.sleep(.025)
  timing.require_budget(time.monotonic(),stop_at)
  if time.monotonic()>=launch_at:raise RuntimeError('Guest launch window closed')
  argv=[str(PYTHON),'-X','faulthandler','-B','-u',str(BASE/'probe.py'),'--label',LABEL]+flags
  (BASE/'attempt-consumed.json').write_text(json.dumps({'created':stamp(),'argv':argv,'rule':f'One guest per fresh attempt; {timing.observation_seconds}s observation and independent +5/+8/+10 bounds plus session deadline.'},indent=2)+'\n') if not (BASE/'attempt-consumed.json').exists() else (_ for _ in ()).throw(RuntimeError('Attempt already consumed'))
  now=time.monotonic()
  armed=timing.deadlines(now)
  actual=client.set_deadlines(**armed,deadline=now+1)
  report['deadline_armed']={'monotonic':now,'observation_seconds':timing.observation_seconds,'requested':armed,'effective':actual};save()
  report['guest']=client.spawn('guest',argv,cwd=PROJECT,stdout=BASE/'supervision/guest.stdout.txt',stderr=BASE/'supervision/guest.stderr.txt',env=host_env,attempt=True,deadline=min(time.monotonic()+2,launch_at));report['guest_processes_created']=1
  (BASE/'observation-deadline.tmp').write_text(json.dumps(report['guest']['deadlines'])+'\n');os.replace(BASE/'observation-deadline.tmp',BASE/'observation-deadline.json');save();print(json.dumps({'guest_started':report['guest'],'label':LABEL}),flush=True)
  last_print=0;offset=0;pending=""
  while client.proc.poll() is None:
   state=client.read_state();now=time.monotonic();term=report['guest']['deadlines']['term_at']
   if state.get('failure') and state['phase']=='running':client.stop('watchdog failure',deadline=min(now+1,term),failure=True)
   if state['phase']=='running' and now+1<term and any(g['role']!='guest' and g['exit_code'] is not None for g in state['groups']):client.stop('unexpected display/helper leader exit',deadline=now+1,failure=True)
   # Inspect only newly available raw event bytes; faults are decisive, alarm is advisory.
   with (BASE/'supervision/guest.stdout.txt').open() as f:
    f.seek(offset);new=f.read();offset=f.tell()
   pending+=new
   complete=pending.split('\n');pending=complete.pop()
   for line in complete:
    if line.startswith('PROBE '):
     event=json.loads(line[6:])
     if decisive_event(event):
      if now+1<term:client.stop('decisive unexplained guest fault/denied operation',deadline=now+1,failure=True)
      break
   if (BASE/'display-observer-error.json').exists() and now+1<term:client.stop('display observer failure',deadline=now+1,failure=True)
   if now-last_print>=10:
    last_print=now;print(json.dumps({'observed_guest_elapsed':now-report['guest']['started_monotonic'],'watchdog_phase':state['phase'],'failure':state['failure']}),flush=True)
   time.sleep(.05)
  report['closure']=client.wait_closed(deadline=report['guest']['deadlines']['reap_at'])
 except BaseException as ex:
  report['exception']={'type':type(ex).__name__,'message':str(ex),'traceback':traceback.format_exc()};print(json.dumps(report['exception']),flush=True)
 finally:
  if client is not None:
   if client.proc.poll() is None:
    try:client.stop('observer finally/exception',deadline=time.monotonic()+1,failure=bool(report.get('exception')))
    except Exception as ex:report['cleanup_request_error']=repr(ex)
   while 'closure' not in report:
    try:report['closure']=client.wait_closed(deadline=time.monotonic()+1)
    except TimeoutError:
     report['essential_cleanup_continues']=stamp();save();print('Essential cleanup continues; owned closure not yet confirmed',flush=True)
    except BaseException as ex:report['cleanup_failure']=repr(ex);save();raise
  report['finished']=stamp();report['endpoints']={p:os.path.lexists(p) for p in ['/private/tmp/.X11-unix/X16','/private/tmp/.X16-lock','/private/tmp/p16008x']};report['native_final_present']=(BASE/(LABEL+'-result.json')).exists();report['native_outcome']=json.loads((BASE/(LABEL+'-result.json')).read_text()).get('outcome') if report['native_final_present'] else None;save();print(json.dumps({'finished':report['finished'],'guest_processes_created':report['guest_processes_created'],'endpoints':report['endpoints'],'exception':report.get('exception'),'native_final_present':report['native_final_present']}),flush=True)
 return int(launch_failed(report))
if __name__=='__main__':raise SystemExit(main())
