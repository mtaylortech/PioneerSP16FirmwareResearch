"""New observer integration and retained parser/scheduling gates; no guest."""
import argparse,ast,contextlib,hashlib,io,json,pathlib,sys,time,types
B=pathlib.Path(__file__).resolve().parent
PROJECT=next(p for p in B.parents if (p/'README.md').exists() and (p/'experiments').is_dir())
SOURCE=PROJECT/'experiments/cooperative-font-20261008/common';rows=[]
changed=[]
for p in SOURCE.glob('*.py'):
 if p.name=='run_once.py':continue
 q=B/p.name
 assert q.exists()
 if q.read_bytes()!=p.read_bytes():changed.append(p.name)
assert changed==['probe.py']
probe=(B/'probe.py').read_text();original=(SOURCE/'probe.py').read_text();normalized=probe
normalized=normalized.replace('from active_enclosing_observer import ActiveEnclosingObserver\nfrom x11_event_observer import OriginalX11Events','from active_enclosing_observer import ActiveEnclosingObserver')
normalized=normalized.replace('active_enclosing.install(q); input_events.install(q); font_quantum.install(q)','active_enclosing.install(q); font_quantum.install(q)')
normalized=normalized.replace('active_enclosing = ActiveEnclosingObserver(event, started, discovery)\ninput_events = OriginalX11Events(event, started, discovery, BASE)','active_enclosing = ActiveEnclosingObserver(event, started, discovery)')
normalized=normalized.replace('active_enclosing=active_enclosing.summary(),original_x11_events=input_events.summary())','active_enclosing=active_enclosing.summary())',1)
normalized=normalized.replace('"active_enclosing":active_enclosing.summary(), "original_x11_events":input_events.summary(),','"active_enclosing":active_enclosing.summary(),')
normalized=normalized.replace('            # Permanent OriginalX11Events owns exact XNextEvent returns/payloads.\n            # Retire this API\'s one-shot hook to avoid mutable callback-list collisions.\n            if name=="XNextEvent": return\n','',1)
assert normalized==original
rows.append({'control':'exact_inherited_sources_and_reverse_observer_patch_equal_original_cooperative_probe','passed':True,'changed_inherited_files':changed,'scheduling_wrappers_byte_identical':True})
# Evaluate only the real parser/guard AST; imports and runtime initialization are absent.
nodes=[];collect=False
for node in ast.parse(probe).body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='parser' for t in node.targets):collect=True
 if collect:nodes.append(node)
 if collect and isinstance(node,ast.If) and 'args.cooperative_font' in ast.unparse(node.test):break
code=compile(ast.Module(body=nodes,type_ignores=[]),str(B/'probe.py'),'exec')
def parse(argv):
 prior=sys.argv;sys.argv=['conditional-parser-control']+argv;namespace={'argparse':argparse};stderr=io.StringIO()
 try:
  with contextlib.redirect_stderr(stderr):exec(code,namespace)
  return namespace['args'],None,stderr.getvalue()
 except SystemExit as e:return None,e.code,stderr.getvalue()
 finally:sys.argv=prior
args,status,error=parse(['--cooperative-font','--font-scan-quantum','--startup-through-font','--post-font-count','313370','--seconds','600'])
assert args.cooperative_font and args.font_scan_quantum and args.startup_through_font and not args.main_startup_quantum and args.post_font_count==313370 and args.seconds==600
for argv in (['--cooperative-font'],['--cooperative-font','--font-scan-quantum','--main-startup-quantum'],['--post-font-count','999999']):
 args,status,error=parse(argv);assert status==2 and error
args,status,error=parse(['--font-scan-quantum','--startup-through-font','--post-font-count','313370']);assert not args.cooperative_font and args.post_font_count==313370
rows.append({'control':'real_parser_accepts_selected_conditional600_cooperative_flags_rejects_missing_quantum_broad_and_unselected_counts_timed_option_preserved','passed':True})
sys.path.insert(0,str(B))
from syscall_boundary_quantum import SyscallBoundaryQuantum,DEFAULT_COUNT,SCAN_EPILOGUE
from font_discovery_observer import FontDiscoveryObserver
app=PROJECT/'experiments/post-font-counted-quantum-20261008-repeat/control/rootfs/root/pdj/EP085_Main_R';disc=FontDiscoveryObserver(lambda *a,**k:None,time.monotonic(),app);disc.main_tid=2000
now=[0.0];calls=[];order=[];hooks={}
os=types.SimpleNamespace(thread_management=types.SimpleNamespace(cur_thread=types.SimpleNamespace(id=2000)),sched_cb='before')
def dispatch(*a,**kw):order.append('original_dispatch');os.sched_cb='retained callback';return -1
os.load_syscall=dispatch
def native(begin,end,timeout=0,count=0):
 calls.append({'begin':begin,'end':end,'timeout':timeout,'count':count});order.append('native');now[0]+=.02;assert q.os.load_syscall('denied guard')==-1;return 17
q=types.SimpleNamespace(arch=types.SimpleNamespace(regs=types.SimpleNamespace(arch_pc=SCAN_EPILOGUE)),os=os,uc=types.SimpleNamespace(ctl_flush_tb=lambda:None),emu_start=native,emu_stop=lambda:order.append('cooperative_stop'),mem=types.SimpleNamespace(read=lambda address,n:disc.expected(address)),hook_address=lambda cb,address:hooks.update({address:cb}))
f=SyscallBoundaryQuantum(lambda *a,**k:None,0,disc,clock=lambda:now[0],post_count=313370);f.install(q)
assert q.emu_start(1,2,count=DEFAULT_COUNT)==17 and calls[-1]['count']==0 and order==['native','original_dispatch','cooperative_stop'] and os.sched_cb=='retained callback'
for tid,count,timeout in ((2000,DEFAULT_COUNT,20000),(2001,DEFAULT_COUNT,0),(2000,7,0)):
 q.os.thread_management.cur_thread.id=tid;before=order.count('cooperative_stop');assert q.emu_start(1,2,count=count,timeout=timeout)==17;assert calls[-1]['count']==count and calls[-1]['timeout']==timeout and order.count('cooperative_stop')==before
q.os.thread_management.cur_thread.id=2000;f.active=True;hooks[SCAN_EPILOGUE](q);assert not f.startup_scope_completed
disc.frames['original_font_scan']={};hooks[SCAN_EPILOGUE](q);assert f.startup_scope_completed
q.emu_start(1,2,count=DEFAULT_COUNT);assert calls[-1]['count']==313370 and calls[-1]['timeout']==0
rows.append({'control':'explicit_timeouts_workers_nondefault_counts_retained_original_guard_dispatch_before_stop_and_phase_limited_count_reversion','passed':True,'isolated_mock_only':True})
assert '"original_x11_events":input_events.summary(),' in probe and 'original_x11_events=input_events.summary()' in probe
controls=json.loads((B/'input-controls.json').read_text());assert controls['passed'] and controls['original_application_guests_launched']==0
result={'passed':True,'original_application_guests_launched':0,'helpers_launched':0,'original_app_sha256':disc.app_sha256,'input_mock_controls':len(controls['controls']),'controls':rows,'preserved_scheduling_sources':{name:hashlib.sha256((B/name).read_bytes()).hexdigest() for name in ('syscall_boundary_quantum.py','font_scan_quantum.py')},'input_helpers_do_not_autoexecute':True}
(B/'cooperative-integration-controls.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
