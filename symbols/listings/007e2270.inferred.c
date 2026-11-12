/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

void FUN_007e2270(int param_1,int param_2,undefined4 param_3,undefined4 param_4)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  undefined4 uVar5;
  uint uVar6;
  undefined4 local_38;
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [4];
  void *local_28;
  undefined4 local_24;
  undefined4 local_20;
  uint local_1c;
  undefined4 local_10;
  
  iVar2 = *(int *)(param_1 + 0xa4);
  *(undefined4 *)(param_1 + 0xbc) = param_3;
  *(char *)(param_1 + 0xda) = (char)param_4;
  local_10 = param_4;
  if (iVar2 != param_2) {
    if (iVar2 != 0) {
      iVar3 = *(int *)(param_1 + 0x98);
      if (iVar3 != 0) {
        iVar3 = iVar3 + 0x14;
      }
      FUN_00781740(iVar2,iVar3);
    }
    *(int *)(param_1 + 0xa4) = param_2;
    if (param_2 == 0) goto LAB_007e22e0;
    iVar2 = *(int *)(param_1 + 0x98);
    if (iVar2 != 0) {
      iVar2 = iVar2 + 0x14;
    }
    FUN_00781648(param_2,iVar2);
    iVar2 = *(int *)(param_1 + 0xa4);
  }
  if (iVar2 == 0) {
LAB_007e22e0:
    if ((*(byte *)(param_1 + 0x69) & 0x20) == 0) {
      return;
    }
    *(byte *)(param_1 + 0x69) = *(byte *)(param_1 + 0x69) & 0xdf;
    if ((*(int *)(param_1 + 0xc) != 0) && (iVar2 = FUN_00761e8c(), iVar2 == 0)) {
      return;
    }
    FUN_00789188(param_1);
    return;
  }
  if (*(int *)(param_1 + 0xa4) == 0) {
    return;
  }
  local_38 = 0;
  FUN_0062ab08(auStack_34);
  FUN_0062ab08(auStack_30);
  FUN_0062ab08(auStack_2c);
  uVar5 = *(undefined4 *)(param_1 + 0xbc);
  local_28 = (void *)0x0;
  local_24 = 0;
  local_20 = 0;
  local_1c = 0;
  iVar2 = (**(code **)(**(int **)(param_1 + 0xa4) + 0xc))(*(int **)(param_1 + 0xa4),uVar5);
  if (iVar2 == 0) {
    if ((*DAT_007e2264 != 0) &&
       (iVar2 = __dynamic_cast(*DAT_007e2264,DAT_007e2268,DAT_007e226c), iVar2 != 0)) {
      iVar2 = iVar2 + 0x10;
      goto LAB_007e2124;
    }
  }
  else {
LAB_007e2124:
    piVar1 = (int *)FUN_00781a04(iVar2,uVar5);
    if (piVar1 != (int *)0x0) {
      local_38 = uVar5;
      (**(code **)(*piVar1 + 0x10))(piVar1,uVar5,&local_38);
      FUN_00765ce8(param_1,&local_38);
      uVar6 = local_1c;
      uVar4 = (*(byte *)(param_1 + 0x69) & 0x3f) >> 5;
      if ((uVar4 == ((local_1c & 1) == 0)) &&
         ((*(byte *)(param_1 + 0x69) = *(byte *)(param_1 + 0x69) & 0xdf | (byte)((uVar4 ^ 1) << 5),
          *(int *)(param_1 + 0xc) == 0 || (iVar2 = FUN_00761e8c(), iVar2 != 0)))) {
        FUN_00789188(param_1);
        uVar6 = local_1c;
      }
      FUN_007e0580(param_1,(uVar6 & 3) >> 1,0);
      goto LAB_007e2194;
    }
  }
  if (((*(byte *)(param_1 + 0x69) & 0x20) == 0) &&
     ((*(byte *)(param_1 + 0x69) = *(byte *)(param_1 + 0x69) | 0x20, *(int *)(param_1 + 0xc) == 0 ||
      (iVar2 = FUN_00761e8c(), iVar2 != 0)))) {
    FUN_00789188(param_1);
  }
LAB_007e2194:
  free(local_28);
  FUN_00627f38(auStack_2c);
  FUN_00627f38(auStack_30);
  FUN_00627f38(auStack_34);
  return;
}

