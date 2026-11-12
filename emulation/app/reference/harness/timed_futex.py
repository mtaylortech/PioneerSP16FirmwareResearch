"""Scoped relative wait correction; stop/save before any cooperative wait."""
import collections
from types import SimpleNamespace
# Linux guest errno values; Darwin host ETIMEDOUT/EAGAIN differ.
errno = SimpleNamespace(EINVAL=22, EFAULT=14, EAGAIN=11, ETIMEDOUT=110, ECANCELED=125)
import hashlib
from pathlib import Path
from queue import Queue
import struct
import time
from gevent.event import Event
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_PC
from qiling.os.posix.syscall.futex import ql_syscall_futex

class TimerFutex:
    NAME = 'Juce Timer'
    NAMES = ('Juce Timer', 'ProjectManager')
    START, END, PC, LR = 0xb4f8, 0xb918, 0xb654, 0xb638
    def __init__(self, emit, names, observer=None, clock=time.monotonic):
        self.emit,self.names,self.observer,self.clock=emit,names,observer,clock
        self.mapping=None;self.active={};self.counts=collections.Counter();self.latest={}
        self.delegate=ql_syscall_futex
    def install_mapping(self,q,path):
        from elftools.elf.elffile import ELFFile
        source=Path(path)
        with source.open('rb') as f:
            elf=ELFFile(f)
            symbol=next(s for s in elf.get_section_by_name('.dynsym').iter_symbols() if s.name=='pthread_cond_timedwait')
            if symbol['st_value']!=self.START:raise RuntimeError('Original timedwait symbol differs')
            segment=next(s for s in elf.iter_segments() if s['p_type']=='PT_LOAD' and s['p_vaddr']<=self.START<s['p_vaddr']+s['p_filesz'])
            expected=segment.data()[self.START-segment['p_vaddr']:self.END-segment['p_vaddr']]
        candidates=sorted({a for a,b,perm,label,*other in q.mem.map_info if 'libpthread' in label and bytes(q.mem.read(a,4))==b'\x7fELF'})
        if len(candidates)!=1:raise RuntimeError('Unique original libpthread mapping required')
        base=candidates[0];actual=bytes(q.mem.read(base+self.START,len(expected)))
        if actual!=expected:raise RuntimeError('Loaded timedwait wrapper bytes differ')
        self.mapping=dict(source=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),base=base,start=base+self.START,end=base+self.END,pc=base+self.PC,lr=base+self.LR,expected=expected.hex(),actual=actual.hex(),matches=True)
        self.emit('timer_futex_wrapper_validated',**self.mapping)
        if self.observer:self.observer.install_library(q,base,source)
    def selected(self,q,op,timeout):
        t=q.os.thread_management.cur_thread
        return bool(timeout and op in (0,128) and self.mapping and self.names.get(t.id) in self.NAMES and q.arch.regs.arch_pc==self.mapping['pc'] and q.arch.regs.lr==self.mapping['lr'])
    def install_wake_filter(self,q):
        original=q.os.futexm.get_futex_wake_list
        def wake_list(guest,addr,number,bitset=0xffffffff):
            # Purge only our elapsed waiters before the held manager counts wakes.
            for row in list(self.active.values()):
                if row['address']==addr and row['state']=='pending' and self.clock()>=row['deadline']:
                    self.resolve(guest,row,-errno.ETIMEDOUT,'timeout_before_wake')
            selected=original(guest,addr,number,bitset)
            for thread,event in selected:
                row=self.active.get(id(event))
                if row is not None:
                    self.resolve(guest,row,0,'wake_selected')
            return selected
        q.os.futexm.get_futex_wake_list=wake_list
    def remove(self,q,row):
        manager=q.os.futexm;queue=manager.wait_list.get(row['address'])
        if queue is None:return False
        removed=False
        with queue.mutex:
            retained=collections.deque()
            for entry in queue.queue:
                if entry[2] is row['event']:removed=True
                else:retained.append(entry)
            queue.queue.clear();queue.queue.extend(retained)
        if queue.empty() and manager.wait_list.get(row['address']) is queue:del manager.wait_list[row['address']]
        return removed
    def resolve(self,q,row,result,source):
        if row['state']!='pending':return False
        row.update(state=source,result=result,resolved=self.clock())
        row['removed']=self.remove(q,row)
        self.counts[source]+=1
        if result!=0:row['event'].set()
        return True
    def receipt(self,row):
        return {k:v for k,v in row.items() if k not in ('event','thread')}
    def call(self,q,uaddr,op,val,timeout,uaddr2,val3):
        if not self.selected(q,op,timeout):return self.delegate(q,uaddr,op,val,timeout,uaddr2,val3)
        thread=q.os.thread_management.cur_thread;tid=thread.id
        self.counts['selected']+=1;seq=self.counts['selected']
        self.counts['selected:'+self.names[tid]]+=1;verbose=self.counts['selected:'+self.names[tid]]<=4
        identity=self.observer.call_begin(q,seq) if self.observer else {}
        def immediate(result):
            self.counts['immediate:'+str(result)]+=1
            if self.observer:self.observer.call_immediate(q,identity,result)
            return result
        try:
            sec,nsec=struct.unpack('<ii',bytes(q.mem.read(timeout,8)))
            if sec<0 or not 0<=nsec<1000000000:return immediate(-errno.EINVAL)
            if uaddr&3:return immediate(-errno.EINVAL)
            if q.unpack32(q.mem.read(uaddr,4))!=val:return immediate(-errno.EAGAIN)
        except Exception:return immediate(-errno.EFAULT)
        begin=self.clock();duration=sec+nsec/1e9;ev=Event()
        row=dict(**identity,sequence=seq,tid=tid,address=uaddr,operation=op,expected_value=val,timespec=[sec,nsec],begin=begin,deadline=begin+duration,duration_requested=duration,state='pending',event=ev,thread=thread,sp=q.arch.regs.sp)
        q.emu_stop()
        self.active[id(ev)]=row
        manager=q.os.futexm
        if uaddr not in manager.wait_list:manager.wait_list[uaddr]=Queue()
        manager.wait_list[uaddr].put((0xffffffff,thread,ev))
        if self.observer:self.observer.wait_entry(q,row)
        if verbose:self.emit('timer_futex_entry',thread=tid,thread_name=self.names[tid],**self.receipt(row))
        def deferred(current):
            if current is not thread or current.saved_context is None:raise RuntimeError('Timed futex requires calling thread saved context')
            try:
                if row['state']=='pending':
                    ev.wait(timeout=max(0,row['deadline']-self.clock()))
                if row['state']=='pending':self.resolve(q,row,-errno.ETIMEDOUT,'timeout')
                current.saved_context.reg_write(UC_ARM_REG_R0,row['result']&0xffffffff)
                self.counts['saved_completion']+=1
                self.counts['completed:'+self.names[tid]]+=1
                completed=dict(**self.receipt(row),actual_seconds=self.clock()-begin,saved_pc=hex(current.saved_context.reg_read(UC_ARM_REG_PC)),saved_r0=hex(current.saved_context.reg_read(UC_ARM_REG_R0)),saved_context_only=True)
                self.latest[tid]=completed
                if self.observer:self.observer.wait_completed(row,completed)
                if verbose:self.emit('timer_futex_completion',thread=tid,thread_name=self.names[tid],**completed)
            finally:
                if row['state']=='pending':self.resolve(q,row,-errno.ECANCELED,'cancelled')
                self.remove(q,row);self.active.pop(id(ev),None)
        thread.sched_cb=deferred
        return 0
    def summary(self):
        return dict(enabled=True,scope='named Juce Timer and ProjectManager; loaded pthread_cond_timedwait PC/LR; finite relative WAIT only',counts=dict(self.counts),pending=[self.receipt(r) for r in self.active.values()],latest=self.latest,wrapper=self.mapping)
