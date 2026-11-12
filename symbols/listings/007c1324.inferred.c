/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int * FUN_007c1324(int param_1,uint param_2,int param_3,int param_4)

{
  char cVar1;
  int iVar2;
  void *__dest;
  undefined4 uVar3;
  uint uVar4;
  int *piVar5;
  int *piVar6;
  int *piVar7;
  undefined8 local_48;
  undefined8 local_40;
  undefined1 auStack_38 [16];
  int local_28 [2];
  
  uVar4 = *(uint *)(param_1 + 0x30);
  if (uVar4 <= param_2) {
    return (int *)0x0;
  }
  piVar6 = *(int **)(*(int *)(param_1 + 0x28) + param_2 * 4);
  if (piVar6 == (int *)0x0) {
    return (int *)0x0;
  }
  piVar7 = piVar6;
  if (param_3 == 0) {
LAB_007c1368:
    param_3 = 0;
  }
  else {
    do {
      if ((*(byte *)(piVar7 + 0x1a) & 2) == 0) goto LAB_007c1368;
      piVar7 = (int *)piVar7[3];
    } while (piVar7 != (int *)0x0);
    piVar7 = (int *)FUN_0078ddc8();
    if ((piVar7 == (int *)0x0) || (cVar1 = (**(code **)(*piVar7 + 0x38))(), cVar1 == '\x01')) {
      uVar4 = *(uint *)(param_1 + 0x30);
      goto LAB_007c1368;
    }
    iVar2 = FUN_0078ca5c();
    if ((*(uint *)(**(int **)(*(int *)(iVar2 + 0x20) + 0x14) + 0x20) & 0x70) == 0) {
      FUN_00699b64();
    }
    if (((*(byte *)(piVar6 + 0x1a) & 2) == 0) || (iVar2 = piVar6[3], iVar2 == 0)) {
      uVar4 = *(uint *)(param_1 + 0x30);
    }
    else {
      local_40 = *(undefined8 *)(piVar6 + 6);
      local_48 = 0;
      FUN_0078f660(auStack_38,piVar6,&local_48);
      FUN_0078fb14(iVar2,auStack_38);
      uVar4 = *(uint *)(param_1 + 0x30);
    }
  }
  if (param_2 < uVar4) {
    iVar2 = uVar4 - 1;
    *(int *)(param_1 + 0x30) = iVar2;
    if (0 < (int)(iVar2 - param_2)) {
      __dest = (void *)(*(int *)(param_1 + 0x28) + param_2 * 4);
      memmove(__dest,(void *)((int)__dest + 4),(iVar2 - param_2) * 4);
      iVar2 = *(int *)(param_1 + 0x30);
    }
    if ((iVar2 << 1 & ~((iVar2 << 1) >> 0x1f)) < *(int *)(param_1 + 0x2c)) {
      if (iVar2 < 0x10) {
        iVar2 = 0x10;
      }
      if (iVar2 < *(int *)(param_1 + 0x2c)) {
        FUN_0080b4dc(param_1 + 0x28);
      }
    }
  }
  piVar6[3] = 0;
  if ((int *)piVar6[0x10] != (int *)0x0) {
    (**(code **)(*(int *)piVar6[0x10] + 0x14))();
  }
  iVar2 = DAT_007c1634;
  piVar7 = *(int **)(DAT_007c1634 + 100);
  if (piVar7 != piVar6) {
    if (piVar7 == (int *)0x0) goto LAB_007c1450;
    for (piVar5 = (int *)piVar7[3]; piVar6 != piVar5; piVar5 = (int *)piVar5[3]) {
      if (piVar5 == (int *)0x0) goto LAB_007c1450;
    }
  }
  if (param_3 == 0) {
    if ((param_4 == 0) && (piVar7 == piVar6)) {
      *(undefined4 *)(DAT_007c1634 + 100) = 0;
    }
    else {
      *(undefined4 *)(DAT_007c1634 + 100) = 0;
      if (piVar7 != (int *)0x0) {
        FUN_007fd748(local_28,piVar7);
        (**(code **)(*piVar7 + 0x7c))(piVar7,2);
        if ((local_28[0] != 0) && (*(int *)(local_28[0] + 8) != 0)) {
          FUN_0078b3fc(piVar7,2,local_28);
        }
        FUN_00607cf4(local_28[0]);
      }
    }
    iVar2 = FUN_0078ca5c();
    FUN_00699b64(iVar2 + 0x18);
  }
  else {
    FUN_007fd748(local_28,param_1);
    if (param_4 == 0) {
      uVar3 = 0;
      if (*(int **)(iVar2 + 100) != piVar6) {
        uVar3 = 1;
      }
    }
    else {
      uVar3 = 1;
    }
    FUN_0078d3d8(uVar3);
    if ((local_28[0] == 0) || (*(int *)(local_28[0] + 8) == 0)) {
      FUN_00607cf4();
      return piVar6;
    }
    FUN_0079ad8c(param_1,2,1);
    FUN_00607cf4(local_28[0]);
  }
LAB_007c1450:
  if (param_4 != 0) {
    FUN_007894fc(piVar6);
  }
  if (param_3 != 0) {
    FUN_00789604(param_1);
  }
  return piVar6;
}

