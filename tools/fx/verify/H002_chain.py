#!/usr/bin/env python3
"""H002 - static audio call chain (ALSA thread -> FX processors) and buffer-format facts, as machine checks.

Each check reads raw file bytes of target/EP085_Main_R_fw160 (SHA-256 asserted in harness/lib/sp16img.py) and asserts
either (a) an instruction at an address (capstone text must match a regex), or (b) a vtable slot word equals a target,
or (c) a data word / typeinfo name. All addresses 1.60. Nothing is executed. Every edge of the chain in
kb/cycles/002.md (Worker) is one or more checks here; the run fails loudly (exit 1) if any check fails.
Outputs (only in --out DIR): chain_checks.txt, chain_checks.json, format_table.txt
Usage: .venv/bin/python harness/H002_chain.py --out harness/out/H002
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import sp16img

ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(sp16img.ROOT, "harness", "out", "H002"))
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
im = sp16img.Image(); plt = im.plt()
RES = []


def ins(va):
    i = list(im.md.disasm(im.data[im.off(va):im.off(va) + 4], va))
    return ("%s %s" % (i[0].mnemonic, i[0].op_str)) if i else "<undecodable>"


def I(edge, va, rx):                      # instruction check
    t = ins(va); ok = re.fullmatch(rx, t) is not None
    RES.append((edge, "0x%x" % va, t, ok))


def V(edge, vt, slot, tgt):              # vtable slot check
    w = im.u32(vt + 4 * slot); RES.append((edge, "vt 0x%x[%d]" % (vt, slot), "0x%x" % w, w == tgt))


def W(edge, va, val):                    # data word / literal check
    w = im.u32(va); RES.append((edge, "word 0x%x" % va, "0x%x" % w, w == val))


def TI(edge, vt, name):                  # typeinfo name of a vtable (vt-4 -> typeinfo, +4 -> name)
    ti = im.u32(vt - 4); n = im.cstr(im.u32(ti + 4)); RES.append((edge, "typeinfo(0x%x)" % vt, n, name in n))


def P(edge, va, name):                   # direct bl to PLT import
    t = ins(va); m = re.match(r"bl #(0x[0-9a-f]+)", t); ok = bool(m) and plt.get(int(m.group(1), 16)) == name
    RES.append((edge, "0x%x" % va, t + " <%s>" % plt.get(int(m.group(1), 16)) if m else t, ok))


H = r"(?:0x[0-9a-f]+|\d+)"
# ---------------- thread entry: pthread_create -> juce Thread::threadEntryPoint -> run() (slot 2) -------------------
W("T1 launchThread literal start_routine", 0x646f44, 0x6682ac)
I("T1 launchThread loads start_routine", 0x646f08, r"ldr r2, \[pc, #0x34\]")
I("T1 launchThread arg=this", 0x646f10, r"mov r3, r4")
P("T1 pthread_create call", 0x646f18, "pthread_create")
I("T2 start_routine -> threadEntryPoint", 0x6682b0, r"bl #0x6680b8")
I("T3 startSuspensionEvent.wait(10000)", 0x6680f4, r"movw r1, #0x2710")
I("T3 threadEntryPoint r0=this", 0x668114, r"mov r0, r4")
I("T3 threadEntryPoint run()=vt+8", 0x668118, r"ldr r3, \[r3, #8\]")
I("T3 threadEntryPoint call run()", 0x66811c, r"blx r3")
I("T4 startThread -> launchThread", 0x6472c4, r"bl #0x646ef4")
I("T5 ALSA open: r4 = device+0x18", 0x5903c8, r"add r4, r6, #0x18")
I("T5 ALSA open: startThread prio 9", 0x590bfc, r"mov r1, #9")
I("T5 ALSA open: startThread(ALSAThread)", 0x590c00, r"bl #0x64722c")
TI("T6 vtable 0x936000 is ALSAThread", 0x936000, "ALSAThread")
V("T6 ALSAThread slot2 = run", 0x936000, 2, 0x58e394)
W("T7 createDevice literal AudioIODevice vt", 0x58c2d0 + 8 + 0x730, 0x935e10)
I("T7 createDevice sl += 0x188 (-> 0x935f98)", 0x58c2ec, r"add sl, sl, #0x188")
I("T7 createDevice store ALSAAudioIODevice vptr", 0x58c304, r"str sl, \[r8\], #0xc")
I("T7 createDevice Thread ctor(this+0x18)", 0x58c340, r"bl #0x637dc8")
I("T7 createDevice r3 = 0x935f98+0x68 = 0x936000", 0x58c360, r"add r3, sl, #0x68")
I("T7 createDevice store ALSAThread vptr @+0x18", 0x58c364, r"str r3, \[r6, #0x18\]")
TI("T7 vtable 0x935f98 is ALSAAudioIODevice", 0x935f98, "ALSAAudioIODevice")
# ---------------- ALSAThread::run -> callback->audioDeviceIOCallback (slot 2) ----------------------------------------
P("A1 run: snd_pcm_wait", 0x58e848, "snd_pcm_wait")
P("A1 run: snd_pcm_avail_update", 0x58e898, "snd_pcm_avail_update")
I("A1 run: callbackLock enter (this+0x158)", 0x58e9c0, r"bl #0x644d08")
I("A1 run: callback = [this+0x130]", 0x58e9c4, r"ldr r0, \[r4, #0x130\]")
I("A1 run: numOut on stack", 0x58e494, r"ldr r8, \[r4, #0x8a4\]")
I("A1 run: bufferSize [this+0xe0]", 0x58e498, r"ldr lr, \[r4, #0xe0\]")
I("A1 run: vt+8 (audioDeviceIOCallback)", 0x58e4ac, r"ldr ip, \[ip, #8\]")
I("A1 run: call callback", 0x58e4b0, r"blx ip")
I("A1 run: write device 0", 0x58e428, r"bl #0x58df80")
V("A2 ALSAAudioIODevice slot10 = start", 0x935f98, 10, 0x589ab8)
I("A2 start: callback stored at device+0x148 (=thread+0x130)", 0x589b04, r"str r5, \[r4, #0x148\]")
I("A3 devmgr: device=[+0x78]", 0x594fa4, r"ldr r0, \[r4, #0x78\]")
I("A3 devmgr: callbackHandler=[+0x1d8]", 0x594fa8, r"ldr r1, \[r4, #0x1d8\]")
I("A3 devmgr: vt+0x28 (start)", 0x594fb0, r"ldr r3, \[r3, #0x28\]")
I("A3 devmgr: device->start(handler)", 0x594fb4, r"blx r3")
W("A4 devmgr ctor literal CallbackHandler vt", 0x5968c8 + 8 + 0x124, 0x934af0)
I("A4 devmgr ctor handler->owner=this", 0x5968d0, r"str r4, \[r0, #0xc\]")
I("A4 devmgr ctor store vptrs", 0x5968dc, r"stm r0, \{r2, ip\}")
I("A4 devmgr ctor this+0x1d8=handler", 0x5968ec, r"str r0, \[r4, #0x1d8\]")
TI("A4 vtable 0x934af0 is CallbackHandler", 0x934af0, "CallbackHandler")
V("A5 CallbackHandler slot2", 0x934af0, 2, 0x59971c)
I("A5 handler: owner=[this+0xc]", 0x59971c, r"ldr r0, \[r0, #0xc\]")
I("A5 handler -> audioDeviceIOCallbackInt", 0x599720, r"b #0x591f48")
I("A6 IOCallbackInt: callbacks=[+0x7c]", 0x592088, r"ldr r0, \[r8, #0x7c\]")
I("A6 IOCallbackInt: vt+8", 0x5920a4, r"ldr ip, \[ip, #8\]")
I("A6 IOCallbackInt: callbacks[0]->audioDeviceIOCallback", 0x5920a8, r"blx ip")
I("A6 IOCallbackInt: callbacks[i]->audioDeviceIOCallback", 0x5920f8, r"blx ip")
I("A7 addAudioCallback: aboutToStart vt+0xc", 0x591d30, r"ldr r3, \[r3, #0xc\]")
I("A7 addAudioCallback: array [+0x7c] grow", 0x591db0, r"str r0, \[r5, #0x7c\]")
I("A7 start: r4 = this+0x268 (player)", 0x1b5be0, r"add r4, r6, #0x268")
I("A7 start: setProcessor(player, this)", 0x1b5be4, r"mov r1, r6")
I("A7 start: setProcessor call", 0x1b5bec, r"bl #0x612b50")
I("A7 start: devMgr=[this+0x264]", 0x1b5bf4, r"ldr r0, \[r6, #0x264\]")
I("A7 start: addAudioCallback(devMgr, player)", 0x1b5bf8, r"bl #0x591cb4")
I("A7 setProcessor: processor stored at player+8", 0x612ba8, r"str r5, \[r4, #8\]")
I("A8 AudioSystemBase ctor: player ctor", 0x1b8254, r"bl #0x612a9c")
W("A8 literal AudioProcessorPlayerChild vt", 0x1b8258 + 8 + 0x1a0, 0x8635c8)
I("A8 AudioSystemBase ctor: player vptr @+0x268", 0x1b8268, r"str r3, \[r4, #0x268\]")
TI("A8 vtable 0x8635c8 is AudioProcessorPlayerChild", 0x8635c8, "AudioProcessorPlayerChild")
V("A8 PlayerChild slot2 = AudioProcessorPlayer::audioDeviceIOCallback", 0x8635c8, 2, 0x60b560)
I("A9 player cb: processor=[this+8]", 0x60b698, r"ldr r0, \[r4, #8\]")
I("A9 player cb: vt+0x14 processBlock", 0x60b6b4, r"ldr r3, \[r3, #0x14\]")
I("A9 player cb: processor->processBlock", 0x60b6b8, r"blx r3")
# ---------------- processor = HexaTrackAudioSystem (graph) ---------------------------------------------------------
I("G1 HexaTrack ctor: AudioSystemBase ctor", 0x1c2ce4, r"bl #0x1b8198")
W("G1 literal HexaTrackAudioSystem vt", 0x1c2ce8 + 8 + 0x2a0, 0x863da0)
I("G1 HexaTrack ctor: vptr store", 0x1c2d04, r"str r2, \[r4\]")
TI("G1 vtable 0x863da0 is HexaTrackAudioSystem", 0x863da0, "HexaTrackAudioSystem")
V("G1 HexaTrack slot5 = own processBlock", 0x863da0, 5, 0x1c12a0)
V("G1 HexaTrack slot55 = graph build 0x1bc8d4", 0x863da0, 55, 0x1bc8d4)
V("G1 IAudioSystem-in-HexaTrack slot48 = start thunk", 0x863f74, 48, 0x1b5b7c)
I("G1 start thunk this-0x200", 0x1b5b7c, r"sub r0, r0, #0x200")
I("G2 HexaTrack processBlock r0=this", 0x1c1400, r"mov r0, r4")
I("G2 HexaTrack processBlock -> AudioProcessorGraph::processBlock", 0x1c140c, r"bl #0x5f91fc")
V("G2 juce::AudioProcessorGraph slot5", 0xaa4938, 5, 0x5f91fc)
I("G3 graph: ops=[+0x148]", 0x5f9274, r"ldr r0, \[r5, #0x148\]")
I("G3 graph: vt+8 perform", 0x5f9290, r"ldr ip, \[ip, #8\]")
I("G3 graph: op->perform", 0x5f9294, r"blx ip")
TI("G4 vtable 0xaa3ad0 is ProcessBufferOp", 0xaa3ad0, "ProcessBufferOp")
V("G4 ProcessBufferOp slot2 = perform", 0xaa3ad0, 2, 0x601f90)
I("G4 perform: processor=[op+8]", 0x601ff4, r"ldr r0, \[r4, #8\]")
I("G4 perform: vt+0x14", 0x60200c, r"ldr r3, \[r3, #0x14\]")
I("G4 perform: processor->processBlock", 0x602010, r"blx r3")
I("G5 op builder: vptr ProcessBufferOp", 0x606918, r"str r2, \[r0\]")
W("G5 op builder literal", 0x60690c + 8 - 0xa7c, 0xaa3ad0)
I("G5 op builder: r3=node->processor [node+0x18]", 0x606948, r"ldr r3, \[r3, #0x18\]")
I("G5 op builder: op+8 = processor", 0x60695c, r"str r3, \[r4, #8\]")
I("G5 addNode compares [node+0x18]", 0x5fe064, r"ldr sb, \[r0, #0x18\]")
I("G6 build: r7=this", 0x1bc8ec, r"mov r7, r0")
I("G6 build: new CompositeFxUnit ctor", 0x1bdeb4, r"bl #0x1aa808")
I("G6 build: this+0x698 = compositeFxUnit", 0x1bdeb8, r"str r4, \[r7, #0x698\]")
I("G6 build: addNamedNode(this, compositeFxUnit, 'compositeFxUnitNode')", 0x1bded4, r"bl #0x1b6020")
I("G6 addNamedNode -> addNode(graph, proc, 0)", 0x1b6034, r"bl #0x5fdfec")
# ---------------- CompositeFxUnit -> Master/SendFxUnit -> FxProcessor ----------------------------------------------
I("F1 build: MasterFxUnit ctor", 0x1bdc68, r"bl #0x1b1d30")
I("F1 build: this+0x608 = MasterFxUnit", 0x1bdc7c, r"str r4, \[r7, #0x608\]")
I("F1 build: SendFxUnit ctor", 0x1bdd5c, r"bl #0x1b3314")
I("F1 build: this+0x604 = SendFxUnit", 0x1bdd70, r"str r4, \[r7, #0x604\]")
I("F1 build: composite arg1 = MasterFxUnit", 0x1bde8c, r"ldr r5, \[r7, #0x608\]")
I("F1 build: composite arg2 = SendFxUnit", 0x1bde90, r"ldr r6, \[r7, #0x604\]")
I("F1 build: composite arg3 = pool [+0x5cc]", 0x1bde94, r"ldr r8, \[r7, #0x5cc\]")
I("F2 Composite ctor: vptr = 0x861a34-0x1e0", 0x1aa85c, r"sub r1, r8, #0x1e0")
I("F2 Composite ctor: vptr store", 0x1aa864, r"str r1, \[r6\]")
I("F2 Composite ctor: +0x8c = arg1", 0x1aa870, r"str r4, \[r6, #0x8c\]")
I("F2 Composite ctor: +0x90 = arg2", 0x1aa884, r"str r7, \[r6, #0x90\]")
I("F2 Composite ctor: +0x94 = arg3", 0x1aa888, r"str sl, \[r6, #0x94\]")
TI("F2 vtable 0x861854 is CompositeFxUnit", 0x861854, "CompositeFxUnit")
V("F2 CompositeFxUnit slot5", 0x861854, 5, 0x1a94cc)
I("F3 Composite pb: pool==0 -> inline path", 0x1a9588, r"beq #0x1a96e8")
I("F3 inline: MasterFxUnit->processBlock", 0x1a96fc, r"blx r3")
I("F3 inline: SendFxUnit=[+0x90]", 0x1a9700, r"ldr r0, \[r4, #0x90\]")
I("F3 inline: SendFxUnit->processBlock", 0x1a9714, r"blx r3")
I("F3 pooled: job.set(MasterFxUnit)", 0x1a959c, r"bl #0x153978")
I("F3 pooled: pool->slot5 execute", 0x1a95ec, r"blx r3")
I("F3 job.set = stm", 0x153978, r"stm r0, \{r1, r2, r3\}")
I("F3 job.run vt+0x14", 0x15398c, r"ldr r3, \[r3, #0x14\]")
I("F3 job.run -> unit->processBlock", 0x153990, r"blx r3")
I("F3 HexaTrack pool = new ParallelAudioProcessingManager", 0x1bc970, r"bl #0x153e98")
I("F3 pool ctor vptr store", 0x153eb8, r"str r3, \[r0\]")
TI("F3 vtable 0x849190 is ParallelAudioProcessingManager", 0x849190, "ParallelAudioProcessingManager")
V("F3 pool slot5 = execute", 0x849190, 5, 0x1539c0)
I("F3 execute: caller thread runs own jobs", 0x153a30, r"bl #0x153980")
TI("F3 vtable 0x849288 is ParallelAudioProcessingWorkerThread", 0x849288, "ParallelAudioProcessingWorkerThread")
V("F3 worker slot2 = run", 0x849288, 2, 0x155ea0)
V("F3 worker slot6 = runJobs", 0x849288, 6, 0x156384)
I("F3 worker run -> this->slot6", 0x155fdc, r"blx r3")
I("F3 worker runJobs -> job.run", 0x1563b4, r"bl #0x153980")
I("F3 worker ctor: Thread ctor", 0x1561bc, r"bl #0x637dc8")
TI("F4 vtable 0x862978 is MasterFxUnit", 0x862978, "MasterFxUnit")
V("F4 MasterFxUnit slot5", 0x862978, 5, 0x1b1b80)
I("F4 MasterFxUnit pb: proc=[+0x84]", 0x1b1b80, r"ldr r0, \[r0, #0x84\]")
I("F4 MasterFxUnit pb: vt+0x14", 0x1b1b94, r"ldr r3, \[r3, #0x14\]")
I("F4 MasterFxUnit pb: call", 0x1b1b98, r"blx r3")
I("F4 MasterFxUnit ctor: MasterFxProcessor ctor", 0x1b1d8c, r"bl #0x114bc0")
I("F4 MasterFxUnit ctor: +0x84 = proc", 0x1b1da0, r"str r5, \[r4, #0x84\]")
I("F4 MasterFxProcessor ctor: vptr store", 0x114be4, r"str r2, \[r4\]")
W("F4 MasterFxProcessor ctor literal", 0x114bd4 + 8 + 0x78c, 0x842aa8)
V("F4 MasterFxProcessor slot5 = 0x112acc (F010)", 0x842aa8, 5, 0x112acc)
TI("F5 vtable 0x862e28 is SendFxUnit", 0x862e28, "SendFxUnit")
V("F5 SendFxUnit slot5", 0x862e28, 5, 0x1b3068)
I("F5 SendFxUnit pb: proc=[+0x8c]", 0x1b3070, r"ldr r0, \[r0, #0x8c\]")
I("F5 SendFxUnit pb: call", 0x1b308c, r"blx r3")
I("F5 SendFxUnit ctor: SendFxProcessor ctor", 0x1b33f4, r"bl #0x11bbe4")
I("F5 SendFxUnit ctor: +0x8c = proc", 0x1b3408, r"str r5, \[r4, #0x8c\]")
I("F5 SendFxProcessor ctor: vptr store", 0x11bc10, r"str r2, \[r4\]")
W("F5 SendFxProcessor ctor literal", 0x11bbf8 + 8 + 0x798, 0x842d40)
V("F5 SendFxProcessor slot5 = 0x119994 (F010)", 0x842d40, 5, 0x119994)
# ---------------- buffer format -----------------------------------------------------------------------------------
I("B1 AudioSystemBase ctor: sampleRate hi = 0x40e58880 (44100.0)", 0x1b8300, r"movw sb, #0x8880")
I("B1 ... movt", 0x1b8308, r"movt sb, #0x40e5")
I("B1 ... bufferSize 64", 0x1b8304, r"mov r3, #0x40")
I("B1 ... call setup", 0x1b8314, r"bl #0x1b5e0c")
I("B2 setup: getAudioDeviceSetup", 0x1b5e40, r"bl #0x591440")
I("B3 ALSA open: bufferSize -> thread+0xe0", 0x5903ec, r"str r8, \[r6, #0xf8\]")
I("B3 ALSA open: sampleRate -> thread+0xd8", 0x5903f0, r"vstr d8, \[r6, #0xf0\]")
I("B4 setParameters: access RW_INTERLEAVED(3)", 0x58ef88, r"mov r2, #3")
P("B4 setParameters: set_access", 0x58ef8c, "snd_pcm_hw_params_set_access")
I("B4 setParameters: access RW_NONINTERLEAVED(4)", 0x58f2d4, r"mov r2, #4")
I("B4 setParameters: format table copy 0x48", 0x58efa8, r"mov r2, #0x48")
W("B4 format table addr", 0x58efa0 + 8 + 0x7e8, 0x936058)
I("B4 setParameters: flag -> S16_LE(2)", 0x58f1a0, r"mov r2, #2")
I("B4 setParameters: channels*2 if flag", 0x58f150, r"lslne r2, sl, #1")
I("B4 setParameters: periods = 2", 0x58f134, r"mov ip, #2")
I("B4 setParameters: period_size = bufferSize", 0x58f130, r"str r8, \[fp, #-0x40\]")
P("B4 setParameters: period_size_near", 0x58f390, "snd_pcm_hw_params_set_period_size_near")
I("B5 write: float->s32 inline (interleaved path)", 0x58e164, r"vcvt\.s32\.f32 s15, s15")
P("B5 write: snd_pcm_writei", 0x58e2b0, "snd_pcm_writei")
P("B5 write: snd_pcm_writen", 0x58e004, "snd_pcm_writen")
I("B6 MasterFxProcessor ctor: effect(…, 44100, 64)", 0x114bf0, r"movw r1, #0xac44")

L = []; bad = 0
for e, where, got, ok in RES:
    L.append("%s  %-62s %-18s %s" % ("OK  " if ok else "FAIL", e, where, got)); bad += (not ok)
L.append("TOTAL %d checks, %d failed" % (len(RES), bad))
open(os.path.join(a.out, "chain_checks.txt"), "w").write("\n".join(L) + "\n")
json.dump([dict(edge=e, where=w, got=g, ok=o) for e, w, g, o in RES], open(os.path.join(a.out, "chain_checks.json"), "w"), indent=1)
F = {0: "S8", 2: "S16_LE", 3: "S16_BE", 6: "S24_LE", 10: "S32_LE", 11: "S32_BE", 14: "FLOAT_LE", 15: "FLOAT_BE", 32: "S24_3LE", 33: "S24_3BE"}
T = [im.u32(0x936058 + 4 * i) for i in range(18)]
open(os.path.join(a.out, "format_table.txt"), "w").write("".join(
    "try %d: %-9s flags=0x%05x (bits=%d float=%d LE=%d low24=%d)\n" % (i // 2, F.get(T[i], T[i]), T[i + 1], T[i + 1] & 0xffff,
     (T[i + 1] >> 16) & 1, (T[i + 1] >> 17) & 1, (T[i + 1] >> 18) & 1) for i in range(0, 18, 2)))
print("\n".join(l for l in L if l.startswith("FAIL")) or "all checks OK"); print(L[-1])
sys.exit(1 if bad else 0)
