/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_007fd958(int param_1,undefined4 *param_2)

{
  undefined8 uVar1;
  undefined4 uVar2;
  float extraout_r0;
  float extraout_r0_00;
  float extraout_r0_01;
  undefined8 *puVar3;
  undefined8 *puVar4;
  undefined8 *puVar5;
  int iVar6;
  code *pcVar7;
  int iVar8;
  int *__ptr;
  int iVar9;
  uint uVar10;
  uint in_fpscr;
  float __x;
  float fVar11;
  int iVar12;
  float fVar13;
  float fVar14;
  float fVar15;
  undefined1 auStack_f8 [36];
  undefined1 auStack_d4 [36];
  undefined1 auStack_b0 [24];
  undefined1 auStack_98 [24];
  undefined8 local_80;
  int local_78;
  int iStack_74;
  int local_70;
  int local_6c;
  int local_68;
  int local_64;
  undefined8 *local_60;
  undefined4 local_5c;
  int local_58;
  int *local_54 [3];
  undefined1 auStack_48 [4];
  undefined1 auStack_44 [4];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [8];
  
  uVar2 = (**(code **)(*(int *)*param_2 + 0x14))();
  iVar8 = *(int *)(param_1 + 0x14);
  iVar6 = *(int *)(iVar8 + 0x18);
  iVar9 = *(int *)(iVar8 + 0x1c);
  uVar1 = *(undefined8 *)(iVar8 + 0x18);
  fVar15 = (float)VectorSignedToFloat(iVar6,(byte)(in_fpscr >> 0x16) & 3);
  *(undefined4 *)(param_1 + 0x18) = uVar2;
  fVar14 = (float)VectorSignedToFloat(iVar9,(byte)(in_fpscr >> 0x16) & 3);
  fVar11 = floorf(__x);
  iVar12 = (int)extraout_r0;
  fVar11 = ceilf(fVar11);
  ceilf(fVar11);
  local_80 = CONCAT44(iVar12,iVar12);
  local_78 = (int)extraout_r0_00 - iVar12;
  iStack_74 = (int)extraout_r0_01 - iVar12;
  iVar12 = param_1 + 4;
  if (*(int *)(param_1 + 4) == 0) {
LAB_007fda48:
    uVar10 = -((int)((uint)*(byte *)(iVar8 + 0x68) << 0x1d) >> 0x1f);
    iVar6 = local_78;
    if (local_78 < 1) {
      iVar6 = 1;
    }
    if (uVar10 == 0) {
      uVar2 = 2;
    }
    else {
      uVar2 = 1;
    }
    iVar8 = iStack_74;
    if (iStack_74 < 1) {
      iVar8 = 1;
    }
    FUN_006d3188(auStack_48,uVar2,iVar6,iVar8,uVar10 ^ 1);
    FUN_006d3310(iVar12,auStack_48);
    FUN_00707778(auStack_48);
    *(undefined4 *)(param_1 + 0x10) = 0;
  }
  else {
    FUN_006d3380(&local_70,iVar12);
    if (((((int)local_80 != local_70) || (local_80._4_4_ != local_6c)) || (local_68 != local_78)) ||
       (local_64 != iStack_74)) {
      iVar8 = *(int *)(param_1 + 0x14);
      goto LAB_007fda48;
    }
    iVar8 = *(int *)(param_1 + 0x10);
    if (iVar8 < 2) {
      if (iVar8 == 1) {
        __ptr = *(int **)(param_1 + 8);
        if (((*__ptr < 1) && (__ptr[1] < 1)) &&
           ((iVar6 <= *__ptr + __ptr[2] && (iVar9 <= __ptr[1] + __ptr[3])))) goto LAB_007fdb30;
      }
    }
    else {
      local_60 = (undefined8 *)0x0;
      local_5c = 0;
      local_58 = 0;
      if ((0 < iVar6) && (0 < iVar9)) {
        local_60 = malloc(0x80);
        local_5c = 8;
        local_58 = 1;
        if (local_60 == (undefined8 *)0x0) {
          iVar8 = *(int *)(param_1 + 0x10);
        }
        else {
          iVar8 = *(int *)(param_1 + 0x10);
          *local_60 = 0;
          local_60[1] = uVar1;
        }
      }
      iVar8 = iVar8 + -1;
      iVar6 = iVar8 * 0x10;
      for (; -1 < iVar8; iVar8 = iVar8 + -1) {
        iVar9 = *(int *)(param_1 + 8) + iVar6;
        iVar6 = iVar6 + -0x10;
        FUN_004ff798(&local_60,iVar9);
        if (local_58 == 0) {
          free(local_60);
          __ptr = *(int **)(param_1 + 8);
          goto LAB_007fdb30;
        }
      }
      free(local_60);
    }
  }
  FUN_006cf768(local_54,iVar12);
  iVar6 = *(int *)(param_1 + 8);
  iVar8 = iVar6 + *(int *)(param_1 + 0x10) * 0x10;
  for (; iVar6 != iVar8; iVar6 = iVar6 + 0x10) {
    (**(code **)(*local_54[0] + 0x20))(local_54[0],iVar6);
  }
  if ((*(byte *)(*(int *)(param_1 + 0x14) + 0x68) & 4) == 0) {
    pcVar7 = *(code **)(*local_54[0] + 0x48);
    FUN_006c1630(auStack_44,DAT_007fdd28);
    FUN_006c5848(auStack_f8,auStack_44);
    (*pcVar7)(local_54[0],auStack_f8);
    FUN_007079a8(auStack_f8);
    FUN_006a0280(auStack_44);
    (**(code **)(*local_54[0] + 0x54))(local_54[0],&local_80,1);
    pcVar7 = *(code **)(*local_54[0] + 0x48);
    FUN_006c1630(auStack_40,DAT_007fdd2c);
    FUN_006c5848(auStack_d4,auStack_40);
    (*pcVar7)(local_54[0],auStack_d4);
    FUN_007079a8(auStack_d4);
    FUN_006a0280(auStack_40);
  }
  pcVar7 = *(code **)(*local_54[0] + 0x10);
  FUN_006c67fc(auStack_b0,*(undefined4 *)(param_1 + 0x18));
  (*pcVar7)(local_54[0],auStack_b0);
  FUN_00789950(*(undefined4 *)(param_1 + 0x14),local_54,1);
  FUN_006cf7b8(local_54);
  __ptr = *(int **)(param_1 + 8);
LAB_007fdb30:
  iVar8 = iStack_74;
  iVar6 = local_78;
  if ((local_78 < 1) || (iStack_74 < 1)) {
    puVar4 = (undefined8 *)0x0;
    puVar3 = puVar4;
    puVar5 = puVar4;
  }
  else {
    puVar3 = malloc(0x80);
    if (puVar3 == (undefined8 *)0x0) {
      puVar4 = (undefined8 *)&DAT_00000008;
      puVar5 = (undefined8 *)0x1;
    }
    else {
      puVar4 = (undefined8 *)&DAT_00000008;
      *puVar3 = local_80;
      puVar3[1] = CONCAT44(iVar8,iVar6);
      puVar5 = (undefined8 *)0x1;
    }
  }
  *(undefined8 **)(param_1 + 8) = puVar3;
  *(undefined8 **)(param_1 + 0xc) = puVar4;
  *(undefined8 **)(param_1 + 0x10) = puVar5;
  free(__ptr);
  fVar11 = (float)VectorSignedToFloat(0xff - (uint)*(byte *)(*(int *)(param_1 + 0x14) + 0x6c),
                                      (byte)(in_fpscr >> 0x16) & 3);
  FUN_006c20c8(auStack_3c,DAT_007fdd2c,fVar11 / DAT_007fdd24);
  FUN_0070acf0(param_2,auStack_3c);
  FUN_006a0280(auStack_3c);
  fVar11 = (float)VectorSignedToFloat(local_78,(byte)(in_fpscr >> 0x16) & 3);
  fVar13 = (float)VectorSignedToFloat(iStack_74,(byte)(in_fpscr >> 0x16) & 3);
  FUN_006c67dc(auStack_98,fVar15 / fVar11,fVar14 / fVar13);
  FUN_006d1bcc(param_2,iVar12,auStack_98,0);
  return;
}

