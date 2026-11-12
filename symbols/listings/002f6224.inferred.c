/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_002f6224(undefined4 param_1,undefined4 param_2)

{
  int *piVar1;
  
  piVar1 = (int *)FUN_0032b664();
  piVar1 = (int *)(**(code **)(*piVar1 + 0xa4))(piVar1,8);
  (**(code **)(*piVar1 + 8))(piVar1,param_2);
  return;
}

