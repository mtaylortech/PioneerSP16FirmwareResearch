/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00790630(int param_1)

{
  int iVar1;
  undefined8 local_18;
  undefined8 local_10;
  
  local_18 = 0;
  local_10 = *(undefined8 *)(param_1 + 0x18);
  if (((*(byte *)(param_1 + 0x68) & 2) != 0) &&
     ((*(int **)(param_1 + 0x40) == (int *)0x0 ||
      (iVar1 = (**(code **)(**(int **)(param_1 + 0x40) + 0xc))(), iVar1 != 0)))) {
    FUN_0078f8d8(param_1,&local_18);
  }
  return;
}

