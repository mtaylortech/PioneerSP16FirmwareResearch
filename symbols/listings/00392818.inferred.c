/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void candidate_00392818(int param_1,undefined4 param_2)

{
  int iVar1;
  int iStack_30;
  int iStack_2c;
  int iStack_28;
  int iStack_24;
  int iStack_20;
  int iStack_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  
  if ((*(int *)(param_1 + 0xa8) != 0) && (iVar1 = FUN_00761e8c(), iVar1 != 0)) {
    FUN_0076165c(&iStack_30,param_1);
    FUN_007649e0(&iStack_20,param_2);
    if (iStack_30 <= iStack_20) {
      if (((iStack_2c <= iStack_1c) && (iStack_20 < iStack_30 + iStack_28)) &&
         (iStack_1c < iStack_2c + iStack_24)) {
        uStack_18 = *DAT_003928dc;
        uStack_14 = DAT_003928dc[1];
        FUN_00394614(param_1 + 0xa0,uStack_18,uStack_14,param_1 + 0x98);
      }
    }
    iVar1 = FUN_0078e78c(param_1);
    if (iVar1 != 0) {
      FUN_00790630(param_1);
    }
  }
  return;
}

