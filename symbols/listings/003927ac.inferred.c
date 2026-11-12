/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void candidate_003927ac(int param_1)

{
  int iVar1;
  
  if ((*(int *)(param_1 + 0xa8) != 0) && (iVar1 = FUN_00761e8c(), iVar1 != 0)) {
    FUN_00394614(param_1 + 0xa0,*DAT_00392814,DAT_00392814[1],param_1 + 0x98);
    iVar1 = FUN_0078e78c(param_1);
    if (iVar1 != 0) {
      FUN_00790630(param_1);
      return;
    }
  }
  return;
}

