/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0079b524(int *param_1,uint param_2)

{
  int *piVar1;
  int iVar2;
  undefined8 local_48;
  undefined8 local_40;
  undefined1 auStack_38 [16];
  int local_28 [2];
  int local_20 [3];
  
  if ((*(byte *)(param_1 + 0x1a) & 3) >> 1 != param_2) {
    FUN_007fd748(local_28,param_1);
    *(byte *)(param_1 + 0x1a) = *(byte *)(param_1 + 0x1a) & 0xfd | (byte)((param_2 & 1) << 1);
    if (param_2 == 0) {
      iVar2 = param_1[3];
      if (iVar2 != 0) {
        local_40 = *(undefined8 *)(param_1 + 6);
        local_48 = 0;
        FUN_0078f660(auStack_38,param_1,&local_48);
        FUN_0078fb14(iVar2,auStack_38);
      }
    }
    else {
      FUN_00790630(param_1);
    }
    iVar2 = FUN_0078ca5c();
    if ((*(uint *)(**(int **)(*(int *)(iVar2 + 0x20) + 0x14) + 0x20) & 0x70) == 0) {
      FUN_00699b64();
    }
    if (param_2 == 0) {
      if ((int *)param_1[0x10] != (int *)0x0) {
        (**(code **)(*(int *)param_1[0x10] + 0x14))();
      }
      for (piVar1 = *(int **)(DAT_0079b764 + 100); piVar1 != param_1; piVar1 = (int *)piVar1[3]) {
        if (piVar1 == (int *)0x0) goto LAB_0079b624;
      }
      if (param_1[3] == 0) {
        FUN_0078d3d8(1);
      }
      else {
        FUN_0079ad8c(param_1[3],2,1);
      }
    }
LAB_0079b624:
    if ((local_28[0] != 0) && (*(int *)(local_28[0] + 8) != 0)) {
      FUN_007fd748(local_20,param_1);
      (**(code **)(*param_1 + 0x30))(param_1);
      if ((local_20[0] != 0) && (*(int *)(local_20[0] + 8) != 0)) {
        iVar2 = param_1[0x15];
        while ((*(int *)(local_20[0] + 8) != 0 && (0 < iVar2))) {
          iVar2 = iVar2 + -1;
          if (((param_1[0x15] <= iVar2) && (iVar2 = param_1[0x15] + -1, iVar2 < 0)) ||
             (piVar1 = *(int **)(param_1[0x13] + iVar2 * 4),
             (**(code **)(*piVar1 + 0x10))(piVar1,param_1), local_20[0] == 0)) break;
        }
      }
      FUN_00607cf4();
      if ((((local_28[0] != 0) && (*(int *)(local_28[0] + 8) != 0)) &&
          ((*(byte *)(param_1 + 0x1a) & 1) != 0)) &&
         (piVar1 = (int *)FUN_0078ddc8(param_1), piVar1 != (int *)0x0)) {
        (**(code **)(*piVar1 + 0xc))(piVar1,param_2);
        FUN_007894fc(param_1);
      }
    }
    FUN_00607cf4(local_28[0]);
  }
  return;
}

