/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0038aa4c(int param_1,undefined4 param_2)

{
  int iVar1;
  undefined1 auStack_14 [8];
  
  if (*(int *)(param_1 + 0x88) == 0) {
    iVar1 = FUN_006c2058(param_1 + 0x8c);
    if (iVar1 == 0) {
      FUN_006c1630(auStack_14,param_1 + 0x8c);
      FUN_0070c1a8(param_2,auStack_14);
      FUN_006a0280(auStack_14);
    }
  }
  else {
    FUN_006d1844(param_2,param_1 + 0x88,0,0,0);
  }
  return;
}

