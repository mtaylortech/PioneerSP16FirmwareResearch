/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0026c654(int param_1,int param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 extraout_r1;
  undefined4 extraout_r2;
  undefined4 extraout_r2_00;
  undefined4 uVar3;
  
  FUN_002ebd38();
  if (param_2 != 0) {
    FUN_0026c238(param_1,extraout_r1,extraout_r2,param_4);
    return;
  }
  FUN_00697918(param_1 + 0x114);
  iVar1 = FUN_002ee9fc(param_1);
  if (*(int *)(param_1 + 0x6b0) != iVar1) {
    return;
  }
  FUN_002ee918(param_1);
  uVar3 = *(undefined4 *)(param_1 + 0x128);
  uVar2 = (**(code **)(**(int **)(param_1 + 0x6b0) + 0x14))();
  FUN_007c1644(uVar3,uVar2,extraout_r2_00,param_4);
  return;
}

