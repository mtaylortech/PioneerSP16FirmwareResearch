"""Focused correlation of original lifecycle receipts, fresh readiness, pixels and closure."""
import hashlib,json,pathlib,shutil,struct
E=pathlib.Path('/private/tmp/pioneer_current_lifecycle_run.txt').read_text().strip();E=pathlib.Path(E);R=E/'run-1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
events=[]
for line in (R/'supervision/guest.stdout.txt').read_text().splitlines():
 if line.startswith('PROBE '):events.append(json.loads(line[6:]))
checks=[]
def check(name,ok):checks.append(dict(check=name,passed=bool(ok)))
def one(kind,function=None):
 rows=[e for e in events if e.get('kind')==kind and (function is None or e.get('function')==function)]
 check('one_'+kind+'_'+str(function),len(rows)==1)
 return rows[0] if rows else {}
app_entry=one('lifecycle_entry','application_initializer');app_return=one('lifecycle_return','application_initializer');wrapper_entry=one('lifecycle_entry','wrapper_initializer');wrapper_return=one('lifecycle_return','wrapper_initializer');cont=one('lifecycle_initializer_continuation');branch=one('lifecycle_post_init_branch');dispatch=one('lifecycle_dispatch_entry');xp=one('lifecycle_dispatch_xpending_return');boundary=one('lifecycle_boundary_complete');ready=one('async_readiness_correlation');producer=one('async_producer_completion');hooks=one('lifecycle_hooks_validated')
for label,entry,returned,caller in [('application',app_entry,app_return,0x698548),('wrapper',wrapper_entry,wrapper_return,0xb4060)]:
 a=entry.get('frame',{});b=returned.get('frame',{})
 check(label+'_original_frame_return',all(a.get(k)==b.get(k) for k in ('thread','sp','caller','object')) and a.get('thread')==2000 and a.get('caller')==caller and b.get('pop') is True and returned.get('matched_thread_sp') is True)
order=[wrapper_entry,app_entry,app_return,cont,wrapper_return,branch,dispatch,xp,boundary,ready]
check('original_returns_continuations_dispatch_readiness_order',all(a.get('probe_sequence',-1)<b.get('probe_sequence',-1) for a,b in zip(order,order[1:])))
check('success_wrapper_and_dispatch_caller',wrapper_return.get('result')==1 and branch.get('success_branch') is True and dispatch.get('frame',{}).get('caller')==0xb4098 and xp.get('matched_thread_sp') is True)
mapping=read(R/'lifecycle-map.json');check('live_original_hook_bytes',bool(hooks.get('points')) and all(mapping['points'].get(a)==b for a,b in hooks['points'].items()))
accept=ready.get('evidence',{});f=accept.get('frame',{});p=producer.get('evidence',{})
check('fresh_producer_main_acceptance',accept.get('passed') is True and accept.get('matched_main_thread_saved_lr_restored_sp') is True and f.get('thread')==2000 and f.get('before',{}).get('completed')==1 and f.get('selected') is True and f.get('popup_return') is True and accept.get('producer')==p)
start=boundary.get('host_monotonic',0)-boundary.get('elapsed',0);D=read(R/'display-observations.json');captures=[]
for row in D['captures']:
 if not row.get('window') or row.get('finished_monotonic',0)<=ready.get('host_monotonic',float('inf')):continue
 path=R/row['path'];data=path.read_bytes();h=struct.unpack_from('>25I',data);pixels=data[h[0]+h[19]*12:];actual=hashlib.sha256(pixels).hexdigest()
 valid=(row.get('exit_code')==0 and row.get('reaped') is True and h[1]==7 and h[2]==2 and h[4]==800 and h[5]==480 and h[6]==0 and len(pixels)==h[5]*h[12] and actual==row.get('pixel_sha256') and row.get('root_capture') is False and row.get('attributes',{}).get('exact_id_matches') is True and row.get('attributes',{}).get('class')=='InputOutput' and row.get('attributes',{}).get('map_state')=='IsViewable' and row.get('ownership',{}).get('source')=='byte_validated_original_XCreateWindow_returned_XID_and_request' and row['ownership'].get('request',{}).get('window')==row['window'] and row['ownership']['request'].get('matches_returned_id') is True and (R/row['correlated_tree']).is_file())
 check('fresh_owned_capture_'+path.name,valid)
 captures.append(dict(path=row['path'],window=row['window'],elapsed=round(row['finished_monotonic']-start,6),width=h[4],height=h[5],pixel_sha256=actual,valid=valid,nonblack_pixels=row.get('nonblack_pixels')))
