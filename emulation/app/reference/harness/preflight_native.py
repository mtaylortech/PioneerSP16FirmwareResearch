"""Read-only native process/endpoint census; never signal or change endpoints."""
import datetime,json,os,pathlib,stat,subprocess,time
BASE=pathlib.Path(__file__).resolve().parent
def main():
 r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'monotonic':time.monotonic(),'paths':{},'commands':[]}
 for p in ['/private/tmp/.X11-unix','/private/tmp/.X11-unix/X16','/private/tmp/.X16-lock','/private/tmp/p16008x']:
  try:
   s=os.lstat(p);r['paths'][p]={'exists':True,'uid':s.st_uid,'gid':s.st_gid,'mode':oct(stat.S_IMODE(s.st_mode)),'type':stat.S_IFMT(s.st_mode),'is_symlink':stat.S_ISLNK(s.st_mode)}
  except FileNotFoundError:r['paths'][p]={'exists':False}
 for name,argv in [('processes',['ps','-axo','pid,ppid,pgid,state,command']),('tcp',['lsof','-nP','-iTCP:6016','-sTCP:LISTEN'])]:
  z=subprocess.run(argv,capture_output=True,text=True,timeout=10)
  (BASE/(name+'-preflight.stdout.txt')).write_text(z.stdout);(BASE/(name+'-preflight.stderr.txt')).write_text(z.stderr)
  r['commands'].append({'argv':argv,'exit':z.returncode,'stdout':name+'-preflight.stdout.txt','stderr':name+'-preflight.stderr.txt'})
  r[name]=[x for x in z.stdout.splitlines() if any(k in x for k in ['/probe.py','/Xvfb', '/display_server.py','/supervise_attempt.py','/xkbcomp'])] if name=='processes' else z.stdout
 d=r['paths']['/private/tmp/.X11-unix']
 fixtures=['static/mapping.json','alsa-null.conf','null-device','full-device','xkbcomp-wrapper.sh','xquartz-package/XQuartzComponent.pkg/Payload/opt/X11/lib']
 r['required_fixture_paths']={name:(BASE/name).exists() for name in fixtures}
 r['passed']=all(r['required_fixture_paths'].values()) and d.get('uid')==0 and d.get('mode')=='0o1777' and not d.get('is_symlink') and all(not r['paths'][p]['exists'] for p in ['/private/tmp/.X11-unix/X16','/private/tmp/.X16-lock','/private/tmp/p16008x']) and not r['processes'] and not r['tcp'] and r['commands'][0]['exit']==0 and r['commands'][1]['exit'] in (0,1) and not (BASE/r['commands'][1]['stderr']).read_text().strip()
 (BASE/'endpoint-preflight-initial.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
