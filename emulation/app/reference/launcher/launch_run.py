import json,pathlib,shutil,subprocess,time
E=pathlib.Path('/private/tmp/pioneer_current_lifecycle_run.txt').read_text().strip(); E=pathlib.Path(E); R=E/'run-1'; config=json.loads((E/'command.json').read_text()); clock=config['session_clock']
assert not (R/'attempt-consumed.json').exists(),'Consumed attempt cannot be relaunched'
assert time.monotonic()<clock['launch_latest_monotonic'],'Launch window expired'
shutil.copy2(__file__,E/'launch_run.py')
print(json.dumps({'launching':str(E),'observation_seconds':600,'input':False}),flush=True)
try:
 with (E/'observer-client.stdout.txt').open('x') as out,(E/'observer-client.stderr.txt').open('x') as err:
  result=subprocess.run(config['launch_argv'],cwd=E.parents[1],stdout=out,stderr=err)
 config['observer_client_exit']=result.returncode
finally:
 with (E/'postflight.stdout.json').open('x') as out,(E/'postflight.stderr.txt').open('x') as err:
  rc=subprocess.run(config['postflight_argv'],cwd=E.parents[1],stdout=out,stderr=err,timeout=max(1,clock['process_stop_monotonic']-time.monotonic())).returncode
 config['postflight_exit']=rc
 config['finished_monotonic']=time.monotonic();config['launches']=json.loads((R/'attempt-supervision.json').read_text()).get('guest_processes_created')
 (E/'command-result.json').write_text(json.dumps(config,indent=2)+'\n')
print(json.dumps({'observer_client_exit':config.get('observer_client_exit'),'postflight_exit':rc,'guest_processes_created':config['launches'],'experiment':str(E)}),flush=True)
raise SystemExit(int(bool(config.get('observer_client_exit') or rc)))
