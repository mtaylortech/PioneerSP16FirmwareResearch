# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Pure-Python model of the TORAIZ SP-16 1.60 `PerformanceFxLoFi` effect, slot 25 (0xfc434), its parameter path (0xfc278),
filter update (own slot 32, 0xfacec), wet/dry law (slot 26, 0xfac70) and reset (slot 27, 0xfb02c).

Own re-implementation written from the analysis in docs/effects/lofi.md (F128-F130). It contains no firmware bytes; constants are the
documented numeric values of the algorithm. It reuses the LoFi building blocks of lofi.py (LinearParameter
change detection, the 0x44-byte filter container 0xfc5e4/0xfbb70 with its biquads, SignalGate and cutoff/Q step ramp), which
the 1.60 code also shares; lofi.py itself is not modified.

Signal flow per block (slot 25 0xfc434):  apply parameters (0xfc278) -> filter A (LPF container, obj+0x330, 0xfbb70)
  -> bit crusher (obj+0x32c, 0xfaf28, only if bits <= 31) -> sample-and-hold (obj+0x328, inline) -> filter B (HPF container,
  obj+0x334, 0xfbb70) -> slot 26 (wet/dry from LEVEL, every block). No preamp, no position gate, no call of the LoFi kernel 0xfbf64.

Parameters (EffectBase slot 14 index; ctor "last" value): 0 LEVEL (0.0), 1 REDUCTION (0.5), 2 CUTOFFMAX (0.5), 3 RESONANCE (0.5).
  LEVEL L drives everything (one "amount" control):
    bits    b = 12 * (5/12)^(2L) for L < 0.5, else 5          (12 ... 5 bits; crusher int = round(b), scale = powf(2, b) / 2)
    S&H     step = max(1, L * 44.1 * REDUCTION)                (hold length in samples, 1 ... 44.1)
    LPF     fc = 20000 * 0.015^((1 - CUTOFFMAX) * L)           (20 kHz ... 300 Hz)
    HPF     fc = 20 * 400^(CUTOFFMAX * L)                      (20 Hz ... 8 kHz)
    Q       q = 0.707107 + 7.2928929 * RESONANCE, then scaled down near the ends (fc > 2500: * (20000 - fc) / 17500, floor 0.707107;
            fc < 700: * (fc - 20) / 680, floor 0.1), per filter
    wet/dry w = clamp((L - 4/255) / (33/255), 0, 1): wet = w, dry = 1 - w (EffectBase +0x14 / +0x10)
