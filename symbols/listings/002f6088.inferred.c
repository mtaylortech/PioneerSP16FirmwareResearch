/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_002f6088(undefined4 param_1,undefined4 param_2)

{
  int *piVar1;
  undefined4 uVar2;
  
  piVar1 = (int *)FUN_0032b664();
  piVar1 = (int *)(**(code **)(*piVar1 + 0x10))(piVar1,param_2);
  if (piVar1 == (int *)0x0) {
    return 0;
  }
  piVar1 = (int *)(**(code **)(*piVar1 + 0x30))(piVar1);
  if (piVar1 == (int *)0x0) {
    return 0;
  }
  uVar2 = (**(code **)(*piVar1 + 0x1c))();
  return uVar2;
}