check('stable_owned_HOME_after_readiness',len(captures)>=2 and all(c['valid'] and c['nonblack_pixels']>0 for c in captures) and len({(c['window'],c['pixel_sha256']) for c in captures})==1)
label=E.name+'-run-1';native=read(R/(label+'-result.json'));attempt=read(R/'attempt-supervision.json');post=read(R/'endpoint-postflight-initial.json');command=read(E/'command-result.json');closure=read(R/'supervision/attempt-owned/client-closure.json')
check('600s_native_observation',native['elapsed_seconds']>=600 and native['elapsed_seconds']<605 and native['outcome']['status']=='bounded_stop' and native['outcome']['deadline_reached'])
check('native_lifecycle_agrees',native['lifecycle']['state']=='mapped_initializer_returned_and_dispatch_observed' and native['lifecycle']['retired'] and not native['lifecycle']['pending'] and native['lifecycle']['first_missing_boundary'] is None)
fault_kinds={'lifecycle_mismatch','invalid_memory','worker_failure_owned_stop','synchronous_emulator_exception_context','emulator_exception_context','timer_futex_error','timer_observer_error'}
faults=[dict(kind=e['kind'],elapsed=e.get('elapsed'),reason=e.get('reason')) for e in events if e.get('kind') in fault_kinds or (e.get('kind')=='denied_host_operation' and e.get('syscall')!='ql_syscall_vfork')]
check('no_fault_or_unexpected_denied_operation',not faults)
check('one_guest_no_input',command['launches']==1 and command['input_allowed'] is False and attempt['guest_processes_created']==1 and read(R/'session-clock.json')['input_authorized'] is False and native['event_pump']['enabled'] is False)
check('loaded_original_identities',bool(attempt.get('identity_checks')) and all(r['matches'] for r in attempt['identity_checks']) and native['application_sha256']=='3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464')
check('direct_children_and_watchdog_reaped',closure.get('closed') is True and closure.get('all_direct_children_reaped') is True and closure.get('watchdog_reaped') is True and closure.get('watchdog_exit_code')==0 and closure.get('control_endpoint_remaining') is False and closure.get('control_directory_remaining') is False)
check('owned_closure_and_independent_postflight',command['observer_client_exit']==0 and command['postflight_exit']==0 and not attempt.get('exception') and not attempt.get('cleanup_failure') and not any(attempt['endpoints'].values()) and post['passed'] and post['verdict']=='pass' and not post['errors'] and not attempt.get('closure',{}).get('failure'))
result=dict(passed=all(c['passed'] for c in checks),checks=checks,milestone='Mapped original application initializer returns, successful enclosing return, subsequent main dispatch, fresh async acceptance and stable owned HOME are correlated in one 600s run.',timing={key:val['elapsed'] for key,val in [('application_initializer_return',app_return),('wrapper_initializer_return',wrapper_return),('subsequent_dispatch_boundary',boundary),('fresh_main_readiness',ready)]},lifecycle_receipts=[e for e in events if e.get('kind','').startswith('lifecycle_')],fresh_async_receipts=[producer,ready],owned_HOME_captures=captures,native_outcome=native['outcome'],native_elapsed_seconds=native['elapsed_seconds'],postflight_passed=post['passed'],faults=faults,limitations=['Original application front-end startup boundary; physical boot, DSP/real audio and broader instrument usability are unproved.','Baseline clock semantics retained; this is not a speed comparison.','HOME appearance visually inspected from fresh original-periodic-2 capture; payload hashes independently read back.','Raw observer full_startup_proved=False describes its lifecycle-only scope; this result adds same-run readiness and owned display correlation.','Independent postflight retains its documented second-resolution and unrecorded-child coverage limits.'],next_test='Prepare and run one reversible post-startup MIXER navigation tap with original event/handler and changed owned pixel correlation. Retire repeat initializer-only and identical Track 2 discovery. A new runtime/input allowance is needed; current one guest/no-input allowance is consumed.')
shutil.copy2(__file__,E/'verify_result.py');(E/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['passed','timing','native_outcome','native_elapsed_seconds','postflight_passed']}));print(json.dumps({'checks':len(checks),'failed':[c['check'] for c in checks if not c['passed']],'owned_HOME_captures':len(captures)}))
raise SystemExit(0 if result['passed'] else 1)
