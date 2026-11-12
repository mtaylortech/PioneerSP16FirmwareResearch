/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0031f790(int param_1,int param_2,undefined4 param_3,undefined4 *param_4,undefined4 *param_5
                 )

{
  bool bVar1;
  void *pvVar2;
  int iVar3;
  void *pvVar4;
  void *pvVar5;
  void *pvVar6;
  void *pvVar7;
  int *piVar8;
  int *piVar9;
  int iVar10;
  int iVar11;
  uint uVar12;
  undefined1 auStack_68 [4];
  void *local_64;
  undefined1 auStack_60 [4];
  void *local_5c;
  undefined1 auStack_58 [4];
  void *local_54;
  undefined1 auStack_50 [4];
  void *local_4c;
  undefined1 auStack_48 [4];
  void *local_44;
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [8];
  
  param_2 = param_2 + 0x88;
  pvVar2 = operator_new(0x5c);
  FUN_002ead0c(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  iVar11 = param_1 + 0x2c;
  FUN_0032a908(iVar11,pvVar2);
  if (((*DAT_00320794 & 1) == 0) && (iVar3 = __cxa_guard_acquire(), iVar3 != 0)) {
    FUN_00666e84(DAT_00320798,DAT_003207dc);
    __cxa_guard_release(DAT_00320794);
    __aeabi_atexit(DAT_00320798,DAT_003207c4,DAT_003207c8);
  }
  FUN_00627ba0(auStack_68,DAT_00320798);
  iVar3 = param_4[2];
  iVar10 = iVar3 + 1;
  local_64 = pvVar2;
  if (((int)param_4[1] < iVar10) &&
     (uVar12 = iVar10 + iVar10 / 2 + 8U & 0xfffffff8, param_4[1] != uVar12)) {
    pvVar4 = (void *)*param_4;
    if ((int)uVar12 < 1) {
      free(pvVar4);
      iVar3 = param_4[2];
      pvVar4 = (void *)0x0;
      param_4[1] = uVar12;
      *param_4 = 0;
      iVar10 = iVar3 + 1;
    }
    else {
      if (pvVar4 == (void *)0x0) {
        pvVar4 = malloc(uVar12 << 3);
        *param_4 = pvVar4;
      }
      else {
        pvVar4 = realloc(pvVar4,uVar12 << 3);
        iVar3 = param_4[2];
        iVar10 = iVar3 + 1;
        *param_4 = pvVar4;
      }
      param_4[1] = uVar12;
    }
  }
  else {
    pvVar4 = (void *)*param_4;
  }
  pvVar4 = (void *)((int)pvVar4 + iVar3 * 8);
  param_4[2] = iVar10;
  if (pvVar4 != (void *)0x0) {
    FUN_00627ba0(pvVar4,auStack_68);
    *(void **)((int)pvVar4 + 4) = local_64;
  }
  FUN_006280c8(auStack_68);
  *param_5 = pvVar2;
  pvVar2 = operator_new(0x74);
  FUN_002d26f0(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  if (((*DAT_003207f4 & 1) == 0) && (iVar3 = __cxa_guard_acquire(), iVar3 != 0)) {
    FUN_00666e84(DAT_0032079c,DAT_003207d8);
    __cxa_guard_release(DAT_003207f4);
    __aeabi_atexit(DAT_0032079c,DAT_003207c4,DAT_003207c8);
  }
  FUN_00627ba0(auStack_60,DAT_0032079c);
  iVar3 = param_4[2];
  iVar10 = iVar3 + 1;
  local_5c = pvVar2;
  if (((int)param_4[1] < iVar10) &&
     (uVar12 = iVar10 + iVar10 / 2 + 8U & 0xfffffff8, param_4[1] != uVar12)) {
    pvVar4 = (void *)*param_4;
    if ((int)uVar12 < 1) {
      free(pvVar4);
      iVar3 = param_4[2];
      pvVar4 = (void *)0x0;
      param_4[1] = uVar12;
      *param_4 = 0;
      iVar10 = iVar3 + 1;
    }
    else {
      if (pvVar4 == (void *)0x0) {
        pvVar4 = malloc(uVar12 << 3);
        *param_4 = pvVar4;
      }
      else {
        pvVar4 = realloc(pvVar4,uVar12 << 3);
        iVar3 = param_4[2];
        iVar10 = iVar3 + 1;
        *param_4 = pvVar4;
      }
      param_4[1] = uVar12;
    }
  }
  else {
    pvVar4 = (void *)*param_4;
  }
  pvVar4 = (void *)((int)pvVar4 + iVar3 * 8);
  param_4[2] = iVar10;
  if (pvVar4 != (void *)0x0) {
    FUN_00627ba0(pvVar4,auStack_60);
    *(void **)((int)pvVar4 + 4) = local_5c;
  }
  FUN_006280c8(auStack_60);
  param_5[1] = pvVar2;
  pvVar4 = operator_new(0x50);
  FUN_001f893c(pvVar4,param_2);
  if (((*DAT_00320804 & 1) == 0) && (iVar3 = __cxa_guard_acquire(), iVar3 != 0)) {
    FUN_00666e84(DAT_003207a0,DAT_003207d0);
    __cxa_guard_release(DAT_00320804);
    __aeabi_atexit(DAT_003207a0,DAT_003207c4,DAT_003207c8);
  }
  FUN_00627ba0(auStack_40,DAT_003207a0);
  pvVar5 = operator_new(0x124);
  FUN_003ccafc(pvVar5,param_3,pvVar4,auStack_40);
  FUN_001f82f4(pvVar4,pvVar5);
  FUN_0032a908(iVar11,pvVar4);
  FUN_006280c8(auStack_40);
  pvVar5 = operator_new(0x50);
  FUN_001f893c(pvVar5,param_2);
  if (((*DAT_003207fc & 1) == 0) && (iVar3 = __cxa_guard_acquire(), iVar3 != 0)) {
    FUN_00666e84(DAT_003207a4,DAT_003207c0);
    __cxa_guard_release(DAT_003207fc);
    __aeabi_atexit(DAT_003207a4,DAT_003207c4,DAT_003207c8);
  }
  FUN_00627ba0(auStack_3c,DAT_003207a4);
  pvVar6 = operator_new(0x124);
  FUN_003ccafc(pvVar6,param_3,pvVar5,auStack_3c);
  FUN_001f82f4(pvVar5,pvVar6);
  FUN_0032a908(iVar11,pvVar5);
  FUN_006280c8(auStack_3c);
  pvVar6 = operator_new(0x50);
  FUN_001f893c(pvVar6,param_2);
  if (((DAT_00f543c0 & 1) == 0) && (iVar3 = __cxa_guard_acquire(DAT_00320800), iVar3 != 0)) {
    FUN_00666e84(DAT_003207a8,DAT_003207cc);
    __cxa_guard_release(DAT_00320800);
    __aeabi_atexit(DAT_003207a8,DAT_003207c4,DAT_003207c8);
  }
  FUN_00627ba0(auStack_38,DAT_003207a8);
  pvVar7 = operator_new(0x124);
  FUN_003ccafc(pvVar7,param_3,pvVar6,auStack_38);
  FUN_001f82f4(pvVar6,pvVar7);
  FUN_0032a908(iVar11,pvVar6);
  FUN_006280c8(auStack_38);
  FUN_002d3ad0(pvVar2,pvVar4,pvVar5,pvVar6);
  pvVar4 = operator_new(100);
  FUN_001eca30(pvVar4,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_00666e84(auStack_34,DAT_003207ac);
  piVar8 = operator_new(0x21c);
  FUN_003b60ec(piVar8,param_3,pvVar4,auStack_34);
  piVar9 = *(int **)((int)pvVar4 + 0x50);
  if (piVar8 != piVar9) {
    if (piVar8 != (int *)0x0) {
      piVar9 = piVar8 + 0x1d;
      DataMemoryBarrier(0xf);
      do {
        bVar1 = (bool)hasExclusiveAccess(piVar9);
      } while (!bVar1);
      *piVar9 = *piVar9 + 1;
      DataMemoryBarrier(0xf);
      piVar9 = *(int **)((int)pvVar4 + 0x50);
    }
    *(int **)((int)pvVar4 + 0x50) = piVar8;
    if (piVar9 != (int *)0x0) {
      piVar8 = piVar9 + 0x1d;
      DataMemoryBarrier(0xf);
      do {
        iVar3 = *piVar8;
        bVar1 = (bool)hasExclusiveAccess(piVar8);
      } while (!bVar1);
      *piVar8 = iVar3 + -1;
      DataMemoryBarrier(0xf);
      if (iVar3 + -1 == 0) {
        (**(code **)(*piVar9 + 4))();
      }
    }
  }
  FUN_0032a908(iVar11,pvVar4);
  FUN_006280c8(auStack_34);
  FUN_002d3e1c(pvVar2,pvVar4);
  pvVar2 = operator_new(0x68);
  FUN_002d605c(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  if (((*DAT_003207f0 & 1) == 0) && (iVar3 = __cxa_guard_acquire(), iVar3 != 0)) {
    FUN_00666e84(DAT_003207b0,DAT_003207e4);
    __cxa_guard_release(DAT_003207f0);
    __aeabi_atexit(DAT_003207b0,DAT_003207c4,DAT_003207c8);
  }
  FUN_00627ba0(auStack_58,DAT_003207b0);
  iVar10 = param_4[2];
  iVar3 = iVar10 + 1;
  local_54 = pvVar2;
  if (((int)param_4[1] < iVar3) &&
     (uVar12 = iVar3 + iVar3 / 2 + 8U & 0xfffffff8, param_4[1] != uVar12)) {
    pvVar4 = (void *)*param_4;
    if ((int)uVar12 < 1) {
      free(pvVar4);
      pvVar4 = (void *)0x0;
      iVar10 = param_4[2];
      *param_4 = 0;
      iVar3 = iVar10 + 1;
      param_4[1] = uVar12;
    }
    else {
      if (pvVar4 == (void *)0x0) {
        pvVar4 = malloc(uVar12 << 3);
        *param_4 = pvVar4;
      }
      else {
        pvVar4 = realloc(pvVar4,uVar12 << 3);
        iVar10 = param_4[2];
        iVar3 = iVar10 + 1;
        *param_4 = pvVar4;
      }
      param_4[1] = uVar12;
    }
  }
  else {
    pvVar4 = (void *)*param_4;
  }
  pvVar4 = (void *)((int)pvVar4 + iVar10 * 8);
  param_4[2] = iVar3;
  if (pvVar4 != (void *)0x0) {
    FUN_00627ba0(pvVar4,auStack_58);
    *(void **)((int)pvVar4 + 4) = local_54;
  }
  FUN_006280c8(auStack_58);
  param_5[2] = pvVar2;
  pvVar4 = operator_new(0x3c);
  FUN_001fac24(pvVar4,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_00666e84(auStack_30,DAT_003207b4);
  FUN_0031d798(param_1,param_3,pvVar4,auStack_30);
  FUN_006280c8(auStack_30);
  FUN_002d6550(pvVar2,pvVar4);
  pvVar4 = operator_new(0x50);
  FUN_001f893c(pvVar4,param_2);
  if (((DAT_00f543c0 & 1) == 0) && (iVar3 = __cxa_guard_acquire(DAT_00320800), iVar3 != 0)) {
    FUN_00666e84(DAT_003207a8,DAT_003207cc);
    __cxa_guard_release(DAT_00320800);
    __aeabi_atexit(DAT_003207a8,DAT_003207c4,DAT_003207c8);
  }
  FUN_00627ba0(auStack_2c,DAT_003207a8);
  pvVar5 = operator_new(0x124);
  FUN_003ccafc(pvVar5,param_3,pvVar4,auStack_2c);
  FUN_001f82f4(pvVar4,pvVar5);
  FUN_0032a908(iVar11,pvVar4);
  FUN_006280c8(auStack_2c);
  FUN_002d6738(pvVar2,pvVar4);
  pvVar2 = operator_new(0x4c);
  FUN_002d0994(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  if (((*DAT_003207f8 & 1) == 0) && (iVar3 = __cxa_guard_acquire(), iVar3 != 0)) {
    FUN_00666e84(DAT_003207b8,DAT_003207d4);
    __cxa_guard_release(DAT_003207f8);
    __aeabi_atexit(DAT_003207b8,DAT_003207c4,DAT_003207c8);
  }
  FUN_00627ba0(auStack_50,DAT_003207b8);
  iVar10 = param_4[2];
  iVar3 = iVar10 + 1;
  local_4c = pvVar2;
  if (((int)param_4[1] < iVar3) &&
     (uVar12 = iVar3 + iVar3 / 2 + 8U & 0xfffffff8, param_4[1] != uVar12)) {
    pvVar4 = (void *)*param_4;
    if ((int)uVar12 < 1) {
      free(pvVar4);
      iVar10 = param_4[2];
      pvVar4 = (void *)0x0;
      param_4[1] = uVar12;
      *param_4 = 0;
      iVar3 = iVar10 + 1;
    }
    else {
      if (pvVar4 == (void *)0x0) {
        pvVar4 = malloc(uVar12 << 3);
        *param_4 = pvVar4;
      }
      else {
        pvVar4 = realloc(pvVar4,uVar12 << 3);
        iVar10 = param_4[2];
        iVar3 = iVar10 + 1;
        *param_4 = pvVar4;
      }
      param_4[1] = uVar12;
    }
  }
  else {
    pvVar4 = (void *)*param_4;
  }
  pvVar4 = (void *)((int)pvVar4 + iVar10 * 8);
  param_4[2] = iVar3;
  if (pvVar4 != (void *)0x0) {
    FUN_00627ba0(pvVar4,auStack_50);
    *(void **)((int)pvVar4 + 4) = local_4c;
  }
  FUN_006280c8(auStack_50);
  param_5[3] = pvVar2;
  pvVar2 = operator_new(0x2c);
  FUN_002d50bc(pvVar2,param_2);
  FUN_0032a908(iVar11,pvVar2);
  if (((*DAT_003207e8 & 1) == 0) && (iVar3 = __cxa_guard_acquire(), iVar3 != 0)) {
    FUN_00666e84(DAT_003207bc,DAT_003207e0);
    __cxa_guard_release(DAT_003207e8);
    __aeabi_atexit(DAT_003207bc,DAT_003207c4,DAT_003207c8);
  }
  FUN_00627ba0(auStack_48,DAT_003207bc);
  iVar10 = param_4[2];
  iVar3 = iVar10 + 1;
  local_44 = pvVar2;
  if (((int)param_4[1] < iVar3) &&
     (uVar12 = iVar3 + iVar3 / 2 + 8U & 0xfffffff8, param_4[1] != uVar12)) {
    pvVar4 = (void *)*param_4;
    if ((int)uVar12 < 1) {
      free(pvVar4);
      iVar10 = param_4[2];
      pvVar4 = (void *)0x0;
      param_4[1] = uVar12;
      *param_4 = 0;
      iVar3 = iVar10 + 1;
    }
    else {
      if (pvVar4 == (void *)0x0) {
        pvVar4 = malloc(uVar12 << 3);
        *param_4 = pvVar4;
      }
      else {
        pvVar4 = realloc(pvVar4,uVar12 << 3);
        iVar10 = param_4[2];
        iVar3 = iVar10 + 1;
        *param_4 = pvVar4;
      }
      param_4[1] = uVar12;
    }
  }
  else {
    pvVar4 = (void *)*param_4;
  }
  pvVar4 = (void *)((int)pvVar4 + iVar10 * 8);
  param_4[2] = iVar3;
  if (pvVar4 != (void *)0x0) {
    FUN_00627ba0(pvVar4,auStack_48);
    *(void **)((int)pvVar4 + 4) = local_44;
  }
  FUN_006280c8(auStack_48);
  param_5[4] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002d9f7c(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[5] = pvVar2;
  pvVar2 = operator_new(0x9c);
  FUN_002e7098(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[10] = pvVar2;
  pvVar2 = operator_new(0xd4);
  FUN_002ce710(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0xe] = pvVar2;
  pvVar2 = operator_new(0xd4);
  FUN_002cd984(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0xd] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002c8160(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x10] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002c7488(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0xf] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002ca8fc(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x12] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002cb530(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x11] = pvVar2;
  pvVar2 = operator_new(0xd4);
  FUN_002c9a7c(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x14] = pvVar2;
  pvVar2 = operator_new(0xd4);
  FUN_002c8cf0(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x13] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002db538(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x15] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002c2ed4(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x16] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002c3bac(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x17] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002c15d4(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x18] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002c22a0(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x19] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002cc11c(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0xb] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002ccdf4(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0xc] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002bec5c(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x1a] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002d0104(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x1b] = pvVar2;
  pvVar2 = operator_new(0xb8);
  FUN_002cf414(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x1c] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002bf83c(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x1d] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002be028(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x1e] = pvVar2;
  pvVar2 = operator_new(0xd4);
  FUN_002bd1a8(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x1f] = pvVar2;
  pvVar2 = operator_new(0xd4);
  FUN_002d7ce8(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[7] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002dfb9c(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[8] = pvVar2;
  pvVar2 = operator_new(0xd4);
  FUN_002e0aa8(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[9] = pvVar2;
  pvVar2 = operator_new(0xf4);
  FUN_002d8760(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x20] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002e1f24(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[6] = pvVar2;
  pvVar2 = operator_new(0xf4);
  FUN_002e5468(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x21] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002e44cc(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x22] = pvVar2;
  pvVar2 = operator_new(0x48);
  FUN_002bb048(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x2b] = pvVar2;
  pvVar2 = operator_new(0xd4);
  FUN_002bbeec(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x2c] = pvVar2;
  pvVar2 = operator_new(100);
  FUN_002bb528(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x2d] = pvVar2;
  pvVar2 = operator_new(0xc0);
  FUN_002b8940(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x2e] = pvVar2;
  pvVar2 = operator_new(0xc0);
  FUN_002ba3a0(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x2f] = pvVar2;
  pvVar2 = operator_new(0xb8);
  FUN_002e2ae4(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x23] = pvVar2;
  pvVar2 = operator_new(0x9c);
  FUN_002dabdc(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x24] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002deb8c(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x25] = pvVar2;
  pvVar2 = operator_new(0xf4);
  FUN_002dbeec(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x26] = pvVar2;
  pvVar2 = operator_new(0xf0);
  FUN_002dd2cc(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x27] = pvVar2;
  pvVar2 = operator_new(0xd8);
  FUN_002e61ec(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x28] = pvVar2;
  pvVar2 = operator_new(0x9c);
  FUN_002c4edc(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x29] = pvVar2;
  pvVar2 = operator_new(0x80);
  FUN_002c5370(pvVar2,param_2,*(undefined4 *)(param_1 + 0x44));
  FUN_0032a908(iVar11,pvVar2);
  param_5[0x2a] = pvVar2;
  return;
}

