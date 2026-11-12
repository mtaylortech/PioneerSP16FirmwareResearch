/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 *
FUN_004c8d3c(undefined4 *param_1,undefined4 *param_2,int *param_3,undefined4 param_4,
            undefined4 *param_5)

{
  byte bVar1;
  undefined4 uVar2;
  void *pvVar3;
  uint uVar4;
  int iVar5;
  uint uVar6;
  undefined4 uVar7;
  uint uVar8;
  uint uVar9;
  byte *pbVar10;
  undefined1 auStack_58 [4];
  undefined1 auStack_54 [4];
  undefined1 auStack_50 [4];
  undefined1 auStack_4c [4];
  undefined1 auStack_48 [4];
  undefined1 auStack_44 [4];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [8];
  
  FUN_006c1630(auStack_58,DAT_004c914c);
  FUN_0039173c(param_1,param_2 + 1,param_4,0,auStack_58);
  FUN_006a0280(auStack_58);
  uVar2 = DAT_004c9154;
  iVar5 = DAT_004c9150;
  *param_1 = *param_2;
  param_1[0x1c] = iVar5;
  param_1[0x25] = iVar5 + 0x10;
  uVar7 = param_2[7];
  *(undefined1 *)(param_1 + 0x2b) = 0;
  param_1[0x2c] = 0;
  param_1[0x26] = uVar7;
  param_1[0x2d] = 0;
  param_1[0x2e] = 0;
  *(undefined1 *)(param_1 + 0x2f) = 0;
  FUN_0062ab18(param_1 + 0x30,uVar2);
  param_1[0x31] = 0xffffffff;
  *(undefined1 *)(param_1 + 0x32) = 1;
  FUN_0062ab08(param_1 + 0x33);
  FUN_0064a3fc(auStack_54,DAT_004c9158);
  FUN_006c1630(auStack_50,DAT_004c914c);
  FUN_006c1630(auStack_4c,DAT_004c914c);
  pvVar3 = operator_new(0xd4);
  FUN_0038e434(pvVar3,auStack_54,auStack_50,auStack_4c);
  param_1[0x34] = pvVar3;
  FUN_007cbf98(param_1,pvVar3,0xffffffff);
  FUN_006a0280(auStack_4c);
  FUN_006a0280(auStack_50);
  FUN_00627f38(auStack_54);
  (**(code **)(*(int *)param_1[0x34] + 0x2c))((int *)param_1[0x34],0);
  FUN_0064a3fc(auStack_48,DAT_004c915c);
  FUN_006c1630(auStack_44,DAT_004c914c);
  FUN_006c1630(auStack_40,DAT_004c914c);
  pvVar3 = operator_new(0xd4);
  FUN_0038e434(pvVar3,auStack_48,auStack_44,auStack_40);
  param_1[0x35] = pvVar3;
  FUN_007ccc24(param_1,pvVar3,0xffffffff);
  FUN_006a0280(auStack_40);
  FUN_006a0280(auStack_44);
  FUN_00627f38(auStack_48);
  FUN_0064a3fc(auStack_3c,DAT_004c9160);
  FUN_0062d868(auStack_38,param_1[0x2e]);
  pvVar3 = operator_new(0xe4);
  FUN_0038e928(pvVar3,auStack_3c,auStack_38);
  param_1[0x36] = pvVar3;
  FUN_007ccc24(param_1,pvVar3,0xffffffff);
  FUN_00627f38(auStack_38);
  FUN_00627f38(auStack_3c);
  if (((*DAT_004c9164 & 1) == 0) && (iVar5 = __cxa_guard_acquire(), iVar5 != 0)) {
    FUN_00666e84(DAT_004c9168,DAT_004c916c);
    __cxa_guard_release(DAT_004c9164);
    __aeabi_atexit(DAT_004c9168,DAT_004c9170,DAT_004c9174);
  }
  FUN_0038fb1c(param_1,param_3,DAT_004c9168,0,0);
  pbVar10 = (byte *)*param_5;
  bVar1 = *pbVar10;
  uVar4 = (uint)bVar1;
  if ((bVar1 & 0x80) != 0) {
    if ((bVar1 & 0x40) == 0) {
      uVar4 = uVar4 & 0x7f;
    }
    else {
      uVar9 = 0x40;
      uVar8 = 0;
      uVar6 = 0x7f;
      do {
        uVar9 = uVar9 >> 1;
        uVar6 = uVar6 >> 1;
        uVar8 = uVar8 + 1;
      } while (0x10 < uVar9 && (uVar9 & uVar4) != 0);
      uVar4 = uVar6 & uVar4;
      if ((uVar8 != 0) && (uVar9 = (uint)pbVar10[1], (uVar9 & 0xc0) == 0x80)) {
        uVar6 = 1;
        do {
          uVar6 = uVar6 + 1;
          uVar4 = uVar9 & 0x3f | uVar4 << 6;
          if (uVar8 < uVar6) break;
          uVar9 = (uint)pbVar10[uVar6];
        } while ((uVar9 & 0xc0) == 0x80);
      }
    }
  }
  if (uVar4 != 0) {
    (**(code **)(*param_3 + 0xc))(auStack_30,param_3);
    FUN_00636894(auStack_2c,param_5);
    FUN_00659dc8(auStack_34,auStack_30,auStack_2c);
    FUN_00620248(param_1 + 0x33,auStack_34);
    FUN_00627f38(auStack_34);
    FUN_00627f38(auStack_30);
  }
  return param_1;
}

