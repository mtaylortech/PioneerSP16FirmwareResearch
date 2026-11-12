/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_002f3b40(int param_1)

{
  int *piVar1;
  int iVar2;
  undefined4 uVar3;
  
  uVar3 = *(undefined4 *)(*(int *)(param_1 + 4) + 0x54);
  piVar1 = (int *)FUN_0032b664();
  piVar1 = (int *)(**(code **)(*piVar1 + 0x10))(piVar1,uVar3);
  if ((piVar1 == (int *)0x0) || (((uint)piVar1 & 3) != 0)) {
    FUN_004f782c(DAT_002f3bc8,DAT_002f3bc4,DAT_002f3bcc);
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
  FUN_004f7534(DAT_002f3bc0,DAT_002f3bc4);
  return 0;
}

