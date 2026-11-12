/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_00787364(undefined4 *param_1,int *param_2,int param_3,undefined1 *param_4)

{
  int iVar1;
  int iVar2;
  void *pvVar3;
  undefined4 uVar4;
  void *pvVar5;
  uint uVar6;
  int *piVar7;
  int iVar8;
  int iVar9;
  int iVar10;
  int local_50;
  undefined1 auStack_4c [4];
  undefined1 auStack_48 [4];
  undefined1 auStack_44 [4];
  void *local_40;
  int local_3c;
  int local_38;
  uint local_34;
  undefined1 auStack_2c [8];
  
  iVar1 = param_2[5] + -1;
  iVar2 = iVar1 * 4;
  while( true ) {
    if (iVar1 < 0) {
      return;
    }
    piVar7 = *(int **)(param_2[3] + iVar2);
    iVar2 = iVar2 + -4;
    if (param_3 == *piVar7) break;
    iVar1 = iVar1 + -1;
  }
  local_50 = param_3;
  FUN_0062ab18(auStack_4c,piVar7 + 1);
  FUN_0062ab18(auStack_48,piVar7 + 2);
  FUN_0062ab18(auStack_44,piVar7 + 3);
  iVar1 = piVar7[6];
  local_40 = (void *)0x0;
  local_3c = 0;
  iVar8 = piVar7[6];
  iVar2 = local_3c;
  local_38 = iVar1;
  if ((iVar8 != 0) && (iVar2 = iVar8, 0 < iVar8)) {
    local_40 = malloc(iVar8 * 0xc);
  }
  local_3c = iVar2;
  if (0 < iVar1) {
    iVar10 = piVar7[4];
    iVar8 = 0;
    iVar2 = 0;
    pvVar3 = local_40;
    do {
      if (pvVar3 != (void *)0x0) {
        iVar9 = iVar10 + iVar8;
        *(undefined4 *)((int)local_40 + iVar8) = *(undefined4 *)(iVar10 + iVar8);
        *(undefined4 *)((int)pvVar3 + 4) = *(undefined4 *)(iVar9 + 4);
        *(undefined4 *)((int)pvVar3 + 8) = *(undefined4 *)(iVar9 + 8);
      }
      iVar2 = iVar2 + 1;
      pvVar3 = (void *)((int)pvVar3 + 0xc);
      iVar8 = iVar8 + 0xc;
    } while (iVar2 != iVar1);
  }
  local_34 = piVar7[7];
  iVar2 = (**(code **)(*param_2 + 0xc))(param_2,param_3);
  if (iVar2 == 0) {
    piVar7 = (int *)0x0;
    if ((*DAT_00787668 == 0) ||
       (iVar2 = __dynamic_cast(*DAT_00787668,DAT_0078766c,DAT_00787670,0), iVar2 == 0))
    goto LAB_007874c4;
    iVar2 = iVar2 + 0x10;
  }
  piVar7 = (int *)FUN_00781a04(iVar2,param_3);
  if (piVar7 != (int *)0x0) {
    local_50 = param_3;
    (**(code **)(*piVar7 + 0x10))(piVar7,param_3,&local_50);
  }
LAB_007874c4:
  iVar2 = FUN_007f0fd4(param_4);
  if (iVar2 == 0) {
    param_4 = auStack_4c;
  }
  FUN_006c1630(auStack_2c,DAT_00787664);
  pvVar3 = operator_new(0x20);
  if ((piVar7 == (int *)0x0) || ((local_34 & 1) != 0)) {
    uVar4 = 0;
  }
  else {
    uVar4 = 1;
  }
  FUN_00786ae8(pvVar3,param_3,param_4,uVar4,(local_34 & 3) >> 1,0,auStack_2c,0,0,0,param_2);
  iVar1 = param_1[2];
  iVar2 = iVar1 + 1;
  if (((int)param_1[1] < iVar2) &&
     (uVar6 = iVar2 + iVar2 / 2 + 8U & 0xfffffff8, param_1[1] != uVar6)) {
    pvVar5 = (void *)*param_1;
    if ((int)uVar6 < 1) {
      free(pvVar5);
      iVar1 = param_1[2];
      pvVar5 = (void *)0x0;
      param_1[1] = uVar6;
      *param_1 = 0;
      iVar2 = iVar1 + 1;
    }
    else {
      if (pvVar5 == (void *)0x0) {
        pvVar5 = malloc(uVar6 << 2);
        *param_1 = pvVar5;
      }
      else {
        pvVar5 = realloc(pvVar5,uVar6 << 2);
        iVar1 = param_1[2];
        iVar2 = iVar1 + 1;
        *param_1 = pvVar5;
      }
      param_1[1] = uVar6;
    }
  }
  else {
    pvVar5 = (void *)*param_1;
  }
  param_1[2] = iVar2;
  *(void **)((int)pvVar5 + iVar1 * 4) = pvVar3;
  FUN_006a0280(auStack_2c);
  free(local_40);
  FUN_00627f38(auStack_44);
  FUN_00627f38(auStack_48);
  FUN_00627f38(auStack_4c);
  return;
}

