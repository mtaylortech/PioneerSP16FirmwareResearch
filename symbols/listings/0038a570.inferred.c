/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0038a570(int param_1)

{
  int *piVar1;
  int iVar2;
  uint uVar3;
  
  piVar1 = *(int **)(param_1 + 0x80);
  if (piVar1 == (int *)0x0) {
    return;
  }
  if (((uint)piVar1 & 3) == 0) {
    iVar2 = *(int *)(*piVar1 + -0xc);
    uVar3 = (int)piVar1 + iVar2;
    if (((uVar3 != 0) && ((uVar3 & 3) == 0)) && (*(int *)((int)piVar1 + iVar2) == 0x5e715e28)) {
      (**(code **)(*piVar1 + 8))();
      return;
    }
  }
  FUN_004f782c(DAT_0038a5e0,DAT_0038a5e4,DAT_0038a5e8);
  *(undefined4 *)(param_1 + 0x80) = 0;
  return;
}

