/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0026c6c8(int param_1)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  
  iVar1 = FUN_002ee9fc();
  if (*(int *)(param_1 + 0x6b0) != iVar1) {
    return;
  }
  FUN_002ee918(param_1);
  uVar3 = *(undefined4 *)(param_1 + 0x128);
  uVar2 = (**(code **)(**(int **)(param_1 + 0x6b0) + 0x14))();
  FUN_007c1644(uVar3,uVar2);
  return;
}

