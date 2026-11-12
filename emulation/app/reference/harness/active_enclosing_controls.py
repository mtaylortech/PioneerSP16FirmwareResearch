"""Focused in-memory original-instruction controls; launches no application guest."""
from pathlib import Path
import ast
import hashlib
import json
import sys
import time
import types

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_R0
from font_discovery_observer import FontDiscoveryObserver
from active_enclosing_observer import ActiveEnclosingObserver, POINTS, ENTRY, LOCAL_SUB, LOCAL_ADD, POP, DIRECT_CALL, CALLER, SUBSEQUENT

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[2]
SOURCE = PROJECT / 'experiments/post-font-counted-quantum-20261008-repeat/common'
APP = PROJECT / 'experiments/post-font-counted-quantum-20261008-repeat/control/rootfs/root/pdj/EP085_Main_R'
d = FontDiscoveryObserver(lambda *a, **k: None, time.monotonic(), APP)
d.main_tid = 2000
rows = []


class Registers:
    mapping = dict(arch_pc=UC_ARM_REG_PC, sp=UC_ARM_REG_SP, lr=UC_ARM_REG_LR, r0=UC_ARM_REG_R0)

    def __init__(self, uc):
        self.uc = uc

    def __getattr__(self, name):
        return self.uc.reg_read(self.mapping[name])

    def __setattr__(self, name, value):
        if name == 'uc':
            object.__setattr__(self, name, value)
        else:
            self.uc.reg_write(self.mapping[name], value)


def fixture(install=True):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    for page in sorted({a & ~0xfff for a in POINTS} | {0x900000}):
        uc.mem_map(page, 0x1000)
    for address, h in POINTS.items():
        uc.mem_write(address, bytes.fromhex(h))
    q = types.SimpleNamespace(uc=uc, arch=types.SimpleNamespace(regs=Registers(uc)),
        mem=types.SimpleNamespace(read=uc.mem_read, write=uc.mem_write),
        os=types.SimpleNamespace(thread_management=types.SimpleNamespace(cur_thread=types.SimpleNamespace(id=2000))))
    q.hook_address = lambda callback, address: uc.hook_add(UC_HOOK_CODE, lambda u, a, size, data: callback(q), begin=address, end=address)
    q.arch.regs.sp = 0x900800
    q.arch.regs.lr = CALLER
    q.arch.regs.r0 = 0x1234
    events = []
    observer = ActiveEnclosingObserver(lambda kind, **row: events.append(dict(kind=kind, **row)), time.monotonic(), d)
    if install:
        observer.install(q)
    return q, observer, events


def step(q, address):
    q.uc.emu_start(address, address + 4, count=1)


q, o, events = fixture()
before = {a: bytes(q.mem.read(a, 4)) for a in POINTS}
step(q, DIRECT_CALL)
assert q.arch.regs.arch_pc == ENTRY and q.arch.regs.lr == CALLER and q.arch.regs.sp == 0x900800
step(q, ENTRY)
assert q.arch.regs.sp == 0x900800 - 36 and len(o.frames) == 1
step(q, LOCAL_SUB)
assert q.arch.regs.sp == 0x900800 - 36 - 0x94
step(q, LOCAL_ADD)
assert q.arch.regs.sp == 0x900800 - 36
step(q, POP)
assert q.arch.regs.arch_pc == CALLER and q.arch.regs.sp == 0x900800 and not o.completed
step(q, CALLER)
assert o.completed[-1]['matched_return'] and not o.continuations
step(q, SUBSEQUENT)
assert o.completed[-1]['subsequent_execution_observed'] and len(o.continuations) == 1
assert all(bytes(q.mem.read(a, 4)) == b for a, b in before.items())
rows.append(dict(control='isolated_original_BL_push_local_sub_add_pop_cmp_and_subsequent_mov', passed=True,
                 full_application_guest_launched=False, events=events, summary=o.summary()))

