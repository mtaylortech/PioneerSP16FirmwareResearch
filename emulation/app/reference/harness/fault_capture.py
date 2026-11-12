"""Read-only failure capture before Qiling can restore another thread's context.

Wrap the existing interrupt dispatcher: adding a Qiling interrupt hook would
mark an otherwise unhandled interrupt handled and change the failure itself.
"""
class FaultCaptureMixin:
    fault_emit = None

    def fault_context(self, error, **details):
        row = dict(error_type=type(error).__name__, error=str(error), read_only=True, **details)
        try:
            row['thread'] = self.os.thread_management.cur_thread.id
        except AttributeError:
            row['thread'] = None
        try:
            regs = {n: self.arch.regs.read(n) for n in ['r'+str(i) for i in range(13)]+['sp','lr','pc','cpsr']}
            row['registers'] = {n: hex(v) for n,v in regs.items()}
            maps = list(self.mem.get_mapinfo())
            row['mappings'] = maps
            def cell(address, size=64):
                result = dict(address=hex(address), alignment_mod4=address&3,
                              mappings=[m for m in maps if m[0] <= address < m[1]])
                try: result['bytes'] = bytes(self.mem.read(address, size)).hex()
                except Exception as exc: result['read_error'] = repr(exc)
                return result
            row['pointer_cells'] = {n: cell(regs[n]) for n in ('r0','r1','r3','r4','r5','sp')}
            row['instruction_address'] = hex(regs['pc'])
            row['instruction_bytes'] = bytes(self.mem.read(regs['pc'],4)).hex()
            row['instruction_context'] = cell(regs['pc']-16,48)
            try:
                row['instruction'] = [{'address':hex(i.address),'mnemonic':i.mnemonic,'operands':i.op_str}
                                      for i in self.arch.disassembler.disasm(bytes.fromhex(row['instruction_bytes']),regs['pc'])]
            except Exception as exc: row['disassembly_error'] = repr(exc)
            row['derived_pointer_cells'] = {}
            for n in ('r0','r4','r5'):
                try:
                    value = int.from_bytes(self.mem.read(regs[n],4),'little')
                    row['derived_pointer_cells'][n] = dict(pointee=cell(value), header_minus_8=cell((value-8)&0xffffffff))
                except Exception as exc: row['derived_pointer_cells'][n] = {'read_error':repr(exc)}
            try: row['outer_assignment_caller_sp_plus_20'] = hex(int.from_bytes(self.mem.read(regs['sp']+20,4),'little'))
            except Exception as exc: row['stack_caller_error'] = repr(exc)
        except Exception as exc:
            row['diagnostic_error'] = repr(exc)
        return row

    def _hook_intr_cb(self, uc, intno, pack_data):
        try:
            return super()._hook_intr_cb(uc,intno,pack_data)
        except Exception as error:
            try: self._fault_interrupt = self.fault_context(error, interrupt=intno, capture_site='original interrupt dispatcher exception')
            except Exception: pass
            raise

    def emu_start(self, begin, end, timeout=0, count=0):
        self._observation_slice = dict(begin=hex(begin), end=hex(end), timeout=timeout, count=count)
        self._fault_interrupt = None
        try:
            return super().emu_start(begin,end,timeout=timeout,count=count)
        except Exception as error:
            try:
                row = self.fault_context(error, begin=hex(begin), end=hex(end), count=count, timeout=timeout,
                                         capture_site='emu_start exception before scheduler return',
                                         interrupt_context=self._fault_interrupt)
                if self.fault_emit is not None: self.fault_emit('synchronous_emulator_exception_context', **row)
            except Exception: pass
            raise
