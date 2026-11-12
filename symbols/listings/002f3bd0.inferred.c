/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_002f3bd0(undefined4 param_1,undefined4 param_2)

{
  int *piVar1;
  int iVar2;
  
  piVar1 = (int *)FUN_0032b664();
  piVar1 = (int *)(**(code **)(*piVar1 + 0x10))(piVar1,param_2);
  if ((piVar1 == (int *)0x0) || (((uint)piVar1 & 3) != 0)) {
    FUN_004f782c(DAT_002f3c54,DAT_002f3c50,DAT_002f3c58);
    return 0;
  }
  iVar2 = (**(code **)(*piVar1 + 0x40))();
  if (iVar2 == 0) {
    return 0;
  }
  if (iVar2 == 1) {
    return 1;
  }
  if (iVar2 == 2) {
    return 2;
  }
  FUN_004f7534(DAT_002f3c4c,DAT_002f3c50);
  return 0;
}

