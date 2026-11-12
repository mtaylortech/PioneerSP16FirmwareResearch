/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 *
FUN_004e6fd4(undefined4 *param_1,undefined4 *param_2,undefined4 param_3,int *param_4,int *param_5)

{
  void *pvVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  undefined4 uVar5;
  int iVar6;
  int iVar7;
  undefined4 uVar8;
  int local_1f8 [2];
  int local_1f0 [2];
  int local_1e8 [2];
  int local_1e0 [2];
  int local_1d8 [2];
  int local_1d0 [2];
  int local_1c8 [2];
  int local_1c0 [2];
  int local_1b8 [2];
  int local_1b0 [2];
  int local_1a8 [2];
  int local_1a0 [2];
  int local_198 [2];
  int local_190 [2];
  int local_188 [2];
  int local_180 [2];
  int local_178 [2];
  int local_170 [2];
  int local_168 [2];
  int local_160 [2];
  int local_158 [2];
  int local_150 [2];
  int local_148 [2];
  int local_140 [2];
  int local_138 [2];
  int local_130 [2];
  int local_128 [2];
  int local_120 [2];
  int local_118 [2];
  int local_110 [2];
  int local_108 [2];
  int local_100 [2];
  int local_f8 [2];
  int local_f0 [2];
  int local_e8 [2];
  int local_e0 [2];
  int local_d8 [2];
  int local_d0 [2];
  int local_c8 [2];
  int local_c0 [2];
  int local_b8 [2];
  int local_b0 [2];
  int local_a8 [2];
  int local_a0 [2];
  int local_98 [2];
  int local_90 [2];
  int local_88 [2];
  int local_80 [2];
  int local_78 [2];
  int local_70 [2];
  int local_68 [2];
  int local_60 [2];
  int local_58 [2];
  int local_50;
  undefined1 auStack_4c [4];
  undefined1 auStack_48 [4];
  undefined1 auStack_44 [4];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [8];
  
  FUN_006c1630(auStack_4c,DAT_004e7e78);
  FUN_00391adc(param_1,param_2 + 2,param_4);
  iVar6 = DAT_004e7e7c;
  iVar4 = 0;
  *param_1 = param_2[1];
  param_1[0x1c] = DAT_004e7e80;
  FUN_006d3148(param_1 + 0x22);
  FUN_006c1630(param_1 + 0x23,auStack_4c);
  FUN_0062ab08(param_1 + 0x24);
  FUN_006a0280(auStack_4c);
  *param_1 = *param_2;
  param_1[0x1c] = DAT_004e7e84;
  do {
    iVar7 = iVar6 + iVar4 * 0xc;
    FUN_00627ba0(local_1f8,iVar7);
    iVar3 = local_1f8[0];
    iVar2 = *param_4;
    FUN_006280c8(local_1f8);
    if (iVar2 == iVar3) {
      uVar5 = *(undefined4 *)(iVar7 + 8);
      uVar8 = *(undefined4 *)(iVar7 + 4);
      goto LAB_004e70ac;
    }
    iVar4 = iVar4 + 1;
  } while (iVar4 != 0x33);
  uVar5 = 0;
  uVar8 = uVar5;
LAB_004e70ac:
  FUN_00666e84(auStack_48,DAT_004e7e88);
  pvVar1 = operator_new(0xe4);
  FUN_004e5c0c(pvVar1,param_3,uVar8,auStack_48);
  param_1[0x25] = pvVar1;
  FUN_006280c8(auStack_48);
  FUN_007ccc24(param_1,param_1[0x25],0xffffffff);
  switch(uVar5) {
  case 0:
    if (((*DAT_004e7f54 & 1) == 0) && (iVar6 = __cxa_guard_acquire(), iVar6 != 0)) {
      FUN_00666e84(DAT_004e7e90,DAT_004e7ed4);
      __cxa_guard_release(DAT_004e7f54);
      __aeabi_atexit(DAT_004e7e90,DAT_004e7ecc,DAT_004e7ed0);
    }
    iVar6 = 0;
    if (0 < param_5[2]) {
      do {
        iVar2 = *param_5;
        FUN_00627ba0(local_80,DAT_004e7e90);
        iVar4 = local_80[0];
        iVar3 = *(int *)(iVar2 + iVar6 * 8);
        FUN_006280c8(local_80);
        if (iVar3 == iVar4) {
          iVar6 = *(int *)(iVar2 + iVar6 * 8 + 4);
          goto LAB_004e7930;
        }
        iVar6 = iVar6 + 1;
      } while (iVar6 < param_5[2]);
      iVar6 = 0;
    }
LAB_004e7930:
    FUN_00666e84(auStack_44,DAT_004e7eb4);
    pvVar1 = operator_new(0x130);
    FUN_00499ee4(pvVar1,param_3,auStack_44,iVar6,param_4);
    param_1[0x26] = pvVar1;
    FUN_006280c8(auStack_44);
    FUN_007ccc24(param_1,param_1[0x26],0xffffffff);
    goto switchD_004e70f4_default;
  case 1:
    if (((*DAT_004e7f84 & 1) == 0) && (iVar6 = __cxa_guard_acquire(), iVar6 != 0)) {
      FUN_00666e84(DAT_004e7eb8,DAT_004e7ec8);
      __cxa_guard_release(DAT_004e7f84);
      __aeabi_atexit(DAT_004e7eb8,DAT_004e7ecc,DAT_004e7ed0);
    }
    if (0 < param_5[2]) {
      iVar6 = 0;
      do {
        iVar2 = *param_5;
        FUN_00627ba0(local_78,DAT_004e7eb8);
        iVar4 = local_78[0];
        iVar3 = *(int *)(iVar2 + iVar6 * 8);
        FUN_006280c8(local_78);
        if (iVar3 == iVar4) {
          uVar8 = *(undefined4 *)(iVar2 + iVar6 * 8 + 4);
          goto LAB_004e79ec;
        }
        iVar6 = iVar6 + 1;
      } while (iVar6 < param_5[2]);
    }
    uVar8 = 0;
LAB_004e79ec:
    if (((*DAT_004e7f54 & 1) == 0) && (iVar6 = __cxa_guard_acquire(), iVar6 != 0)) {
      FUN_00666e84(DAT_004e7e90,DAT_004e7ed4);
      __cxa_guard_release(DAT_004e7f54);
      __aeabi_atexit(DAT_004e7e90,DAT_004e7ecc,DAT_004e7ed0);
    }
    iVar6 = 0;
    if (0 < param_5[2]) {
      do {
        iVar2 = *param_5;
        FUN_00627ba0(local_70,DAT_004e7e90);
        iVar4 = local_70[0];
        iVar3 = *(int *)(iVar2 + iVar6 * 8);
        FUN_006280c8(local_70);
        if (iVar3 == iVar4) {
          iVar6 = *(int *)(iVar2 + iVar6 * 8 + 4);
          goto LAB_004e7a60;
        }
        iVar6 = iVar6 + 1;
      } while (iVar6 < param_5[2]);
      iVar6 = 0;
    }
LAB_004e7a60:
    FUN_00666e84(auStack_40,DAT_004e7ebc);
    pvVar1 = operator_new(200);
    FUN_0049d7f0(pvVar1,param_3,auStack_40,uVar8,iVar6,param_4);
    param_1[0x29] = pvVar1;
    FUN_006280c8(auStack_40);
    iVar6 = param_1[0x29];
    break;
  case 2:
    if (((*DAT_004e7f50 & 1) == 0) && (iVar6 = __cxa_guard_acquire(), iVar6 != 0)) {
      FUN_00666e84(DAT_004e7ec0,DAT_004e7ed8);
      __cxa_guard_release(DAT_004e7f50);
      __aeabi_atexit(DAT_004e7ec0,DAT_004e7ecc,DAT_004e7ed0);
    }
    if (0 < param_5[2]) {
      iVar6 = 0;
      do {
        iVar2 = *param_5;
        FUN_00627ba0(local_68,DAT_004e7ec0);
        iVar4 = local_68[0];
        iVar3 = *(int *)(iVar2 + iVar6 * 8);
        FUN_006280c8(local_68);
        if (iVar3 == iVar4) {
          uVar8 = *(undefined4 *)(iVar2 + iVar6 * 8 + 4);
          goto LAB_004e7ae8;
        }
        iVar6 = iVar6 + 1;
      } while (iVar6 < param_5[2]);
    }
    uVar8 = 0;
LAB_004e7ae8:
    if (((*DAT_004e7f54 & 1) == 0) && (iVar6 = __cxa_guard_acquire(), iVar6 != 0)) {
      FUN_00666e84(DAT_004e7e90,DAT_004e7ed4);
      __cxa_guard_release(DAT_004e7f54);
      __aeabi_atexit(DAT_004e7e90,DAT_004e7ecc,DAT_004e7ed0);
    }
    iVar6 = 0;
    if (0 < param_5[2]) {
      do {
        iVar2 = *param_5;
        FUN_00627ba0(local_60,DAT_004e7e90);
        iVar4 = local_60[0];
        iVar3 = *(int *)(iVar2 + iVar6 * 8);
        FUN_006280c8(local_60);
        if (iVar3 == iVar4) {
          iVar6 = *(int *)(iVar2 + iVar6 * 8 + 4);
          goto LAB_004e7b5c;
        }
        iVar6 = iVar6 + 1;
      } while (iVar6 < param_5[2]);
      iVar6 = 0;
    }
LAB_004e7b5c:
    FUN_00666e84(auStack_3c,DAT_004e7ec4);
    pvVar1 = operator_new(0xe0);
    FUN_0049ea88(pvVar1,param_3,auStack_3c,uVar8,iVar6,param_4);
    param_1[0x27] = pvVar1;
    FUN_006280c8(auStack_3c);
    iVar6 = param_1[0x27];
    break;
  case 3:
    if (((*DAT_004e7f58 & 1) == 0) && (iVar6 = __cxa_guard_acquire(), iVar6 != 0)) {
      FUN_00666e84(DAT_004e7e8c,DAT_004e7edc);
      __cxa_guard_release(DAT_004e7f58);
      __aeabi_atexit(DAT_004e7e8c,DAT_004e7ecc,DAT_004e7ed0);
    }
    if (0 < param_5[2]) {
      iVar6 = 0;
      do {
        iVar2 = *param_5;
        FUN_00627ba0(local_58,DAT_004e7e8c);
        iVar4 = local_58[0];
        iVar3 = *(int *)(iVar2 + iVar6 * 8);
        FUN_006280c8(local_58);
        if (iVar3 == iVar4) {
          uVar8 = *(undefined4 *)(iVar2 + iVar6 * 8 + 4);
          goto LAB_004e7154;
        }
        iVar6 = iVar6 + 1;
      } while (iVar6 < param_5[2]);
    }
    uVar8 = 0;
LAB_004e7154:
    if (((*DAT_004e7f54 & 1) == 0) && (iVar6 = __cxa_guard_acquire(), iVar6 != 0)) {
      FUN_00666e84(DAT_004e7e90,DAT_004e7ed4);
      __cxa_guard_release(DAT_004e7f54);
      __aeabi_atexit(DAT_004e7e90,DAT_004e7ecc,DAT_004e7ed0);
    }
    iVar6 = 0;
    if (0 < param_5[2]) {
      do {
        iVar2 = *param_5;
        FUN_00627ba0(&local_50,DAT_004e7e90);
        iVar4 = local_50;
        iVar3 = *(int *)(iVar2 + iVar6 * 8);
        FUN_006280c8(&local_50);
        if (iVar3 == iVar4) {
          iVar6 = *(int *)(iVar2 + iVar6 * 8 + 4);
          goto LAB_004e71c8;
        }
        iVar6 = iVar6 + 1;
      } while (iVar6 < param_5[2]);
      iVar6 = 0;
    }
LAB_004e71c8:
    FUN_00666e84(auStack_38,DAT_004e7e94);
    pvVar1 = operator_new(0xf4);
    FUN_00495fe4(pvVar1,param_3,auStack_38,uVar8,iVar6,param_4);
    param_1[0x28] = pvVar1;
    FUN_006280c8(auStack_38);
    iVar6 = param_1[0x28];
    break;
  default:
    goto switchD_004e70f4_default;
  }
  param_1[0x26] = *(undefined4 *)(iVar6 + 0xc0);
  FUN_007ccc24(param_1,iVar6,0xffffffff);
switchD_004e70f4_default:
  FUN_00627ba0(local_1f0,DAT_004e7e98);
  iVar6 = *param_4;
  FUN_006280c8(local_1f0);
  if (iVar6 == local_1f0[0]) {
    pvVar1 = operator_new(0xc4);
    FUN_004a4c54(pvVar1,param_3,DAT_004e7e98);
    param_1[0x2a] = pvVar1;
    FUN_007ccc24(param_1,pvVar1,0xffffffff);
  }
  else {
    FUN_00627ba0(local_1e8,DAT_004e7ee0);
    iVar6 = *param_4;
    FUN_006280c8(local_1e8);
    if (iVar6 == local_1e8[0]) {
      pvVar1 = operator_new(0xc4);
      FUN_004a4c54(pvVar1,param_3,DAT_004e7ee0);
      param_1[0x2b] = pvVar1;
      FUN_007ccc24(param_1,pvVar1,0xffffffff);
    }
    else {
      FUN_00627ba0(local_1e0,DAT_004e7ee4);
      iVar6 = *param_4;
      FUN_006280c8(local_1e0);
      if (iVar6 == local_1e0[0]) {
        pvVar1 = operator_new(0xc4);
        FUN_004a4c54(pvVar1,param_3,DAT_004e7ee4);
        param_1[0x2c] = pvVar1;
        FUN_007ccc24(param_1,pvVar1,0xffffffff);
      }
      else {
        FUN_00627ba0(local_1d8,DAT_004e7e9c);
        iVar6 = *param_4;
        FUN_006280c8(local_1d8);
        if (iVar6 == local_1d8[0]) {
          pvVar1 = operator_new(0xc4);
          FUN_004a4c54(pvVar1,param_3,DAT_004e7e9c);
          param_1[0x2d] = pvVar1;
          FUN_007ccc24(param_1,pvVar1,0xffffffff);
        }
        else {
          FUN_00627ba0(local_1d0,DAT_004e7ea0);
          iVar6 = *param_4;
          FUN_006280c8(local_1d0);
          if (iVar6 == local_1d0[0]) {
            pvVar1 = operator_new(0xc4);
            FUN_004a4c54(pvVar1,param_3,DAT_004e7ea0);
            param_1[0x2e] = pvVar1;
            FUN_007ccc24(param_1,pvVar1,0xffffffff);
          }
          else {
            FUN_00627ba0(local_1c8,DAT_004e7ea4);
            iVar6 = *param_4;
            FUN_006280c8(local_1c8);
            if (iVar6 == local_1c8[0]) {
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7ee0);
              param_1[0x2b] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7ee4);
              param_1[0x2c] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7efc);
              param_1[0x33] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f04);
              param_1[0x35] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f0c);
              param_1[0x36] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f1c);
              param_1[0x3a] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f24);
              param_1[0x3b] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f30);
              param_1[0x3d] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f14);
              param_1[0x38] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7eec);
              param_1[0x31] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f40);
              param_1[0x46] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f88);
              param_1[0x49] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f78);
              param_1[0x4a] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f38);
              param_1[0x41] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f74);
              param_1[0x4b] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f70);
              param_1[0x4c] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f44);
              param_1[0x43] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              pvVar1 = operator_new(0xc4);
              FUN_004a4c54(pvVar1,param_3,DAT_004e7f48);
              param_1[0x44] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              FUN_00666e84(auStack_34,DAT_004e7ef4);
              pvVar1 = operator_new(0xc4);
              FUN_004a54d0(pvVar1,param_3,auStack_34);
              param_1[0x55] = pvVar1;
              FUN_007ccc24(param_1,pvVar1,0xffffffff);
              FUN_006280c8(auStack_34);
            }
            else {
              FUN_00627ba0(local_1c0,DAT_004e7ee8);
              iVar6 = *param_4;
              FUN_006280c8(local_1c0);
              if (iVar6 == local_1c0[0]) {
                pvVar1 = operator_new(0xc4);
                FUN_004a4c54(pvVar1,param_3,DAT_004e7ee8);
                param_1[0x2f] = pvVar1;
                FUN_007ccc24(param_1,pvVar1,0xffffffff);
              }
              else {
                FUN_00627ba0(local_1b8,DAT_004e7ea8);
                iVar6 = *param_4;
                FUN_006280c8(local_1b8);
                if (iVar6 == local_1b8[0]) {
                  FUN_00666e84(auStack_30,DAT_004e7ef4);
                  pvVar1 = operator_new(0xc4);
                  FUN_004a54d0(pvVar1,param_3,auStack_30);
                  param_1[0x55] = pvVar1;
                  FUN_007ccc24(param_1,pvVar1,0xffffffff);
                  FUN_006280c8(auStack_30);
                }
                else {
                  FUN_00627ba0(local_1b0,DAT_004e7eac);
                  iVar6 = *param_4;
                  FUN_006280c8(local_1b0);
                  if (iVar6 == local_1b0[0]) {
                    FUN_00666e84(auStack_2c,DAT_004e7ef4);
                    pvVar1 = operator_new(0xc4);
                    FUN_004a54d0(pvVar1,param_3,auStack_2c);
                    param_1[0x55] = pvVar1;
                    FUN_007ccc24(param_1,pvVar1,0xffffffff);
                    FUN_006280c8(auStack_2c);
                  }
                  else {
                    FUN_00627ba0(local_1a8,DAT_004e7eec);
                    iVar6 = *param_4;
                    FUN_006280c8(local_1a8);
                    if (iVar6 == local_1a8[0]) {
                      pvVar1 = operator_new(0xc4);
                      FUN_004a4c54(pvVar1,param_3,DAT_004e7eec);
                      param_1[0x31] = pvVar1;
                      FUN_007ccc24(param_1,pvVar1,0xffffffff);
                    }
                    else {
                      FUN_00627ba0(local_1a0,DAT_004e7ef8);
                      iVar6 = *param_4;
                      FUN_006280c8(local_1a0);
                      if (iVar6 == local_1a0[0]) {
                        pvVar1 = operator_new(0xc4);
                        FUN_004a4c54(pvVar1,param_3,DAT_004e7ef8);
                        param_1[0x30] = pvVar1;
                        FUN_007ccc24(param_1,pvVar1,0xffffffff);
                      }
                      else {
                        FUN_00627ba0(local_198,DAT_004e7efc);
                        iVar6 = *param_4;
                        FUN_006280c8(local_198);
                        if (iVar6 == local_198[0]) {
                          pvVar1 = operator_new(0xc4);
                          FUN_004a4c54(pvVar1,param_3,DAT_004e7efc);
                          param_1[0x33] = pvVar1;
                          FUN_007ccc24(param_1,pvVar1,0xffffffff);
                        }
                        else {
                          FUN_00627ba0(local_190,DAT_004e7f00);
                          iVar6 = *param_4;
                          FUN_006280c8(local_190);
                          if (iVar6 == local_190[0]) {
                            pvVar1 = operator_new(0xc4);
                            FUN_004a4c54(pvVar1,param_3,DAT_004e7f00);
                            param_1[0x32] = pvVar1;
                            FUN_007ccc24(param_1,pvVar1,0xffffffff);
                          }
                          else {
                            FUN_00627ba0(local_188,DAT_004e7f04);
                            iVar6 = *param_4;
                            FUN_006280c8(local_188);
                            if (iVar6 == local_188[0]) {
                              pvVar1 = operator_new(0xc4);
                              FUN_004a4c54(pvVar1,param_3,DAT_004e7f04);
                              param_1[0x35] = pvVar1;
                              FUN_007ccc24(param_1,pvVar1,0xffffffff);
                            }
                            else {
                              FUN_00627ba0(local_180,DAT_004e7f08);
                              iVar6 = *param_4;
                              FUN_006280c8(local_180);
                              if (iVar6 == local_180[0]) {
                                pvVar1 = operator_new(0xc4);
                                FUN_004a4c54(pvVar1,param_3,DAT_004e7f08);
                                param_1[0x34] = pvVar1;
                                FUN_007ccc24(param_1,pvVar1,0xffffffff);
                              }
                              else {
                                FUN_00627ba0(local_178,DAT_004e7f0c);
                                iVar6 = *param_4;
                                FUN_006280c8(local_178);
                                if (iVar6 == local_178[0]) {
                                  pvVar1 = operator_new(0xc4);
                                  FUN_004a4c54(pvVar1,param_3,DAT_004e7f0c);
                                  param_1[0x36] = pvVar1;
                                  FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                }
                                else {
                                  FUN_00627ba0(local_170,DAT_004e7f10);
                                  iVar6 = *param_4;
                                  FUN_006280c8(local_170);
                                  if (iVar6 == local_170[0]) {
                                    pvVar1 = operator_new(0xc4);
                                    FUN_004a4c54(pvVar1,param_3,DAT_004e7f10);
                                    param_1[0x37] = pvVar1;
                                    FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                  }
                                  else {
                                    FUN_00627ba0(local_168,DAT_004e7f14);
                                    iVar6 = *param_4;
                                    FUN_006280c8(local_168);
                                    if (iVar6 == local_168[0]) {
                                      pvVar1 = operator_new(0xc4);
                                      FUN_004a4c54(pvVar1,param_3,DAT_004e7f14);
                                      param_1[0x38] = pvVar1;
                                      FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                    }
                                    else {
                                      FUN_00627ba0(local_160,DAT_004e7ef0);
                                      iVar6 = *param_4;
                                      FUN_006280c8(local_160);
                                      if (iVar6 == local_160[0]) {
                                        pvVar1 = operator_new(0xc4);
                                        FUN_004a4c54(pvVar1,param_3,DAT_004e7ef0);
                                        param_1[0x39] = pvVar1;
                                        FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                      }
                                      else {
                                        FUN_00627ba0(local_158,DAT_004e7f1c);
                                        iVar6 = *param_4;
                                        FUN_006280c8(local_158);
                                        if (iVar6 == local_158[0]) {
                                          pvVar1 = operator_new(0xc4);
                                          FUN_004a4c54(pvVar1,param_3,DAT_004e7f1c);
                                          param_1[0x3a] = pvVar1;
                                          FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                        }
                                        else {
                                          FUN_00627ba0(local_150,DAT_004e7f18);
                                          iVar6 = *param_4;
                                          FUN_006280c8(local_150);
                                          if (iVar6 == local_150[0]) {
                                            pvVar1 = operator_new(0xc4);
                                            FUN_004a4c54(pvVar1,param_3,DAT_004e7f18);
                                            param_1[0x3c] = pvVar1;
                                            FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                          }
                                          else {
                                            FUN_00627ba0(local_148,DAT_004e7f24);
                                            iVar6 = *param_4;
                                            FUN_006280c8(local_148);
                                            if (iVar6 == local_148[0]) {
                                              pvVar1 = operator_new(0xc4);
                                              FUN_004a4c54(pvVar1,param_3,DAT_004e7f24);
                                              param_1[0x3b] = pvVar1;
                                              FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                            }
                                            else {
                                              FUN_00627ba0(local_140,DAT_004e7f20);
                                              iVar6 = *param_4;
                                              FUN_006280c8(local_140);
                                              if (iVar6 == local_140[0]) {
                                                pvVar1 = operator_new(0xc4);
                                                FUN_004a4c54(pvVar1,param_3,DAT_004e7f20);
                                                param_1[0x3e] = pvVar1;
                                                FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                              }
                                              else {
                                                FUN_00627ba0(local_138,DAT_004e7f30);
                                                iVar6 = *param_4;
                                                FUN_006280c8(local_138);
                                                if (iVar6 == local_138[0]) {
                                                  pvVar1 = operator_new(0xc4);
                                                  FUN_004a4c54(pvVar1,param_3,DAT_004e7f30);
                                                  param_1[0x3d] = pvVar1;
                                                  FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                }
                                                else {
                                                  FUN_00627ba0(local_130,DAT_004e7f2c);
                                                  iVar6 = *param_4;
                                                  FUN_006280c8(local_130);
                                                  if (iVar6 == local_130[0]) {
                                                    pvVar1 = operator_new(0xc4);
                                                    FUN_004a4c54(pvVar1,param_3,DAT_004e7f2c);
                                                    param_1[0x3f] = pvVar1;
                                                    FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                  }
                                                  else {
                                                    FUN_00627ba0(local_128,DAT_004e7f28);
                                                    iVar6 = *param_4;
                                                    FUN_006280c8(local_128);
                                                    if (iVar6 == local_128[0]) {
                                                      pvVar1 = operator_new(0xc4);
                                                      FUN_004a4c54(pvVar1,param_3,DAT_004e7f28);
                                                      param_1[0x40] = pvVar1;
                                                      FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                    }
                                                    else {
                                                      FUN_00627ba0(local_120,DAT_004e7f38);
                                                      iVar6 = *param_4;
                                                      FUN_006280c8(local_120);
                                                      if (iVar6 == local_120[0]) {
                                                        pvVar1 = operator_new(0xc4);
                                                        FUN_004a4c54(pvVar1,param_3,DAT_004e7f38);
                                                        param_1[0x41] = pvVar1;
                                                        FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                      }
                                                      else {
                                                        FUN_00627ba0(local_118,DAT_004e7f4c);
                                                        iVar6 = *param_4;
                                                        FUN_006280c8(local_118);
                                                        if (iVar6 == local_118[0]) {
                                                          pvVar1 = operator_new(0xc4);
                                                          FUN_004a4c54(pvVar1,param_3,DAT_004e7f4c);
                                                          param_1[0x42] = pvVar1;
                                                          FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                        }
                                                        else {
                                                          FUN_00627ba0(local_110,DAT_004e7f44);
                                                          iVar6 = *param_4;
                                                          FUN_006280c8(local_110);
                                                          if (iVar6 == local_110[0]) {
                                                            pvVar1 = operator_new(0xc4);
                                                            FUN_004a4c54(pvVar1,param_3,DAT_004e7f44
                                                                        );
                                                            param_1[0x43] = pvVar1;
                                                            FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                          }
                                                          else {
                                                            FUN_00627ba0(local_108,DAT_004e7f48);
                                                            iVar6 = *param_4;
                                                            FUN_006280c8(local_108);
                                                            if (iVar6 == local_108[0]) {
                                                              pvVar1 = operator_new(0xc4);
                                                              FUN_004a4c54(pvVar1,param_3,
                                                                           DAT_004e7f48);
                                                              param_1[0x44] = pvVar1;
                                                              FUN_007ccc24(param_1,pvVar1,0xffffffff
                                                                          );
                                                            }
                                                            else {
                                                              FUN_00627ba0(local_100,DAT_004e7f3c);
                                                              iVar6 = *param_4;
                                                              FUN_006280c8(local_100);
                                                              if (iVar6 == local_100[0]) {
                                                                pvVar1 = operator_new(0xc4);
                                                                FUN_004a4c54(pvVar1,param_3,
                                                                             DAT_004e7f3c);
                                                                param_1[0x45] = pvVar1;
                                                                FUN_007ccc24(param_1,pvVar1,
                                                                             0xffffffff);
                                                              }
                                                              else {
                                                                FUN_00627ba0(local_f8,DAT_004e7f40);
                                                                iVar6 = *param_4;
                                                                FUN_006280c8(local_f8);
                                                                if (iVar6 == local_f8[0]) {
                                                                  pvVar1 = operator_new(0xc4);
                                                                  FUN_004a4c54(pvVar1,param_3,
                                                                               DAT_004e7f40);
                                                                  param_1[0x46] = pvVar1;
                                                                  FUN_007ccc24(param_1,pvVar1,
                                                                               0xffffffff);
                                                                }
                                                                else {
                                                                  FUN_00627ba0(local_f0,DAT_004e7f34
                                                                              );
                                                                  iVar6 = *param_4;
                                                                  FUN_006280c8(local_f0);
                                                                  if (iVar6 == local_f0[0]) {
                                                                    pvVar1 = operator_new(0xc4);
                                                                    FUN_004a4c54(pvVar1,param_3,
                                                                                 DAT_004e7f34);
                                                                    param_1[0x47] = pvVar1;
                                                                    FUN_007ccc24(param_1,pvVar1,
                                                                                 0xffffffff);
                                                                  }
                                                                  else {
                                                                    FUN_00627ba0(local_e8,
                                                  DAT_004e7f8c);
                                                  iVar6 = *param_4;
                                                  FUN_006280c8(local_e8);
                                                  if (iVar6 == local_e8[0]) {
                                                    pvVar1 = operator_new(0xc4);
                                                    FUN_004a4c54(pvVar1,param_3,DAT_004e7f8c);
                                                    param_1[0x48] = pvVar1;
                                                    FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                  }
                                                  else {
                                                    FUN_00627ba0(local_e0,DAT_004e7f88);
                                                    iVar6 = *param_4;
                                                    FUN_006280c8(local_e0);
                                                    if (iVar6 == local_e0[0]) {
                                                      pvVar1 = operator_new(0xc4);
                                                      FUN_004a4c54(pvVar1,param_3,DAT_004e7f88);
                                                      param_1[0x49] = pvVar1;
                                                      FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                    }
                                                    else {
                                                      FUN_00627ba0(local_d8,DAT_004e7f78);
                                                      iVar6 = *param_4;
                                                      FUN_006280c8(local_d8);
                                                      if (iVar6 == local_d8[0]) {
                                                        pvVar1 = operator_new(0xc4);
                                                        FUN_004a4c54(pvVar1,param_3,DAT_004e7f78);
                                                        param_1[0x4a] = pvVar1;
                                                        FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                      }
                                                      else {
                                                        FUN_00627ba0(local_d0,DAT_004e7f74);
                                                        iVar6 = *param_4;
                                                        FUN_006280c8(local_d0);
                                                        if (iVar6 == local_d0[0]) {
                                                          pvVar1 = operator_new(0xc4);
                                                          FUN_004a4c54(pvVar1,param_3,DAT_004e7f74);
                                                          param_1[0x4b] = pvVar1;
                                                          FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                        }
                                                        else {
                                                          FUN_00627ba0(local_c8,DAT_004e7f70);
                                                          iVar6 = *param_4;
                                                          FUN_006280c8(local_c8);
                                                          if (iVar6 == local_c8[0]) {
                                                            pvVar1 = operator_new(0xc4);
                                                            FUN_004a4c54(pvVar1,param_3,DAT_004e7f70
                                                                        );
                                                            param_1[0x4c] = pvVar1;
                                                            FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                          }
                                                          else {
                                                            FUN_00627ba0(local_c0,DAT_004e7f6c);
                                                            iVar6 = *param_4;
                                                            FUN_006280c8(local_c0);
                                                            if (iVar6 == local_c0[0]) {
                                                              pvVar1 = operator_new(0xc4);
                                                              FUN_004a4c54(pvVar1,param_3,
                                                                           DAT_004e7f6c);
                                                              param_1[0x4d] = pvVar1;
                                                              FUN_007ccc24(param_1,pvVar1,0xffffffff
                                                                          );
                                                            }
                                                            else {
                                                              FUN_00627ba0(local_b8,DAT_004e7f68);
                                                              iVar6 = *param_4;
                                                              FUN_006280c8(local_b8);
                                                              if (iVar6 == local_b8[0]) {
                                                                pvVar1 = operator_new(0xc4);
                                                                FUN_004a4c54(pvVar1,param_3,
                                                                             DAT_004e7f68);
                                                                param_1[0x4e] = pvVar1;
                                                                FUN_007ccc24(param_1,pvVar1,
                                                                             0xffffffff);
                                                              }
                                                              else {
                                                                FUN_00627ba0(local_b0,DAT_004e7f64);
                                                                iVar6 = *param_4;
                                                                FUN_006280c8(local_b0);
                                                                if (iVar6 == local_b0[0]) {
                                                                  pvVar1 = operator_new(0xc4);
                                                                  FUN_004a4c54(pvVar1,param_3,
                                                                               DAT_004e7f64);
                                                                  param_1[0x4f] = pvVar1;
                                                                  FUN_007ccc24(param_1,pvVar1,
                                                                               0xffffffff);
                                                                }
                                                                else {
                                                                  FUN_00627ba0(local_a8,DAT_004e7f60
                                                                              );
                                                                  iVar6 = *param_4;
                                                                  FUN_006280c8(local_a8);
                                                                  if (iVar6 == local_a8[0]) {
                                                                    pvVar1 = operator_new(0xc4);
                                                                    FUN_004a4c54(pvVar1,param_3,
                                                                                 DAT_004e7f60);
                                                                    param_1[0x50] = pvVar1;
                                                                    FUN_007ccc24(param_1,pvVar1,
                                                                                 0xffffffff);
                                                                  }
                                                                  else {
                                                                    FUN_00627ba0(local_a0,
                                                  DAT_004e7f5c);
                                                  iVar6 = *param_4;
                                                  FUN_006280c8(local_a0);
                                                  if (iVar6 == local_a0[0]) {
                                                    pvVar1 = operator_new(0xc4);
                                                    FUN_004a4c54(pvVar1,param_3,DAT_004e7f5c);
                                                    param_1[0x51] = pvVar1;
                                                    FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                  }
                                                  else {
                                                    FUN_00627ba0(local_98,DAT_004e7f80);
                                                    iVar6 = *param_4;
                                                    FUN_006280c8(local_98);
                                                    if (iVar6 == local_98[0]) {
                                                      pvVar1 = operator_new(0xc4);
                                                      FUN_004a4c54(pvVar1,param_3,DAT_004e7f80);
                                                      param_1[0x52] = pvVar1;
                                                      FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                    }
                                                    else {
                                                      FUN_00627ba0(local_90,DAT_004e7f7c);
                                                      iVar6 = *param_4;
                                                      FUN_006280c8(local_90);
                                                      if (iVar6 == local_90[0]) {
                                                        pvVar1 = operator_new(0xc4);
                                                        FUN_004a4c54(pvVar1,param_3,DAT_004e7f7c);
                                                        param_1[0x53] = pvVar1;
                                                        FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                      }
                                                      else {
                                                        FUN_00627ba0(local_88,DAT_004e7eb0);
                                                        iVar6 = *param_4;
                                                        FUN_006280c8(local_88);
                                                        if (iVar6 == local_88[0]) {
                                                          pvVar1 = operator_new(0xc4);
                                                          FUN_004a4c54(pvVar1,param_3,DAT_004e7eb0);
                                                          param_1[0x54] = pvVar1;
                                                          FUN_007ccc24(param_1,pvVar1,0xffffffff);
                                                        }
                                                      }
                                                    }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                  }
                                                }
                                              }
                                            }
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  return param_1;
}