# Separate frame conditions cannot substitute for all of the required evidence.
for label, direct, saved, pop_sp, restored in (
    ('missing_direct_BL', False, CALLER, 0x900800 - 36, 0x900800),
    ('wrong_saved_caller', True, CALLER + 4, 0x900800 - 36, 0x900800),
    ('wrong_pop_SP', True, CALLER, 0x900800 - 40, 0x900800),
    ('wrong_restored_SP', True, CALLER, 0x900800 - 36, 0x900804),
):
    q, o, events = fixture()
    if direct:
        step(q, DIRECT_CALL)
    step(q, ENTRY)
    q.arch.regs.sp = pop_sp
    q.mem.write(pop_sp + 32, saved.to_bytes(4, 'little'))
    q.arch.regs.arch_pc = POP
    o.checkpoint(q, POP)
    q.arch.regs.sp = restored
    q.arch.regs.arch_pc = CALLER
    o.checkpoint(q, CALLER)
    q.arch.regs.arch_pc = SUBSEQUENT
    o.checkpoint(q, SUBSEQUENT)
    assert len(o.completed) == 1 and not o.completed[-1]['matched_return'] and not o.continuations
    rows.append(dict(control=label, passed=True, summary=o.summary()))

q, o, events = fixture()
step(q, DIRECT_CALL)
step(q, ENTRY)
q.arch.regs.arch_pc = CALLER
o.checkpoint(q, CALLER)
assert not o.completed and o.frames and o.counts['caller_without_pop'] == 1
rows.append(dict(control='caller_without_pop_remains_pending', passed=True, summary=o.summary()))

q, o, events = fixture()
q.os.thread_management.cur_thread.id = 2001
for address in (DIRECT_CALL, ENTRY, POP, CALLER, SUBSEQUENT):
    q.arch.regs.arch_pc = address
    o.checkpoint(q, address)
assert not o.frames and not o.completed and not o.continuations and not o.counts
rows.append(dict(control='identified_main_only', passed=True))

for address in POINTS:
    q, o, events = fixture(install=False)
    q.mem.write(address, bytes(4))
    try:
        o.install(q)
    except RuntimeError as ex:
        assert hex(address) in str(ex)
    else:
        raise AssertionError('Changed loaded instruction accepted: ' + hex(address))
rows.append(dict(control='each_original_hook_and_frame_byte_fails_closed', passed=True,
                 points={hex(a): h for a, h in POINTS.items()}, original_app_sha256=d.app_sha256))

def functions(path):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef)}

source_functions, new_functions = functions(SOURCE / 'probe.py'), functions(BASE / 'probe.py')
for name in ('deny', 'clone_guard', 'local_socketpair', 'guarded_read', 'arm_tls_helper', 'display_readv', 'display_write', 'display_writev', 'display_poll', 'network_count'):
    assert source_functions[name] == new_functions[name], name
for name in ('font_scan_quantum.py', 'fault_capture.py', 'constructor_observer.py', 'font_discovery_observer.py', 'resource_application_observer.py', 'layout_chain_observer.py', 'startup_trace.py'):
    assert (BASE / name).read_bytes() == (SOURCE / name).read_bytes(), name
source = (BASE / 'probe.py').read_text()
assert 'next_phase.install(q)' not in source and 'stdio.install(q)' not in source
assert 'function_trace(name), address' not in source and 'startup.syscall_enter(name)' not in source
assert 'snd_pcm_readi' not in source[source.index('        if args.trace_startup:'):source.index('        ql.hook_address(marker("application_entry")')]
namespace = {'__file__': str(BASE / 'startup_trace.py')}
exec((BASE / 'startup_trace.py').read_text().split('class StartupTrace:')[0], namespace)
assert set(namespace['POINTS']) == {0x6980f4}
rows.append(dict(control='unchanged_guards_TLS_count_selector_fault_capture_and_sparse_observations', passed=True))

identity = [dict(path=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            for p in (BASE / 'probe.py', BASE / 'active_enclosing_observer.py', Path(__file__))]
result = dict(passed=True, full_application_guests_launched=0, original_app_sha256=d.app_sha256,
              code_identities=identity, rows=rows,
              limits='Isolated original instruction and observer controls; not full routine execution or a scheduler reliability proof.')
(BASE / 'active-enclosing-controls.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(passed=True, controls=len(rows), full_application_guests_launched=0, code_identities=identity)))
