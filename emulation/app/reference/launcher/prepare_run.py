import ast,datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time
from zoneinfo import ZoneInfo
P=pathlib.Path('<RESEARCH_ROOT>')
OLD='<RESEARCH_ROOT>'
B=P/'experiments/audit-remediation-20261009'; S=P/'experiments/input-response-preparation-20261009/prepared'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
name='startup-lifecycle-live-'+datetime.datetime.now(ZoneInfo('America/Chicago')).strftime('%Y%m%d-%H%M%S')
E=P/'experiments'/name; E.mkdir(); R=E/'run-1'; start=time.monotonic(); end=start+1200
clock=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),started_monotonic=start,authorized_guest_attempts=1,observation_seconds=600,total_budget_seconds=1200,launch_latest_monotonic=start+120,process_stop_monotonic=end,session_deadlines=dict(term_at=end-5,kill_at=end-2,reap_at=end),input_authorized=False,authorized_input_interactions=0,max_conditional_tagged_interactions=0,authorization='User: Do we need to fire up a guest? if so, let\'s do that and get started with the test. Bounded implementation: one fresh 600s original application guest and owned observation/display/watchdog helpers within 1200s; no input or replacement guest.')
(E/'session-clock.json').write_text(json.dumps(clock,indent=2)+'\n')
shutil.copy2(__file__,E/'prepare_run.py')
for n in ['attempt-consumed.json','session-clock.json','display.xauth','rootfs/root/display.xauth','supervision/attempt-owned']:
 assert not (S/n).exists(),n
v=read(B/'overlay/lifecycle-validation.json')
assert v['passed'] and v['no_input'] and v['baseline_clock_retained']
for row in v['code_identities']: assert sha(B/'overlay'/row['path'])==row['sha256'],row['path']
assert read(B/'cleanup/focused-controls.json')['passed'] and read(B/'lifecycle/offline-controls.json')['passed']
shutil.copytree(S,R,symlinks=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copytree(B/'overlay',R,dirs_exist_ok=True)
shutil.copy2(B/'supervision-validation.json',E/'supervision-validation.json')
(R/'session-clock.json').write_text(json.dumps(clock,indent=2)+'\n')
repairs=[]
for d,dirs,files in os.walk(R,followlinks=False):
 for n in dirs+files:
  p=pathlib.Path(d)/n
  if p.is_symlink():
   target=os.readlink(p)
   if target.startswith(OLD+'/'):
    new=str(P)+target[len(OLD):]; assert pathlib.Path(new).exists(),new
    p.unlink();p.symlink_to(new);repairs.append(dict(path=str(p.relative_to(R)),old=target,new=new))
w=R/'xkbcomp-wrapper.sh'; old=w.read_text(); new=old.replace(OLD,str(P)); assert new!=old
w.write_text(new);assert 'Code Projects' not in new
for q in [P/'experiments/post-parent-startup-20261008-150354/display-bin/xkbcomp',P/'experiments/post-parent-startup-20261008-150354/xquartz-package/XQuartzComponent.pkg/Payload/opt/X11/lib']:assert q.exists()
repairs.append(dict(path=w.name,old_sha256=hashlib.sha256(old.encode()).hexdigest(),new_sha256=sha(w),change='Relocated host paths only'))
base=read(P/'experiments/input-response-live-20261009/run-1/observer-validation.json')
changed={r['path'] for r in v['code_identities']}
unchanged=[]
for row in base['code_identities']:
 if row['path'] in changed:continue
 assert sha(R/row['path'])==row['sha256'],'Unexplained seed mismatch '+row['path']
 unchanged.append(row)
for q in R.rglob('*.py'):
 if '/rootfs/' not in str(q) and '/xquartz-package/' not in str(q):ast.parse(q.read_text())
obs=dict(passed=True,code_identities=unchanged+v['code_identities'],reused_validation=str(P/'experiments/input-response-preparation-20261009/reused-validation.json'),provenance=dict(unchanged_observer_manifest=str(P/'experiments/input-response-live-20261009/run-1/observer-validation.json'),unchanged_seed_identity_comparison=True,changed_overlay_manifest=str(B/'overlay/lifecycle-validation.json'),changed_contract_controls=v['controls'],path_relocation_repairs=repairs),guards_unchanged=True,new_hooks_controlled=True,no_input=True,live_integration_unvalidated=True)
(R/'observer-validation.json').write_text(json.dumps(obs,indent=2)+'\n')
PYTHON=P/'experiments/emulation-20261007/tools/venv/bin/python'
assert sha(PYTHON)==read(R/'runtime-identity.json')['python_sha256']
assert sha(R/'display-bin/Xvfb')==read(R/'runtime-identity.json')['display_binary_sha256']
argv=[str(PYTHON),'-B','-u',str(R/'run_once.py'),'--seconds','600','--cooperative-main','--post-font-count','313370']
config=dict(experiment=str(E),seed=str(S),overlay=str(B/'overlay'),session_clock=clock,launch_argv=argv,postflight_argv=[str(PYTHON),'-B',str(R/'postflight_native.py')],relocation_repairs=repairs,baseline_clock_retained=True,input_allowed=False,overlay_identities=v['code_identities'],wrapper_identity=sha(w),launches=0)
(E/'command.json').write_text(json.dumps(config,indent=2)+'\n')
with (E/'preflight.stdout.json').open('w') as out,(E/'preflight.stderr.txt').open('w') as err:
 rc=subprocess.run([str(PYTHON),'-B',str(R/'preflight_native.py')],cwd=P,stdout=out,stderr=err,timeout=25).returncode
print(json.dumps(dict(experiment=str(E),preflight_exit=rc,preflight_passed=read(R/'endpoint-preflight-initial.json')['passed'],elapsed=time.monotonic()-start,remaining=end-time.monotonic(),launch_argv=argv)),flush=True)
assert rc==0,'Preflight failed; no helpers or guest launched'
assert time.monotonic()<clock['launch_latest_monotonic'],'Launch window expired'
pathlib.Path('/private/tmp/pioneer_current_lifecycle_run.txt').write_text(str(E)+'\n')
