"""Bounded startup probe of the unchanged SP-16 ARM executable with Qiling.

No real devices, network sockets, host forks, child executables, or vendor boot
scripts are used. This is application emulation, not SP-16 hardware emulation.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import time
import traceback
import runpy
import sys
import types
import signal
import os
import select
import struct
import gevent

# Keystone is imported eagerly by Qiling but only needed when assembling new
# instructions (e.g. driver relocation trampolines). This executable probe runs
# existing instructions. Fail explicitly if assembly is unexpectedly requested.
ASSEMBLER_FALLBACK = False
try:
    import keystone
except ImportError:
    ASSEMBLER_FALLBACK = True
    keystone_dir = Path(sys.prefix) / "lib/python3.10/site-packages/keystone"
    module = types.ModuleType("keystone")
    for key, value in runpy.run_path(str(keystone_dir / "keystone_const.py")).items():
        if key.startswith("KS_"): setattr(module, key, value)
    class UnsupportedAssembler:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Native Keystone unavailable; this probe does not support instruction assembly")
    module.Ks = UnsupportedAssembler
    module.KsError = RuntimeError
    sys.modules["keystone"] = module

from qiling import Qiling as OriginalQiling
from ioctl_observer import IoctlObserver
from arm32_statfs import Arm32Statfs
from constructor_observer import ConstructorObserver
from active_enclosing_observer import ActiveEnclosingObserver
from x11_event_observer import OriginalX11Events
from natural_dispatch import NaturalDispatch
from expose_chain import ExposeChain
from cooperative_select import CooperativeSelect
from wait_observer import WaitObserver
from redraw_observer import RedrawObserver
from timed_futex import TimerFutex
from timer_observer import TimerObserver
from project_request_observer import ProjectRequests
from completion_observer import CompletionObserver
from consumer_observer import ConsumerObserver
from event_pump_observer import EventPump
from lifecycle_observer import LifecycleObserver, DisabledEventPump
from async_readiness import SparseProducer, SparseConsumer
from fault_capture import FaultCaptureMixin
from outcome_policy import final_outcome
from worker_failure import WorkerFailures
class Qiling(FaultCaptureMixin, OriginalQiling):
    pass
from qiling.const import QL_VERBOSE, QL_INTERCEPT
from qiling.os.posix.syscall.sched import ql_syscall_clone
from qiling.os.posix.const_mapping import ql_open_flag_mapping
from qiling.os.posix.syscall.unistd import ql_syscall_brk
from qiling.os.posix.syscall.socket import ql_syscall_socketpair
from qiling.exception import QlMemoryMappedError
from qiling.os.mapper import QlFsMappedObject
from qiling.os.posix.syscall.unistd import ql_syscall_read
from qiling.os.posix.filestruct import ql_socket
from qiling.os.posix.syscall.uio import ql_syscall_readv, ql_syscall_writev
from qiling.os.posix.syscall.poll import ql_syscall_poll
from qiling.os.posix.syscall.socket import ql_syscall_getpeername, ql_syscall_getsockname
from qiling.os.posix.syscall.fcntl import ql_syscall_fcntl64
from local_display import LocalDisplayFixture, verify_endpoint
from display_diagnostics import DisplayDiagnostics
from startup_trace import StartupTrace, WAIT_NAMES
from font_observer import FontObserver, FONT_NAMES
from font_discovery_observer import FontDiscoveryObserver
from font_scan_quantum import FontScanQuantum
from syscall_boundary_quantum import SyscallBoundaryQuantum
from resource_application_observer import ResourceApplicationObserver
from layout_chain_observer import LayoutChainObserver
from deadline_expiry import OuterDeadline, DeadlineExpired
from stdio_lock_observer import StdioLockObserver
from invalid_recv_pacing import InvalidRecvPacer
from qiling.os.posix.syscall.socket import ql_syscall_recv, ql_syscall_recvfrom
from static.parent_observer import ParentObserver
from next_phase_observer import NextPhaseObserver
from qiling.os.posix.syscall.unistd import ql_syscall_write

BASE = Path(__file__).resolve().parent
ROOT = BASE / "rootfs"
APP = ROOT / "root/pdj/EP085_Main_R"
parser = argparse.ArgumentParser()
parser.add_argument("--label", default="baseline")
parser.add_argument("--seconds", type=int, default=15)
parser.add_argument("--stop-at-entry", action="store_true")
parser.add_argument("--library-aliases", action="store_true",
                    help="Expose copied /usr/lib objects under /lib in the emulator only")
parser.add_argument("--linux-brk-failure", action="store_true",
                    help="Return the existing Linux break on rejected heap extension")
parser.add_argument("--high-loader", action="store_true",
                    help="Place the loader above the application's initial heap reservation")
parser.add_argument("--null-audio", action="store_true",
                    help="Map the supplied ALSA configuration to a fixture using its null PCM plugin")
parser.add_argument("--trace-startup", action="store_true")
parser.add_argument("--trace-affinity", action="store_true")
parser.add_argument("--local-ipc", action="store_true",
                    help="Allow anonymous local Unix socket pairs for guest thread wakeups")
parser.add_argument("--epoll-fixture", action="store_true",
                    help="Provide a limited ARM epoll fixture for local guest IPC")
parser.add_argument("--fast", action="store_true",
                    help="Omit expensive per-basic-block activity tracing; retain wall-clock signal limit")
parser.add_argument("--correct-arm-tls", action="store_true",
                    help="Make the emulated kernel TLS helper read the current thread's ARM TLS register")
parser.add_argument("--local-display", action="store_true",
                    help="Allow only guest X0 to authenticated local Xvfb X16; requires verified server")
parser.add_argument("--post-font-count", type=int, choices=(31337,313370), default=31337)
parser.add_argument("--font-scan-quantum", action="store_true", help="Increase finite main instruction quantum only within observed original font scan")
schedule = parser.add_mutually_exclusive_group()
schedule.add_argument("--startup-through-font", action="store_true", help="Supported default when quantum enabled")
schedule.add_argument("--main-startup-quantum", action="store_true", help="Explicit experimental broad scheduling diagnostic")
parser.add_argument("--cooperative-main", action="store_true", help="Diagnostic cooperative main execution throughout the bounded guest")
parser.add_argument("--cooperative-font", action="store_true", help="Experimental cooperative early/font slices, reverting to selected finite counted slices at validated font epilogue")
parser.add_argument("--startup-lifecycle", action="store_true", help="Sparse original initializer return and subsequent dispatch; no input detail hooks")
args = parser.parse_args()
if (args.cooperative_font or args.cooperative_main) and (not args.font_scan_quantum or args.main_startup_quantum or (args.cooperative_font and args.cooperative_main)):
    parser.error("--cooperative-font requires --font-scan-quantum and excludes timed broad mode and simultaneous cooperative scopes")
events = []
blocks = collections.deque(maxlen=30)
started = time.monotonic()
ql = None
deadline_reached = False
expiry_guard = None
api_counts = collections.Counter()
thread_activity = {}
ipc_descriptors = set()
tls_counts = collections.Counter()
display_fixture = LocalDisplayFixture(ql_socket.open, lambda kind, **values: event(kind, **values), time.sleep)


def event(kind, **values):
    if kind == "parent_observer_progress": values["startup_trace"] = startup.summary(); values["next_phase"] = next_phase.summary(ql)
    row = {"probe_sequence": len(events)+1, "host_monotonic": time.monotonic(), "elapsed": round(time.monotonic()-started, 6), "kind": kind, **values}
    row = json.loads(json.dumps(row))
    events.append(row)
    print("PROBE " + json.dumps(row), flush=True)
    if kind == "parent_observer_progress" and ql is not None: diagnostics.snapshot(ql, "parent_progress_sample")


progress_sample_clock = {"last": started}
def take_progress_sample():
    now = time.monotonic()
    if now-progress_sample_clock["last"] < 5: return False
    progress_sample_clock["last"] = now
    return True

diagnostics = DisplayDiagnostics(lambda kind, **values: event(kind, **values), started, display_fixture)


startup = StartupTrace(event, started, diagnostics)
parent = ParentObserver(event, started, APP)
next_phase = NextPhaseObserver(event, started, APP)
pacer = InvalidRecvPacer(ql_syscall_recv,ql_syscall_recvfrom,gevent.sleep)
worker_failures = WorkerFailures(event)
wait_observer = WaitObserver(event)
select_override = CooperativeSelect(event, wait_observer.names)
next_phase.summary = lambda *unused: dict(enabled=False, reason='observer not installed; completed earlier question')
font = FontObserver(event,started,gate=lambda:discovery.main_tid is not None)
discovery = FontDiscoveryObserver(event,started,APP)
timer_observer = TimerObserver(event, wait_observer.names, discovery, BASE)
project_requests = ProjectRequests(event,wait_observer.names,discovery)
completion = SparseProducer(event,discovery,BASE) if args.startup_lifecycle else CompletionObserver(event,discovery,BASE)
consumer = SparseConsumer(event,discovery,completion) if args.startup_lifecycle else ConsumerObserver(event,discovery,completion)
event_pump = DisabledEventPump() if args.startup_lifecycle else EventPump(event,discovery,display_fixture,BASE)
lifecycle = LifecycleObserver(event,discovery) if args.startup_lifecycle else None
timer_futex = TimerFutex(event, wait_observer.names, timer_observer)
wait_observer.handler = timer_futex.call
wait_observer.timing_enforced = timer_futex.selected
filesystem = Arm32Statfs(event, discovery, ROOT/"lib/libc.so.6")
font_quantum = (SyscallBoundaryQuantum(event,started,discovery,post_count=args.post_font_count,scope="main_startup" if args.cooperative_main else "startup_through_font") if (args.cooperative_font or args.cooperative_main) else FontScanQuantum(event,started,discovery,mode="time_budget",time_budget_us=20000,scope="main_startup" if args.main_startup_quantum else "startup_through_font",post_count=args.post_font_count)) if args.font_scan_quantum else None
resource_application = ResourceApplicationObserver(event,started,discovery)
layout_chain = LayoutChainObserver(event,started,discovery)
stdio = StdioLockObserver(event,started,discovery,ROOT/"lib/libc.so.6")
stdio.summary = lambda *unused: dict(enabled=False, reason='observer not installed; focused waits replace this summary')
startup.progress_gate = lambda: False
parent.progress_gate = take_progress_sample


network_syscall_counts = collections.Counter()
def network_count(name):
    def cb(q,*values):
        tid=q.os.thread_management.cur_thread.id;key=name+':'+str(tid);network_syscall_counts[key]+=1
        if network_syscall_counts[key]<=3:event('network_syscall_context',name=name,thread=tid,thread_name=pacer.thread_names.get(tid),pc=hex(q.arch.regs.arch_pc),lr=hex(q.arch.regs.lr),arguments=list(values))
    return cb

def compose(*callbacks):
    def cb(q,*values):
        for callback in callbacks:callback(q,*values)
    return cb

def sampled_main_state():
    # Runs only when the cooperative runtime yields; saved context is read without restoring it.
    from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_SP
    while ql is not None:
        gevent.sleep(5)
        try:
            tm=ql.os.thread_management;mt=tm.main_thread
            ctx=mt.saved_context
            regs={n:hex(ctx.reg_read(a)) for n,a in [('pc',UC_ARM_REG_PC),('lr',UC_ARM_REG_LR),('sp',UC_ARM_REG_SP)]} if ctx is not None else None
            event('sampled_main_state',main_tid=startup.main_tid,context_source='saved context at last thread yield',saved_registers=regs,startup_trace=startup.summary(),next_phase=next_phase.summary(ql),font=font.summary(),network_syscall_counts=dict(network_syscall_counts),pacing=pacer.summary(),font_discovery=discovery.summary(),font_scan_quantum=font_quantum.summary() if font_quantum else None,layout_chain=layout_chain.summary(detail=False),stdio_lock=stdio.summary(),resource_application=resource_application.summary(detail=False),constructor=constructor.summary(),active_enclosing=active_enclosing.summary(),original_x11_events=input_events.summary(),natural_dispatch=natural_dispatch.summary(),expose_chain=expose_chain.summary(),redraw=redraw_observer.summary(),waits=wait_observer.summary(),select_service=select_override.summary(),timer_futex=timer_futex.summary(),timer_original=timer_observer.summary(),project_requests=project_requests.summary(),completion=completion.summary(),consumer=consumer.summary(),lifecycle=lifecycle.summary() if lifecycle else None,event_pump=event_pump.summary(),deadline_state=expiry_guard.summary() if expiry_guard else None)
            diagnostics.snapshot(ql,'cooperative_sample')
        except Exception as ex:
            event('main_sampling_error',error=repr(ex))


def marker(name):
    def callback(q):
        event(name, pc=hex(q.arch.regs.arch_pc))
        if name == "application_entry" and args.local_display: filesystem.install_boundaries(q); diagnostics.install(q); startup.install(q); discovery.install(q); layout_chain.install(q); resource_application.install(q); timer_observer.install(q); completion.install(q); consumer.install(q); event_pump.install(q); natural_dispatch.install(q); input_events.install(q) if not args.startup_lifecycle else None; lifecycle.install(q) if lifecycle else None; timer_futex.install_mapping(q,ROOT/"lib/libpthread.so.0"); font_quantum.install(q) if font_quantum else None; event('pacing_wrapper_bytes',**pacer.install(q)); event('pacing_callsite_bytes',address='0x51d078',expected=discovery.expected(0x51d078).hex(),actual=bytes(q.mem.read(0x51d078,4)).hex(),matches=bytes(q.mem.read(0x51d078,4))==discovery.expected(0x51d078))
        if name == "main_entry": startup.identify_main(q); font.identify_main(q); discovery.identify_main(q)
        if name == "application_entry" and args.stop_at_entry: q.emu_stop()
    return callback


def deny(q):
    event("denied_host_operation", syscall=q.os.syscall_mapper(q.os.get_syscall()))
    return -1


def clone_guard(q, flags, child_stack, parent_tidptr, newtls, child_tidptr):
    event("clone", flags=hex(flags), child_stack=hex(child_stack))
    if not flags & 0x100:
        return -1
    return ql_syscall_clone(q, flags, child_stack, parent_tidptr, newtls, child_tidptr)


constructor = ConstructorObserver(event, started, discovery)
active_enclosing = ActiveEnclosingObserver(event, started, discovery)
input_events = OriginalX11Events(event, started, discovery, BASE)
natural_dispatch = NaturalDispatch(event, started, discovery)
expose_chain = ExposeChain(event, started, discovery)
redraw_observer = RedrawObserver(event, started, discovery)
expose_chain.redraw = redraw_observer
natural_dispatch.expose = expose_chain
natural_dispatch.retire_events = None
def paint_confirmed(q):
    timer_observer.retire_timer(q)
    if getattr(resource_application,'details_retired',False):return
    resource_application.details_retired=True
    # Installed points keep counts through traversal; disable callbacks after painting frontier.
    for observer in (resource_application,layout_chain):
        for handle in observer.observation_handles:q.hook_del(handle)
        observer.observation_handles.clear()
    event('completed_resource_details_retired',reason='first original paint confirmation',resource_returns=sum(resource_application.return_counts.values()))
natural_dispatch.paint_confirmed = paint_confirmed
ioctl_observer = IoctlObserver(event, discovery)
path_counts={}
next_stage_observed=False
def path_call(q, *values):
    global next_stage_observed
    try:
        name = q.os.syscall_mapper(q.os.get_syscall())
        address = values[1] if "openat" in name else values[0]
        path=q.mem.string(address)
        cache_related=('fontconfig' in path or '.cache-2' in path or path.endswith('fonts.conf'))
        if path not in path_counts:path_counts[path]=0
        path_counts[path]+=1
        post_scan=any(r.get('matched_return') and r.get('entry')=='0x706948' for r in discovery.completed)
        if cache_related or (path_counts[path]<=1 and not ('/picture/' in path)):
            event("path_syscall",syscall=name,path=path,font_scan_return_observed=post_scan)
        if post_scan and q.os.thread_management.cur_thread.id==discovery.main_tid and ('/picture/' in path or '/layout' in path or path.endswith('.csv')) and not next_stage_observed:
            next_stage_observed=True;event('post_font_scan_initialization',path=path,syscall=name,thread=q.os.thread_management.cur_thread.id,pc=hex(q.arch.regs.arch_pc),lr=hex(q.arch.regs.lr),font_discovery=discovery.summary(),font_scan_quantum=font_quantum.summary() if font_quantum else None,layout_chain=layout_chain.summary(detail=False),stdio_lock=stdio.summary(),resource_application=resource_application.summary(detail=False),constructor=constructor.summary(),active_enclosing=active_enclosing.summary())
    except Exception as exc:
        event("path_trace_error", error=str(exc))


def auth_access_return(q, path, mode, result):
    if q.mem.string(path) == "/root/display.xauth":
        event("display_auth_access", path="/root/display.xauth", mode=mode, result=result,
              pc=hex(q.arch.regs.arch_pc), lr=hex(q.arch.regs.lr))


def prctl_trace(q, option, arg2, arg3, arg4, arg5):
    if option == 15:
        pacer.observe_thread_name(q,q.mem.string(arg2))
        event("thread_name", name=q.mem.string(arg2),
              thread=q.os.thread_management.cur_thread.id)


def linux_brk(q, address):
    previous = q.loader.brk_address
    try:
        return ql_syscall_brk(q, address)
    except QlMemoryMappedError:
        event("brk_rejected", requested=hex(address), previous=hex(previous),
              maps=[(hex(a), hex(b), label) for a, b, _, label, _ in q.mem.map_info])
        return previous


def record_block(q, address, size):
    blocks.append((hex(address), size))
    if time.monotonic() - started > args.seconds:
        deadline()
    current = getattr(q.os, "thread_management", None)
    if current and current.cur_thread:
        tid = current.cur_thread.id
        item = thread_activity.setdefault(tid, {"blocks": 0, "application_blocks": 0})
        item["blocks"] += 1
        if 0x8000 <= address < 0xb68000:
            item["application_blocks"] += 1
        item["last_pc"] = hex(address)
        item["last_elapsed"] = round(time.monotonic()-started,6)


def deadline(*unused):
    global deadline_reached
    if not deadline_reached:
        deadline_reached = True
        if ql and args.local_display: diagnostics.snapshot(ql, "native_deadline"); event("main_native_deadline", startup_trace=startup.summary(), next_phase=next_phase.summary(ql))
        event("deadline_stop", requested_seconds=args.seconds)


def api_trace(name):
    def callback(q):
        if args.local_display: diagnostics.maybe_near_stop(q)
        tid = q.os.thread_management.cur_thread.id
        key = name + ":" + str(tid)
        api_counts[key] += 1
        if api_counts[key] <= (12 if name=="snd_pcm_open" else 3):
            values = [q.arch.regs.read("r"+str(i)) for i in range(4)]
            event("api_call", name=name, thread=tid, arguments=[hex(x) for x in values],
                  text=q.mem.string(values[1]) if name == "snd_pcm_open" else q.mem.string(values[0]) if name=="XOpenDisplay" else None)
            # Permanent OriginalX11Events owns exact XNextEvent returns/payloads.
            # Retire this API's one-shot hook to avoid mutable callback-list collisions.
            if name=="XNextEvent": return
            address=q.arch.regs.lr
            holder={}
            def returned(q2):
                if q2.os.thread_management.cur_thread.id != tid: return
                raw=q2.arch.regs.r0
                event("api_return",name=name,thread=tid,result=raw if raw<0x80000000 else raw-0x100000000)
                q2.hook_del(holder["hook"])
            holder["hook"]=q.hook_address(returned,address)
    return callback


def invalid_memory(q, access, address, size, value):
    event("invalid_memory", access=access, address=hex(address), size=size,
          pc=hex(q.arch.regs.arch_pc),
          registers={name: hex(q.arch.regs.read(name)) for name in
                     ("r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "sp", "lr")})
    return False


def function_trace(name):
    def callback(q):
        event("function_trace", name=name, pc=hex(q.arch.regs.arch_pc),
              lr=hex(q.arch.regs.lr),
              arguments=[hex(q.arch.regs.read("r"+str(i))) for i in range(4)])
    return callback


def affinity_trace(q, pid, cpusetsize, mask):
    if cpusetsize > 4096:
        return -22
    raw = bytes(q.mem.read(mask, cpusetsize))
    event("cpu_affinity_request", pid=pid, current_thread=q.os.thread_management.cur_thread.id,
          mask=raw.hex(), cpus=[i for i in range(len(raw)*8) if raw[i//8] & (1 << (i%8))],
          emulated=False)
    return -38


def arm_tls_helper(q):
    tid=q.os.thread_management.cur_thread.id
    current=q.arch.regs.c13_c0_3
    stored=q.mem.read_ptr(0xffff0ff0)
    tls_counts["calls"]+=1
    if stored != current:
        tls_counts["mismatches"]+=1
        if tls_counts["mismatches"] <= 8:
            event("tls_helper_mismatch",thread=tid,current_thread_tls=hex(current),shared_helper_value=hex(stored))
    q.arch.regs.r0=current
    q.arch.regs.arch_pc=q.arch.regs.lr


def local_socketpair(q, domain, socktype, protocol, sv):
    if domain != 1 or socktype & 15 not in (1, 2) or protocol != 0:
        return -97
    result = ql_syscall_socketpair(q, domain, socktype, protocol, sv)
    if result == 0:
        for i in range(2):
            fd=q.mem.read_ptr(sv+4*i)
            ipc_descriptors.add(fd)
            os.set_blocking(q.os.fd[fd].fileno(),False)
    event("local_ipc_pair", domain=domain, socktype=socktype, result=result)
    return result


def guarded_read(q, fd, buf, length):
    if fd not in ipc_descriptors and not display_fixture.owns(q, fd):
        return ql_syscall_read(q,fd,buf,length)
    try:
        read_row=event_pump.before_read(q,fd,"read",length)
        content=q.os.fd[fd].read(length)
    except BlockingIOError:
        event_pump.after_read(q,read_row,-11)
        return -11
    if display_fixture.owns(q, fd) and fd not in display_fixture.setup_reply_observed and len(content) >= 8:
        display_fixture.setup_reply_observed.add(fd)
        status, reason_length, major, minor, units = struct.unpack('<BBHHH', content[:8])
        event('display_setup_reply_metadata', descriptor=fd, status=status, reason_length=reason_length,
              protocol_major=major, protocol_minor=minor, body_bytes=units*4, cookie_disclosed=False)
    q.mem.write(buf,content)
    event_pump.after_read(q,read_row,len(content),content)
    return len(content)


def display_readv(q, fd, vec, count):
    if not display_fixture.owns(q,fd):return ql_syscall_readv(q,fd,vec,count)
    row=event_pump.before_read(q,fd,'readv',count)
    result=display_fixture.readv(q,fd,vec,count);data=b'';remaining=max(0,result)
    for i in range(count):
        address,length=struct.unpack('<II',bytes(q.mem.read(vec+i*8,8)));size=min(length,remaining)
        if size:data+=bytes(q.mem.read(address,size));remaining-=size
    event_pump.after_read(q,row,result,data);return result


def observed_recv(q,fd,buf,length,flags):
    row=event_pump.before_read(q,fd,'recv',length);result=pacer.recv(q,fd,buf,length,flags)
    event_pump.after_read(q,row,result,bytes(q.mem.read(buf,result)) if result>0 and row else b'');return result
def observed_recvfrom(q,fd,buf,length,flags,address,addrlen):
    row=event_pump.before_read(q,fd,'recvfrom',length);result=pacer.recvfrom(q,fd,buf,length,flags,address,addrlen)
    event_pump.after_read(q,row,result,bytes(q.mem.read(buf,result)) if result>0 and row else b'');return result

def display_write(q, fd, buf, length):
    tracked=display_fixture.owns(q,fd)
    result=ql_syscall_write(q,fd,buf,length)
    if tracked: event("display_write_metadata",operation="write",descriptor=fd,requested_bytes=length,result=result,pc=hex(q.arch.regs.arch_pc),lr=hex(q.arch.regs.lr))
    return result


def display_writev(q, fd, vec, count):
    if not display_fixture.owns(q,fd):return ql_syscall_writev(q,fd,vec,count)
    sizes=[q.mem.read_ptr(vec+i*8+4) for i in range(count)] if 0<=count<=1024 else []
    result=display_fixture.writev(q,fd,vec,count)
    event("display_write_metadata",operation="writev",descriptor=fd,vector_count=count,vector_sizes=sizes,requested_bytes=sum(sizes),result=result,pc=hex(q.arch.regs.arch_pc),lr=hex(q.arch.regs.lr))
    return result


def display_poll(q, pointer, count, timeout):
    if 0 < count <= 1024:
        fds = [struct.unpack('<i', bytes(q.mem.read(pointer+i*8, 4)))[0] for i in range(count)]
        if all(display_fixture.owns(q, fd) for fd in fds):
            return display_fixture.poll(q, pointer, count, timeout)
    return ql_syscall_poll(q, pointer, count, timeout)


def display_getpeername(q, fd, address, length_ptr):
    return display_fixture.socket_name(q, fd, address, length_ptr, True) if display_fixture.owns(q, fd) else ql_syscall_getpeername(q, fd, address, length_ptr)


def display_getsockname(q, fd, address, length_ptr):
    return display_fixture.socket_name(q, fd, address, length_ptr, False) if display_fixture.owns(q, fd) else ql_syscall_getsockname(q, fd, address, length_ptr)


def display_fcntl64(q, fd, cmd, arg):
    if not display_fixture.owns(q, fd):
        return ql_syscall_fcntl64(q, fd, cmd, arg)
    if cmd == 3:  # Linux F_GETFL: virtual O_RDWR | O_NONBLOCK
        result = 2 | 0x800
    elif cmd == 4:  # Linux F_SETFL; do not pass Linux O_NONBLOCK to Darwin.
        os.set_blocking(q.os.fd[fd].fileno(), False)
        result = 0
    else:
        return ql_syscall_fcntl64(q, fd, cmd, arg)
    event('display_fcntl64', descriptor=fd, cmd=cmd, guest_argument=hex(arg), result=result,
          host_nonblocking=not os.get_blocking(q.os.fd[fd].fileno()),
          pc=hex(q.arch.regs.arch_pc), lr=hex(q.arch.regs.lr))
    return result


class EpollFixture(QlFsMappedObject):
    def __init__(self): self.registrations={}
    def close(self): pass


def epoll_create(q,size):
    if size <= 0: return -22
    fd=next((i for i,f in enumerate(q.os.fd) if f is None),-1)
    if fd >= 0:
        q.os.fd[fd]=EpollFixture()
        event("epoll_created",descriptor=fd)
    return fd


def epoll_ctl(q,epfd,op,fd,event_ptr):
    ep=q.os.fd[epfd] if epfd < len(q.os.fd) else None
    if not isinstance(ep,EpollFixture) or fd >= len(q.os.fd) or q.os.fd[fd] is None: return -9
    if op==2:
        ep.registrations.pop(fd,None)
    elif op in (1,3):
        raw=bytes(q.mem.read(event_ptr,16))
        ep.registrations[fd]=raw
        event("epoll_registered",descriptor=epfd,target_fd=fd,flags=hex(struct.unpack_from('<I',raw)[0]),data=raw.hex())
    else: return -22
    return 0


def epoll_wait(q,epfd,events_ptr,maxevents,timeout):
    if args.local_display: diagnostics.maybe_near_stop(q)
    ep=q.os.fd[epfd] if epfd < len(q.os.fd) else None
    if not isinstance(ep,EpollFixture) or maxevents<=0: return -22
    items=[]
    for fd,raw in ep.registrations.items():
        obj=q.os.fd[fd]
        if obj is None: continue
        flags=struct.unpack_from('<I',raw)[0]
        hostfd=obj.fileno()
        readable,writable,errors=select.select([hostfd] if flags&1 else [],[hostfd] if flags&4 else [],[hostfd],0)
        ready=(1 if readable else 0)|(4 if writable else 0)|(8 if errors else 0)
        if ready: items.append(struct.pack('<I',ready)+raw[4:])
    items=items[:maxevents]
    if items:
        q.mem.write(events_ptr,b''.join(items))
        return len(items)
    if timeout != 0:
        q.emu_stop()
        q.os.thread_management.cur_thread.sched_cb=lambda current: gevent.sleep(0.001)
    return 0


def main():
    global ql, deadline_reached, expiry_guard
    outcome = {}
    monitor = None
    expiry = OuterDeadline(args.seconds, request_stop=lambda: ql.emu_stop() if ql else None, on_expire=deadline)
    expiry_guard = expiry
    try:
        expiry.start()
        profile = {"KERNEL": {"uid": "0", "gid": "0"},
                   "MISC": {"current_path": "/root/pdj"}}
        if args.high_loader:
            profile["OS32"] = {"interp_address": "0x70000000"}
        guest_env = {"LD_LIBRARY_PATH": "/lib:/usr/lib", "HOME": "/root", "DISPLAY": ":0"}
        if args.local_display:
            event("display_endpoint_verified", **verify_endpoint(BASE / "display.xauth"))
            guest_env["XAUTHORITY"] = "/root/display.xauth"
            actual_auth = ROOT / "root/display.xauth"
            if actual_auth.stat().st_mode & 0o777 != 0o600 or actual_auth.read_bytes() != (BASE / "display.xauth").read_bytes():
                raise RuntimeError("Guest authentication visibility preflight failed")
            event("display_auth_file_preflight", actual_path_present=True, mode="0600", current_server_file_matches=True, cookie_disclosed=False)
        ql = Qiling([str(APP)], str(ROOT),
                    env=guest_env,
                    profile=profile,
                    verbose=QL_VERBOSE.DISABLED, log_plain=True,
                    log_file=str(BASE / "logs" / f"{args.label}-qiling.log"), multithread=True)
        ql.fault_emit = event
        worker_failures.install(ql)
        event("loaded", loader_entry=hex(ql.loader.entry_point), application_entry=hex(ql.loader.elf_entry),
              unused_assembler_import_fallback=ASSEMBLER_FALLBACK)
        for path in ("/lib/libX11.so.6", "/usr/lib/libX11.so.6", "/etc/ld.so.cache"):
            host_path = ql.os.path.virtual_to_host_path(path)
            try:
                handle = ql.os.fs_mapper.open_ql_file(path, ql_open_flag_mapping(ql, 0), 0)
                handle.close()
                event("host_open_preflight", path=path, host_path=host_path, result="ok")
            except Exception as exc:
                event("host_open_preflight", path=path, host_path=host_path, result=str(exc),
                      errno=getattr(exc, "errno", None))
        event("environment", env=ql.env, uid=ql.os.uid, euid=ql.os.euid,
              readonly_host_flags=hex(ql_open_flag_mapping(ql, 0)))
        if args.library_aliases:
            for path in sorted((ROOT / "usr/lib").glob("*.so*")):
                if path.is_file() and not (ROOT / "lib" / path.name).exists():
                    resolved = path.resolve()
                    resolved.relative_to(ROOT)
                    ql.add_fs_mapper("/lib/" + path.name, str(resolved))
                    event("library_alias", guest="/lib/" + path.name,
                          source=str(resolved.relative_to(ROOT)))
        if args.null_audio:
            ql.add_fs_mapper("/usr/share/alsa/alsa.conf", str(BASE / "alsa-null.conf"))
            ql.add_fs_mapper("/dev/null", str(BASE / "null-device"))
            ql.add_fs_mapper("/dev/full", str(BASE / "full-device"))
            event("audio_fixture", kind_name="ALSA null PCM", config="alsa-null.conf",
                  original_library_bytes_unchanged=True)
        if args.local_display:
            ql.add_fs_mapper("/root/display.xauth", str(BASE / "display.xauth"))
        if args.trace_startup:
            symbols=json.loads((BASE / "plt-symbols.json").read_text())
            for name in ("XOpenDisplay", "XCreateWindow", "XCreateSimpleWindow", "XMapWindow", "XFlush", "XSync", "XPutImage", "XPending", "XNextEvent"):
                if name in symbols and not (args.startup_lifecycle and name in ("XPending", "XNextEvent")):
                    ql.hook_address(api_trace(name), int(symbols[name],16))
        ql.hook_address(marker("application_entry"), 0xb5cc8)
        if args.correct_arm_tls:
            ql.hook_address(arm_tls_helper,0xffff0fe0)
        ql.hook_address(marker("main_entry"), 0xb3ac4)
        if not args.fast:
            ql.hook_block(record_block)
        ql.hook_mem_invalid(invalid_memory)
        for name in ("fork", "vfork", "execve", "execveat", "socket", "socketpair", "connect", "bind", "ptrace", "mount", "umount", "umount2", "reboot"):
            ql.os.set_syscall(name, deny)
        ql.os.set_syscall("clone", clone_guard)
        filesystem.install_syscalls(ql)
        ql.os.set_syscall("ioctl", ioctl_observer.call)
        if args.local_ipc:
            ql.os.set_syscall("socketpair", local_socketpair)
            ql.os.set_syscall("read", guarded_read)
        if args.local_display:
            ql.os.set_syscall("socket", display_fixture.socket)
            ql.os.set_syscall("connect", display_fixture.connect)
            ql.os.set_syscall("read", guarded_read)
            ql.os.set_syscall("readv", display_readv)
            ql.os.set_syscall("writev", display_writev)
            ql.os.set_syscall("write", display_write)
            ql.os.set_syscall("poll", display_poll)
            ql.os.set_syscall("getpeername", display_getpeername)
            ql.os.set_syscall("getsockname", display_getsockname)
            ql.os.set_syscall("fcntl64", display_fcntl64)
        if args.epoll_fixture:
            ql.os.set_syscall("epoll_create", epoll_create)
            ql.os.set_syscall("epoll_ctl", epoll_ctl)
            ql.os.set_syscall("epoll_wait", epoll_wait)
        if args.trace_affinity:
            ql.os.set_syscall("sched_setaffinity", affinity_trace)
        if args.linux_brk_failure:
            ql.os.set_syscall("brk", linux_brk)
        ql.os.set_syscall('recv',observed_recv)
        ql.os.set_syscall('recvfrom',observed_recvfrom)
        for name in ("open", "openat", "access"):
            ql.os.set_syscall(name, compose(path_call,completion.path_enter(name)), QL_INTERCEPT.ENTER)
        ql.os.set_syscall("access", compose(auth_access_return,completion.path_exit("access")), QL_INTERCEPT.EXIT)
        for name in FONT_NAMES:
            enters=[];exits=[]
            if name in FONT_NAMES:enters.append(font.syscall_enter(name));exits.append(font.syscall_exit(name))
            if name in ('open','openat'):
                enters.insert(0,path_call);enters.append(completion.path_enter(name));exits.append(completion.path_exit(name))
            ql.os.set_syscall(name,compose(*enters),QL_INTERCEPT.ENTER)
            ql.os.set_syscall(name,compose(*exits),QL_INTERCEPT.EXIT)
        for name in ('recv','recvfrom','recvmsg','send','sendto','sendmsg'):
            ql.os.set_syscall(name,network_count(name),QL_INTERCEPT.ENTER)
        wait_observer.install(ql)
        select_override.install(ql)
        timer_futex.install_wake_filter(ql)
        event('execution_condition', changed='finite relative FUTEX_WAIT for verified named Juce Timer and ProjectManager wrapper only', prctl_observation_enabled=True, pacer_name_delivery=False, autoip_pacing_enabled=False, clocks_setitimer_other_futex_devices_quanta_unchanged=True,cooperative_select_retained=True)
        monitor=gevent.spawn(sampled_main_state)
        ql.run(timeout=args.seconds * 1_000_000, count=30_000_000)
        expiry.check()
        event("ql_run_return", guest_exit_code=ql.os.exit_code, advisory_deadline_reached=deadline_reached)
        outcome = {"status": "returned", "exit_code": ql.os.exit_code}
    except DeadlineExpired as exc:
        deadline_reached = True
        event("deadline_reached_outer_owner", expiry=expiry.summary())
        outcome = {"status": "bounded_stop", "reason": str(exc)}
    except Exception as exc:
        if ql is not None:
            context = {"error_type": type(exc).__name__, "error": str(exc), "read_only": True}
            try:
                context["thread"] = ql.os.thread_management.cur_thread.id
                context["registers"] = {n: hex(ql.arch.regs.read(n)) for n in ["r"+str(i) for i in range(13)]+["sp","lr","pc","cpsr"]}
                context["pointer_cells"] = {}
                for n in ("r0","r1","r3","r4","r5","sp"):
                    address = ql.arch.regs.read(n)
                    cell = {"address": hex(address), "alignment_mod4": address & 3}
                    try: cell["bytes"] = bytes(ql.mem.read(address,32)).hex()
                    except Exception as read_error: cell["read_error"] = repr(read_error)
                    context["pointer_cells"][n] = cell
                context["instruction_bytes"] = bytes(ql.mem.read(ql.arch.regs.arch_pc-8,24)).hex()
            except Exception as diagnostic_error: context["diagnostic_error"] = repr(diagnostic_error)
            event("emulator_exception_context", **context)
        traceback.print_exc()
        outcome = {"status": "exception", "type": type(exc).__name__, "message": str(exc)}
    finally:
        expiry.close()
        deadline_reached = deadline_reached or expiry.expired
        if ql is not None and ql.os.thread_management is not None:
            ql.os.thread_management.stop()
        if monitor is not None:
            monitor.kill(block=False)
        if ql and args.local_display: diagnostics.snapshot(ql,"native_finally")
        outcome = final_outcome(worker_failures.outcome(outcome), deadline_reached, ql.os.exit_code if ql else None)
        worker_failures.close()
        report = {"label": args.label, "elapsed_seconds": time.monotonic()-started,
                  "options": vars(args), "deadline_expiry": expiry.summary(),
                  "application_sha256": hashlib.sha256(APP.read_bytes()).hexdigest(),
                  "outcome": outcome, "events": events, "recent_blocks": list(blocks),
                  "api_counts": dict(api_counts), "thread_activity": thread_activity,
                  "tls_helper_counts": dict(tls_counts), "startup_trace": startup.summary(), "parent_trace": parent.summary(), "font_trace": font.summary(), "network_syscall_counts":dict(network_syscall_counts), "pacing":pacer.summary(), "font_discovery":discovery.summary(), "font_scan_quantum":font_quantum.summary() if font_quantum else None, "layout_chain":layout_chain.summary(), "stdio_lock":stdio.summary(), "resource_application":resource_application.summary(), "constructor":constructor.summary(), "active_enclosing":active_enclosing.summary(), "original_x11_events":input_events.summary(), "natural_dispatch":natural_dispatch.summary(), "expose_chain":expose_chain.summary(), "redraw":redraw_observer.summary(), "waits":wait_observer.summary(), "select_service":select_override.summary(), "timer_futex":timer_futex.summary(), "timer_original":timer_observer.summary(), "project_requests":project_requests.summary(), "completion":completion.summary(), "consumer":consumer.summary(), "lifecycle":lifecycle.summary() if lifecycle else None, "event_pump":event_pump.summary(),
                  "final_pc": hex(ql.arch.regs.arch_pc) if ql else None,
                  "scope": "Qiling application emulation with original binary/libraries; documented fixtures; no physical peripherals"}
        (BASE / f"{args.label}-result.json").write_text(json.dumps(report, indent=2)+"\n")
        event("native_final_written", path=str(BASE / f"{args.label}-result.json"), outcome=outcome, expiry=expiry.summary())
        print("RESULT " + json.dumps({k:v for k,v in report.items() if k not in ("events", "recent_blocks")}), flush=True)


if __name__ == "__main__": main()
