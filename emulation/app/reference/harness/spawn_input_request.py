"""Prepare/reuse one existing watchdog spawn; never starts a guest or supervisor.

Without --spawn this prints the nonsecret request only. --execute is passed to
the optional helper only when explicitly supplied by the controlling agent.
Existing owner, deadlines, private credentials and cleanup remain unchanged.
"""
import argparse,importlib.util,json,os,pathlib,stat,time
from live_prerequisite import validate_for_send

def prepare(run,python,execute=False,interaction='click',xid=0,x=None,y=None):
 if execute:
  if interaction!='click' or [x,y]!=[250,350]:raise ValueError('Only prepared Track 2 click is permitted')
  validate_for_send(run,xid)
 run=run.resolve();owned=run/'supervision/attempt-owned';launcher=json.loads((owned/'launcher.json').read_text());state=json.loads((owned/'state.json').read_text());now=time.monotonic()
 if state.get('phase')!='running' or state.get('closed') or now-state['monotonic']>2 or state['watchdog_pid']!=launcher['pid'] or state['owner_pid']!=launcher['owner_pid']:raise ValueError('Exact existing watchdog is not fresh/running')
 if now+16>=state['deadlines']['term_at']:raise ValueError('Insufficient time inside existing TERM deadline')
 socket=pathlib.Path(launcher['control_socket']);private=pathlib.Path(launcher['private_socket_directory'])
 if socket.parent!=private or private.parent!=pathlib.Path('/private/tmp') or not private.name.startswith('p16wd-'):raise ValueError('Recorded private control endpoint differs')
 ds=private.lstat();ss=socket.lstat()
 if ds.st_uid!=os.getuid() or stat.S_IMODE(ds.st_mode)!=0o700 or not stat.S_ISDIR(ds.st_mode) or ss.st_uid!=os.getuid() or not stat.S_ISSOCK(ss.st_mode):raise ValueError('Private control directory/socket ownership differs')
 if any(g['role']=='drawable-input' for g in state.get('groups',[])):raise ValueError('This owned helper role was already launched; no retry')
 helper=pathlib.Path(__file__).with_name('drawable_input.py').resolve();output=run/'supervision/drawable-input-observations';stdout=run/'supervision/drawable-input.stdout.txt';stderr=run/'supervision/drawable-input.stderr.txt'
 if any(p.exists() for p in (output,stdout,stderr,run/'drawable-input-consumed.json')):raise ValueError('One-input/helper evidence paths already occupied; no retry')
 argv=[str(python),'-B','-u',str(helper),'--run',str(run),'--xid',hex(xid),'--output',str(output),'--stop-at',str(state['deadlines']['term_at']),'--interaction',interaction]
 if execute:argv.append('--execute')
 if x is not None:argv+=['--x',str(x)]
 if y is not None:argv+=['--y',str(y)]
 request={'op':'spawn','role':'drawable-input','argv':argv,'cwd':str(run),'stdout':str(stdout),'stderr':str(stderr),'env':None,'attempt':False}
 return owned,socket,request,min(now+2,state['deadlines']['term_at']-14)

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=pathlib.Path,required=True);p.add_argument('--python',type=pathlib.Path,required=True);p.add_argument('--xid',type=lambda s:int(s,0),required=True);p.add_argument('--x',type=int);p.add_argument('--y',type=int);p.add_argument('--interaction',choices=['click','motion'],default='click');p.add_argument('--execute',action='store_true');p.add_argument('--spawn',action='store_true');a=p.parse_args()
 owned,socket,request,deadline=prepare(a.run,a.python,a.execute,a.interaction,a.xid,a.x,a.y)
 print(json.dumps({'spawn_requested':a.spawn,'input_execute_requested':a.execute,'request':request,'control_deadline':deadline,'existing_private_control_socket':str(socket)}),flush=True)
 if a.spawn:
  # This wrapper does not own the existing watchdog direct child: use only its
  # transport API. Never call wait_closed, terminate, start, or set_deadlines.
  from supervision.supervisor import WatchdogClient
  module=type('ExistingClientModule',(),{'WatchdogClient':WatchdogClient})
  client=module.WatchdogClient(owned,None,socket)
  result=client._request(request,deadline)
  print(json.dumps({'existing_watchdog_spawn_result':result,'owner_unchanged':True,'attempt':False,'deadline_extended':False}),flush=True)
if __name__=='__main__':main()