Usage: m = PerfLoFi(); m.set_param(idx, v); L, R = m.process(L, R)
"""
import math
import crmath as CR                                    # glibc-exact double pow (H029)
from lofi import F, EPS, Param, FilterContainer, near, rnd      # shared LoFi building blocks (own code, F025-F031)
from fdlibm_powf import powf

FS = 44100
PARAM_NAMES = ["LEVEL", "REDUCTION", "CUTOFFMAX", "RESONANCE"]
CTOR_LAST = [0.0, 0.5, 0.5, 0.5]
C_LO, C_HI, C_SPAN = F(4.0 / 255.0), F(37.0 / 255.0), F(33.0 / 255.0)    # 0x3c808081 0x3e149495 0x3e048485
Q0, QK = F(0.707107), F(7.2928929)                                       # 0x3f3504f7 0x40e95f61
LPF_BASE = float(F(0.015))                                               # double of float 0.015 (0x3f8eb851e0000000)
K_SH = F(44.1)
B_BASE = float(F(5.0 / 12.0))                                            # double of float 5/12 (0x3fdaaaaaa0000000)


class PerfLoFi:
    def __init__(self, fs=FS, block=64):
        self.fs = fs
        self.params = [Param("float", v) for v in CTOR_LAST]
        self.L = F(0.0); self.R = F(0.0); self.CM = F(0.5); self.RES = F(0.5)     # +0x338 +0x33c +0x340 +0x344
        self.flag_sh = 0; self.flag_filt = 0                                     # bytes +0x348 / +0x349
        self.sh_phase = F(1.0); self.sh_step = F(1.0); self.sh_hold = [F(0.0), F(0.0)]   # +0x328 (0x18)
        self.bits = 32; self.scale = F(256.0); self.inv = F(1.0 / 256.0)         # +0x32c (0xc)
        self.fa = FilterContainer(fs); self.fa.pending = 1; self.fa.gate.close()   # +0x330: LPF
        self.fb = FilterContainer(fs); self.fb.pending = 0; self.fb.gate.close()   # +0x334: HPF
        self.dry = None; self.wet = None

    # --- parameters ---------------------------------------------------------------------------------------------
    def set_param(self, idx, v):                        # EffectBase slot 14 0x105d24 (index 0..3, else returns 3)
        if 0 <= idx < 4: self.params[idx].set(v); return 0
        return 3

    def _bits(self):
        L = self.L
        if L < F(0.5):
            b = F(CR.pow(B_BASE, float(F(L + L))) * 12.0)
        else:
            b = F(5.0)
        self.bits = rnd(b)
        self.scale = F(powf(F(2.0), b) * F(0.5))
        self.inv = F(F(1.0) / self.scale)

    def _step(self):
        s = F(F(self.L * K_SH) * self.R)
        return F(1.0) if s < F(1.0) else s

    def apply_params(self):                             # 0xfc278 (order REDUCTION, CUTOFFMAX, RESONANCE, LEVEL)
        P = self.params
        if P[1].changed(): self.R = P[1].get(); self.flag_sh = 1
        if P[2].changed(): self.CM = P[2].get(); self.flag_filt = 1
        if P[3].changed(): self.RES = P[3].get(); self.flag_filt = 1
        if P[0].changed():
            self.L = P[0].get(); self.flag_sh = 1; self.flag_filt = 1
            self._bits()
        if self.flag_sh:
            self.flag_sh = 0; self.sh_step = self._step()
        if self.flag_filt:
            self.flag_filt = 0; self.update_filters()

    @staticmethod
    def _q(fc, res):
        q = F(Q0 + F(res * QK))
        if fc > F(2500.0):
            q = F(q * F(F(F(20000.0) - fc) * F(5.7142857e-05)))
            if q < Q0: q = Q0
        if fc < F(700.0):
            q = F(q * F(F(fc - F(20.0)) * F(0.00147058826)))
            if q < F(0.1): q = F(0.1)
        return q

    def _set(self, fc_cont, fc, q):
        fc_cont.cut_t = fc; fc_cont.dirty41 = 1
        d = F(fc_cont.q_t - q)
        if d <= 0: d = -d
        if not d < EPS: fc_cont.q_t = q

    def update_filters(self):                           # own slot 32 0xfacec
        fa = F(CR.pow(LPF_BASE, float(F(F(F(1.0) - self.CM) * self.L))) * 20000.0)
        self._set(self.fa, fa, self._q(fa, self.RES))
        fb = F(CR.pow(400.0, float(F(self.L * self.CM))) * 20.0)
        self._set(self.fb, fb, self._q(fb, self.RES))

    def update_mix(self):                               # slot 26 0xfac70
        L = self.L
        if L < C_LO: self.dry, self.wet = F(1.0), F(0.0)
        elif not L < C_HI: self.dry, self.wet = F(0.0), F(1.0)
        else:
            w = F(F(L - C_LO) / C_SPAN); self.dry, self.wet = F(F(1.0) - w), w

    def reset(self):                                    # slot 27 0xfb02c
        self.L = self.params[0].get(); self.R = self.params[1].get()
        self.sh_hold = [F(0.0), F(0.0)]
        s = self._step(); self.sh_step = s; self.sh_phase = s
        self._bits()
        for c in (self.fa, self.fb):                    # clear the current sub-filter's history (both channels)
            if 0 <= c.cur < len(c.subs):
                sub = c.subs[c.cur]
                sub.v = [[F(0.0), F(0.0)] for _ in range(4)]; sub.y = [[F(0.0), F(0.0)] for _ in range(4)]
                sub.yprev = [F(0.0), F(0.0)]
        self.CM = self.params[2].get(); self.RES = self.params[3].get()
        self.update_filters()
        self.flag_sh = 0; self.flag_filt = 0
        return 0

    # --- stages -------------------------------------------------------------------------------------------------
    def crush(self, L, R, n):                           # 0xfaf28 (as LoFi): sign * (trunc(S * sqrt|x|) / S)^2
        sc = self.scale; inv = float(self.inv)
        for j in range(n):
            for buf in (L, R):
                x = buf[j]
                sg = F(1.0) if x > 0 else F(-1.0)
                a = F(math.sqrt(F(x * sg)))
                q = F(math.trunc(float(F(sc * a))) * inv)
                buf[j] = F(sg * F(q * q))

    def sample_hold(self, L, R, n):                     # inline in 0xfc434
        ph = self.sh_phase; st = self.sh_step; hL, hR = self.sh_hold
        for j in range(n):
            if ph < F(1.0):
                ph = F(ph + st); hL = L[j]; hR = R[j]
            else:
                L[j] = hL; R[j] = hR
            ph = F(ph - F(1.0))
        self.sh_phase = ph; self.sh_hold = [hL, hR]

    def process(self, L, R, order="perf"):              # slot 25 0xfc434; `order` only for the harness's alternative tests
        L = [F(x) for x in L]; R = [F(x) for x in R]; n = len(L)
        self.apply_params()
        if order == "perf":
            self.fa.process(L, R, 0, n)
            if self.bits <= 31: self.crush(L, R, n)
            self.sample_hold(L, R, n)
            self.fb.process(L, R, 0, n)
        elif order == "sh_before_crush":                # mutant: LoFi-kernel order of crusher / S&H swapped
            self.fa.process(L, R, 0, n)
            self.sample_hold(L, R, n)
            if self.bits <= 31: self.crush(L, R, n)
            self.fb.process(L, R, 0, n)
        elif order == "filters_last":                   # mutant: LoFi 'post' order (crush -> S&H -> both filters)
            if self.bits <= 31: self.crush(L, R, n)
            self.sample_hold(L, R, n)
            self.fa.process(L, R, 0, n); self.fb.process(L, R, 0, n)
        else:
            raise ValueError(order)
        self.update_mix()
        return [float(x) for x in L], [float(x) for x in R]
